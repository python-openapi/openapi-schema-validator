# AGENTS.md

Agent guide for `openapi-schema-validator`.
Use this as the default operating playbook when making changes.

## Project Snapshot

- Language: Python.
- Build backend and packaging: Poetry (`poetry-core`).
- Runtime package: `openapi_schema_validator/`.
- Tests: `pytest` in `tests/unit` and `tests/integration`.
- Type checking: `mypy` with `strict = true`.
- Formatting and imports: `black` and `isort`.
- Extra static analysis: `deptry`.
- Supported Python versions: 3.10, 3.11, 3.12, 3.13, 3.14.

## Source Layout

- `openapi_schema_validator/__init__.py`: public exports + package metadata.
- `openapi_schema_validator/validators.py`: validator class setup for OAS 3.0/3.1/3.2.
- `openapi_schema_validator/_keywords.py`: custom keyword handlers and ValidationError generation.
- `openapi_schema_validator/_format.py`: format checker functions and registrations.
- `openapi_schema_validator/_types.py`: custom type checker setup.
- `openapi_schema_validator/shortcuts.py`: top-level `validate` helper.
- `tests/unit/`: focused unit tests.
- `tests/integration/`: validator behavior integration coverage.
- `docs/`: Sphinx source files.

## Environment Setup

1. Install Poetry.
2. Recommended one-time config:
   - `poetry config virtualenvs.in-project true`
3. Install dependencies:
   - `poetry install`
4. Include docs toolchain when needed:
   - `poetry install --with docs`

## Build, Lint, and Test Commands

Run commands from repository root.

### Install / bootstrap

- `poetry install`
- `poetry install --all-extras` (matches CI tests job)

### Test suite

- Full suite: `poetry run pytest`
- Unit only: `poetry run pytest tests/unit`
- Integration only: `poetry run pytest tests/integration`

### Running a single test (important)

- Single file: `poetry run pytest tests/unit/test_shortcut.py`
- Single test function:
  - `poetry run pytest tests/unit/test_shortcut.py::test_validate_does_not_mutate_schema`
- Single test class:
  - `poetry run pytest tests/integration/test_validators.py::TestOAS31ValidatorValidate`
- Pattern selection: `poetry run pytest -k nullable`

### Type checks

- `poetry run mypy`

### Lint / formatting / static checks

- Full pre-commit run: `poetry run pre-commit run -a`
- Staged files pre-commit run: `poetry run pre-commit run`
- Format explicitly: `poetry run black .`
- Sort imports explicitly: `poetry run isort .`
- Convert to f-strings where safe: `poetry run flynt .`
- Dependency hygiene: `poetry run deptry .`

### Build package / docs

- Build distributions: `poetry build`
- Build docs (CI-equivalent command):
  - `poetry run python -m sphinx -T -b html -d docs/_build/doctrees -D language=en docs docs/_build/html -n -W`

## Pytest Behavior Notes

- Default `pytest` options are defined in `pyproject.toml`.
- Normal runs are verbose and include local variable display on failures.
- Reports are generated in `reports/junit.xml` and `reports/coverage.xml`.
- Coverage is collected for `openapi_schema_validator` by default.
- Test commands usually update files under `reports/`.

## Code Style Rules (Repository-Specific)

### Formatting

- Black line length is 79; keep new code Black-compatible.
- Prefer clear, wrapped multi-line literals for schemas and parametrized test data.
- Follow existing wrapping style for function signatures and long calls.

### Imports

- Isort is configured with `profile = "black"`, `line_length = 79`, and `force_single_line = true`.
- Import one symbol per line in `from ... import ...` blocks.
- Keep import grouping conventional: stdlib, third-party, local package.
- Prefer absolute imports from `openapi_schema_validator`.

### Types

- Keep all new functions fully type-annotated (mypy strict mode).
- Use `Mapping[str, Any]` for schema-like readonly mappings.
- Use `Iterator[ValidationError]` for keyword handler generators.
- Use `Any` and `cast(...)` only when necessary for interop with jsonschema internals.

### Naming conventions

- Functions and variables: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE` (e.g., validator maps).
- Tests: `test_*` functions; group with `Test*` classes when useful.
- Preserve OpenAPI field spellings exactly (`readOnly`, `writeOnly`, `nullable`, etc.).

### Error handling and validation behavior

- Validation failures should raise or yield `jsonschema.exceptions.ValidationError`.
- Prefer narrow exception handling (`FormatError`, etc.) instead of broad catches.
- If broad catches are required for ref-resolution boundaries, convert to explicit `ValidationError` messages.
- Keep error text stable and human-readable; tests assert message content.
- Preserve `None` return behavior for successful `.validate(...)` paths.

### Behavioral constraints to preserve

- Do not mutate incoming schema objects in helper APIs.
- Maintain compatibility for OAS 3.0, OAS 3.1, and OAS 3.2 validators.
- Keep existing read/write behavior around `readOnly` and `writeOnly`.
- Keep format and type checker semantics aligned with current tests.

## Testing Expectations for Changes

- For small edits, run the most targeted pytest selection first.
- Before handoff when feasible, run:
  - `poetry run pytest`
  - `poetry run mypy`
  - `poetry run pre-commit run -a`
- If you changed dependencies/import graph, also run `poetry run deptry .`.

## CI Parity Checklist

- CI tests run on Python 3.10-3.14.
- CI static checks run via `pre-commit`.
- CI docs job builds Sphinx docs with warnings treated as errors.
- Keep local validation aligned with `.github/workflows/`.

## Cursor / Copilot Instructions Status

- `.cursor/rules/` was not found.
- `.cursorrules` was not found.
- `.github/copilot-instructions.md` was not found.
- If any of these appear later, treat them as higher-priority instructions and update this guide.

## Practical Workflow for Agents

1. Read `pyproject.toml` and the nearest related module/tests before editing.
2. Make minimal, focused changes that match existing patterns.
3. Add or update tests in the closest relevant test module.
4. Run a single-test command first, then broader checks.
5. Keep `openapi_schema_validator/__init__.py` exports synchronized if public API changes.
