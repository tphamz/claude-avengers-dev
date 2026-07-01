# Python Toolbelt

## When to Equip

Use when implementing Python code - scripts, libraries, APIs, CLI tools, or
data processing pipelines.

## Conventions

- **PEP 8**: 4-space indent, snake_case for functions/vars, PascalCase for classes
- **Type hints** on all function signatures
- **f-strings** for formatting (not .format() or %)
- **pathlib.Path** for all file path operations
- **Context managers** for resource management

## Implementation Patterns

- [ ] `dataclasses` or `pydantic` for structured data
- [ ] `argparse` for CLI interfaces with `--help`
- [ ] `logging` module - not `print()` for operational output
- [ ] Handle exceptions specifically - `except ValueError:` not bare `except:`
- [ ] Generators for large data processing
- [ ] `enum.Enum` for fixed sets of values
- [ ] Prefer standard library over third-party when equivalent

## Testing Patterns

- `pytest` as the test framework
- `pytest.fixture` for shared setup
- `pytest.mark.parametrize` for multiple inputs
- `tmp_path` fixture for file system tests
- `unittest.mock.patch` for external dependencies
- Test edge cases: empty input, None, boundary values

## Patterns to Avoid

- Mutable default arguments (`def f(items=[]):`)
- Bare `except:` without re-raising or logging
- Star imports (`from module import *`)
- Global mutable state
- `os.system()` or `subprocess.call(shell=True)`
