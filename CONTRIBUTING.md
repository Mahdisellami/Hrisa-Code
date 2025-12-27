# Contributing to Hrisa-Code

Welcome! We are thrilled to have you interested in contributing to Hrisa-Code. Your help is essential in making this project better. Whether you want to contribute code, documentation, bug reports, or feature requests, please read through this guide to understand how best to get involved.

## Welcome & Introduction

Thank you for your interest in contributing! We adhere to a [Code of Conduct](CODE_OF_CONDUCT.md) that all contributors must follow. Contributions can take many forms:

- **Code**: Fix bugs, add new features.
- **Documentation**: Improve or expand existing documentation.
- **Issues**: Report bugs and request features.

## Getting Started

### Prerequisites

- Python 3.9 or later
- Git

### Fork and Clone Instructions

1. [Fork the repository](https://github.com/yourusername/Hrisa-Code/fork).
2. Clone your forked repository:
   ```bash
   git clone https://github.com/yourusername/Hrisa-Code.git
   cd Hrisa-Code
   ```

### Development Environment Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the project locally to ensure everything is set up correctly.

## Development Workflow

### Creating a Branch

Create a new branch for your work:

```bash
git checkout -b feature/your-feature-name main
```

- **Branch Naming Conventions**:
  - `feature/<description>`
  - `bugfix/<description>`

### Making Changes

Feel free to make changes to the project. Ensure you follow the [Code Standards](#code-standards) and write tests for your new features or bug fixes.

### Running Tests Locally

Run the test suite to ensure your changes don't break existing functionality:

```bash
pytest
```

### Running Linters/Formatters

We use `black` for code formatting and `ruff` for linting. Ensure your code adheres to these standards:

- Format code:
  ```bash
  black .
  ```
  
- Run linter:
  ```bash
  ruff .
  ```

### Committing Changes

Commit your changes with a descriptive message:

```bash
git commit -m "feat(module): description of changes"
```

## Code Standards

### Code Style

- Use `black` for code formatting.
- Use `ruff` for linting.

### Type Hints Expectations

Include type hints in your code to improve readability and maintainability.

### Docstring Requirements

Use docstrings to document classes, methods, and modules. Follow the [PEP 257](https://peps.python.org/pep-0257/) conventions.

### Testing Requirements

Write tests for all new features or bug fixes. Ensure test coverage is high.

### How to Run Quality Checks

Run quality checks before submitting your PR:

```bash
black .
ruff .
pytest
```

## Testing

### How to Write Tests

Place tests in the `tests/` directory following naming conventions like `test_<module_name>.py`.

### How to Run Tests

Run the test suite using pytest:

```bash
pytest
```

### Coverage Expectations

Strive for high test coverage. Aim for at least 80% coverage.

### Test Structure and Organization

Organize tests logically within the `tests/` directory. Use fixtures and parameterized tests where appropriate.

## Submitting Changes

### Creating a Pull Request

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Open a Pull Request (PR) targeting `main`.

### PR Title and Description Guidelines

- **Title**: Use a descriptive title, e.g., `feat(module): add new feature`.
- **Description**: Provide details about the changes and any relevant context.

### What to Include in PR

- New features should include tests.
- Bug fixes should include regression tests.
- Documentation updates should be comprehensive.

### CI Checks that Must Pass

Ensure all checks pass before merging. If you encounter issues, seek help from maintainers or other contributors.

### Review Process and Timeline

- PRs will be reviewed by the maintainers or other contributors.
- Be prepared for feedback and iterations.
- Once approved, a maintainer will merge your PR into `main`.

## Code Review

### What to Expect During Review

- Reviewers will check code quality, adherence to project standards, and functionality.
- They may request changes or improvements.

### How to Respond to Feedback

- Address comments from reviewers.
- Make additional changes if needed.
- Push updates to your branch, which should automatically update the PR.

### Iteration and Updates

Iterate on feedback until the PR is approved. Communicate with reviewers if further clarification is needed.

### When PRs Get Merged

Once all checks pass and the PR is approved by a maintainer, it will be merged into `main`.

## Project Structure

### Overview of Directory Layout

- **`src/hrisa_code/core/`**: Core modules containing main logic and functionalities.
- **`src/hrisa_code/tools/`**: Utility functions and classes for various operations.
- **`tests/`**: Test files for the project.

### Where Different Types of Code Live

- **Core Modules**: `src/hrisa_code/core/`
- **Tools Modules**: `src/hrisa_code/tools/`

### Key Modules and Their Purposes

- **Orchestrators**: Manage complex operations, e.g., `api_orchestrator.py`.
- **Managers**: Handle specific tasks, e.g., `approval_manager.py`, `goal_tracker.py`.

### Where to Add New Features

1. Identify the module (core or tools).
2. Create or modify files in the appropriate directory.
3. Update existing modules as needed.

## Common Contribution Types

### Adding a New Tool

1. **Create a new file**:
   - Example: `src/hrisa_code/tools/new_tool.py`
   
2. **Write utility functions**:
   - Follow existing patterns and conventions.
   
3. **Add corresponding tests**:
   - Example: `tests/test_new_tool.py`

4. **Update documentation**:
   - Modify `docs/ARCHITECTURE.md` to include the new tool.

5. **Commit changes**:
   ```bash
   git add src/hrisa_code/tools/new_tool.py tests/test_new_tool.py docs/ARCHITECTURE.md
   git commit -m "feat(tools): add new_tool utility"
   ```

6. **Push and create PR**:
   ```bash
   git push origin feature/new-tool-feature
   ```
   - Open a Pull Request targeting `main`.

### Adding a New Orchestrator

1. **Modify or add methods**:
   - Example: `api_orchestrator.py`
   
2. **Update related tests**:
   - Ensure new functionality is covered.

3. **Commit changes**:
   ```bash
   git commit -m "feat(core): enhance api_orchestrator"
   ```

4. **Push and create PR**:
   ```bash
   git push origin feature/new-orchestrator-feature
   ```
   - Open a Pull Request targeting `main`.

### Fixing Bugs

1. **Identify the bug**.
2. **Create a new branch**:
   ```bash
   git checkout -b bugfix/bug-description main
   ```
3. **Make changes**.
4. **Add tests to prevent regressions**.
5. **Commit changes**:
   ```bash
   git commit -m "fix(module): resolve bug"
   ```
6. **Push and create PR**:
   ```bash
   git push origin bugfix/bug-description
   ```

### Improving Documentation

1. **Identify areas for improvement**.
2. **Make updates** in `docs/` or inline documentation.
3. **Commit changes**:
   ```bash
   git commit -m "docs(module): improve documentation"
   ```
4. **Push and create PR**:
   ```bash
   git push origin docs/improvements
   ```

### Adding Tests

1. **Identify the module to test**.
2. **Create or modify tests** in `tests/`.
3. **Commit changes**:
   ```bash
   git commit -m "test(module): add new tests"
   ```
4. **Push and create PR**:
   ```bash
   git push origin test/new-tests
   ```

## Resources

- [Project Documentation](docs/)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Development Guides](docs/DEVELOPMENT.md)
- Communication Channels:
  - Discord: [Join our channel](https://discord.gg/your-channel-link)
  - Issues: [Open an issue](https://github.com/yourusername/Hrisa-Code/issues)

## Questions?

If you have any questions, feel free to ask:

- **Discord**: Join our community and chat with us.
- **Issues**: Open a new issue for help or further discussion.

We look forward to your contributions!