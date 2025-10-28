import json
from core.config import llm
from core.utils import to_json_str

def refine_insights_with_rag(insights, vectorstore, eda):
    """
    Deep RAG-based insight generation:
    - Understands dataset context (via RAG)
    - Uses external knowledge (AI common sense / global data)
    - Produces long-form, structured insights
    """
    detailed_insights = []

    for topic in insights[:5]:  # limit for efficiency
        try:
            retrieved_docs = vectorstore.similarity_search(topic, k=5)
            retrieved_context = "\n".join([d.page_content for d in retrieved_docs])

            prompt = f"""
You are an expert data scientist and domain analyst.

You have access to:
1. A dataset context built from its structure, statistics, and correlations.
2. A generic insight or topic hint.
3. Public knowledge (economic, environmental, or social, if relevant).

### Goal:
Generate detailed, contextual, and domain-aware insights about this dataset.
If possible, compare it to public benchmarks or real-world trends.
Each insight should include:
- **Analytical Summary:** what patterns and relationships exist
- **Possible Causes/Drivers:** why they might occur
- **Implications:** what this means for the domain or business
- **Optional External Context:** (e.g., “this trend is consistent with global coffee consumption data”)

### Input:
Dataset EDA Summary:
{to_json_str(eda)}

Retrieved Context:
{retrieved_context}

Insight Seed:
{topic}

### Output:
Write 2-3 detailed paragraphs of analytical text.
Be data-driven and contextual, not generic.
"""

            res = llm.invoke(prompt)
            text = res.content.strip().replace("```", "")
            detailed_insights.append(text)

        except Exception as e:
            print(f"⚠️ Detailed RAG insight failed for '{topic}': {e}")
            detailed_insights.append(topic)

    return detailed_insights
