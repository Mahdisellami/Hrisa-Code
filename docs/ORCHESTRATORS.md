# Orchestrator Architecture

## Overview

Hrisa Code uses **orchestrators** to guide LLMs through complex, multi-step workflows. There are two main orchestration strategies:

1. **Base Orchestration**: LLM-guided discovery with synthesis
2. **Progressive Orchestration**: Static analysis with assembly (prevents hallucination)

## Orchestration Strategies

### 1. Base Orchestration (Legacy)

**Best for**: Exploratory analysis, architectural understanding, workflow tracing

**Approach**:
1. **Discovery Steps**: LLM explores codebase with guidance
2. **Synthesis**: LLM combines discoveries into final document

**Example workflow**:
```
User Request: "Generate HRISA.md"
├─ Step 1: Architecture Discovery (LLM explores structure)
├─ Step 2: Component Analysis (LLM identifies components)
├─ Step 3: Feature Detection (LLM finds features)
├─ Step 4: Workflow Tracing (LLM traces execution flows)
└─ Step 5: Synthesis (LLM writes comprehensive doc)
```

**Base Class**: `BaseOrchestrator`

**Key Characteristics**:
- LLM has freedom to explore
- Each step builds on previous discoveries
- Final synthesis combines all insights
- May include hallucinations (LLM fills gaps)

### 2. Progressive Orchestration (Current)

**Best for**: User-facing documentation, API references, installation guides

**Approach**:
1. **Extract Facts**: Static analysis extracts ground truth (no LLM)
2. **Build Sections**: Each section built from verified facts
3. **Validate**: Each section validated before proceeding
4. **Assemble**: Sections combined (no synthesis)

**Example workflow**:
```
User Request: "Generate README.md"
├─ Phase 1: Extract Facts (parse pyproject.toml, no LLM)
├─ Phase 2: Title Section (template + facts)
├─ Phase 3: Features Section (AST parse CLI commands)
├─ Phase 4: Installation Section (find setup methods)
├─ Phase 5: Usage Section (extract CLI examples)
└─ Phase 6: Assembly (concatenate sections, no synthesis)
```

**Base Class**: `ProgressiveBaseOrchestrator`

**Key Characteristics**:
- Ground truth first (static analysis)
- Each phase validated independently
- No freeform "synthesis" thinking
- Prevents hallucination

## Base Classes

### BaseOrchestrator

Located: `src/hrisa_code/core/orchestrators/base_orchestrator.py`

**Key Components**:
- `WorkflowStep`: Defines a discovery step with prompt template
- `WorkflowDefinition`: Complete workflow specification
- `generate()`: Main orchestration loop

**Usage**:
```python
from hrisa_code.core.orchestrators import BaseOrchestrator, WorkflowStep, WorkflowDefinition

class MyOrchestrator(BaseOrchestrator):
    @property
    def workflow_definition(self) -> WorkflowDefinition:
        return WorkflowDefinition(
            name="My Doc",
            description="Generate custom documentation",
            steps=[
                WorkflowStep(
                    name="analysis",
                    display_name="Code Analysis",
                    prompt_template="Analyze {project_path}...",
                ),
            ],
            synthesis_prompt_template="Generate doc from: {discoveries}",
            output_filename="MY_DOC.md",
        )

orchestrator = MyOrchestrator(conversation, project_path)
content = await orchestrator.generate()
```

### ProgressiveBaseOrchestrator

Located: `src/hrisa_code/core/orchestrators/progressive_base.py`

**Key Components**:
- `PhaseDefinition`: Defines a progressive phase
- `ProgressiveWorkflow`: Complete progressive workflow
- `extract_facts()`: Must implement fact extraction
- `build_X_section()`: One method per phase
- `assemble_document()`: Must implement assembly logic

**Usage**:
```python
from hrisa_code.core.orchestrators import (
    ProgressiveBaseOrchestrator,
    PhaseDefinition,
    ProgressiveWorkflow
)

class MyProgressiveOrchestrator(ProgressiveBaseOrchestrator):
    @property
    def workflow_definition(self) -> ProgressiveWorkflow:
        return ProgressiveWorkflow(
            name="My Progressive Doc",
            description="Generate doc progressively",
            output_filename="MY_DOC.md",
            phases=[
                PhaseDefinition(
                    name="title",
                    display_name="Title Section",
                    description="Build title from facts",
                    uses_llm=False
                ),
            ],
        )

    async def extract_facts(self) -> Dict[str, Any]:
        metadata = self.extract_project_metadata()
        return {"name": metadata.get("name")}

    async def build_title_section(self) -> str:
        return f"# {self.facts['name']}\n"

    async def assemble_document(self) -> str:
        return self.sections["title"]
```

## Template-Based Orchestration

For one-off custom workflows, use **template orchestrators** instead of creating subclasses:

Located: `src/hrisa_code/core/orchestrators/template_orchestrator.py`

### TemplateOrchestrator

Create orchestrators from workflow definitions without subclassing:

```python
from hrisa_code.core.orchestrators.template_orchestrator import (
    TemplateOrchestrator,
    WorkflowStep,
    WorkflowDefinition
)

# Define workflow
workflow = WorkflowDefinition(
    name="Changelog",
    description="Generate CHANGELOG.md",
    steps=[
        WorkflowStep(
            name="git_history",
            display_name="Git History",
            prompt_template="Analyze git history of {project_path}...",
        ),
    ],
    synthesis_prompt_template="Generate changelog from: {discoveries}",
    output_filename="CHANGELOG.md",
)

# Create orchestrator
orchestrator = TemplateOrchestrator(
    conversation=conversation,
    project_path=Path("."),
    workflow=workflow,
)

content = await orchestrator.generate()
```

