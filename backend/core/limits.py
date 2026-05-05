PLAN_LIMITS: dict[str, dict] = {
    "free": {"queries": 50,   "documents": 3,  "history": False, "page_number": False, "summaries": 3},
    "solo": {"queries": 300,  "documents": 10, "history": True,  "page_number": False, "summaries": 10},
    "pro":  {"queries": 1000, "documents": 20, "history": True,  "page_number": True,  "summaries": 30},
}

def get_limit(plan: str, metric: str):
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])[metric]
