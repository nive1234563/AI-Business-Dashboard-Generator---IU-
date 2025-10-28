import json
import re
import numpy as np
import pandas as pd
from core.config import llm
from core.utils import to_json_str
from langchain.prompts import ChatPromptTemplate


def run_ai_agent(eda_summary, df):
    """
    Memory-optimized AI Agent
    - Uses minimal sample (3 rows)
    - Returns KPIs with 'aggregation' instead of type
    - Automatically computes KPI values
    """

    # ✅ 1️⃣ Prepare compact dataset summary
    sample_data = df.head(3).to_dict(orient="records")
    column_summary = [{"name": c, "dtype": str(df[c].dtype)} for c in df.columns]

    # ✅ 2️⃣ Define the AI prompt
    prompt = ChatPromptTemplate.from_template("""
        You are an expert business data analyst AI.
        Based on the dataset summary and sample rows, design analytics KPIs and charts.

        ### Dataset Summary ###
        {eda}

        ### Columns ###
        {cols}

        ### Sample Rows (3) ###
        {sample}

        ### Tasks ###
        1. Read the summary, columns, and sample rows, infer the **real-world domain**
            (e.g. retail, logistics, finance, healthcare, HR, marketing, etc.).Identify the dataset's **industry/domain** (e.g., retail, healthcare, finance, etc.)
        2. Suggest **insightful and domain-specific** **5–8 KPIs** as JSON objects with:
           - "name": KPI name
           - "description": brief explanation
           - "related_columns": which columns are used
           - "aggregation": what operation to use — choose from ["sum", "mean", "count", "unique", "max", "min"]
        3. Suggest **insightful and domain-specific** visualizations for a dataset.
             and return only **charts that reveal meaningful business patterns** — never random column
            combinations.Suggest **3–9 charts** as JSON objects with: "title", "type" (bar, line, pie, etc.), and "columns".
        4. Suggest **structured insights** from the summary, grouped by topic inside a single key `"insights"`.Give as many points as possible from the perspective of the dataset's field or domain or business perspective. Keep it maximum to 15 points and give little detailed .Each point must be atleast 20 words.

        ### Output JSON Format ###
        {{
          "industry": "Retail",
          "kpis": [
            {{
              "name": "Total Revenue",
              "description": "Sum of all sales transactions.",
              "related_columns": ["transaction_qty"],
              "aggregation": "sum"
            }},
            {{
              "name": "Average Order Value",
              "description": "Mean value of each transaction.",
              "related_columns": [ "unit_price"],
              "aggregation": "mean"
            }}
          ],
          "charts": [
            {{
              "title": "Revenue Over Time",
              "type": "line",
              "columns": ["transaction_date", "transaction_qty"]
            }},
            {{
              "title": "Sales by Category",
              "type": "bar",
              "columns": ["product_category", "transaction_qty"]
            }}
          ],
          "insights": {{
            "Sales Performance": [
              "Revenue shows strong seasonality with peaks in Q4.",
              "High contribution from electronics category."
            ],
            "Opportunities": [
              "Introduce loyalty discounts for repeat customers."
            ]
          }}
        }}
    """)

    # ✅ 3️⃣ Format LLM message
    messages = prompt.format_messages(
        eda=to_json_str(eda_summary),
        cols=to_json_str(column_summary),
        sample=to_json_str(sample_data),
    )

    # ✅ 4️⃣ Call LLM
    res = llm.invoke(messages)
    raw_text = res.content.strip()
    print("AI output",raw_text)

    # ✅ 5️⃣ Clean raw JSON output
    raw_text = re.sub(r"^```[a-zA-Z]*", "", raw_text)
    raw_text = raw_text.replace("```", "").strip()
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        raw_text = match.group(0)

    # ✅ 6️⃣ Safe JSON parsing
    try:
        parsed = json.loads(raw_text)
    except Exception:
        print("⚠️ Invalid JSON — trying to auto-repair...")
        fix_prompt = f"""
        The following text was invalid JSON.
        Fix and return valid JSON containing keys: industry, kpis, charts, insights.
        Text:
        {res.content}
        """
        fixed_res = llm.invoke([{"role": "user", "content": fix_prompt}])
        fixed_text = fixed_res.content.strip()
        fixed_text = re.sub(r"^```[a-zA-Z]*", "", fixed_text).replace("```", "").strip()
        match = re.search(r"\{.*\}", fixed_text, re.DOTALL)
        if match:
            fixed_text = match.group(0)
        parsed = json.loads(fixed_text)

    # ✅ 7️⃣ Normalize keys
    normalized = {k.strip().lower(): v for k, v in parsed.items()}
    parsed = {
        "industry": normalized.get("industry", "Unknown"),
        "kpis": normalized.get("kpis", []),
        "charts": normalized.get("charts", []),
        "insights": normalized.get("insights", {}),
    }

    # ✅ 8️⃣ Compute KPI values based on aggregation
    def compute_kpi_value(df, kpi):
        cols = [c for c in kpi.get("related_columns", []) if c in df.columns]
        agg = kpi.get("aggregation", "sum").lower()
        if not cols:
            return None

        try:
            numeric_cols = [c for c in cols if np.issubdtype(df[c].dtype, np.number)]
            cat_cols = [c for c in cols if df[c].dtype == "object"]

            # If grouping columns exist → top 10 groups
            if cat_cols and numeric_cols:
                grouped = df.groupby(cat_cols)[numeric_cols].agg(agg).head(10).reset_index()
                return grouped.to_dict(orient="records")

            # Multiple numeric columns → product then aggregate
            if len(numeric_cols) >= 2:
                result = np.prod([df[c] for c in numeric_cols], axis=0)
                if agg == "mean":
                    return float(np.mean(result))
                if agg == "max":
                    return float(np.max(result))
                if agg == "min":
                    return float(np.min(result))
                if agg == "count":
                    return int(np.count_nonzero(result))
                return float(np.sum(result))

            # Single numeric column
            if len(numeric_cols) == 1:
                col = numeric_cols[0]
                if agg == "mean":
                    return float(df[col].mean())
                if agg == "max":
                    return float(df[col].max())
                if agg == "min":
                    return float(df[col].min())
                if agg == "count":
                    return int(df[col].count())
                if agg == "unique":
                    return int(df[col].nunique())
                return float(df[col].sum())

            # Single categorical column → unique counts
            if len(cat_cols) == 1 and agg == "unique":
                return df[cat_cols[0]].value_counts().head(10).to_dict()

        except Exception as e:
            print(f"⚠️ KPI calc failed for {kpi.get('name', '')}: {e}")
            return None

        # ---- Compute KPI values for all ----
    computed_kpis = []
    for kpi in parsed["kpis"]:
        value = compute_kpi_value(df, kpi)
        kpi_with_value = {**kpi, "value": value}
        computed_kpis.append(kpi_with_value)
    parsed["kpis"] = computed_kpis

    # ✅ Generate simple chart-ready data based on existing KPIs and dataset
    # ✅ Generate chart-ready data from AI-defined columns
    parsed_charts = []

    for chart_def in parsed.get("charts", []):
        try:
            cols = chart_def.get("columns", [])
            title = chart_def.get("title", "Untitled Chart")
            chart_type = chart_def.get("type", "bar")

            if not cols or len(cols) < 2:
                continue

            # Identify categorical and numeric columns based on AI suggestion
            cat_cols = [c for c in cols if c in df.columns and df[c].dtype == "object"]
            num_cols = [c for c in cols if c in df.columns and np.issubdtype(df[c].dtype, np.number)]
            date_cols = [c for c in cols if "date" in c.lower() and c in df.columns]

            # --- CASE 1: Time series ---
            if date_cols and num_cols:
                date_col = date_cols[0]
                num_col = num_cols[-1]
                df_temp = df[[date_col, num_col]].copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")
                df_temp = df_temp.dropna(subset=[date_col])
                grouped = df_temp.groupby(date_col)[num_col].sum().reset_index().sort_values(date_col)

                parsed_charts.append({
                    "title": title,
                    "type": chart_type,
                    "data": {
                        "labels": grouped[date_col].astype(str).tolist()[:30],
                        "series": [{"name": num_col, "values": grouped[num_col].round(2).tolist()[:30]}],
                    },
                })
                continue

            # --- CASE 2: Category + numeric (Bar or Pie) ---
            if cat_cols and num_cols:
                cat_col = cat_cols[0]
                num_col = num_cols[-1]
                grouped = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()

                parsed_charts.append({
                    "title": title,
                    "type": chart_type,
                    "data": {
                        "labels": grouped[cat_col].astype(str).tolist(),
                        "series": [{"name": num_col, "values": grouped[num_col].round(2).tolist()}],
                    },
                })
                continue

            # --- CASE 3: Fallback (two numerics, show correlation line) ---
            if len(num_cols) >= 2:
                x, y = num_cols[:2]
                parsed_charts.append({
                    "title": title,
                    "type": "scatter",
                    "data": {
                        "labels": df[x].head(30).astype(str).tolist(),
                        "series": [{"name": y, "values": df[y].head(30).round(2).tolist()}],
                    },
                })

        except Exception as e:
            print(f"⚠️ Chart generation failed for {chart_def.get('title', '')}: {e}")

    parsed["charts"] = parsed_charts
    print(f"✅ Generated {len(parsed_charts)} charts from AI definitions.")


    print(f"✅ Generated {len(parsed_charts)} charts.")
    return parsed


    
