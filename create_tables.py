from database import engine, Base

# Create all tables in the PostgreSQL database
print("Creating tables in PostgreSQL...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
