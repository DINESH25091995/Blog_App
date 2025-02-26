from database import engine, Base
from models import *  # Import all your models

# ✅ Create tables in PostgreSQL
Base.metadata.create_all(bind=engine)

print("Tables created successfully!")
