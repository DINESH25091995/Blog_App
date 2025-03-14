from fastapi import APIRouter, Form, Request, Depends, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from models import Blog,BlogImage,Shop, ShopImage, Appointment, User, Worker, Service,appointment_services
from database import get_db
import os
import shutil
from typing import List
from datetime import datetime,timedelta,time
import pytz
from fastapi import Query
from sqlalchemy.sql import func, and_

from routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SHOP_DIR = "static/uploads/shopprofile"
os.makedirs(SHOP_DIR, exist_ok=True)  # Create directory if not exists

# ✅ IST Timezone
IST = pytz.timezone("Asia/Kolkata")

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
def shop_detail(request: Request, 
                shop_id: int, 
                view_all: bool = Query(False),  # Flag to show full history
                date_filter: str = Query(None),
                db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    users = db.query(User).all()  # Fetch all users for the dropdown
    user = request.session.get("user")
    
    today_date = datetime.now(IST).strftime('%Y-%m-%d')  # Get today's date
    
    # ✅ Use `date_filter` if provided, otherwise default to today
    selected_date = date_filter if date_filter else today_date

    query = (
    db.query(Appointment)
    .join(Worker)
    .outerjoin(Worker.services)  # Join with services
    .filter(Appointment.shop_id == shop_id))

    if not view_all:
        query = query.filter(Appointment.date == selected_date)  # Show only today's appointments

    appointments = query.all()

    # appointments = db.query(Appointment).filter(Appointment.shop_id == shop_id).all()
    # appointments = (
    # db.query(Appointment)
    # .join(Worker)
    # .outerjoin(Worker.services)  # Join with services
    # .filter(Appointment.shop_id == shop_id)
    # .all())

    # appointments = db.query(Appointment).filter(Appointment.user_id == user["id"]).all()
    return templates.TemplateResponse("shop_detail.html", {"request": request, "shop": shop, 
                                    "current_user": user, "users": users,"appointments":appointments,
                                    "selected_date": selected_date})


@router.post("/delete/{shop_id}")
def delete_shop(shop_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Blog not found")

    if shop.user_id != user["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this blog")

    # db.delete(shop)
    # db.commit()
    # Delete all workers associated with the shop
    db.query(Worker).filter(Worker.shop_id == shop_id).delete(synchronize_session=False)

    # Delete all appointments related to the shop
    db.query(Appointment).filter(Appointment.shop_id == shop_id).delete(synchronize_session=False)

    # Delete the shop itself
    db.query(Shop).filter(Shop.id == shop_id).delete(synchronize_session=False)

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


# @router.post("/{shop_id}/book_appointment")
# def book_appointment(
#     shop_id: int,
#     worker_id: int = Form(...),  # Get worker ID from form
#     date: str = Form(...),       # Get date from form
#     time: str = Form(...),       # Get time from form
#     selected_service_ids: List[int] = Form(...),  # Get selected service IDs as a list
#     db: Session = Depends(get_db),
#     user: dict = Depends(get_current_user),
# ):
    
#     shop = db.query(Shop).filter(Shop.id == shop_id).first()
#     if not shop.is_open:
#         raise HTTPException(status_code=400, detail="Shop is closed, cannot book appointment.")

#     booking_time = datetime.strptime(time, "%H:%M").time()
#     open_time = datetime.strptime(shop.open_time, "%H:%M").time()
#     close_time = datetime.strptime(shop.close_time, "%H:%M").time()

#     if not (open_time <= booking_time <= close_time):
#         raise HTTPException(status_code=400, detail="Appointment time must be within shop hours.")

#     # ✅ Calculate total price based on selected services
#     total_price = (
#         db.query(func.sum(Service.price))
#         .filter(Service.id.in_(selected_service_ids))
#         .scalar()
#     ) or 0.0  # If no services selected, default to 0


#      # ✅ Convert current UTC time to IST
#     ist_timezone = pytz.timezone('Asia/Kolkata')
#     created_at_ist = datetime.now(pytz.utc).astimezone(ist_timezone)

#     appointment = Appointment(user_id=user["id"], 
#                             worker_id=worker_id, 
#                             shop_id=shop_id, 
#                             date=date, 
#                             time=time,
#                             total_price=total_price,  # ✅ Save total amount
#                             created_at=created_at_ist)
#     db.add(appointment)
#     db.commit()
#     db.refresh(appointment)

#     # Insert selected services into the association table
#     if selected_service_ids:
#         db.execute(
#             appointment_services.insert(),
#             [{"appointment_id": appointment.id, "service_id": service_id} for service_id in selected_service_ids]
#         )
#         db.commit()

#     return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@router.post("/{shop_id}/add_service")
def add_service(shop_id: int, 
                service_name: str = Form(...),
                duration_minutes: int = Form(...),  # New field for duration
                price: float = Form(...),  # New field for price 
                db: Session = Depends(get_db), 
                owner=Depends(get_current_user)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()

    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if shop.user_id != owner["id"]:
        raise HTTPException(status_code=403, detail="You are not allowed to add services")

    new_service = Service(name=service_name,
                          duration_minutes=duration_minutes,
                          price=price,
                          shop_id=shop_id)
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


@router.post("/{shop_id}/set_schedule")
def set_shop_schedule(
    shop_id: int,
    open_time: str = Form(...),
    close_time: str = Form(...),
    is_open: bool = Form(...),
    db: Session = Depends(get_db)
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        return {"error": "Shop not found"}
    if open_time and close_time :
        shop.open_time = open_time
        shop.close_time = close_time
    
    shop.is_open = is_open
        
    db.commit()
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


def get_next_available_time(db, worker_id, date, shop_open_time):
    """Finds the earliest available time slot for a worker on a given date."""
    
    # Ensure shop_open_time is a time object
    shop_open = shop_open_time if isinstance(shop_open_time, time) else datetime.strptime(shop_open_time, "%H:%M").time()
    
    # Fetch all existing appointments for the worker
    appointments = (
        db.query(Appointment)
        .filter(Appointment.worker_id == worker_id, Appointment.date == date)
        .order_by(Appointment.time.asc())
        .all()
    )

    current_ist = datetime.now(IST).time()
    available_time = max(shop_open, current_ist) if date == datetime.now(IST).date().isoformat() else shop_open

    # Convert available_time to a datetime object for easy comparison
    available_datetime = datetime.combine(datetime.today(), available_time)

    for appointment in appointments:
        start_time = datetime.strptime(appointment.time, "%H:%M").time()
        start_datetime = datetime.combine(datetime.today(), start_time)

        # ✅ Correctly calculate the end time of this appointment
        appointment_duration = (
            db.query(func.sum(Service.duration_minutes))
            .join(appointment_services)
            .filter(appointment_services.c.appointment_id == appointment.id)
            .scalar()
        ) or 0

        # end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=appointment_duration)).time()
        end_datetime = start_datetime + timedelta(minutes=appointment_duration)

        if available_datetime + timedelta(minutes=appointment_duration) <= start_datetime:
            return available_datetime.time()

        # Move available time forward if this slot is occupied
        available_datetime = end_datetime

    # return available_time  # ✅ Return as time object (not string)
    # If no gaps found, return the next available time after the last appointment
    return available_datetime.time()


@router.post("/{shop_id}/book_appointment")
def book_appointment(
    shop_id: int,
    worker_id: int = Form(...),
    date: str = Form(...),
    time: str = Form(None),  # Optional time for serial booking
    selected_service_ids: list[int] = Form(...),
    prefer_earliest: bool = Form(False),  # ✅ Option to book earliest available slot
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Handles appointment booking with custom time selection or earliest available slot."""
    
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop or not shop.is_open:
        raise HTTPException(status_code=400, detail="Shop is closed, cannot book appointment.")

    # ✅ Convert shop open/close times
    shop_open_time = datetime.strptime(shop.open_time, "%H:%M").time()
    shop_close_time = datetime.strptime(shop.close_time, "%H:%M").time()

    # ✅ Get current IST time
    current_time_ist = datetime.now(IST).time()

    # ✅ Restrict booking dates to only today or tomorrow
    today = datetime.now(IST).date()
    tomorrow = today + timedelta(days=1)

    if date not in [today.isoformat(), tomorrow.isoformat()]:
        raise HTTPException(status_code=400, detail="You can only book for today or tomorrow.")

    # ✅ Ensure booking only within shop hours
    if date == today.isoformat() and current_time_ist > shop_close_time:
        raise HTTPException(status_code=400, detail="Shop is closed for today, try tomorrow.")


    # ✅ Calculate total duration of selected services
    total_duration = (
        db.query(func.sum(Service.duration_minutes))
        .filter(Service.id.in_(selected_service_ids))
        .scalar()
    ) or 0

    # ✅ Determine booking time (Earliest or Custom)
    if prefer_earliest or not time:
        booking_time = get_next_available_time(db, worker_id, date, shop_open_time)  # ✅ Already a `datetime.time` object
    else:
        booking_time = datetime.strptime(time, "%H:%M").time()  # Convert string to `datetime.time`

    # ✅ Ensure booking time is within shop hours
    if booking_time < shop_open_time or booking_time > shop_close_time:
        raise HTTPException(status_code=400, detail="Appointment time must be within shop hours.")

    if date == today.isoformat() and booking_time < current_time_ist:
        raise HTTPException(status_code=400, detail="Cannot book a past time.")


    # ✅ Check for overlapping appointments
    existing_appointments = db.query(Appointment).filter(
        Appointment.worker_id == worker_id,
        Appointment.date == date
    ).all()

    for appointment in existing_appointments:
        start_time = datetime.strptime(appointment.time, "%H:%M").time()

        # ✅ Calculate the end time correctly
        appointment_duration = (
            db.query(func.sum(Service.duration_minutes))
            .join(appointment_services)
            .filter(appointment_services.c.appointment_id == appointment.id)
            .scalar()
        ) or 0

        end_time = (datetime.combine(datetime.today(), start_time) + timedelta(minutes=appointment_duration)).time()

        # ✅ Check if new appointment overlaps with existing one
        if start_time <= booking_time < end_time:
            raise HTTPException(status_code=400, detail="Selected time is already booked. Try another time.")

    # # ✅ Calculate end time
    # start_time_obj = datetime.combine(datetime.today(), booking_time)
    # end_time_obj = start_time_obj + timedelta(minutes=total_duration)
    # end_time = end_time_obj.time()

    # # ✅ Ensure appointment doesn't exceed shop closing time
    # if end_time > shop_close_time:
    #     raise HTTPException(status_code=400, detail="Services extend beyond shop closing time.")
     # ✅ Ensure appointment does not exceed shop closing time
    end_time = (datetime.combine(datetime.today(), booking_time) + timedelta(minutes=total_duration)).time()
    if end_time > shop_close_time:
        raise HTTPException(status_code=400, detail="Services extend beyond shop closing time.")

    # ✅ Calculate total price
    total_price = (
        db.query(func.sum(Service.price))
        .filter(Service.id.in_(selected_service_ids))
        .scalar()
    ) or 0.0

    # # ✅ Convert current time to IST (Indian Standard Time)
    # ist_timezone = pytz.timezone("Asia/Kolkata")
    # created_at_ist = datetime.now(pytz.utc).astimezone(ist_timezone)

    # ✅ Create and save the appointment
    appointment = Appointment(
        user_id=user["id"],
        worker_id=worker_id,
        shop_id=shop_id,
        date=date,
        time=booking_time.strftime("%H:%M"),  # Convert time object to string before storing
        total_price=total_price,
        created_at=datetime.now(IST),
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # ✅ Link selected services to appointment
    if selected_service_ids:
        db.execute(
            appointment_services.insert(),
            [{"appointment_id": appointment.id, "service_id": service_id} for service_id in selected_service_ids]
        )
        db.commit()

    # return {"message": "Appointment booked successfully", "appointment_time": booking_time.strftime("%H:%M")}
    return RedirectResponse(url=f"/shops/{shop_id}", status_code=303)


@router.get("/{shop_id}/available_time")
def get_available_time_slots(shop_id: int, worker_id: int, date: str, db: Session = Depends(get_db)):
    """Finds the available time slots for a worker on a given date."""
    
    # Convert date string to date object
    date = datetime.strptime(date, "%Y-%m-%d").date()

    # Fetch shop details
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        return {"error": "Shop not found."}

    # Convert shop opening and closing times
    shop_open_time = datetime.combine(date, datetime.strptime(shop.open_time, "%H:%M").time())
    shop_close_time = datetime.combine(date, datetime.strptime(shop.close_time, "%H:%M").time())

    # Fetch all existing appointments for the worker
    appointments = (
        db.query(Appointment)
        .filter(Appointment.worker_id == worker_id, Appointment.date == date)
        .order_by(Appointment.time.asc())
        .all()
    )

    # Get current time in IST
    current_ist = datetime.now(IST).time()
    
    # Ensure available time starts correctly
    available_time = max(shop_open_time, datetime.combine(date, current_ist)) if date == datetime.now(IST).date() else shop_open_time

    available_slots = []
    
    for appointment in appointments:
        start_time = datetime.strptime(appointment.time, "%H:%M").time()
        start_datetime = datetime.combine(date, start_time)

        # Get appointment duration
        appointment_duration = (
            db.query(func.sum(Service.duration_minutes))
            .join(appointment_services)
            .filter(appointment_services.c.appointment_id == appointment.id)
            .scalar()
        ) or 0

        end_datetime = start_datetime + timedelta(minutes=appointment_duration)

        
        # If there's a gap before this appointment, add it to available slots
        if available_time < start_datetime:
            available_slots.append([
                available_time.strftime("%H:%M"),
                start_datetime.strftime("%H:%M")
            ])

        # Move available time to after this appointment
        available_time = end_datetime

    current_ist_date = datetime.now(IST).date()
    # If there's free time after the last appointment, add it
    if available_time < shop_close_time:
        if date == current_ist_date:
            if (current_ist.strftime("%H:%M") < shop_close_time.strftime("%H:%M")) and (current_ist.strftime("%H:%M") > available_time.strftime("%H:%M")):
                available_slots.append([
                    current_ist.strftime("%H:%M"),
                    shop_close_time.strftime("%H:%M")
                ])
            else:
                available_slots.append([
                available_time.strftime("%H:%M"),
                shop_close_time.strftime("%H:%M")
            ])
        else:
            available_slots.append([
                available_time.strftime("%H:%M"),
                shop_close_time.strftime("%H:%M")
            ])

        # available_slots.append([
        #         available_time.strftime("%H:%M"),
        #         shop_close_time.strftime("%H:%M")
        #     ])

    return {"available_slots": available_slots}



@router.put("/appointments/{appointment_id}/status")
def update_appointment_status(request: Request,
    appointment_id: int,
    db: Session = Depends(get_db),
    owner=Depends(get_current_user)
):
    """Allows shop owners to mark an appointment as 'Done'."""
    
    # Fetch appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    # Check if the user is the shop owner
    if owner["id"] != appointment.shop.user_id:
        raise HTTPException(status_code=403, detail="Only shop owners can update appointment status.")

    # Update status if it's "Queue"
    if appointment.status == "Queue":
        appointment.status = "Done"
        db.commit()
        db.refresh(appointment)

    return {"message": "Appointment marked as Done"}