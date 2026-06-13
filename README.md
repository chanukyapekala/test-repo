# World Bank Countries Explorer

A simple Streamlit app that fetches country data from the [World Bank API](https://api.worldbank.org/v2/country?format=json&per_page=300), writes it to a local JSON file in a single batch, and displays it as an interactive table and chart.

## Features

- **Refresh Data** button fetches all ~296 countries from the World Bank API and saves them to `data/countries.json`
- Filter by **Region** and **Income Level**
- Sortable countries table (name, ISO3, region, income level, capital)
- Bar chart of country count by region

## Getting started

**Prerequisites:** Python 3.11+, [Poetry](https://python-poetry.org/)

```bash
# Install dependencies
poetry install

# Run the app
poetry run streamlit run app.py
```

Open http://localhost:8501, then click **Refresh Data** to fetch and display the data.

## Project structure

```
.
├── app.py              # Streamlit app — fetch + display
├── pyproject.toml      # Poetry dependencies
├── data/               # Runtime output (gitignored)
│   └── countries.json
└── CLAUDE.md           # Context for AI-assisted development
```

## Data source

[World Bank REST API](https://datahelpdesk.worldbank.org/knowledgebase/articles/898590-country-api-queries) — free, no authentication required.