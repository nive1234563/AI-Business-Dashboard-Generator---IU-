from pydantic import BaseModel
from typing import List, Dict, Any

class DashboardResponse(BaseModel):
    kpis: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    insights: List[str]
    industry: str
    eda: Dict[str, Any]
