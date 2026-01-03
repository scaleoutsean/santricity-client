# Contributing

Thank you for considering a contribution to the SANtricity Client (Python). The project aims to be useful to NetApp E-Series administrators, automation engineers, and Python developers alike.

## Getting started

1. Fork and clone the repository.
2. Create a virtual environment and install dependencies with `pip install -e .[dev]`.
3. Create a feature branch for your work.
4. Run `ruff check .` and `pytest` before pushing.

## Contribution types

- Documentation improvements (README, examples, inline comments).
- Bug fixes and regression tests for existing modules.
- New resource modules aligned with SANtricity API endpoints.
- Enhancements to authentication strategies and transport logic.

## Pull Request checklist

- Reference related issues in the PR description.
- Include unit tests and JSON request/response example for new behavior when possible.
- Update `CHANGELOG.md` with a short entry under the "Unreleased" heading.
- Ensure lint and test suites pass locally.

## Release checklist

- Update `CHANGELOG.md`
- Update `pyproject.toml`

## Reporting Security Issues

Do file public issues for security problems. Nonsense issues will be closed with no comment.
