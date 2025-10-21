# Contributing to Crawly

Thank you for your interest in contributing to Crawly! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or screenshots

### Suggesting Enhancements

1. Check if the enhancement has been suggested
2. Create an issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions considered
   - Impact on existing functionality

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/Crawly.git
   cd Crawly
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
   - Keep commits focused and atomic

4. **Test your changes**
   ```bash
   make test
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description
   - Reference any related issues
   - Include screenshots for UI changes

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Git

### Setup

1. **Clone and setup environment**
   ```bash
   git clone https://github.com/oasis4/Crawly.git
   cd Crawly
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   make install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Initialize database**
   ```bash
   make init-db
   ```

5. **Run tests**
   ```bash
   make test
   ```

## Code Style

### Python
- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small
- Maximum line length: 100 characters

### Docstrings
Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When something is wrong
    """
    pass
```

### Imports
Organize imports in this order:
1. Standard library imports
2. Third-party imports
3. Local imports

```python
import os
from typing import List

from playwright.async_api import Page
import sqlalchemy

from src.utils.logger import get_logger
```

## Project Structure

```
Crawly/
├── src/              # Application source code
│   ├── api/          # FastAPI application
│   ├── scraper/      # Scraping modules
│   ├── database/     # Database connections
│   ├── models/       # Data models
│   └── utils/        # Utility functions
├── tests/            # Test files
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── config/           # Configuration files
└── docs/             # Documentation
```

## Testing

### Writing Tests

- Use pytest for testing
- Test files should match `test_*.py`
- Test functions should start with `test_`
- Use descriptive test names
- Organize tests in classes when appropriate

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_validators.py

# Run with coverage
pytest --cov=src tests/
```

### Test Coverage

Aim for:
- 80%+ overall coverage
- 100% for critical paths (data validation, database operations)

## Documentation

### Code Documentation
- Add docstrings to all public functions and classes
- Document complex logic with inline comments
- Keep comments up-to-date with code changes

### README Updates
- Update README.md for new features
- Add usage examples
- Update configuration documentation

### API Documentation
- FastAPI auto-generates documentation
- Add clear descriptions to endpoints
- Document request/response schemas

## Commit Guidelines

### Commit Messages

Use conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add endpoint for product search

fix(scraper): handle pagination correctly

docs(readme): update installation instructions

test(validators): add tests for price validation
```

## Release Process

1. Update version in `setup.py` and `src/__init__.py`
2. Update CHANGELOG.md
3. Create release branch
4. Test thoroughly
5. Create pull request to main
6. Tag release after merge

## Questions?

Feel free to:
- Open an issue for questions
- Ask in pull request comments
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
