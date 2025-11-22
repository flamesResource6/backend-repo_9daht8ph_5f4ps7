import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import create_document, get_documents, db
from schemas import Product

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return doc
    d = doc.copy()
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # Convert datetime fields to isoformat strings
    for k, v in list(d.items()):
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


@app.get("/")
def read_root():
    return {"message": "Gym Store Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/api/products")
def list_products(category: Optional[str] = None, limit: Optional[int] = None):
    """List products, optionally filtered by category"""
    try:
        filter_dict = {"category": category} if category else {}
        items = get_documents("product", filter_dict, limit)
        return [serialize_doc(x) for x in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/products")
def create_product(product: Product):
    """Create a new product"""
    try:
        new_id = create_document("product", product)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/seed")
def seed_products():
    """Seed the database with a basic gym equipment catalog if empty"""
    try:
        existing = get_documents("product", {}, limit=1)
        if existing:
            return {"status": "ok", "message": "Products already exist"}
        sample_products = [
            Product(
                title="Adjustable Dumbbell (Pair)",
                description="Space-saving adjustable dumbbells with quick-select weight system.",
                price=249.99,
                category="Strength",
                in_stock=True,
            ),
            Product(
                title="Kettlebell 16kg",
                description="Cast iron kettlebell with flat base and comfortable handle.",
                price=59.99,
                category="Strength",
                in_stock=True,
            ),
            Product(
                title="Yoga Mat Pro",
                description="Non-slip, 6mm cushioning yoga mat for comfort and stability.",
                price=39.99,
                category="Mobility",
                in_stock=True,
            ),
            Product(
                title="Resistance Bands Set",
                description="Set of 5 bands with varying resistance levels and door anchor.",
                price=24.99,
                category="Accessories",
                in_stock=True,
            ),
            Product(
                title="Foldable Treadmill",
                description="Compact treadmill with incline and app connectivity.",
                price=699.0,
                category="Cardio",
                in_stock=True,
            ),
        ]
        for p in sample_products:
            create_document("product", p)
        return {"status": "ok", "count": len(sample_products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
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
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
