import os
import json
import numpy as np
import pandas as pd
from prophet import Prophet
from json import loads, JSONDecodeError

# ✅ Unified OpenAI initialization (optional)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False


def _get_openai_client():
    """Return initialized OpenAI client if key available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not HAS_OPENAI or api_key in (None, "", "None"):
        print("⚙️ Running in heuristic mode (no OpenAI key found).")
        return None
    try:
        print("🤖 Using OpenAI client with key.")
        return OpenAI(api_key=api_key)
    except Exception as e:
        print("⚠️ OpenAI client init failed:", e)
        return None


# ------------------------------------------------------------
# 1️⃣ Forecast feasibility detection (AI + heuristic fallback)
# ------------------------------------------------------------
# def assess_forecastability(sample_df: pd.DataFrame):
#     def _heuristic(df: pd.DataFrame):
#         cols = df.columns.tolist()

#         # Detect date-like
#         ds_guess = None
#         for c in cols:
#             s = df[c]
#             if np.issubdtype(s.dtype, np.datetime64):
#                 ds_guess = c
#                 break
#             try:
#                 pd.to_datetime(s, errors="raise", dayfirst=True)
#                 ds_guess = c
#                 break
#             except Exception:
#                 pass
#         if ds_guess is None:
#             for c in cols:
#                 lc = c.lower()
#                 if any(k in lc for k in ["date", "ds", "day", "month", "year"]):
#                     ds_guess = c
#                     break

#         # Detect numeric
#         bad_words = {"id", "code", "key"}
#         num_candidates = []
#         for c in cols:
#             if c == ds_guess:
#                 continue
#             lc = c.lower()
#             if any(w in lc for w in bad_words):
#                 continue
#             if pd.api.types.is_numeric_dtype(df[c]):
#                 num_candidates.append(c)
#         y_guess = None
#         for pref in ["sales", "revenue", "amount", "value", "target", "qty", "price"]:
#             for c in num_candidates:
#                 if pref in c.lower():
#                     y_guess = c
#                     break
#             if y_guess:
#                 break
#         if y_guess is None and num_candidates:
#             y_guess = num_candidates[0]

#         ok = ds_guess is not None and y_guess is not None
#         reason = "Detected date and numeric target." if ok else "Could not find a date column and numeric target."
#         return {"possible": ok, "ds": ds_guess, "y": y_guess, "reason": reason}

#     # Try AI client
#     client = _get_openai_client()
#     # if not client:
#     #     return _heuristic(sample_df)

#     try:
#         as_csv = sample_df.to_csv(index=False)
#         cols_str = ", ".join(sample_df.columns.tolist())
#         msg = f"""
# You are given the first 3 rows of a dataset.
# Decide if time-series forecasting is possible.
# Return STRICT JSON: {{possible: bool, ds: string|null, y: string|null, reason: string}}.

# Columns: {cols_str}

# CSV (3 rows):
# {as_csv}
# """
#         resp = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are a careful data analyst. Respond only in JSON."},
#                 {"role": "user", "content": msg},
#             ],
#             temperature=0.2,
#             max_tokens=250,
#         )
#         raw = (resp.choices[0].message.content or "").strip()
#         print("🧠 Raw AI response:\n", raw[:500])

#         # Extract JSON substring between first { and last }
#         if "{" in raw and "}" in raw:
#             json_str = raw[raw.find("{"): raw.rfind("}") + 1]
#         else:
#             json_str = raw

#         try:
#             data = loads(json_str)
#         except Exception:
#             print("⚠️ Could not parse AI output as JSON, falling back to heuristic.")
#             return _heuristic(sample_df)

        
#         if not isinstance(data, dict):
#             return _heuristic(sample_df)
#         if not data.get("possible"):
#             return _heuristic(sample_df)
#         return data
#     except Exception as e:
#         print("⚠️ assess_forecastability AI error:", e)
#         return _heuristic(sample_df)

