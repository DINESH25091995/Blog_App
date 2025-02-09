from fastapi import APIRouter, Form, Request, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from models import Blog,BlogImage
from database import get_db
import os
import shutil

from routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Create directory if not exists

@router.get("/")
def list_blogs(request: Request, db: Session = Depends(get_db)):
    blogs = db.query(Blog).all()
    user = request.session.get("user")
    return templates.TemplateResponse("blogs.html", {"request": request, "blogs": blogs})

@router.get("/create")
def create_blog_form(request: Request):
    # return templates.TemplateResponse("create_blog.html", {"request": request})
    user = request.session.get("user")  # Check if user is logged in
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)  # Redirect to login page
    
    return templates.TemplateResponse("create_blog.html", {"request": request, "user": user})


@router.post("/create")
async def create_blog(request: Request,
    title: str = Form(...), 
    content: str = Form(...),
    images: list[UploadFile] = File(...), 
    db: Session = Depends(get_db)):

    user = get_current_user(request)
    # image_path = None
    # if image and image.filename:
    #     # file_location = f"{UPLOAD_DIR}/{image.filename}"
    #     file_location = f"static/uploads/{image.filename}"
    #     with open(file_location, "wb") as buffer:
    #         buffer.write(await image.read())
    #     image_path = file_location  # Save image path
    #     print("Image path",image_path)
    # blog = Blog(title=title, content=content,user_id=user["id"],image=image_path)
    blog = Blog(title=title, content=content,user_id=user["id"])
    db.add(blog)
    db.commit()
    db.refresh(blog)

    if images:
        for image in images:
            if image.filename:
                images_path = f"static/uploads/{blog.title}_{blog.id}"
                os.makedirs(images_path, exist_ok=True)  # Create directory if not exists

                file_path = os.path.join(images_path, image.filename)
                with open(file_path, "wb") as buffer:
                    buffer.write(await image.read())

                # Save image reference in the database
                blog_image = BlogImage(blog_id=blog.id, image_path=file_path)
                db.add(blog_image)

        db.commit()

    return RedirectResponse(url="/blogs/", status_code=303)

@router.get("/{blog_id}")
def blog_detail(request: Request, blog_id: int, db: Session = Depends(get_db)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    comments = blog.comments
    user = request.session.get("user")
    return templates.TemplateResponse("blog_detail.html", {"request": request, "blog": blog, "comments": comments, "current_user": user})


@router.post("/delete/{blog_id}")
def delete_blog(blog_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()

    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this blog")

    db.delete(blog)
    db.commit()

    return RedirectResponse(url="/blogs", status_code=303)