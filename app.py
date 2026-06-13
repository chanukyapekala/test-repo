import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

DATA_FILE = Path("data/countries.json")
API_URL = "https://api.worldbank.org/v2/country?format=json&per_page=300"

REGION_COLORS = [
    "#2563EB", "#7C3AED", "#0891B2", "#059669",
    "#D97706", "#DC2626", "#DB2777", "#65A30D",
]


def fetch_and_save() -> None:
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    payload = response.json()
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


def format_fetched_at(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except ValueError:
        return iso


# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="World Bank Countries Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  [data-testid="stMetric"] {
      background: #F1F5F9;
      border-radius: 12px;
      padding: 1rem 1.25rem;
      border-left: 4px solid #2563EB;
  }
  [data-testid="stMetricLabel"] { font-size: 0.8rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: .05em; }
  [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; color: #0F172A; }
  .block-container { padding-top: 2rem; }
  h1 { font-weight: 800 !important; }
  [data-testid="stSidebar"] { border-right: 1px solid #E2E8F0; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 Countries Explorer")
    st.markdown("Data sourced from the **World Bank REST API**.")
    st.divider()

    data, fetched_at = load_from_file()
    df_full = to_dataframe(data) if data else pd.DataFrame()

    if not df_full.empty:
        regions = ["All"] + sorted(df_full["Region"].dropna().unique().tolist())
        selected_region = st.selectbox("Region", regions)

        income_levels = ["All"] + sorted(df_full["Income Level"].dropna().unique().tolist())
        selected_income = st.selectbox("Income Level", income_levels)
    else:
        selected_region = "All"
        selected_income = "All"

    st.divider()
    refresh = st.button("⟳  Refresh Data", use_container_width=True, type="primary")
    if fetched_at:
        st.caption(f"Last updated: {format_fetched_at(fetched_at)}")

# ── Fetch ──────────────────────────────────────────────────────────────────────
if refresh:
    with st.spinner("Fetching from World Bank API…"):
        try:
            fetch_and_save()
            st.success("Data refreshed successfully.")
            data, fetched_at = load_from_file()
            df_full = to_dataframe(data) if data else pd.DataFrame()
        except (requests.RequestException, ValueError) as e:
            st.error(f"Fetch failed: {e}")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("World Bank Countries Explorer")
st.markdown("Browse and filter countries by region and income level across the globe.")
st.divider()

# ── Empty state ────────────────────────────────────────────────────────────────
if data is None:
    st.info("No data loaded yet — click **⟳ Refresh Data** in the sidebar to fetch from the World Bank API.")
    st.stop()

# ── Apply filters ──────────────────────────────────────────────────────────────
df = df_full.copy()
if selected_region != "All":
    df = df[df["Region"] == selected_region]
if selected_income != "All":
    df = df[df["Income Level"] == selected_income]

# ── Metrics ────────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Countries", f"{len(df):,}", delta=f"{len(df) - len(df_full):,}" if len(df) != len(df_full) else None)
m2.metric("Regions", df["Region"].nunique())
m3.metric("Income Levels", df["Income Level"].nunique())
m4.metric("With Capital Listed", int(df["Capital"].str.strip().astype(bool).sum()))

st.markdown("<br>", unsafe_allow_html=True)

# ── Table ──────────────────────────────────────────────────────────────────────
st.subheader("Country Directory")
st.dataframe(
    df,
    use_container_width=True,
    height=400,
    column_config={
        "Name": st.column_config.TextColumn("Country", width="medium"),
        "ISO3": st.column_config.TextColumn("ISO3", width="small"),
        "Region": st.column_config.TextColumn("Region", width="medium"),
        "Income Level": st.column_config.TextColumn("Income Level", width="medium"),
        "Capital": st.column_config.TextColumn("Capital City", width="medium"),
    },
    hide_index=True,
)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
chart_col, pie_col = st.columns([3, 2])

with chart_col:
    st.subheader("Countries by Region")
    region_counts = (
        df.groupby("Region").size()
        .rename("Count")
        .reset_index()
        .sort_values("Count", ascending=True)
    )
    fig_bar = px.bar(
        region_counts,
        x="Count",
        y="Region",
        orientation="h",
        color="Count",
        color_continuous_scale=["#BFDBFE", "#2563EB", "#1E3A8A"],
        text="Count",
    )
    fig_bar.update_traces(textposition="outside")
    fig_bar.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=0, r=20, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False),
        yaxis=dict(showgrid=False),
        font=dict(family="sans-serif", size=13),
        height=360,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with pie_col:
    st.subheader("Countries by Income Level")
    income_counts = df.groupby("Income Level").size().rename("Count").reset_index()
    fig_pie = px.pie(
        income_counts,
        names="Income Level",
        values="Count",
        color_discrete_sequence=REGION_COLORS,
        hole=0.45,
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value} countries<extra></extra>",
    )
    fig_pie.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=12),
        height=360,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Data: [World Bank REST API](https://datahelpdesk.worldbank.org/knowledgebase/articles/898590)  ·  Updates only when you click Refresh")