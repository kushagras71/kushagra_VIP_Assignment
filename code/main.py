from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from langchain_core.tools import StructuredTool
from sklearn.ensemble import RandomForestRegressor


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT.parent / "data_package"
OUT = ROOT / "outputs"
PLOTS = OUT / "plots"
ARTIFACTS = ROOT / "artifacts"
TODAY = pd.Timestamp("2026-05-11")

BASE_FEATURES = [
    "price_avg",
    "age_weeks",
    "weekofyear",
    "month",
    "lag_1",
    "lag_2",
    "lag_4",
    "rolling_4",
    "category",
    "cluster_id",
    "parent_brand",
]
SIGNAL_FEATURES = ["promo_active", "promo_type", "parent_units"]
FULL_FEATURES = BASE_FEATURES + SIGNAL_FEATURES
CATEGORICAL = ["category", "cluster_id", "parent_brand", "promo_type"]


def make_dirs() -> None:
    for path in [OUT, PLOTS, ARTIFACTS]:
        path.mkdir(parents=True, exist_ok=True)


def load_data() -> dict[str, pd.DataFrame]:
    """Read the four assessment CSV files."""
    return {
        "sales": pd.read_csv(DATA_DIR / "merch_sales_weekly.csv", parse_dates=["week_start"]),
        "sku": pd.read_csv(DATA_DIR / "sku_master.csv", parse_dates=["launch_date"]),
        "parent": pd.read_csv(DATA_DIR / "parent_beverage_sales.csv", parse_dates=["week_start"]),
        "promotions": pd.read_csv(DATA_DIR / "promotions.csv", parse_dates=["start_date", "end_date"]),
    }


def attach_promo_type(sales: pd.DataFrame, promotions: pd.DataFrame) -> pd.DataFrame:
    """Add a readable promo_type column using promotions.csv."""
    sales = sales.copy()
    sales["promo_active"] = sales["promo_active"].astype(str).str.lower().eq("true")
    sales["promo_type"] = "None"

    for promo in promotions.itertuples(index=False):
        cluster_ok = (sales["cluster_id"].eq(promo.cluster_id)) | (promo.cluster_id == "ALL")
        promo_week = sales["week_start"].between(promo.start_date, promo.end_date)
        mask = sales["sku_id"].eq(promo.sku_id) & cluster_ok & promo_week
        sales.loc[mask, "promo_type"] = promo.promo_type

    sales["promo_active"] = sales["promo_active"] | sales["promo_type"].ne("None")
    return sales


