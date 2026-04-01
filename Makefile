.PHONY: test
test:
	.venv/bin/python -m black .
	.venv/bin/python -m ruff check --preview --fix .
	.venv/bin/python -m mypy custom_components/
