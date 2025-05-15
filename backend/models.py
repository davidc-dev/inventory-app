# backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

# --- Database Setup (SQLAlchemy) ---
DATABASE_URL = "postgresql://user:password@db:5432/inventory_db" # Same as in docker-compose

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models (Database Tables) ---

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    products = relationship("Product", back_populates="category") # Relationship to Product model

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    contact_person = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    phone_number = Column(String, nullable=True)
    address = Column(String, nullable=True)

    products = relationship("Product", back_populates="supplier") # Relationship to Product model

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False) # Stock Keeping Unit
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    purchase_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    quantity_on_hand = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=10) # Alert when quantity falls below this
    location = Column(String, nullable=True) # e.g., Warehouse A, Shelf B2
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="products")

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier = relationship("Supplier", back_populates="products")

# --- Pydantic Models (API Data Schemas) ---
# These models are used for request and response validation and serialization.

# Base models (for common fields, helps with DRY principle)
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the category")
    description: Optional[str] = Field(None, max_length=500, description="Optional description for the category")

class SupplierBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Name of the supplier")
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$") # Basic email regex
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=3, max_length=50, description="Stock Keeping Unit, must be unique")
    name: str = Field(..., min_length=3, max_length=200, description="Product name")
    description: Optional[str] = Field(None, max_length=1000)
    purchase_price: float = Field(..., gt=0, description="Price at which the product was purchased")
    sale_price: float = Field(..., gt=0, description="Price at which the product is sold")
    quantity_on_hand: int = Field(default=0, ge=0, description="Current stock quantity")
    reorder_level: Optional[int] = Field(default=10, ge=0)
    location: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=2048) # Assuming a URL
    is_active: Optional[bool] = True
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None

# Create models (for POST requests - typically don't include 'id' or read-only fields)
class CategoryCreate(CategoryBase):
    pass

class SupplierCreate(SupplierBase):
    pass

class ProductCreate(ProductBase):
    pass

# Read models (for GET responses - include 'id' and potentially other computed/related fields)
class CategoryRead(CategoryBase):
    id: int

    class Config:
        orm_mode = True # Allows Pydantic to work with SQLAlchemy ORM objects

class SupplierRead(SupplierBase):
    id: int

    class Config:
        orm_mode = True

class ProductRead(ProductBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    category: Optional[CategoryRead] = None # Include related category details
    supplier: Optional[SupplierRead] = None # Include related supplier details

    class Config:
        orm_mode = True

# Update models (for PUT/PATCH requests - fields are often optional)
class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)

class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    purchase_price: Optional[float] = Field(None, gt=0)
    sale_price: Optional[float] = Field(None, gt=0)
    quantity_on_hand: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=2048)
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None

# Helper function to create database tables
def create_db_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # This will create the tables in the database if they don't exist
    # You would typically run this once, perhaps in your main.py or a separate script
    # For a production setup, you'd use migrations (e.g., Alembic).
    print("Creating database tables...")
    create_db_tables()
    print("Database tables created (if they didn't exist).")
