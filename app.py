import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

DATA_FILE = Path("data/countries.json")
API_URL = "https://api.worldbank.org/v2/country?format=json&per_page=300"


def fetch_and_save() -> None:
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()
    # World Bank returns [meta, list_of_countries]
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise ValueError(f"Unexpected API response: {payload}")
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(
            {"fetched_at": datetime.now(timezone.utc).isoformat(), "data": payload[1]},
            f,
        )


def load_from_file() -> tuple[list | None, str | None]:
    if not DATA_FILE.exists():
        return None, None
    with open(DATA_FILE) as f:
        raw = json.load(f)
    return raw["data"], raw["fetched_at"]


def to_dataframe(countries: list) -> pd.DataFrame:
    rows = [
        {
            "Name": c.get("name", ""),
            "ISO3": c.get("id", ""),
            "Region": (c.get("region") or {}).get("value", ""),
            "Income Level": (c.get("incomeLevel") or {}).get("value", ""),
            "Capital": c.get("capitalCity", ""),
        }
        for c in countries
        if isinstance(c, dict)
    ]
    return pd.DataFrame(rows).sort_values("Name").reset_index(drop=True)


st.set_page_config(page_title="World Bank Countries Explorer", layout="wide")
st.title("World Bank Countries Explorer")

if st.button("Refresh Data"):
    with st.spinner("Fetching from World Bank API..."):
        try:
            fetch_and_save()
            st.success("Data saved to disk.")
        except (requests.RequestException, ValueError) as e:
            st.error(f"Fetch failed: {e}")

data, fetched_at = load_from_file()

if data is None:
    st.info("No data yet — click **Refresh Data** to fetch from the World Bank API.")
    st.stop()

st.caption(f"Last fetched: {fetched_at}  |  {len(data)} entries")

df = to_dataframe(data)

col1, col2 = st.columns(2)
with col1:
    regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
    selected_region = st.selectbox("Filter by Region", regions)
with col2:
    income_levels = ["All"] + sorted(df["Income Level"].dropna().unique().tolist())
    selected_income = st.selectbox("Filter by Income Level", income_levels)

if selected_region != "All":
    df = df[df["Region"] == selected_region]
if selected_income != "All":
    df = df[df["Income Level"] == selected_income]

st.subheader("Countries")
st.dataframe(df, use_container_width=True, height=420)

st.subheader("Countries by Region")
region_counts = df.groupby("Region").size().rename("Count").sort_values(ascending=False)
st.bar_chart(region_counts)