import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(
    temperature=0.3,
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY
)

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