def assess_forecastability(sample_df: pd.DataFrame):
    """Ask AI which columns represent time (ds) and numeric target (y). No fallback."""
    client = _get_openai_client()
    if not client:
        return {
            "possible": False,
            "ds": None,
            "y": None,
            "reason": "No OpenAI API key or client available. Cannot assess forecasting feasibility."
        }

    try:
        as_csv = sample_df.to_csv(index=False)
        cols_str = ", ".join(sample_df.columns.tolist())
        msg = f"""
You are a data analyst tasked with identifying time-series structure in a dataset.
From the provided sample, determine if forecasting is possible.

Return strict JSON:
{{"possible": bool, "ds": string|null, "y": string|null, "reason": string}}

Guidelines:
- "ds" = column representing dates or time (contains words like 'date', 'day', 'month', 'year').
- "y" = primary numeric column suitable as a target variable (e.g., rainfall, temperature, sales, etc.).
- If multiple numeric targets exist, choose the one that varies meaningfully.
- If the dataset structure strongly suggests a time series, mark "possible" as true.
- Provide a short rationale based on column names and sample values.

Columns: {cols_str}

CSV (first 3 rows):
{as_csv}
"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a careful data analyst. Respond only in JSON."},
                {"role": "user", "content": msg},
            ],
            temperature=0.2,
            max_tokens=250,
        )
        raw = (resp.choices[0].message.content or "").strip()
        print("🧠 Raw AI response:\n", raw[:500])

        if "{" in raw and "}" in raw:
            json_str = raw[raw.find("{"): raw.rfind("}") + 1]
        else:
            json_str = raw

        data = loads(json_str)
        if not isinstance(data, dict):
            raise ValueError("AI response not a valid dict.")

        return {
            "possible": bool(data.get("possible")),
            "ds": data.get("ds"),
            "y": data.get("y"),
            "reason": data.get("reason", "No reason provided.")
        }

    except Exception as e:
        print("⚠️ AI-based assess_forecastability failed:", e)
        return {
            "possible": False,
            "ds": None,
            "y": None,
            "reason": f"AI-based detection failed: {e}"
        }


# ------------------------------------------------------------
# 2️⃣ Insight generation (simple heuristic)
# ------------------------------------------------------------
def _summary_stats(history: pd.DataFrame, forecast: pd.DataFrame):
    df = history.copy()
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.sort_values("ds")
    y = df["y"].values
    n = len(y)
    trend = float(np.polyfit(np.arange(n), y, 1)[0])
    growth = "rising" if trend > 0 else ("falling" if trend < 0 else "flat")
    cv = float(np.std(y) / (np.mean(y) + 1e-9))
    return f"Baseline trend looks {growth} (slope={trend:.4f}). Volatility (CV)={cv:.2f}."


# ------------------------------------------------------------
# 3️⃣ Main trend generation
# ------------------------------------------------------------
def generate_trends_with_ai(df: pd.DataFrame):
    """Forecast + heuristic insights + frontend-friendly (decimated) output"""
    result = {"forecast_info": {}, "forecast_data": {}, "insights": {}}

    # Normalize date columns
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            print("🧠 Converting possible date column:", col)
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # 1️⃣ Assess forecastability
    sample = df.head(3)
    meta = assess_forecastability(sample)
    result["forecast_info"] = meta

    if not meta.get("possible"):
        result["forecast_info"]["forecast_possible"] = False
        result["forecast_info"]["reason"] = meta.get("reason", "Forecasting not possible.")
        return result

    try:
        x_col, y_col = meta["ds"], meta["y"]
        df_prophet = df[[x_col, y_col]].dropna().copy()
        df_prophet[x_col] = pd.to_datetime(df_prophet[x_col], errors="coerce", dayfirst=True)
        df_prophet = df_prophet.dropna(subset=[x_col])
        df_prophet = df_prophet.rename(columns={x_col: "ds", y_col: "y"})
        df_prophet = df_prophet.groupby("ds").sum().reset_index()

        # 2️⃣ Fit Prophet model
        from prophet import Prophet
        model = Prophet()
        model.fit(df_prophet)

        # 3️⃣ Forecast
        future = model.make_future_dataframe(periods=15)
        forecast = model.predict(future)

        # Keep full forecast for backend reference
        full_points = len(forecast)

        # 4️⃣ Downsample for frontend
        max_points = 500
        if full_points > max_points:
            step = full_points // max_points
            forecast = forecast.iloc[::step].reset_index(drop=True)
            print(f"📉 Decimated forecast from {full_points} → {len(forecast)} points")

        # 5️⃣ Build chart-ready result
        result["forecast_data"] = {
            "labels": forecast["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "series": [{
                "name": y_col,
                "values": forecast["yhat"].round(2).tolist()
            }],
            "x_col": x_col,
            "y_col": y_col,
            "total_points": int(full_points),
            "sent_points": int(len(forecast))
        }

        result["forecast_info"] = {
            "forecast_possible": True,
            "x_axis": x_col,
            "y_axis": y_col,
            "reason": f"{meta.get('reason', '')} Forecast generated using '{x_col}' and '{y_col}'.",
            "data_reduction": f"Sent {len(forecast)} of {full_points} points for performance."
        }

        # 6️⃣ Add summary insights
        result["insights"] = {
            "heuristics": _summary_stats(df_prophet, forecast)
        }

    except Exception as e:
        print("⚠️ Forecasting failed:", e)
        result["forecast_info"] = {
            "forecast_possible": False,
            "x_axis": None,
            "y_axis": None,
            "reason": f"Forecasting failed: {e}"
        }

    return result

