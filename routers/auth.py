from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User,Blog, Appointment
from database import get_db

templates = Jinja2Templates(directory="templates")

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request,username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        request.session["login_error"] = "Invalid username or password"
        return RedirectResponse(url="/auth/login", status_code=303)  # Redirect back to login page
        # raise HTTPException(status_code=400, detail="Invalid credentials")

    request.session["user"] = {"id": user.id, "username": user.username}
    return RedirectResponse(url="/", status_code=303)

@router.get("/logout")
def logout(request: Request):
    get_current_user(request)  # Ensure user is logged in
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@router.get("/profile")
def profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    blogs = db.query(Blog).filter(Blog.user_id == user["id"]).all()
    appointments = db.query(Appointment).filter(Appointment.user_id == user["id"]).all()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "blogs":blogs,"appointments":appointments})

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=403, detail="Authentication required")
    return user