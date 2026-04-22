PLAN_LIMITS: dict[str, dict] = {
    "free": {"queries": 30,   "documents": 3,    "history": False, "page_number": False},
    "solo": {"queries": 300,  "documents": None, "history": True,  "page_number": False},
    "pro":  {"queries": 1000, "documents": None, "history": True,  "page_number": True},
}

def get_limit(plan: str, metric: str):
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])[metric]
