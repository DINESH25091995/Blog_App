from fastapi import APIRouter, Form, Request, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from models import Blog,BlogImage,Shop, ShopImage, Appointment, User, Worker, Service
from database import get_db
import os
import shutil
from typing import List

from routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SHOP_DIR = "static/uploads/shopprofile"
os.makedirs(SHOP_DIR, exist_ok=True)  # Create directory if not exists

@router.get("/")
def list_shops(request: Request, db: Session = Depends(get_db)):
    shops = db.query(Shop).all()
    user = request.session.get("user")
    return templates.TemplateResponse("shops.html", {"request": request, "shops": shops})

@router.get("/create")
def create_shop_form(request: Request):
    user = request.session.get("user")  # Check if user is logged in
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)  # Redirect to login page
    
    return templates.TemplateResponse("create_shop.html", {"request": request, "user": user})


@router.post("/create")
async def create_shop(request: Request,
    shop_name: str = Form(...), 
    address: str = Form(...),
    images: list[UploadFile] = File(...), 
    db: Session = Depends(get_db)):

    user = get_current_user(request)
    shop = Shop(shop_name=shop_name, address=address,user_id=user["id"])
    db.add(shop)
    db.commit()
    db.refresh(shop)

    if images:
        for image in images:
            if image.filename:
                images_path = f"static/uploads/shopprofile/{shop.shop_name}_{shop.id}"
                os.makedirs(images_path, exist_ok=True)  # Create directory if not exists

                file_path = os.path.join(images_path, image.filename)
                with open(file_path, "wb") as buffer:
                    buffer.write(await image.read())

                # Save image reference in the database
                shop_image = ShopImage(shop_id=shop.id, image_path=file_path)
                db.add(shop_image)

        db.commit()
    return RedirectResponse(url="/shops/", status_code=303)

@router.get("/{shop_id}")
def shop_detail(request: Request, shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    users = db.query(User).all()  # Fetch all users for the dropdown
    user = request.session.get("user")
    
    appointments = db.query(Appointment).filter(Appointment.shop_id == shop_id).all()

    # appointments = db.query(Appointment).filter(Appointment.user_id == user["id"]).all()
    return templates.TemplateResponse("shop_detail.html", {"request": request, "shop": shop, "current_user": user, "users": users,"appointments":appointments})


@router.post("/delete/{shop_id}")
def delete_blog(shop_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Blog not found")

    if shop.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this blog")

    db.delete(shop)
    db.commit()

    return RedirectResponse(url="/shops", status_code=303)


@router.get("/users")
def list_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("user_list.html", {"request": request, "users": users})

@router.post("/{shop_id}/add_worker")
def add_worker(request: Request, 
                shop_id: int, 
                user_id: int = Form(...),
                service_ids: List[int] = Form(...),  # Accept multiple services 
                db: Session = Depends(get_db), 
                owner=Depends(get_current_user)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if shop.user_id != owner["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to add workers")

    # Check if worker already exists
    existing_worker = db.query(Worker).filter(Worker.shop_id == shop_id, Worker.user_id == user_id).first()
    if existing_worker:
        request.session["worker_error"] = "User is already added as a worker"
        return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)
        # raise HTTPException(status_code=400, detail="User is already a worker")

    # Create new Worker
    worker = Worker(user_id=user_id, shop_id=shop_id)
    # Assign Selected Services to Worker
    selected_services = db.query(Service).filter(Service.id.in_(service_ids)).all()
    worker.services.extend(selected_services)

    db.add(worker)
    db.commit()

    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@router.post("/{shop_id}/book_appointment")
def book_appointment(shop_id: int, worker_id: int = Form(...), date: str = Form(...), time: str = Form(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    appointment = Appointment(user_id=user["id"], worker_id=worker_id, shop_id=shop_id, date=date, time=time)
    db.add(appointment)
    db.commit()
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@router.post("/{shop_id}/add_service")
def add_service(shop_id: int, 
                service_name: str = Form(...), 
                db: Session = Depends(get_db), 
                owner=Depends(get_current_user)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if shop.user_id != owner["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to add services")

    new_service = Service(name=service_name, shop_id=shop_id)
    db.add(new_service)
    db.commit()

    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@router.post("/{shop_id}/remove_worker")
def remove_worker(
    shop_id: int,
    worker_id: int = Form(...),
    db: Session = Depends(get_db),
    owner=Depends(get_current_user)
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if shop.user_id != owner["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to remove workers")

    worker = db.query(Worker).filter(Worker.id == worker_id, Worker.shop_id == shop_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    db.delete(worker)
    db.commit()

    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@router.post("/{shop_id}/add_worker_service")
def add_worker_service(
    shop_id: int,
    worker_id: int = Form(...),
    service_id: int = Form(...),
    db: Session = Depends(get_db),
    owner=Depends(get_current_user)
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if shop.user_id != owner["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to modify workers")

    worker = db.query(Worker).filter(Worker.id == worker_id, Worker.shop_id == shop_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    service = db.query(Service).filter(Service.id == service_id, Service.shop_id == shop_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service in worker.services:
        raise HTTPException(status_code=400, detail="Service already assigned to this worker")

    worker.services.append(service)
    db.commit()

    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@router.post("/{shop_id}/remove_worker_service")
def remove_worker_service(
    shop_id: int,
    worker_id: int = Form(...),
    service_id: int = Form(...),
    db: Session = Depends(get_db),
    owner=Depends(get_current_user)
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if shop.user_id != owner["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to modify workers")

    worker = db.query(Worker).filter(Worker.id == worker_id, Worker.shop_id == shop_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    service = db.query(Service).filter(Service.id == service_id, Service.shop_id == shop_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service not in worker.services:
        raise HTTPException(status_code=400, detail="Service not assigned to this worker")

    worker.services.remove(service)
    db.commit()

    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)
