from fastapi import APIRouter, Form, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse,JSONResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User,Blog, Appointment
from database import get_db

import random
import smtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

templates = Jinja2Templates(directory="templates")

router = APIRouter()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Simulated OTP Storage (In Production, store in Redis or DB)
otp_storage = {}

def send_email(to_email: str, otp: str):
    """Function to send OTP via email (Use an actual email service in production)"""
    sender_email = "dinesh.kumar.tech1995@gmail.com"
    sender_password = "jtskfipxjcapfxuo"
    
    subject = "Your OTP Code"
    message = f"Your OTP is: {otp}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, f"Subject: {subject}\n\n{message}")
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")

@router.get("/register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(None),
    mobile: str = Form(None),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered!")

    # Check if mobile number already exists (optional)
    existing_mobile = db.query(User).filter(User.mobile == mobile).first()
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered!")

    hashed_password = pwd_context.hash(password)

    user = User(username=username, email=email, mobile=mobile, password=hashed_password)

    # OTP Generating and sending to user to verify
    otp = str(random.randint(100000, 999999))
    user.otp = otp
    db.commit()

    if user.email:
        send_email(email, otp)
    otp_storage[email or mobile] = otp  # Store OTP temporarily

    db.add(user)
    db.commit()

    return RedirectResponse(url="/auth/verify-otp", status_code=303)

# @router.get("/send-otp")
# def send_otp_form(request: Request):
#     return templates.TemplateResponse("send_otp.html", {"request": request})

# @router.post("/send-otp")
# def send_otp(identifier: str = Form(...), db: Session = Depends(get_db)):
#     """Send OTP via email or mobile"""
#     user = db.query(User).filter((User.email == identifier) | (User.mobile == identifier)).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     otp = str(random.randint(100000, 999999))
#     user.otp = otp
#     db.commit()

#     if user.email:
#         send_email(user.email, otp)

#     otp_storage[user.email or user.mobile] = otp  # Store OTP temporarily
#     return RedirectResponse(url="/auth/verify-otp", status_code=303)

@router.get("/verify-otp")
def verify_otp_form(request: Request):
    return templates.TemplateResponse("verify_otp.html", {"request": request})

@router.post("/verify-otp")
def verify_otp(identifier: str = Form(...), otp: str = Form(...), db: Session = Depends(get_db)):
    """Verify the OTP"""
    user = db.query(User).filter((User.email == identifier) | (User.mobile == identifier)).first()
    if not user or user.otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user.is_verified = True
    user.otp = None
    db.commit()
    return RedirectResponse(url="/auth/login", status_code=303)

@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(request: Request, identifier: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter((User.email == identifier) | (User.mobile == identifier)).first()
    if not user or not pwd_context.verify(password, user.password):
        return RedirectResponse(url="/auth/login", status_code=303)

    request.session["user"] = {"id": user.id, "username": user.username}
    return RedirectResponse(url="/", status_code=303)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# @router.get("/register")
# def register_form(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})

# @router.post("/register")
# def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
#     hashed_password = pwd_context.hash(password)
#     user = User(username=username, hashed_password=hashed_password)
#     db.add(user)
#     db.commit()
#     return RedirectResponse(url="/auth/login", status_code=303)

# @router.get("/login")
# def login_form(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})

# @router.post("/login")
# def login(request: Request,username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.username == username).first()
#     if not user or not pwd_context.verify(password, user.hashed_password):
#         request.session["login_error"] = "Invalid username or password"
#         return RedirectResponse(url="/auth/login", status_code=303)  # Redirect back to login page
#         # raise HTTPException(status_code=400, detail="Invalid credentials")

#     request.session["user"] = {"id": user.id, "username": user.username}
#     return RedirectResponse(url="/", status_code=303)

# @router.get("/logout")
# def logout(request: Request):
#     get_current_user(request)  # Ensure user is logged in
#     request.session.clear()
#     return RedirectResponse(url="/", status_code=303)

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