"""Repository context management for long-term memory."""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

if TYPE_CHECKING:
    from hrisa_code.core.ollama_client import OllamaClient


class RepoContext:
    """Manages repository context and HRISA.md file."""

    HRISA_FILE = "HRISA.md"
    MAX_FILE_SIZE = 100_000  # 100KB max for analysis

    def __init__(self, working_directory: Path, ollama_client: Optional["OllamaClient"] = None):
        """Initialize repo context manager.

        Args:
            working_directory: Project directory
            ollama_client: Optional Ollama client for LLM-powered analysis
        """
        self.working_directory = working_directory
        self.hrisa_path = working_directory / self.HRISA_FILE
        self.console = Console()
        self.ollama_client = ollama_client

    def exists(self) -> bool:
        """Check if HRISA.md exists.

        Returns:
            True if HRISA.md exists
        """
        return self.hrisa_path.exists()

    def load(self) -> Optional[str]:
        """Load HRISA.md content.

        Returns:
            Content of HRISA.md or None if not found
        """
        if not self.exists():
            return None

        try:
            return self.hrisa_path.read_text(encoding="utf-8")
        except Exception as e:
            self.console.print(f"[red]Error reading HRISA.md: {e}[/red]")
            return None

    async def inspect_and_generate(self, force: bool = False) -> str:
        """Inspect repository and generate HRISA.md using LLM analysis.

        Args:
            force: Force regeneration even if HRISA.md exists

        Returns:
            Generated HRISA.md content
        """
        if self.exists() and not force:
            self.console.print(
                f"[yellow]HRISA.md already exists. Use --force to regenerate.[/yellow]"
            )
            return self.load() or ""

        # Step 1: Gather repository information with structured extraction
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Extracting structured repository data..."),
            console=self.console,
        ) as progress:
            progress.add_task("inspect", total=None)

            repo_info = {
                "structure": self._analyze_structure(),
                "file_tree": self._generate_file_tree(),
                "key_files": self._analyze_key_files(),
                "code_samples": self._analyze_code_samples(),
                "dependencies": self._analyze_dependencies(),
                "pyproject": self._parse_pyproject_comprehensive(),
                "makefile_commands": self._parse_makefile(),
                "tools": self._extract_tool_definitions(),
                "git_info": self._analyze_git(),
            }

        # Step 2: Use LLM to analyze and generate content
        if self.ollama_client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Asking assistant to analyze repository..."),
                console=self.console,
            ) as progress:
                progress.add_task("analyze", total=None)
                content = await self._llm_generate_hrisa_content(repo_info)
        else:
            # Fallback to simple generation if no LLM available
            content = self._generate_hrisa_content(repo_info)

        # Save to file
        self.hrisa_path.write_text(content, encoding="utf-8")
        self.console.print(f"[green]Generated HRISA.md[/green]")

        return content

    def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze repository structure.

        Returns:
            Structure information
        """
        structure = {
            "root": str(self.working_directory),
            "directories": [],
            "file_types": {},
        }

        # Count files by type
        for path in self.working_directory.rglob("*"):
            # Skip hidden, cache, and build directories
            if any(
                part.startswith(".")
                or part in ["__pycache__", "node_modules", "venv", ".venv", "dist", "build"]
                for part in path.parts
            ):
                continue

            if path.is_file():
                ext = path.suffix or "no_extension"
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
            elif path.is_dir() and path.parent == self.working_directory:
                structure["directories"].append(path.name)

        return structure

    def _analyze_key_files(self) -> Dict[str, str]:
        """Analyze key files in the repository.

        Returns:
            Key file summaries
        """
        key_files = {}

        # Common important files
        important_files = [
            "README.md",
            "README.rst",
            "README.txt",
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "Makefile",
            "docker-compose.yml",
            "Dockerfile",
        ]

        for filename in important_files:
            file_path = self.working_directory / filename
            if file_path.exists() and file_path.stat().st_size < self.MAX_FILE_SIZE:
                try:
                    content = file_path.read_text(encoding="utf-8")
                    # Store full content for LLM analysis
                    key_files[filename] = content
                except Exception:
                    continue

        return key_files

    def _generate_file_tree(self) -> str:
        """Generate directory tree structure.

        Returns:
            Tree structure as string
        """
        try:
            # Try using tree command first
            import subprocess
            result = subprocess.run(
                ['tree', '-L', '3', '-I', '__pycache__|*.pyc|.git|venv|.venv|node_modules|dist|build'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass

        # Fallback: generate tree programmatically
        def build_tree(directory: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> List[str]:
            if current_depth >= max_depth:
                return []

            lines = []
            try:
                items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                # Filter out common excludes
                items = [
                    item for item in items
                    if item.name not in {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'dist', 'build', '.pytest_cache'}
                    and not item.name.endswith('.pyc')
                ]

                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{current_prefix}{item.name}{'/' if item.is_dir() else ''}")

                    if item.is_dir():
                        extension = "    " if is_last else "│   "
                        lines.extend(build_tree(item, prefix + extension, max_depth, current_depth + 1))
            except PermissionError:
                pass

            return lines

        tree_lines = [str(self.working_directory.name) + "/"]
        tree_lines.extend(build_tree(self.working_directory))
        return "\n".join(tree_lines)

    def _parse_makefile(self) -> Dict[str, str]:
        """Parse Makefile to extract commands and descriptions.

        Returns:
            Dict of command -> description
        """
        makefile_path = self.working_directory / "Makefile"
        if not makefile_path.exists():
            return {}

        commands = {}
        try:
            content = makefile_path.read_text(encoding="utf-8")
            current_comment = ""

            for line in content.split("\n"):
                line = line.strip()

                # Capture comment lines
                if line.startswith("#"):
                    current_comment = line.lstrip("# ").strip()
                    continue

                # Capture target lines (make commands)
                if line and not line.startswith("\t") and ":" in line:
                    target = line.split(":")[0].strip()
                    # Skip special targets
                    if not target.startswith(".") and target not in {"PHONY"}:
                        commands[target] = current_comment or "No description"
                        current_comment = ""
        except Exception:
            pass

        return commands

    def _extract_tool_definitions(self) -> List[Dict[str, str]]:
        """Extract tool definitions from code.

        Returns:
            List of tool info dicts
        """
        tools = []
        tool_file = self.working_directory / "src" / "hrisa_code" / "tools" / "file_operations.py"

        if not tool_file.exists():
            return tools

        try:
            content = tool_file.read_text(encoding="utf-8")

            # Look for AVAILABLE_TOOLS dictionary
            if "AVAILABLE_TOOLS" in content:
                # Extract tool names from the dictionary
                import re
                pattern = r'"(\w+)":\s*(\w+Tool)'
                matches = re.findall(pattern, content)

                for tool_name, class_name in matches:
                    # Try to find the tool's description from its get_definition method
                    class_pattern = rf'class {class_name}.*?def get_definition.*?"description":\s*"([^"]+)"'
                    desc_match = re.search(class_pattern, content, re.DOTALL)

                    tools.append({
                        "name": tool_name,
                        "description": desc_match.group(1) if desc_match else "No description available"
                    })
        except Exception:
            pass

        return tools

    def _parse_pyproject_comprehensive(self) -> Dict[str, Any]:
        """Parse pyproject.toml comprehensively.

        Returns:
            Structured project metadata
        """
        pyproject_path = self.working_directory / "pyproject.toml"
        if not pyproject_path.exists():
            return {}

        try:
            import re
            content = pyproject_path.read_text(encoding="utf-8")

            data = {
                "name": "",
                "version": "",
                "description": "",
                "python_version": "",
                "dependencies": [],
                "dev_dependencies": [],
                "scripts": {},
                "tools": {}
            }

            # Extract basic project info
            for line in content.split("\n"):
                if line.startswith("name ="):
                    data["name"] = line.split("=")[1].strip().strip('"')
                elif line.startswith("version ="):
                    data["version"] = line.split("=")[1].strip().strip('"')
                elif line.startswith("description ="):
                    data["description"] = line.split("=")[1].strip().strip('"')
                elif "requires-python" in line:
                    match = re.search(r'[">]=([0-9.]+)', line)
                    if match:
                        data["python_version"] = match.group(1)

            # Extract dependencies
            in_deps = False
            in_dev_deps = False

            for line in content.split("\n"):
                line = line.strip()

                if line == "dependencies = [":
                    in_deps = True
                    in_dev_deps = False
                    continue
                elif "dev = [" in line or "optional-dependencies" in line:
                    in_deps = False
                    in_dev_deps = True
                    continue
                elif line == "]":
                    in_deps = False
                    in_dev_deps = False
                    continue

                if (in_deps or in_dev_deps) and line.startswith('"'):
                    dep = line.strip('",')
                    if in_deps:
                        data["dependencies"].append(dep)
                    else:
                        data["dev_dependencies"].append(dep)

            # Extract scripts
            in_scripts = False
            for line in content.split("\n"):
                if "[project.scripts]" in line:
                    in_scripts = True
                    continue
                elif line.startswith("[") and in_scripts:
                    break

                if in_scripts and "=" in line:
                    parts = line.split("=")
                    if len(parts) == 2:
                        script_name = parts[0].strip()
                        script_path = parts[1].strip().strip('"')
                        data["scripts"][script_name] = script_path

            # Extract tool configuration
            tool_sections = ["black", "ruff", "mypy", "pytest"]
            for tool in tool_sections:
                if f"[tool.{tool}]" in content:
                    data["tools"][tool] = "configured"

            return data
        except Exception:
            return {}

    def _analyze_code_samples(self) -> Dict[str, List[str]]:
        """Analyze code samples from the repository.

        Returns:
            Code samples by language/type
        """
        code_samples = {}

        # Find main source directories
        source_dirs = []
        for name in ["src", "lib", "app", "pkg"]:
            dir_path = self.working_directory / name
            if dir_path.exists() and dir_path.is_dir():
                source_dirs.append(dir_path)

        # If no common source dir, use root
        if not source_dirs:
            source_dirs = [self.working_directory]

        # Collect sample files
        extensions_to_sample = {".py", ".js", ".ts", ".go", ".rs", ".java"}
        samples_per_type = 3

        for source_dir in source_dirs:
            for ext in extensions_to_sample:
                files = list(source_dir.rglob(f"*{ext}"))
                # Filter out test files and common exclude patterns
                files = [
                    f
                    for f in files
                    if not any(
                        part in f.parts
                        for part in ["test", "tests", "__pycache__", "node_modules", ".venv", "venv"]
                    )
                    and f.stat().st_size < self.MAX_FILE_SIZE
                ]

                # Take first N files
                for file_path in files[:samples_per_type]:
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        relative_path = file_path.relative_to(self.working_directory)
                        if ext not in code_samples:
                            code_samples[ext] = []
                        code_samples[ext].append(f"File: {relative_path}\n{content[:2000]}")
                    except Exception:
                        continue

        return code_samples

    def _analyze_dependencies(self) -> Dict[str, List[str]]:
        """Analyze project dependencies.

        Returns:
            Dependencies by ecosystem
        """
        dependencies = {}

        # Python
        pyproject = self.working_directory / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text()
                # Simple extraction - just look for dependency lines
                deps = []
                in_deps = False
                for line in content.split("\n"):
                    if "dependencies = [" in line:
                        in_deps = True
                    elif in_deps:
                        if "]" in line:
                            break
                        if '"' in line:
                            dep = line.strip().strip('",')
                            deps.append(dep)
                if deps:
                    dependencies["python"] = deps
            except Exception:
                pass

        # Node.js
        package_json = self.working_directory / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = list(data.get("dependencies", {}).keys())
                if deps:
                    dependencies["nodejs"] = deps[:10]  # First 10
            except Exception:
                pass

        return dependencies

    def _analyze_git(self) -> Dict[str, Any]:
        """Analyze git repository information comprehensively.

        Returns:
            Git information including history, contributors, recent changes
        """
        git_info = {"is_git_repo": False}

        git_dir = self.working_directory / ".git"
        if not git_dir.exists():
            return git_info

        git_info["is_git_repo"] = True

        try:
            import subprocess

            # Get current branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()

            # Get recent commit history (last 20 commits)
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%h|%an|%ar|%s', '-20'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|', 3)
                        if len(parts) == 4:
                            commits.append({
                                "hash": parts[0],
                                "author": parts[1],
                                "date": parts[2],
                                "message": parts[3]
                            })
                git_info["recent_commits"] = commits

            # Get contributors
            result = subprocess.run(
                ['git', 'shortlog', '-sn', '--all'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                contributors = []
                for line in result.stdout.strip().split('\n')[:10]:  # Top 10
                    if line.strip():
                        parts = line.strip().split('\t', 1)
                        if len(parts) == 2:
                            contributors.append({
                                "commits": int(parts[0]),
                                "name": parts[1]
                            })
                git_info["contributors"] = contributors

            # Get recent file changes
            result = subprocess.run(
                ['git', 'diff', '--stat', 'HEAD~5..HEAD'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                git_info["recent_changes"] = result.stdout.strip()

            # Get total commit count
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                git_info["total_commits"] = int(result.stdout.strip())

        except Exception:
            pass

        return git_info

    async def _llm_generate_hrisa_content(self, repo_info: Dict[str, Any]) -> str:
        """Use LLM to analyze repository and generate HRISA.md content.

        Args:
            repo_info: Repository information

        Returns:
            LLM-generated HRISA.md content
        """
        if not self.ollama_client:
            return self._generate_hrisa_content(repo_info)

        # Build comprehensive prompt with structured data
        prompt_parts = [
            "# HRISA.md Generation Task",
            "",
            "Create a comprehensive project guide (HRISA.md) for AI assistants working on this codebase.",
            "Use ONLY the structured data provided below - be specific, not generic.",
            "",
            "# EXAMPLE REFERENCE (CLAUDE.md style)",
            "",
            "A good HRISA.md looks like this structure:",
            "- Project Overview: 2-3 paragraphs + Key Features list + Tech Stack",
            "- Project Structure: Directory tree WITH specific file descriptions",
            "- Architecture Principles: 6 core principles (Modularity, Async-First, Type Safety, etc.)",
            "- Key Components: Each component with file path and responsibility",
            "- Development Practices: Code Style (Black, Ruff, MyPy) + Testing + Git Workflow",
            "- Common Tasks: Step-by-step with REAL code examples",
            "- Important Files: File paths with one-line descriptions",
            "- Quick Commands: Bash code block with all make commands",
            "- Dependencies: Core + Dev with purposes",
            "- Testing Strategy: Unit/Integration/Manual",
            "- Code Patterns: ACTUAL code from codebase",
            "- Known Limitations: What doesn't work yet",
            "- Future Enhancements: Planned features",
            "- When Making Changes: Before/During/After workflow",
            "- Notes for AI Assistants: Security, Performance, Architecture notes",
            "- Contact & Resources: Links",
            "- Version Information: Current version, Python version, Status",
            "",
            "# STRUCTURED REPOSITORY DATA",
            "",
        ]

        # Project metadata
        pyproject = repo_info.get("pyproject", {})
        if pyproject:
            prompt_parts.extend([
                "## Project Metadata",
                f"- Name: {pyproject.get('name', 'Unknown')}",
                f"- Version: {pyproject.get('version', '0.0.0')}",
                f"- Description: {pyproject.get('description', '')}",
                f"- Python Version: {pyproject.get('python_version', '3.x')}+",
                "",
            ])

        # File tree
        if repo_info.get("file_tree"):
            prompt_parts.extend([
                "## Directory Structure",
                "```",
                repo_info["file_tree"],
                "```",
                "",
            ])

        # Make commands
        if repo_info.get("makefile_commands"):
            prompt_parts.append("## Available Make Commands")
            for cmd, desc in repo_info["makefile_commands"].items():
                prompt_parts.append(f"- `make {cmd}`: {desc}")
            prompt_parts.append("")

        # Tools
        if repo_info.get("tools"):
            prompt_parts.append("## Available Tools")
            for tool in repo_info["tools"]:
                prompt_parts.append(f"- `{tool['name']}`: {tool['description']}")
            prompt_parts.append("")

        # Dependencies
        if pyproject.get("dependencies"):
            prompt_parts.append("## Core Dependencies")
            for dep in pyproject["dependencies"][:15]:
                prompt_parts.append(f"- {dep}")
            prompt_parts.append("")

        if pyproject.get("dev_dependencies"):
            prompt_parts.append("## Dev Dependencies")
            for dep in pyproject["dev_dependencies"][:10]:
                prompt_parts.append(f"- {dep}")
            prompt_parts.append("")

        # CLI Scripts
        if pyproject.get("scripts"):
            prompt_parts.append("## CLI Commands")
            for script, path in pyproject["scripts"].items():
                prompt_parts.append(f"- `{script}` → {path}")
            prompt_parts.append("")

        # Git information
        git_info = repo_info.get("git_info", {})
        if git_info.get("is_git_repo"):
            prompt_parts.append("## Git Repository Info")
            if git_info.get("branch"):
                prompt_parts.append(f"- Current Branch: {git_info['branch']}")
            if git_info.get("total_commits"):
                prompt_parts.append(f"- Total Commits: {git_info['total_commits']}")
            if git_info.get("contributors"):
                prompt_parts.append("- Top Contributors:")
                for contrib in git_info["contributors"][:5]:
                    prompt_parts.append(f"  - {contrib['name']}: {contrib['commits']} commits")

            if git_info.get("recent_commits"):
                prompt_parts.append("\n- Recent Commits (last 10):")
                for commit in git_info["recent_commits"][:10]:
                    prompt_parts.append(f"  - [{commit['hash']}] {commit['message']} ({commit['date']})")

            if git_info.get("recent_changes"):
                prompt_parts.append("\n- Recent File Changes:")
                prompt_parts.append("```")
                prompt_parts.append(git_info["recent_changes"])
                prompt_parts.append("```")
            prompt_parts.append("")

        # Key files with content
        if repo_info.get("key_files"):
            prompt_parts.append("## Key Configuration Files")
            for filename, content in list(repo_info["key_files"].items())[:3]:
                prompt_parts.append(f"\n### {filename}")
                prompt_parts.append("```")
                prompt_parts.append(content[:2000] if len(content) > 2000 else content)
                prompt_parts.append("```")
            prompt_parts.append("")

        # Code samples
        if repo_info.get("code_samples"):
            prompt_parts.append("## Code Samples")
            for ext, samples in list(repo_info["code_samples"].items())[:2]:
                for sample in samples[:2]:
                    prompt_parts.append("```python" if ext == ".py" else "```")
                    prompt_parts.append(sample[:1200])
                    prompt_parts.append("```")
            prompt_parts.append("")

        # Generation instructions
        prompt_parts.extend([
            "",
            "# YOUR TASK",
            "",
            "Generate a CLAUDE.md-style guide with these EXACT sections:",
            "",
            "## 1. Project Overview",
            "**IMPORTANT**: If README.md exists in Key Configuration Files above, use it HEAVILY:",
            "- Extract project description, purpose, and features from README",
            "- Use README's language and tone for the overview paragraphs",
            "- Copy Key Features directly from README if present",
            "- If no README: use description from Project Metadata",
            "- ### Tech Stack (use actual dependencies listed above with versions)",
            "",
            "## 2. Project Structure",
            "```",
            "Use the directory tree above, and add comments explaining each major directory/file",
            "```",
            "",
            "## 3. Key Components",
            "List major components you see in the code samples with their file paths and responsibilities.",
            "Format: ### N. ComponentName (`path/to/file.py`)",
            "",
            "## 4. Development Practices",
            "### Code Style",
            "- Formatting: (look for black in dev dependencies)",
            "- Linting: (look for ruff in dev dependencies)",
            "- Type Checking: (look for mypy in dev dependencies)",
            "",
            "### Testing",
            "- Framework: (look for pytest in dev dependencies)",
            "- Run: `pytest` or check Makefile for test command",
            "",
            "## 5. Common Tasks",
            "### Adding a New [Feature Type]",
            "Provide step-by-step instructions with code examples from patterns you see in code samples.",
            "",
            "## 6. Important Files",
            "List key files with one-line descriptions of their purpose.",
            "",
            "## 7. Quick Commands",
            "```bash",
            "# Setup",
            "make [command from Makefile]",
            "",
            "# Development",
            "make test",
            "make format",
            "...",
            "```",
            "",
            "## 8. Dependencies",
            "### Core Dependencies",
            "- `package` - purpose",
            "(Use actual dependencies from above)",
            "",
            "### Dev Dependencies",
            "- `package` - purpose",
            "",
            "## 9. Code Patterns",
            "Show ACTUAL code snippets from the code samples above demonstrating common patterns.",
            "```python",
            "# Pattern: [Name]",
            "[actual code from samples]",
            "```",
            "",
            "## 10. Notes for AI Assistants",
            "- File Operations: (if this does file ops)",
            "- Testing: Always run tests after changes",
            "- Architecture: (mention key architectural principles)",
            "",
            "## 11. Version Information",
            f"- Current Version: {pyproject.get('version', '0.0.0')}",
            f"- Python: {pyproject.get('python_version', '3.x')}+",
            "- Status: (infer from version number)",
            "",
            "# CRITICAL RULES - READ CAREFULLY",
            "",
            "1. **Use ACTUAL data ONLY**: Every file path, command, dependency - from data above",
            "2. **Be SPECIFIC with paths**: Write `src/hrisa_code/cli.py`, NOT `cli.py` or `(path/to/file.py)`",
            "3. **Extract REAL code**: Copy code snippets from Code Samples above. Do NOT invent examples",
            "4. **Use ACTUAL commands**: List Makefile commands EXACTLY as shown above",
            "5. **Emphasize README**: Use README.md content heavily for Project Overview if available",
            "6. **Git context**: Use recent commits to understand current development focus",
            "7. **NO placeholders**: Never write `[add description]`, `(path/to/file.py)`, or similar",
            "8. **Include ALL sections**: Don't skip Known Limitations, Future Enhancements, When Making Changes",
            "9. **Start with**: `# HRISA.md - Project Guide for AI Assistants`",
            "10. **Architecture Principles**: Infer from code patterns (async, type hints, modularity, etc.)",
            "",
            "# EXAMPLES OF WHAT TO DO",
            "",
            "GOOD:",
            "- `src/hrisa_code/cli.py` - CLI entry point with Typer commands",
            "- `make test` - Run tests with pytest",
            "- Extract from README: 'Hrisa Code is a CLI coding assistant...'",
            "",
            "BAD:",
            "- `cli.py` - Main file (too vague)",
            "- `(path/to/file.py)` - Placeholder (placeholder!)",
            "- Made-up code example not from codebase",
            "",
        ])

        prompt = "\n".join(prompt_parts)

        # Use LLM to analyze
        try:
            response = await self.ollama_client.chat(
                message=prompt,
                system_prompt=(
                    "You are a senior software architect creating technical documentation. "
                    "Analyze the provided codebase information and create a detailed, actionable guide. "
                    "Extract real code examples, identify specific patterns, and provide concrete guidance. "
                    "Be thorough but concise. Focus on practical, useful information for AI assistants working on this code."
                ),
                tools=None,  # Don't use tools for this analysis
            )
            return response
        except Exception as e:
            self.console.print(f"[yellow]Warning: LLM analysis failed ({e}), using fallback[/yellow]")
            return self._generate_hrisa_content(repo_info)

    def _generate_hrisa_content(self, repo_info: Dict[str, Any]) -> str:
        """Generate HRISA.md content from repository information.

        Args:
            repo_info: Repository information

        Returns:
            HRISA.md markdown content
        """
        content = [
            "# HRISA.md - Repository Context",
            "",
            "This file contains important context about the repository for the Hrisa Code assistant.",
            "It's automatically generated and helps maintain consistency across chat sessions.",
            "",
            "---",
            "",
        ]

        # Project Overview
        content.append("## Project Overview")
        content.append("")
        content.append(f"**Root Directory:** `{repo_info['structure']['root']}`")
        if repo_info["git_info"].get("is_git_repo"):
            if "branch" in repo_info["git_info"]:
                content.append(f"**Current Branch:** `{repo_info['git_info']['branch']}`")
        content.append("")

        # Structure
        content.append("## Repository Structure")
        content.append("")
        dirs = repo_info["structure"].get("directories", [])
        if dirs:
            content.append("**Main Directories:**")
            for dir_name in sorted(dirs):
                content.append(f"- `{dir_name}/`")
            content.append("")

        # File Types
        file_types = repo_info["structure"].get("file_types", {})
        if file_types:
            content.append("**File Types:**")
            for ext, count in sorted(file_types.items(), key=lambda x: -x[1])[:10]:
                content.append(f"- `{ext}`: {count} files")
            content.append("")

        # Dependencies
        deps = repo_info.get("dependencies", {})
        if deps:
            content.append("## Dependencies")
            content.append("")
            for ecosystem, packages in deps.items():
                content.append(f"**{ecosystem.title()}:**")
                for pkg in packages[:15]:  # First 15
                    content.append(f"- {pkg}")
                content.append("")

        # Key Files
        key_files = repo_info.get("key_files", {})
        if key_files:
            content.append("## Key Files")
            content.append("")
            if "README.md" in key_files or "README.rst" in key_files or "README.txt" in key_files:
                readme_key = next(
                    k for k in ["README.md", "README.rst", "README.txt"] if k in key_files
                )
                content.append("### README Summary")
                content.append("")
                content.append("```")
                content.append(key_files[readme_key][:300] + "...")
                content.append("```")
                content.append("")

        # Architecture Notes
        content.append("## Architecture Notes")
        content.append("")
        content.append("*Add custom notes about the architecture, patterns, and conventions here.*")
        content.append("")

        # Important Context
        content.append("## Important Context for Assistant")
        content.append("")
        content.append("*Add specific instructions or context for the Hrisa Code assistant here.*")
        content.append("")
        content.append("### Coding Style")
        content.append("- *Document your preferred coding style*")
        content.append("")
        content.append("### Testing Approach")
        content.append("- *Document your testing preferences*")
        content.append("")

        return "\n".join(content)
