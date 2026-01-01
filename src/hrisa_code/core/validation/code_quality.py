"""Code quality validation for generated code."""

import ast
import re
from typing import Dict, List, Optional, Tuple


class CodeQualityValidator:
    """Validates code quality before writing files."""

    @staticmethod
    def validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"

    @staticmethod
    def check_imports(code: str) -> Tuple[bool, List[str]]:
        """Check for undefined imports and classes.

        Args:
            code: Python code to check

        Returns:
            Tuple of (all_imports_ok, list_of_issues)
        """
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False, ["Cannot parse code for import checking"]

        # Collect all imported names
        imported_names = set()
        defined_names = set()

        for node in ast.walk(tree):
            # Track imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.add(alias.asname if alias.asname else alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_names.add(alias.asname if alias.asname else alias.name)

            # Track defined classes and functions
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                defined_names.add(node.name)

        # Check for undefined references (basic check)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                name = node.id
                # Check if it's used but not defined or imported
                # (This is a simplified check - doesn't handle scoping perfectly)
                if (
                    isinstance(node.ctx, ast.Load)
                    and name not in imported_names
                    and name not in defined_names
                    and not name.startswith("_")  # Ignore private names
                    and name
                    not in [
                        "self",
                        "cls",
                        "True",
                        "False",
                        "None",
                    ]  # Ignore built-ins
                ):
                    # Check if it's a common built-in
                    builtins = [
                        "print",
                        "len",
                        "str",
                        "int",
                        "float",
                        "list",
                        "dict",
                        "set",
                        "tuple",
                        "range",
                        "enumerate",
                        "zip",
                        "open",
                        "type",
                        "isinstance",
                        "super",
                        "property",
                        "staticmethod",
                        "classmethod",
                    ]
                    if name not in builtins:
                        issues.append(
                            f"Potentially undefined name '{name}' - "
                            "may need import or definition"
                        )

        return len(issues) == 0, issues

    @staticmethod
    def check_type_hints(code: str, require_hints: bool = False) -> Tuple[bool, List[str]]:
        """Check if functions have type hints.

        Args:
            code: Python code to check
            require_hints: If True, require type hints on all functions

        Returns:
            Tuple of (has_hints, list_of_functions_without_hints)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False, ["Cannot parse code for type hint checking"]

        functions_without_hints = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip __init__, __str__, __repr__, etc.
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue

                # Check if function has parameter hints
                has_param_hints = any(arg.annotation is not None for arg in node.args.args)

                # Check if function has return hint
                has_return_hint = node.returns is not None

                if require_hints and not (has_param_hints or has_return_hint):
                    functions_without_hints.append(node.name)

        if require_hints:
            return len(functions_without_hints) == 0, functions_without_hints
        else:
            # Just return info, don't fail
            return True, functions_without_hints

    @staticmethod
    def check_fstring_syntax(code: str) -> Tuple[bool, List[str]]:
        """Check for common f-string errors like {{variable}} instead of {variable}.

        Args:
            code: Python code to check

        Returns:
            Tuple of (is_ok, list_of_issues)
        """
        issues = []

        # Pattern: f'...{{identifier}}...' or f"...{{identifier}}..."
        # This is likely an error (double braces when single was intended)
        pattern = r'f["\'].*?\{\{(\w+)\}\}.*?["\']'

        matches = re.finditer(pattern, code)
        for match in matches:
            var_name = match.group(1)
            issues.append(
                f"Possible f-string error: '{{{{{{var_name}}}}}}' should likely be '{{{var_name}}}'"
            )

        return len(issues) == 0, issues

    @staticmethod
    def validate_all(
        code: str, file_path: str, require_type_hints: bool = False
    ) -> Dict[str, any]:
        """Run all validations on code.

        Args:
            code: Python code to validate
            file_path: Path to file being validated
            require_type_hints: Whether to require type hints

        Returns:
            Dictionary with validation results
        """
        # Only validate Python files
        if not file_path.endswith(".py"):
            return {
                "valid": True,
                "errors": [],
                "warnings": [],
                "info": ["Non-Python file, skipping validation"],
            }

        errors = []
        warnings = []
        info = []

        # Check syntax
        syntax_ok, syntax_error = CodeQualityValidator.validate_python_syntax(code)
        if not syntax_ok:
            errors.append(f"Syntax Error: {syntax_error}")
            # If syntax is broken, can't do other checks
            return {"valid": False, "errors": errors, "warnings": warnings, "info": info}

        # Check imports
        imports_ok, import_issues = CodeQualityValidator.check_imports(code)
        if not imports_ok:
            warnings.extend([f"Import Issue: {issue}" for issue in import_issues])

        # Check type hints
        hints_ok, functions_without_hints = CodeQualityValidator.check_type_hints(
            code, require_type_hints
        )
        if not hints_ok:
            errors.append(
                f"Missing type hints on functions: {', '.join(functions_without_hints)}"
            )
        elif functions_without_hints:
            info.append(
                f"Functions without type hints: {', '.join(functions_without_hints[:5])}"
                + (
                    f" and {len(functions_without_hints) - 5} more"
                    if len(functions_without_hints) > 5
                    else ""
                )
            )

        # Check f-string syntax
        fstring_ok, fstring_issues = CodeQualityValidator.check_fstring_syntax(code)
        if not fstring_ok:
            errors.extend([f"F-string Error: {issue}" for issue in fstring_issues])

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "info": info,
        }
