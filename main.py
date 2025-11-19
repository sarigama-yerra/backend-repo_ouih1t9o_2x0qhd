import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Product

app = FastAPI(title="Ecommerce API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Ecommerce backend listo"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Seed some sample products if collection is empty
@app.post("/api/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"inserted": 0, "message": "Products already seeded"}

    demo_products = [
        Product(
            title="Minimal Oversized Tee",
            description="Camiseta oversized de algodón premium",
            price=29.99,
            category="Tops",
            in_stock=True,
            brand="FLM",
            gender="unisex",
            image="https://images.unsplash.com/photo-1544441893-675973e319df?q=80&w=1200&auto=format&fit=crop",
            colors=["#111827", "#e5e7eb", "#f3f4f6"],
            sizes=["S","M","L","XL"],
            featured=True,
            tags=["tee","oversized","minimal"]
        ),
        Product(
            title="Tech Shell Jacket",
            description="Chaqueta impermeable con costuras termoselladas",
            price=119.0,
            category="Outerwear",
            in_stock=True,
            brand="FLM",
            gender="unisex",
            image="https://images.unsplash.com/photo-1509631179647-0177331693ae?q=80&w=1200&auto=format&fit=crop",
            colors=["#111827", "#4b5563"],
            sizes=["S","M","L"],
            featured=True,
            tags=["jacket","techwear","shell"]
        ),
        Product(
            title="Relaxed Fit Jeans",
            description="Jeans de corte relajado con lavado enzimático",
            price=69.0,
            category="Bottoms",
            in_stock=True,
            brand="FLM",
            gender="unisex",
            image="https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?q=80&w=1200&auto=format&fit=crop",
            colors=["#1f2937", "#9ca3af"],
            sizes=["28","30","32","34"],
            featured=False,
            tags=["jeans","denim"]
        )
    ]

    inserted = 0
    for p in demo_products:
        create_document("product", p)
        inserted += 1
    return {"inserted": inserted}

class ProductFilters(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    featured: Optional[bool] = None

@app.get("/api/products")
def list_products(q: Optional[str] = None, category: Optional[str] = None, featured: Optional[bool] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    if featured is not None:
        filter_dict["featured"] = featured
    # Simple text search in title/description
    products = get_documents("product", filter_dict)
    # Convert ObjectId to str
    for p in products:
        p["_id"] = str(p["_id"]) if "_id" in p else None
    if q:
        ql = q.lower()
        products = [p for p in products if ql in (p.get("title","")+" "+p.get("description","")) .lower()]
    return products

@app.get("/api/products/featured")
def featured_products():
    return list_products(featured=True)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
