import io
import pandas as pd
from core.utils import dataframe_summary

def process_csv(file_bytes: bytes):
    df = pd.read_csv(io.BytesIO(file_bytes))
    return df

def get_eda_summary(df: pd.DataFrame):
    return dataframe_summary(df)
