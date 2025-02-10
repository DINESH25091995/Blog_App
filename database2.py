from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your actual PostgreSQL credentials
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "Udaykeshri@25"
POSTGRES_DB = "postgres"
POSTGRES_HOST = "localhost"  # Use 'localhost' if running locally
POSTGRES_PORT = "5432"  # Default PostgreSQL port

# PostgreSQL Database URL
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create the engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare Base
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