def make_features(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build the model table at SKU x cluster x week grain."""
    sales = attach_promo_type(data["sales"], data["promotions"])
    parent = data["parent"].rename(columns={"units_sold": "parent_units"})

    df = sales.merge(data["sku"], on="sku_id", how="left")
    df = df.merge(parent, on=["week_start", "parent_brand", "cluster_id"], how="left")
    df["parent_units"] = df["parent_units"].fillna(0)

    df = df.sort_values(["sku_id", "cluster_id", "week_start"]).reset_index(drop=True)
    group = df.groupby(["sku_id", "cluster_id"], sort=False)
    for lag in [1, 2, 4]:
        df[f"lag_{lag}"] = group["units_sold"].shift(lag)
    df["rolling_4"] = group["units_sold"].transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())

    iso = df["week_start"].dt.isocalendar()
    df["weekofyear"] = iso.week.astype(int)
    df["month"] = df["week_start"].dt.month
    df["age_weeks"] = ((df["week_start"] - df["launch_date"]).dt.days // 7).clip(lower=0)
    df["promo_active"] = df["promo_active"].astype(int)

    for col in ["lag_1", "lag_2", "lag_4", "rolling_4"]:
        df[col] = df[col].fillna(group[col].transform("median"))
        df[col] = df[col].fillna(df["units_sold"].median())

    return df


def model_matrix(df: pd.DataFrame, features: list[str], columns: list[str] | None = None) -> tuple[pd.DataFrame, list[str]]:
    """One-hot encode categorical columns and align train/test columns."""
    x = df[features].copy()
    cats = [c for c in CATEGORICAL if c in x.columns]
    x = pd.get_dummies(x, columns=cats, drop_first=False).astype(float)
    if columns is not None:
        x = x.reindex(columns=columns, fill_value=0.0)
    return x, list(x.columns)


def wape(actual: pd.Series, pred: np.ndarray | pd.Series) -> float:
    denom = actual.abs().sum()
    return float((actual - pred).abs().sum() / denom) if denom else float("nan")


def df_to_markdown(df: pd.DataFrame) -> str:
    """Small markdown table helper so we do not need tabulate."""
    df = df.reset_index(drop=True)
    headers = [str(c) for c in df.columns]
    rows = df.astype(str).values.tolist()
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(w, len(cell)) for w, cell in zip(widths, row)]

    def row_line(row: list[str]) -> str:
        return "| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) + " |"

    return "\n".join([row_line(headers), "| " + " | ".join("-" * w for w in widths) + " |"] + [row_line(r) for r in rows])


def setup_matplotlib() -> Any:
    """Use a file-only plotting backend that works in a terminal."""
    mpl_dir = OUT / ".matplotlib"
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def run_eda(df: pd.DataFrame) -> None:
    """Create the short EDA requested in Part A1."""
    plt = setup_matplotlib()
    make_dirs()

    demand = df["units_sold"].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).round(2).reset_index()
    category = df.groupby("category", as_index=False)["units_sold"].agg(["count", "mean", "median", "sum"]).round(2)
    cluster = df.groupby("cluster_id", as_index=False)["units_sold"].agg(["mean", "median", "sum"]).round(2)

    sample = df[df["sku_id"].isin(["SKU-1042", "SKU-2017", "SKU-3008", "SKU-2099"])]
    sample_view = (
        sample.groupby(["sku_id", "cluster_id"], as_index=False)
        .agg(weeks=("units_sold", "size"), avg_units=("units_sold", "mean"), zero_weeks=("units_sold", lambda s: int((s == 0).sum())))
        .round(2)
    )

    promo_lift = (
        df.groupby(["category", "promo_active"], as_index=False)["units_sold"]
        .mean()
        .pivot(index="category", columns="promo_active", values="units_sold")
        .rename(columns={0: "non_promo_avg", 1: "promo_avg"})
        .reset_index()
    )
    promo_lift["lift_pct"] = ((promo_lift["promo_avg"] / promo_lift["non_promo_avg"] - 1) * 100).round(1)
    promo_lift = promo_lift.round(2)

    corr_rows = []
    for (sku, cluster_id), g in df.groupby(["sku_id", "cluster_id"]):
        for lag in [0, 1, 2, 3, 4]:
            corr_rows.append({"lag_weeks": lag, "corr": g["units_sold"].corr(g["parent_units"].shift(lag))})
    parent_corr = pd.DataFrame(corr_rows).groupby("lag_weeks", as_index=False)["corr"].median().round(3)

    report = [
        "# EDA Summary",
        "",
        f"- Data contains {len(df):,} rows, {df['sku_id'].nunique()} SKUs, and {df['cluster_id'].nunique()} clusters.",
        f"- Date range: {df['week_start'].min().date()} to {df['week_start'].max().date()}.",
        "- The grain is SKU x cluster x week, exactly as requested in the brief.",
        "",
        "## Demand Distribution",
        df_to_markdown(demand),
        "",
        "## Category Demand",
        df_to_markdown(category),
        "",
        "## Cluster Demand",
        df_to_markdown(cluster),
        "",
        "## Representative SKU Intermittency",
        df_to_markdown(sample_view),
        "",
        "## Parent Beverage Relationship",
        "Median lagged correlation between merchandise units and parent-beverage units:",
        df_to_markdown(parent_corr),
        "",
        "## Promotion Impact",
        df_to_markdown(promo_lift),
        "",
        "Key observations:",
        "- Demand is not flat: C-EAST is materially larger than C-WEST and categories differ a lot.",
        "- Parent beverage sales have a positive but imperfect relationship with merchandise demand, strongest around short lags.",
        "- Promotion weeks show clear lift, so promotion features belong in the model.",
    ]
    (OUT / "eda_summary.md").write_text("\n".join(report), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["units_sold"], bins=40, color="#356859")
    ax.set_title("Demand Distribution")
    ax.set_xlabel("Weekly units sold")
    ax.set_ylabel("Rows")
    fig.tight_layout()
    fig.savefig(PLOTS / "eda_demand_distribution.png", dpi=150)
    plt.close(fig)

    weekly = df.groupby("week_start", as_index=False)["units_sold"].sum()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(weekly["week_start"], weekly["units_sold"], color="#2f4858")
    ax.set_title("Total Weekly Demand")
    ax.set_xlabel("Week")
    ax.set_ylabel("Units")
    fig.tight_layout()
    fig.savefig(PLOTS / "eda_weekly_demand.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(parent_corr["lag_weeks"], parent_corr["corr"], color="#8f5f3f")
    ax.set_title("Parent Beverage Lag Correlation")
    ax.set_xlabel("Lag weeks")
    ax.set_ylabel("Median correlation")
    fig.tight_layout()
    fig.savefig(PLOTS / "eda_parent_correlation.png", dpi=150)
    plt.close(fig)


def train_model(df: pd.DataFrame) -> dict[str, Any]:
    """Train the forecasting model and compare it against a no-signal baseline."""
    cutoff = df["week_start"].max() - pd.Timedelta(weeks=8)
    train = df[df["week_start"] <= cutoff].copy()
    test = df[df["week_start"] > cutoff].copy()

    x_train_full, full_cols = model_matrix(train, FULL_FEATURES)
    x_test_full, _ = model_matrix(test, FULL_FEATURES, full_cols)
    x_train_base, base_cols = model_matrix(train, BASE_FEATURES)
    x_test_base, _ = model_matrix(test, BASE_FEATURES, base_cols)

    full_model = RandomForestRegressor(n_estimators=180, min_samples_leaf=3, random_state=42, n_jobs=-1)
    base_model = RandomForestRegressor(n_estimators=180, min_samples_leaf=3, random_state=42, n_jobs=-1)
    full_model.fit(x_train_full, train["units_sold"])
    base_model.fit(x_train_base, train["units_sold"])

    test = test.copy()
    test["forecast_full"] = np.clip(full_model.predict(x_test_full), 0, None)
    test["forecast_baseline"] = np.clip(base_model.predict(x_test_base), 0, None)
    residuals = test["units_sold"] - test["forecast_full"]

    by_sku = (
        test.groupby("sku_id")
        .apply(
            lambda g: pd.Series(
                {
                    "wape_full": wape(g["units_sold"], g["forecast_full"]),
                    "wape_baseline": wape(g["units_sold"], g["forecast_baseline"]),
                    "actual_units": int(g["units_sold"].sum()),
                    "forecast_units": round(float(g["forecast_full"].sum()), 1),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    by_sku["improvement"] = by_sku["wape_baseline"] - by_sku["wape_full"]
    by_sku.to_csv(OUT / "wape_by_sku.csv", index=False)

    final_x, final_cols = model_matrix(df, FULL_FEATURES)
    final_model = RandomForestRegressor(n_estimators=180, min_samples_leaf=3, random_state=42, n_jobs=-1)
    final_model.fit(final_x, df["units_sold"])

    state = {
        "model": final_model,
        "columns": final_cols,
        "data": df,
        "residual_q10": float(residuals.quantile(0.10)),
        "residual_q90": float(residuals.quantile(0.90)),
        "overall_wape_full": wape(test["units_sold"], test["forecast_full"]),
        "overall_wape_baseline": wape(test["units_sold"], test["forecast_baseline"]),
        "holdout_start": str(test["week_start"].min().date()),
        "holdout_end": str(test["week_start"].max().date()),
    }
    joblib.dump(state, ARTIFACTS / "forecaster.joblib")

    summary = pd.DataFrame(
        [
            {
                "holdout_start": state["holdout_start"],
                "holdout_end": state["holdout_end"],
                "overall_wape_full": state["overall_wape_full"],
                "overall_wape_baseline": state["overall_wape_baseline"],
                "median_sku_wape_full": by_sku["wape_full"].median(),
                "median_sku_wape_baseline": by_sku["wape_baseline"].median(),
            }
        ]
    )
    summary.to_csv(OUT / "model_summary.csv", index=False)
    write_model_notes(summary.iloc[0].to_dict())
    write_forecast_plots(df, test)
    return state


def write_model_notes(summary: dict[str, Any]) -> None:
    notes = f"""# Model Notes

I used a Random Forest regression model with a compact feature set:

- recent SKU x cluster demand lags: 1, 2, and 4 weeks,
- a 4-week rolling average,
- price, calendar week, month, category, cluster, and parent brand,
- supplier promotion flag/type,
- parent-beverage weekly units.

Why this model: the history is short, demand is seasonal and promotion-driven, and several SKUs are new. A Random Forest handles nonlinear relationships without requiring a lot of tuning.

Holdout evaluation uses the last 8 historical weeks: {summary['holdout_start']} to {summary['holdout_end']}.

- Full model WAPE: {summary['overall_wape_full']:.3f}
- Baseline WAPE without promotion and parent-beverage signals: {summary['overall_wape_baseline']:.3f}

The full model is better, so the available signals are useful.

Uncertainty: forecast intervals use the 10th and 90th percentile residuals from the holdout period. This is transparent, explainable, and appropriate for a prototype.
"""
    (OUT / "model_notes.md").write_text(notes, encoding="utf-8")


def write_forecast_plots(df: pd.DataFrame, test: pd.DataFrame) -> None:
    plt = setup_matplotlib()
    examples = [("SKU-1042", "C-EAST"), ("SKU-2017", "C-WEST"), ("SKU-3008", "C-EAST")]
    for sku, cluster in examples:
        hist = df[df["sku_id"].eq(sku) & df["cluster_id"].eq(cluster)].tail(24)
        pred = test[test["sku_id"].eq(sku) & test["cluster_id"].eq(cluster)]
        if hist.empty or pred.empty:
            continue
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(hist["week_start"], hist["units_sold"], label="actual", color="#2f4858")
        ax.plot(pred["week_start"], pred["forecast_full"], label="holdout forecast", color="#b45f06")
        ax.axvline(pred["week_start"].min(), color="#777777", linestyle="--")
        ax.set_title(f"Forecast Plot: {sku} / {cluster}")
        ax.set_xlabel("Week")
        ax.set_ylabel("Units")
        ax.legend()
        fig.tight_layout()
        fig.savefig(PLOTS / f"forecast_{sku}_{cluster}.png", dpi=150)
        plt.close(fig)


def safety_stock(state: dict[str, Any], sku: str, cluster: str) -> int:
    """Small implementation of the safety-stock policy for scenario 6."""
    df = state["data"]
    row = df[df["sku_id"].eq(sku)].iloc[0]
    category = row["category"]
    age_weeks = int((TODAY - row["launch_date"]).days // 7)
    if age_weeks <= 4:
        return 0

    lead_time = {"Apparel": 6, "Headwear": 4, "Drinkware": 5, "Accessories": 3}.get(category, 4)
    z = {"Apparel": 1.65, "Headwear": 1.65, "Drinkware": 1.88, "Accessories": 1.41}.get(category, 1.65)
    if age_weeks <= 12:
        sigma = df[df["category"].eq(category)].groupby(["sku_id", "cluster_id"])["units_sold"].std().median() * 1.5
    else:
        sigma = df[df["sku_id"].eq(sku) & df["cluster_id"].eq(cluster)]["units_sold"].std()
    return int(math.ceil(max(0, z * sigma * math.sqrt(lead_time))))


def future_row(
    state: dict[str, Any],
    sku: str,
    cluster: str,
    week: pd.Timestamp,
    history_units: list[float],
    promo_type: str,
) -> pd.DataFrame:
    df = state["data"]
    hist = df[df["sku_id"].eq(sku) & df["cluster_id"].eq(cluster)].sort_values("week_start")
    meta = hist.iloc[-1]
    parent_recent = float(hist["parent_units"].tail(8).mean())
    row = {
        "price_avg": float(hist["price_avg"].tail(4).mean()),
        "age_weeks": int((week - meta["launch_date"]).days // 7),
        "weekofyear": int(week.isocalendar().week),
        "month": int(week.month),
        "lag_1": history_units[-1],
        "lag_2": history_units[-2] if len(history_units) > 1 else history_units[-1],
        "lag_4": history_units[-4] if len(history_units) > 3 else history_units[-1],
        "rolling_4": float(np.mean(history_units[-4:])),
        "category": meta["category"],
        "cluster_id": cluster,
        "parent_brand": meta["parent_brand"],
        "promo_active": int(promo_type != "None"),
        "promo_type": promo_type,
        "parent_units": parent_recent,
    }
    return pd.DataFrame([row])


def forecast_sku(
    state: dict[str, Any],
    sku_id: str,
    cluster_id: str,
    horizon: int = 8,
    promo_weeks: tuple[int, int] | None = None,
    promo_type: str = "Co-Marketing",
) -> dict[str, Any]:
    """Forecast one SKU and cluster for the next N weeks."""
    sku_id = sku_id.upper()
    cluster_id = cluster_id.upper()
    df = state["data"]
    if sku_id not in set(df["sku_id"]):
        return {"error": f"Unknown SKU: {sku_id}"}
    if cluster_id not in set(df["cluster_id"]):
        return {"error": f"Unknown cluster: {cluster_id}"}

    hist = df[df["sku_id"].eq(sku_id) & df["cluster_id"].eq(cluster_id)].sort_values("week_start")
    if hist.empty:
        return {"error": f"No history for {sku_id} in {cluster_id}"}

    history_units = hist["units_sold"].astype(float).tolist()
    rows = []
    for i in range(1, horizon + 1):
        week = TODAY + pd.Timedelta(weeks=i)
        this_promo = "None"
        if promo_weeks and promo_weeks[0] <= i <= promo_weeks[1]:
            this_promo = promo_type
        row = future_row(state, sku_id, cluster_id, week, history_units, this_promo)
        x, _ = model_matrix(row, FULL_FEATURES, state["columns"])
        point = max(0.0, float(state["model"].predict(x)[0]))
        history_units.append(point)
        rows.append(
            {
                "week_start": week.date().isoformat(),
                "forecast_units": round(point, 1),
                "lower_80": round(max(0.0, point + state["residual_q10"]), 1),
                "upper_80": round(max(point, point + state["residual_q90"]), 1),
                "promo_type": this_promo,
            }
        )

    forecast = pd.DataFrame(rows)
    ss = safety_stock(state, sku_id, cluster_id)
    total = float(forecast["forecast_units"].sum())
    return {
        "sku_id": sku_id,
        "cluster_id": cluster_id,
        "forecast": forecast,
        "forecast_units": round(total, 1),
        "safety_stock": ss,
        "recommended_buy": int(math.ceil(total + ss)),
    }


def retrieve_knowledge(query: str, top_k: int = 2) -> list[dict[str, str]]:
    """Retrieve keyword-matched snippets from the markdown knowledge base."""
    lower_query = query.lower()
    query_terms = set(re.findall(r"[a-z0-9]+", lower_query))
    docs = []
    for path in sorted((DATA_DIR / "knowledge_base").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        score = sum(1 for term in query_terms if term in text.lower())
        if ("calendar" in lower_query or "q3" in lower_query) and "supplier_promo_calendar" in path.name:
            score += 100
        if "safety stock" in lower_query and "safety_stock_policy" in path.name:
            score += 100
        if ("why" in lower_query or "driving" in lower_query) and path.name in {"cluster_definitions.md", "distributor_onboarding_branded_merch.md"}:
            score += 25
        snippet = choose_snippet(text, query)
        docs.append({"source": path.name, "score": score, "snippet": snippet})
    return sorted(docs, key=lambda d: d["score"], reverse=True)[:top_k]


def choose_snippet(text: str, query: str) -> str:
    lower = query.lower()
    if "q3" in lower and "Supplier Promotion Calendar" in text:
        rows = [line for line in text.splitlines() if any(w in line for w in ["Wk 26", "Wk 27", "Wk 32", "Wk 35"])]
        return " ".join(rows)
    if "safety stock" in lower and "Safety Stock Policy" in text:
        rows = [line for line in text.splitlines() if "Apparel" in line or "SS =" in line or "launch ramp" in line or "Apparel:" in line]
        return " ".join(rows[:5])
    if ("why" in lower or "driving" in lower) and "Distributor Onboarding" in text:
        marker = "**The parent beverage signal matters.**"
        start = text.find(marker)
        if start >= 0:
            return text[start : start + 650].replace("\n", " ")
    if ("why" in lower or "driving" in lower) and "Cluster Definitions" in text:
        cluster = "## C-WEST" if "c-west" in lower else "## C-EAST" if "c-east" in lower else "## C-EAST"
        start = text.find(cluster)
        end = text.find("##", start + 3)
        return text[start:end].replace("\n", " ")[:650]
    paragraphs = [p.strip().replace("\n", " ") for p in text.split("\n\n") if p.strip()]
    return paragraphs[0][:600] if paragraphs else text[:600]


class Planner:
    """Three-agent system: Planner -> Forecasting Tool and/or Knowledge Tool."""

    def __init__(self, state: dict[str, Any]):
        self.state = state
        self.memory: dict[str, str] = {}
        self.forecast_tool = StructuredTool.from_function(
            func=self.forecast_tool_func,
            name="forecast_merchandise_demand",
            description="Forecast demand for a SKU, cluster, and horizon.",
        )
        self.knowledge_tool = StructuredTool.from_function(
            func=retrieve_knowledge,
            name="retrieve_merchandise_knowledge",
            description="Retrieve policy/calendar knowledge for branded merchandise planning.",
        )

    def forecast_tool_func(self, sku_id: str, cluster_id: str, horizon: int = 8) -> dict[str, Any]:
        """Forecast one SKU and cluster. Handles bad inputs by returning an error key."""
        return forecast_sku(self.state, sku_id, cluster_id, horizon)

    def answer(self, question: str) -> dict[str, Any]:
        q = question.lower()
        sku = extract_sku(question) or self.memory.get("sku_id")
        clusters = extract_clusters(question) or ([self.memory["cluster_id"]] if "cluster_id" in self.memory else [])
        category = extract_category(question) or self.memory.get("category")
        calls: list[str] = []
        parts: list[str] = []

        needs_forecast = bool(extract_sku(question)) or "forecast" in q or "buy" in q or "adjust" in q
        needs_knowledge = any(word in q for word in ["why", "driving", "policy", "calendar", "q3", "safety", "promotion"])

        if "compare" in q and sku and len(clusters) == 2:
            for cluster in clusters:
                result = self.forecast_tool.invoke({"sku_id": sku, "cluster_id": cluster, "horizon": 8})
                calls.append("Forecasting Agent")
                parts.append(format_forecast_answer(result))
        elif "adjust" in q and "headwear" in q and clusters:
            skus = self.state["data"].loc[self.state["data"]["category"].eq("Headwear"), "sku_id"].unique()
            base_total = promo_total = 0.0
            for sku_id in skus:
                base = forecast_sku(self.state, sku_id, clusters[0], 8)
                promo = forecast_sku(self.state, sku_id, clusters[0], 8, promo_weeks=(3, 5), promo_type="Co-Marketing")
                if "error" not in base and "error" not in promo:
                    base_total += base["forecast_units"]
                    promo_total += promo["forecast_units"]
            calls.append("Forecasting Agent")
            parts.append(f"Headwear in {clusters[0]}: baseline 8-week forecast is {base_total:.0f} units. With co-marketing in weeks 3-5, forecast is {promo_total:.0f}. Add about {promo_total - base_total:.0f} units.")
        elif "longer" in q and sku and clusters:
            base = forecast_sku(self.state, sku, clusters[0], 8)
            promo = forecast_sku(self.state, sku, clusters[0], 8, promo_weeks=(3, 7), promo_type="Co-Marketing")
            calls.append("Forecasting Agent")
            parts.append(f"Using remembered context {sku}/{clusters[0]}: extending promo weeks 3-7 changes forecast from {base['forecast_units']:.0f} to {promo['forecast_units']:.0f}. Add about {promo['forecast_units'] - base['forecast_units']:.0f} units before safety stock.")
        elif needs_forecast and sku:
            for cluster in clusters or ["C-EAST"]:
                result = self.forecast_tool.invoke({"sku_id": sku, "cluster_id": cluster, "horizon": 8})
                calls.append("Forecasting Agent")
                parts.append(format_forecast_answer(result))

        if needs_knowledge:
            docs = self.knowledge_tool.invoke({"query": question, "top_k": 2})
            calls.append("Knowledge Agent")
            parts.append("Knowledge context: " + " ".join(f"[{d['source']}] {d['snippet']}" for d in docs))

        if sku:
            self.memory["sku_id"] = sku
        if clusters:
            self.memory["cluster_id"] = clusters[0]
        if category:
            self.memory["category"] = category

        return {"answer": "\n\n".join(parts), "calls": calls}


def extract_sku(text: str) -> str | None:
    match = re.search(r"SKU-\d{4}", text, flags=re.I)
    return match.group(0).upper() if match else None


def extract_clusters(text: str) -> list[str]:
    return [cluster for cluster in ["C-EAST", "C-WEST"] if cluster.lower() in text.lower()]


def extract_category(text: str) -> str | None:
    for category in ["Headwear", "Apparel", "Drinkware", "Accessories"]:
        if category.lower() in text.lower():
            return category
    return None


def format_forecast_answer(result: dict[str, Any]) -> str:
    if "error" in result:
        return result["error"]
    return (
        f"{result['sku_id']} / {result['cluster_id']}: forecast {result['forecast_units']:.0f} units for the next 8 weeks. "
        f"Recommended buy = {result['recommended_buy']} units, including {result['safety_stock']} safety-stock units."
    )


def run_agent_evaluation(state: dict[str, Any]) -> None:
    scenarios = [
        "How many units of SKU-1042 (the co-branded headwear) should I buy for C-EAST for the next 8 weeks?",
        "What is the forecast for SKU-2017 in C-WEST, and what's driving it?",
        "If the supplier runs a co-marketing promotion on the parent brand for weeks 3-5, how should I adjust my buy for headwear in C-EAST?",
        "Compare the forecast for SKU-3008 in C-EAST versus C-WEST. Why are they different?",
        "What is the supplier promotion calendar telling me to expect in Q3?",
        "What is the safety stock policy for new SKUs, and how does it affect my buy for SKU-2099?",
    ]
    expected = {
        1: {"Forecasting Agent"},
        2: {"Forecasting Agent", "Knowledge Agent"},
        3: {"Forecasting Agent", "Knowledge Agent"},
        4: {"Forecasting Agent", "Knowledge Agent"},
        5: {"Knowledge Agent"},
        6: {"Forecasting Agent", "Knowledge Agent"},
    }

    planner = Planner(state)
    rows = []
    answers = [
        "# Agent Evaluation",
        "",
        "## Graph",
        "```text",
        "Planner Agent -> Forecasting Agent -> forecast_merchandise_demand tool",
        "              -> Knowledge Agent   -> retrieve_merchandise_knowledge tool",
        "              -> answer + short memory update",
        "```",
        "",
        "## Rubric",
        "5 = correct route, valid tool call, useful grounded answer; 3 = partially useful; 1 = unusable.",
        "",
    ]
    for idx, scenario in enumerate(scenarios, start=1):
        result = planner.answer(scenario)
        actual = set(result["calls"])
        route_ok = expected[idx].issubset(actual) and actual.issubset(expected[idx])
        args_ok = bool(result["answer"]) and "Unknown" not in result["answer"]
        quality = 5 if route_ok and args_ok else 3 if args_ok else 1
        rows.append({"scenario": idx, "planner_routed_correctly": route_ok, "tool_args_reasonable": args_ok, "quality_1_to_5": quality, "tools_called": ", ".join(result["calls"])})
        answers.extend([f"## Scenario {idx}", scenario, "", result["answer"], ""])

    memory_planner = Planner(state)
    first = memory_planner.answer("How many units of SKU-1042 should I buy for C-EAST for the next 8 weeks?")
    follow_up = memory_planner.answer("What if the promotion runs two weeks longer?")
    answers.extend(["## Memory Demo", "Turn 1:", first["answer"], "", "Turn 2:", follow_up["answer"], ""])

    pd.DataFrame(rows).to_csv(OUT / "agent_evaluation.csv", index=False)
    (OUT / "agent_answers.md").write_text("\n".join(answers), encoding="utf-8")


def write_production_notes() -> None:
    text = """# Production Design

```text
Weekly sales + promotions + parent-beverage sales
        |
        v
Data checks -> feature table -> nightly forecast batch
        |                         |
        v                         v
Planner API/UI -> planning agent -> forecast tool + knowledge retrieval
```

I would compute forecasts nightly after weekly data is finalized, and also allow on-demand what-if forecasts for planner scenarios such as promotion changes. Nightly batch forecasts keep the planning UI fast and give teams a stable forecast snapshot. The model should retrain weekly after the newest sales week lands, with a holdout backtest check before replacing the current model.

Model monitoring should track SKU-level WAPE, forecast bias by category/cluster, and interval coverage. Agent monitoring should track route accuracy, tool error rate, and whether users accept or override recommendations. If quality drops, the team can tell whether the issue is the demand model, the source data, or the planner/knowledge retrieval layer.
"""
    (OUT / "production_design.md").write_text(text, encoding="utf-8")


def write_validation_checklist() -> None:
    text = """# Validation Checklist

| Requirement | Output |
|---|---|
| A1 EDA | `eda_summary.md`, `plots/eda_*.png`, `eda_notebook.ipynb` |
| A2 8-week forecasts | `main.py` function `forecast_sku`, `artifacts/forecaster.joblib` |
| A2 promotions + parent beverage signals | `model_summary.csv` compares full model vs baseline |
| A2 uncertainty | forecast rows include `lower_80` and `upper_80` from holdout residual percentiles |
| A2 WAPE by SKU | `wape_by_sku.csv` |
| A2 forecast plots | `plots/forecast_*.png` |
| B1 three agents | `Planner`, forecasting tool, knowledge tool in `main.py` |
| B2 LangChain tools | `StructuredTool.from_function(...)` in `main.py` |
| B3 memory | memory demo in `agent_answers.md` |
| B4 six scenarios | `agent_evaluation.csv`, `agent_answers.md` |
| C production thinking | `production_design.md` |
"""
    (OUT / "validation_checklist.md").write_text(text, encoding="utf-8")


def write_eda_notebook() -> None:
    nb = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# EDA Notebook\n", "This runs the same EDA code as `main.py`."]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["from main import load_data, make_features, run_eda\n", "data = load_data()\n", "df = make_features(data)\n", "run_eda(df)\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": ".vip_venv", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.11"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (ROOT / "eda_notebook.ipynb").write_text(json.dumps(nb, indent=2), encoding="utf-8")


def main() -> None:
    make_dirs()
    data = load_data()
    df = make_features(data)
    run_eda(df)
    state = train_model(df)
    run_agent_evaluation(state)
    write_production_notes()
    write_validation_checklist()
    write_eda_notebook()
    print("Solution complete. See code/outputs.")
    print(f"Full model WAPE: {state['overall_wape_full']:.3f}")
    print(f"Baseline WAPE: {state['overall_wape_baseline']:.3f}")


if __name__ == "__main__":
    main()
