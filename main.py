from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import auth, blog, comment, shop
from database import Base, engine

from sqlalchemy.orm import Session
from fastapi import APIRouter, Form, Request, Depends
from database import get_db
from models import Blog, Shop
from starlette.middleware.sessions import SessionMiddleware
# from fastapi_sessions.middleware import SessionMiddleware

# Initialize the database
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add Session Middleware (REQUIRED for request.session)
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(blog.router, prefix="/blogs", tags=["Blogs"])
app.include_router(comment.router, prefix="/comments", tags=["Comments"])
app.include_router(shop.router, prefix="/shops", tags=["Shops"])
# ✅ Ensure the shop router is included with the correct prefix
# app.include_router(shop.router, prefix="/shops", tags=["Shops"])


# Template engine
templates = Jinja2Templates(directory="templates")

# @app.get("/")
# def home(request: Request):
#     return templates.TemplateResponse(
#         "home.html",
#         {"request": request, "links": [
#             {"name": "Login", "url": "/auth/login"},
#             {"name": "Register", "url": "/auth/register"},
#             {"name": "View Blogs", "url": "/blogs/"},
#             {"name": "Create Blog", "url": "/blogs/create"}
#         ]}
#     )

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    blogs = db.query(Blog).all()
    shops = db.query(Shop).all()
    return templates.TemplateResponse("index.html", {"request": request, "blogs": blogs,"shops":shops})

