from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import io
import json
import pandas as pd
import numpy as np
import math

from services.eda_service import get_eda_summary

from services.ai_agent import run_ai_agent
from services.insights_service import refine_insights_with_rag
from models.responses import DashboardResponse
from services.trends_service import generate_trends_with_ai

from services.rag_service import build_rag_index
# --------------------------------------------------
# Helper: convert NumPy + pandas objects to Python
# --------------------------------------------------
def to_python(obj):
    """Recursively convert numpy and pandas objects to native Python types."""
    if isinstance(obj, (np.generic,)):
        return obj.item()
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    if isinstance(obj, (list, tuple, set)):
        return [to_python(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_python(v) for k, v in obj.items()}
    return obj


# --------------------------------------------------
# FastAPI setup
# --------------------------------------------------
app = FastAPI(title="AI Dashboard Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Upload route
# --------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1️⃣ Load CSV
    df = pd.read_csv(io.BytesIO(await file.read()))

    # 2️⃣ Generate EDA + build RAG index
    eda = get_eda_summary(df)
    store = build_rag_index(df)

    # 3️⃣ Ask the AI agent for dashboard plan
    plan = run_ai_agent(eda, df)

    

    # 4️⃣ Compute KPI values
    formatted_kpis = []
    for k in plan.get("kpis", []):
        cols = k.get("related_columns", []) or k.get("columns", [])
        value = "N/A"

        try:
            # single numeric column → sum
            if len(cols) == 1 and cols[0] in df.columns:
                col = df[cols[0]]
                if pd.api.types.is_numeric_dtype(col):
                    value = round(col.sum(), 2)

            # two numeric columns → ratio
            elif len(cols) == 2 and all(c in df.columns for c in cols):
                num, denom = cols[0], cols[1]
                if pd.api.types.is_numeric_dtype(df[num]) and pd.api.types.is_numeric_dtype(df[denom]):
                    ratio = df[num].sum() / max(df[denom].sum(), 1)
                    value = round(ratio, 2)

            # categorical column → unique count
            elif len(cols) == 1 and not pd.api.types.is_numeric_dtype(df[cols[0]]):
                value = df[cols[0]].nunique()

        except Exception as e:
            print(f"KPI calc error for {k.get('name')}: {e}")

        formatted_kpis.append({
            "name": k.get("name"),
            "description": k.get("description"),
            "value": to_python(value)
        })

    # 5️⃣ Compute chart data
    formatted_charts = []
    for c in plan.get("charts", []):
        chart_type = (c.get("type") or "").lower()
        cols = c.get("columns", [])
        data = {"labels": [], "series": []}

        try:
            # ---- Time-series / line ----
            if chart_type in ["line", "timeseries"]:
                date_col = next((col for col in cols if "date" in col.lower()), None)
                num_col = next((col for col in cols if pd.api.types.is_numeric_dtype(df[col])), None)
                if date_col and num_col:
                    temp = df.copy()
                    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                    temp = temp.groupby(date_col)[num_col].sum().reset_index().sort_values(by=date_col)
                    data = {
                        "labels": [to_python(x) for x in temp[date_col].dt.strftime("%Y-%m-%d").tolist()],
                        "series": [{"name": num_col, "values": [to_python(v) for v in temp[num_col].round(2).tolist()]}]
                    }

            # ---- Bar ----
            elif chart_type == "bar":
                cat_col = next((col for col in cols if df[col].dtype == "object"), None)
                num_col = next((col for col in cols if pd.api.types.is_numeric_dtype(df[col])), None)
                if cat_col and num_col:
                    temp = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()
                    data = {
                        "labels": [to_python(v) for v in temp[cat_col].astype(str).tolist()],
                        "series": [{"name": num_col, "values": [to_python(v) for v in temp[num_col].round(2).tolist()]}]
                    }

            # ---- Pie ----
            elif chart_type == "pie":
                cat_col = next((col for col in cols if df[col].dtype == "object"), None)
                num_col = next((col for col in cols if pd.api.types.is_numeric_dtype(df[col])), None)
                if cat_col and num_col:
                    temp = df.groupby(cat_col)[num_col].sum().nlargest(6).reset_index()
                    data = {
                        "labels": [to_python(v) for v in temp[cat_col].astype(str).tolist()],
                        "series": [{"name": num_col, "values": [to_python(v) for v in temp[num_col].round(2).tolist()]}]
                    }

        except Exception as e:
            print(f"Chart data error for {c.get('title')}: {e}")

        formatted_charts.append({
            "title": c.get("title"),
            "type": chart_type,
            "data": data
        })

    # 6️⃣ Refine insights using RAG
    # refined = refine_insights_with_rag(plan.get("insights_flat", []), store, eda)

    detailed_insights = refine_insights_with_rag(
        plan.get("insights_flat", []),
        store,
        eda
    )
    print("detailed insights",detailed_insights)

    # 7️⃣ Assemble final response
    response = DashboardResponse(
        kpis=formatted_kpis,
        charts=formatted_charts,
        insights=detailed_insights,
        industry=plan.get("industry", "Unknown"),
        eda=eda
    )

    plan = plan or {}
    plan.setdefault("industry", "Unknown")
    plan.setdefault("kpis", [])
    plan.setdefault("charts", [])
    plan.setdefault("insights", [])

    print("✅ FINAL RESPONSE SENT TO FRONTEND:")
    print(json.dumps(plan, indent=2))

    def sanitize_for_json(obj):
        if isinstance(obj, dict):
            return {k: sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_for_json(v) for v in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None  # or 0 if that makes more sense for your KPIs
            return obj
        else:
            return obj

    plan = sanitize_for_json(plan)

    # 8️⃣ Convert to plain JSON-safe structure before returning
    return JSONResponse(content=plan, media_type="application/json")


# --------------------------------------------------
# Trends generation route (triggered manually)
# --------------------------------------------------
@app.post("/trends")
async def generate_trends(file: UploadFile = File(...)):
    try:
        # Load dataset from uploaded CSV
        df = pd.read_csv(io.BytesIO(await file.read()))
        print("📈 Generating trends...")

        trends = generate_trends_with_ai(df)

        return JSONResponse(content=to_python({"trends": trends}), media_type="application/json")

    except Exception as e:
        print("⚠️ Trend generation failed:", e)
        return JSONResponse(
            content={"error": f"Trend generation failed: {str(e)}"},
            status_code=500
        )
