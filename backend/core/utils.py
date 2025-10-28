import pandas as pd
import json

def dataframe_summary(df: pd.DataFrame) -> dict:
    summary = {"shape": df.shape, "columns": []}
    for c in df.columns:
        info = {
            "name": c,
            "dtype": str(df[c].dtype),
            "n_missing": int(df[c].isna().sum()),
            "n_unique": int(df[c].nunique())
        }

        if pd.api.types.is_numeric_dtype(df[c]):
            info["mean"] = float(df[c].mean(skipna=True))
            info["std"] = float(df[c].std(skipna=True))
            info["min"] = float(df[c].min(skipna=True))
            info["max"] = float(df[c].max(skipna=True))

        summary["columns"].append(info)
    return summary

def to_json_str(obj):
    return json.dumps(obj, indent=2, default=str)
