# from langchain_community.vectorstores import FAISS
# from langchain.schema import Document
# from core.config import embeddings

# def build_rag_index(df):
#     docs = []
#     for col in df.columns:
#         sample = df[col].dropna().astype(str).head(50).tolist()
#         text = f"Column: {col}\nType: {df[col].dtype}\nSample: {', '.join(sample[:10])}"
#         docs.append(Document(page_content=text, metadata={"column": col}))
#     return FAISS.from_documents(docs, embeddings)




from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from core.config import embeddings
import pandas as pd
import numpy as np
from openai import OpenAI

client = OpenAI()

def build_rag_index(df: pd.DataFrame):
    """Build a semantic + statistical RAG index from the dataset."""
    docs = []

    # 1️⃣ Add column-level summaries
    for col in df.columns:
        series = df[col].dropna()
        dtype = str(df[col].dtype)
        unique_vals = series.nunique()
        sample_vals = series.astype(str).head(5).tolist()
        summary = ""

        if np.issubdtype(df[col].dtype, np.number):
            summary = (
                f"Column '{col}' is numeric with mean={series.mean():.2f}, "
                f"std={series.std():.2f}, min={series.min():.2f}, max={series.max():.2f}."
            )
        else:
            top_vals = series.value_counts().head(5).to_dict()
            summary = f"Column '{col}' is categorical/text with {unique_vals} unique values. Top values: {top_vals}."

        text = f"{summary}\nSample values: {', '.join(sample_vals)}"
        docs.append(Document(page_content=text, metadata={"column": col}))

    # 2️⃣ Add pairwise numeric correlation insights
    num_cols = df.select_dtypes(include=np.number).columns
    if len(num_cols) >= 2:
        corr = df[num_cols].corr().abs().unstack().sort_values(ascending=False)
        corr = corr[corr < 1].head(10)
        corr_text = "\n".join(
            [f"Correlation between {a} and {b}: {v:.2f}" for (a, b), v in corr.items()]
        )
        docs.append(Document(page_content=f"Top numeric correlations:\n{corr_text}", metadata={"column": "correlations"}))

    # 3️⃣ Ask AI to summarize dataset purpose (semantic understanding)
    try:
        preview = df.head(3).to_csv(index=False)
        msg = f"Analyze this dataset preview and describe in 1-2 sentences what this dataset seems to represent:\n\n{preview}"
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analyst who infers dataset domains."},
                {"role": "user", "content": msg}
            ]
        )
        domain_summary = resp.choices[0].message.content.strip()
        docs.append(Document(page_content=f"Dataset domain description: {domain_summary}", metadata={"column": "dataset_description"}))
    except Exception as e:
        print("⚠️ Domain summary generation failed:", e)

    # 4️⃣ Build FAISS index
    return FAISS.from_documents(docs, embeddings)

def query_rag(store, query: str, k=3):
    return store.similarity_search(query, k=k)