# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

# Import models and database session/creation logic
from . import models # Assuming models.py is in the same directory
from .models import Product, Category, Supplier # SQLAlchemy models
from .models import ProductCreate, ProductRead, ProductUpdate # Pydantic models
from .models import CategoryCreate, CategoryRead, CategoryUpdate
from .models import SupplierCreate, SupplierRead, SupplierUpdate
from .models import SessionLocal, engine, create_db_tables

# Create database tables on startup (if they don't exist)
# For production, use Alembic migrations instead of this.
try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables checked/created successfully.")
except Exception as e:
    print(f"Error creating database tables: {e}")
    # Depending on the error, you might want to exit or handle it differently
    # For now, we'll let the app try to start, but DB operations might fail.

app = FastAPI(
    title="Inventory Management API",
    description="API for managing products, categories, and suppliers.",
    version="0.1.0"
)

# --- Dependency for Database Session ---
def get_db():
    """
    Dependency that provides a database session for each request.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db # Provides the session to the route handler
    finally:
        db.close() # Closes the session

# --- API Endpoints ---

# --- Product Endpoints ---
@app.post("/api/v1/products/", response_model=ProductRead, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Create a new product.
    - **sku**: Stock Keeping Unit (must be unique)
    - **name**: Product name
    - **purchase_price**: Cost of the product
    - **sale_price**: Selling price of the product
    - **quantity_on_hand**: Initial stock quantity (defaults to 0)
    """
    # Check if SKU already exists
    db_product_sku = db.query(Product).filter(Product.sku == product.sku).first()
    if db_product_sku:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with SKU '{product.sku}' already exists.")

    # Check if category_id exists (if provided)
    if product.category_id:
        category = db.query(Category).filter(Category.id == product.category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID {product.category_id} not found.")

    # Check if supplier_id exists (if provided)
    if product.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier with ID {product.supplier_id} not found.")

    db_product = Product(**product.model_dump()) # Create SQLAlchemy model instance
    db.add(db_product)
    db.commit()
    db.refresh(db_product) # Refresh to get DB-generated values like id, created_at
    return db_product

@app.get("/api/v1/products/", response_model=List[ProductRead], tags=["Products"])
def read_products(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    sku: Optional[str] = None,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of products with optional filtering and pagination.
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (for pagination)
    - **name**: Filter by product name (case-insensitive partial match)
    - **sku**: Filter by product SKU (exact match)
    - **category_id**: Filter by category ID
    - **supplier_id**: Filter by supplier ID
    """
    query = db.query(Product)
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%")) # Case-insensitive like
    if sku:
        query = query.filter(Product.sku == sku)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if supplier_id is not None:
        query = query.filter(Product.supplier_id == supplier_id)

    products = query.offset(skip).limit(limit).all()
    return products

@app.get("/api/v1/products/{product_id}", response_model=ProductRead, tags=["Products"])
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single product by its ID.
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return db_product

@app.put("/api/v1/products/{product_id}", response_model=ProductRead, tags=["Products"])
def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)):
    """
    Update an existing product by its ID.
    Allows partial updates (fields not provided will not be changed).
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = product_update.model_dump(exclude_unset=True) # Get only provided fields

    # Special handling for SKU if it's being updated to ensure uniqueness
    if "sku" in update_data and update_data["sku"] != db_product.sku:
        existing_sku = db.query(Product).filter(Product.sku == update_data["sku"]).first()
        if existing_sku:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product with SKU '{update_data['sku']}' already exists.")

    # Check category_id if provided
    if "category_id" in update_data and update_data["category_id"] is not None:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with ID {update_data['category_id']} not found.")

    # Check supplier_id if provided
    if "supplier_id" in update_data and update_data["supplier_id"] is not None:
        supplier = db.query(Supplier).filter(Supplier.id == update_data["supplier_id"]).first()
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Supplier with ID {update_data['supplier_id']} not found.")


    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/api/v1/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Delete a product by its ID.
    Returns 204 No Content on successful deletion.
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return None # For 204 No Content, FastAPI expects no return body

# --- Category Endpoints (Placeholder - Implement similarly to Products) ---
@app.post("/api/v1/categories/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category_name = db.query(Category).filter(Category.name == category.name).first()
    if db_category_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category with name '{category.name}' already exists.")
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.get("/api/v1/categories/", response_model=List[CategoryRead], tags=["Categories"])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(Category).offset(skip).limit(limit).all()
    return categories

@app.get("/api/v1/categories/{category_id}", response_model=CategoryRead, tags=["Categories"])
def read_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category

@app.put("/api/v1/categories/{category_id}", response_model=CategoryRead, tags=["Categories"])
def update_category(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    update_data = category_update.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] != db_category.name:
        existing_name = db.query(Category).filter(Category.name == update_data["name"]).first()
        if existing_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Category with name '{update_data['name']}' already exists.")

    for key, value in update_data.items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/api/v1/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categories"])
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    # Consider how to handle products associated with this category (e.g., set to null, prevent deletion if products exist)
    # For simplicity, we'll delete it. A more robust solution would check for dependencies.
    if db_category.products:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category '{db_category.name}' as it has associated products. Please reassign or delete them first."
        )
    db.delete(db_category)
    db.commit()
    return None

# --- Supplier Endpoints (Placeholder - Implement similarly to Products) ---
@app.post("/api/v1/suppliers/", response_model=SupplierRead, status_code=status.HTTP_201_CREATED, tags=["Suppliers"])
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    if supplier.email:
        db_supplier_email = db.query(Supplier).filter(Supplier.email == supplier.email).first()
        if db_supplier_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Supplier with email '{supplier.email}' already exists.")
    db_supplier = Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.get("/api/v1/suppliers/", response_model=List[SupplierRead], tags=["Suppliers"])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).offset(skip).limit(limit).all()
    return suppliers

@app.get("/api/v1/suppliers/{supplier_id}", response_model=SupplierRead, tags=["Suppliers"])
def read_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return db_supplier

@app.put("/api/v1/suppliers/{supplier_id}", response_model=SupplierRead, tags=["Suppliers"])
def update_supplier(supplier_id: int, supplier_update: SupplierUpdate, db: Session = Depends(get_db)):
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")

    update_data = supplier_update.model_dump(exclude_unset=True)
    if "email" in update_data and update_data["email"] and update_data["email"] != db_supplier.email:
        existing_email = db.query(Supplier).filter(Supplier.email == update_data["email"]).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Supplier with email '{update_data['email']}' already exists.")

    for key, value in update_data.items():
        setattr(db_supplier, key, value)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.delete("/api/v1/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Suppliers"])
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if db_supplier is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    if db_supplier.products:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete supplier '{db_supplier.name}' as it has associated products. Please reassign or delete them first."
        )
    db.delete(db_supplier)
    db.commit()
    return None

# --- Root Endpoint (Optional) ---
@app.get("/api/v1/", tags=["Root"])
async def root():
    """
    Root endpoint for the API.
    Provides basic information or a welcome message.
    """
    return {"message": "Welcome to the Inventory Management API!"}

# --- Health Check Endpoint (Good Practice) ---
@app.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Verifies database connectivity.
    """
    try:
        # Perform a simple query to check DB connection
        db.execute("SELECT 1")
        return {"status": "healthy", "database_connection": "ok"}
    except Exception as e:
        # Log the exception for debugging
        print(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database_connection": "error", "error_message": str(e)}
        )

# If you want to run this directly (e.g., for local testing without Docker/Uvicorn CLI)
# you would add:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
# However, the CMD in the Dockerfile handles running Uvicorn.
