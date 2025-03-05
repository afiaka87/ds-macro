# DS Cargo Analyze - Development Guide

## Commands
- Setup: `source .venv/bin/activate`
- Run tests: `python -m pytest`
- Run single test: `python -m pytest tests/test_file.py::test_name -v`
- Run async tests: `python -m pytest tests/test_file.py --asyncio-mode=strict`
- Run main: `python main.py [--routine ROUTINE] [--delay SECONDS] [--custom]`

## Code Style Guidelines
- **Imports**: Group standard library, third-party, and local imports
- **Typing**: Use type hints for all function parameters and return values
- **Error Handling**: Use try/except blocks with specific exceptions
- **Naming**:
  - Classes: PascalCase
  - Functions/Variables: snake_case
  - Constants: UPPERCASE_WITH_UNDERSCORES
- **Documentation**: Docstrings for all classes and methods
- **Async**: Use asyncio for all I/O operations
- **Models**: Use Pydantic for data validation and serialization

## Project Structure
- `ds_macro/`: Core library for game automation
- `routines/`: Pre-defined action sequences
- `tests/`: Test suite with pytest