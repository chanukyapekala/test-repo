# Project Context

## What this is
A minimal Streamlit app that fetches country data from the World Bank public API and writes it to a local JSON file. The Streamlit UI reads from that file and renders an interactive table and bar chart.

## Stack
- Python 3.11+ managed with Poetry
- `streamlit` — UI
- `requests` — HTTP fetch
- `pandas` — tabular data

## How to run
```bash
poetry install
poetry run streamlit run app.py
```
App runs at http://localhost:8501.

## Key files
- `app.py` — single-file Streamlit app (fetch + display logic)
- `data/countries.json` — written at runtime, gitignored
- `pyproject.toml` — Poetry dependencies

## API
World Bank REST API (free, no auth):
`https://api.worldbank.org/v2/country?format=json&per_page=300`

Response shape: `[meta, list_of_country_dicts]` — we save only index `[1]`.

Fields used: `name`, `id` (ISO3), `region.value`, `incomeLevel.value`, `capitalCity`.

## Notes
- REST Countries API (restcountries.com v3.1) was deprecated; v5 requires a paid auth key. Switched to World Bank API.
- `data/` is gitignored — the JSON file is never committed.
- The "Refresh Data" button is the only way to write to disk; page load is always read-only.