### Pre-built Templates

Two example templates are included:

#### CHANGELOG_WORKFLOW
```python
from hrisa_code.core.orchestrators.template_orchestrator import CHANGELOG_WORKFLOW

# 2-step workflow:
# 1. Git history analysis
# 2. Change categorization
# Output: CHANGELOG.md in Keep a Changelog format
```

#### ARCHITECTURE_WORKFLOW
```python
from hrisa_code.core.orchestrators.template_orchestrator import ARCHITECTURE_WORKFLOW

# 3-step workflow:
# 1. Project structure analysis
# 2. Component identification
# 3. Design pattern detection
# Output: ARCHITECTURE.md with diagrams and rationale
```

### Factory Function

Create orchestrators by name:

```python
from hrisa_code.core.orchestrators.template_orchestrator import create_custom_orchestrator

orchestrator = create_custom_orchestrator(
    conversation=conversation,
    project_path=Path("."),
    workflow_name="changelog",  # or "architecture"
)

if orchestrator:
    content = await orchestrator.generate()
```

## Implemented Orchestrators

### Progressive Orchestrators (✅ Production)

1. **ProgressiveReadmeOrchestrator** (`progressive_readme_orchestrator.py`)
   - Generates: README.md
   - Audience: End users, developers
   - Phases: Facts → Title → Features → Installation → Usage → Assembly
   - Special: AST parses CLI commands, no LLM for facts

2. **ProgressiveApiOrchestrator** (`progressive_api_orchestrator.py`)
   - Generates: API.md
   - Audience: API consumers, developers
   - Phases: Facts → Title → CLI Commands → Tools → Core API → Config → Assembly
   - Special: Extracts tool definitions from code

3. **ProgressiveContributingOrchestrator** (`progressive_contributing_orchestrator.py`)
   - Generates: CONTRIBUTING.md
   - Audience: Contributors
   - Phases: Facts → Title → Setup → Standards → Workflow → Testing → Assembly
   - Special: Detects testing framework, linting tools

4. **ProgressiveHrisaOrchestrator** (`progressive_hrisa_orchestrator.py`)
   - Generates: HRISA.md
   - Audience: AI assistants (like Claude Code)
   - Phases: Facts → Title → Architecture → Usage → Tools → Assembly
   - Special: Comprehensive technical documentation

### Legacy Orchestrators (⚠️ Deprecated)

1. **ReadmeOrchestrator** (`readme_orchestrator.py`)
2. **ApiOrchestrator** (`api_orchestrator.py`)
3. **ContributingOrchestrator** (`contributing_orchestrator.py`)
4. **HrisaOrchestrator** (`hrisa_orchestrator.py`)

These use BaseOrchestrator with LLM-guided discovery. Kept for backward compatibility but progressive versions are preferred.

## Multi-Model Orchestration

Orchestrators support using different models for different steps:

```python
from hrisa_code.core.model_router import ModelRouter

router = ModelRouter(available_models=["qwen2.5:72b", "deepseek-coder-v2:236b"])

orchestrator = BaseOrchestrator(
    conversation=conversation,
    project_path=project_path,
    model_router=router,
    enable_multi_model=True,
)
```

**Model Selection Logic**:
- Architecture analysis → Strong reasoning models (qwen2.5:72b)
- Code understanding → Code-specialized models (deepseek-coder-v2)
- Documentation writing → Writing-optimized models (llama3.1:70b)
- Workflows/tracing → Reasoning models (deepseek-r1:70b)

## Creating Custom Orchestrators

### When to Create a Subclass

Create a **subclass** when:
- You need a reusable workflow across multiple projects
- You want to contribute it back to Hrisa Code
- The workflow requires custom validation logic
- You need complex phase interdependencies

### When to Use Templates

Use **templates** when:
- One-off custom documentation need
- Experimenting with new workflow ideas
- Project-specific documentation formats
- Simple linear workflows

### Best Practices

1. **Progressive over Base**: Prefer progressive orchestration to prevent hallucination
2. **Static Analysis First**: Extract ground truth before involving LLM
3. **Validate Each Phase**: Check output quality at each step
4. **Small Phases**: Break work into focused, testable phases
5. **Fail Fast**: Detect issues early in the pipeline

## Testing Orchestrators

### Unit Tests

Test individual methods:
```python
def test_extract_facts():
    orch = MyOrchestrator(conversation, project_path)
    facts = await orch.extract_facts()
    assert facts["name"] == "expected_name"
```

### Integration Tests

Test full orchestration:
```python
def test_generate_document():
    orch = MyOrchestrator(conversation, project_path)
    content = await orch.generate()
    assert "expected_content" in content
```

### Smoke Tests

Verify orchestrator can be imported and instantiated:
```python
from hrisa_code.core.orchestrators import MyOrchestrator
assert MyOrchestrator is not None
```

## Future Enhancements

See [FUTURE.md](../FUTURE.md) for:
- Meta-orchestration system (auto-generates workflows)
- Complexity detection (decides if orchestration needed)
- Dynamic planning (LLM creates execution plans)
- Adaptive execution (pivots based on discoveries)

## Resources

- **Base Orchestrator**: `src/hrisa_code/core/orchestrators/base_orchestrator.py`
- **Progressive Base**: `src/hrisa_code/core/orchestrators/progressive_base.py`
- **Templates**: `src/hrisa_code/core/orchestrators/template_orchestrator.py`
- **Examples**: All `progressive_*.py` files in orchestrators directory
