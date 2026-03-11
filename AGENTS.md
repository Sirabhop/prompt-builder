# AGENTS.md

## Cursor Cloud specific instructions

**Product**: Prompt Builder for Seniors — a single-file Streamlit app (`main.py`) that helps users construct structured AI prompts via a web form.

**Tech stack**: Python 3.11, Streamlit, uv (package manager), no database or external APIs.

**Running the app**:
```
uv run streamlit run main.py --server.headless true --server.port 8501
```
The app serves on `http://localhost:8501`.

**Dependencies**: Managed by `uv` with `pyproject.toml` + `uv.lock`. Install/sync with `uv sync`.

**Linting / Testing**: No linter (ruff, flake8, etc.) or test framework (pytest) is configured in this project. There are no automated tests. If you add linting or tests, install the tool as a dev dependency via `uv add --dev <package>`.

**Project structure**:
- `main.py` — entire application (UI + logic)
- `prompt-template/` — Markdown template files loaded at runtime
- `.python-version` — pins Python 3.11
