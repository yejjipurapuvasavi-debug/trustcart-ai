from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import csv
import re
import time

ROOT = Path(__file__).parent
DATA = ROOT / "data"

app = FastAPI(title="TrustCart AI API", description="Evidence-first shopping assistant prototype")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local development only; restrict this before deployment.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    history: list[dict] = []

def load_products():
    with open(DATA / "products.csv", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

def load_policy():
    path = DATA / "policies.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""

def norm(value):
    return re.sub(r"[^a-z0-9₹]+", " ", value.lower()).strip()

def previous_constraints(history):
    text = " ".join(item.get("content", "") for item in history if item.get("role") == "user").lower()
    category = "cotton" if "cotton" in text else None
    budgets = re.findall(r"(?:under|below|less than)\s*₹?\s*([\d,]+)", text)
    budget = int(budgets[-1].replace(",", "")) if budgets else None
    return category, budget

def find_matches(query, history):
    products = load_products()
    q = norm(query)
    category, budget = previous_constraints(history)
    # Include current query constraints as well.
    if "cotton" in q:
        category = "cotton"
    m = re.search(r"(?:under|below|less than)\s*₹?\s*([\d,]+)", query.lower())
    if m:
        budget = int(m.group(1).replace(",", ""))
    terms = [t for t in q.split() if t not in {
        "what","is","the","price","of","this","a","an","how","much","do","you","sell",
        "show","me","find","please","under","below","less","than","for","in","stock",
        "available","have","are","your","products","and","already","said","want","i"
    }]
    results = []
    for product in products:
        price = int(product["price"])
        if budget is not None and price > budget:
            continue
        if category and category not in (product["category"] + " " + product["description"]).lower():
            continue
        haystack = norm(" ".join(product.get(key, "") for key in ["name", "category", "color", "description"]))
        score = sum(1 for term in terms if term in haystack)
        if score > 0 or not terms:
            results.append((score, product))
    results.sort(key=lambda item: item[0], reverse=True)
    return [p for _, p in results]

def answer_query(query, history):
    start = time.perf_counter()
    q = query.lower()
    products = load_products()

    if any(word in q for word in ["return", "refund", "exchange", "shipping", "warranty", "policy"]):
        policy = load_policy()
        keywords = [line.strip() for line in policy.splitlines()
                    if line.strip() and any(word in line.lower() for word in ["return", "refund", "exchange", "shipping", "warranty"])]
        if keywords:
            answer = "Here is the relevant information from the sample policy:\n" + "\n".join(f"• {line}" for line in keywords) + "\n\nEvidence: policies.txt — matching policy section(s)."
            status = "verified"
        else:
            answer = "I can’t verify that policy because the supplied policy file contains no supporting section."
            status = "refuse"
        return {"answer": answer, "status": status, "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "token_cost": "Not measured: supplied model not connected."}

    if "iphone" in q or "apple phone" in q:
        iphone_matches = [p for p in products if "iphone" in (p["name"] + " " + p["description"]).lower()]
        if not iphone_matches:
            return {"answer": "I can’t verify an iPhone in the supplied sample catalogue, so I won’t claim a price or availability.", "status": "refuse",
                    "latency_ms": round((time.perf_counter()-start)*1000, 2), "token_cost": "Not measured: supplied model not connected."}

    matches = find_matches(query, history)
    if "blue" in q and ("shoe" in q or "running" in q) and len(matches) > 1:
        options = "\n".join(f"• {p['name']} — ₹{int(p['price']):,} · Product ID: {p['product_id']}" for p in matches[:5])
        return {"answer": "Several products match. Which one do you mean, or what is your budget?\n" + options,
                "status": "clarify", "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "token_cost": "Not measured: supplied model not connected."}

    if not matches:
        return {"answer": "I couldn’t find a matching item in the supplied sample catalogue. I won’t guess its price, stock status or attributes. Try a product name or category from the catalogue.",
                "status": "refuse", "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "token_cost": "Not measured: supplied model not connected."}

    # Require unique top-scoring result; do not guess between equal candidates.
    best = matches[0]
    best_terms = norm(" ".join([best["name"], best["category"], best["color"], best["description"]]))
    query_terms = [t for t in norm(query).split() if t not in {"what","is","the","price","of","this","a","an","how","much"}]
    score = sum(1 for t in query_terms if t in best_terms)
    tied = [p for p in matches if sum(1 for t in query_terms if t in norm(" ".join([p["name"],p["category"],p["color"],p["description"]]))) == score]
    if len(tied) > 1:
        options = "\n".join(f"• {p['name']} — Product ID: {p['product_id']}" for p in tied[:5])
        return {"answer": "I found multiple possible matches. Please choose a product so I don’t give you the wrong facts.\n" + options,
                "status": "clarify", "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "token_cost": "Not measured: supplied model not connected."}

    price = int(best["price"])
    answer = (f"{best['name']}\nPrice: ₹{price:,}\nStock: {best['stock_status']}\n"
              f"Product ID: {best['product_id']}\nEvidence: products.csv — Product ID {best['product_id']}.\n"
              "Note: these are illustrative sample records, not live inventory.")
    return {"answer": answer, "status": "verified", "latency_ms": round((time.perf_counter()-start)*1000, 2),
            "token_cost": "Not measured: supplied model not connected."}

@app.get("/")
def root():
    return {"app": "TrustCart AI", "mode": "sample data", "message": "API is running."}

@app.post("/chat")
def chat(request: ChatRequest):
    return answer_query(request.query, request.history)
