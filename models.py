from sqlalchemy import Column, Integer, String, ForeignKey, Text,Table, Boolean,DateTime,Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# Many-to-Many Relationship Table
worker_services = Table(
    "worker_services",
    Base.metadata,
    Column("worker_id", Integer, ForeignKey("workers.id"), primary_key=True),
    Column("service_id", Integer, ForeignKey("services.id"), primary_key=True),
)

# Many-to-Many Table for Appointments and Services
appointment_services = Table(
    "appointment_services",
    Base.metadata,
    Column("appointment_id", ForeignKey("appointments.id"), primary_key=True),
    Column("service_id", ForeignKey("services.id"), primary_key=True),
)

# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     hashed_password = Column(String)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    mobile = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True)  # Will be hashed
    is_verified = Column(Boolean, default=False)  # For OTP verification
    otp = Column(String, nullable=True)  # Stores the OTP temporarily


class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    comments = relationship("Comment", back_populates="blog")
    user_id = Column(Integer, ForeignKey("users.id"))
    # image = Column(String, nullable=True)  # Store image filename/path
    images = relationship("BlogImage", back_populates="blog", cascade="all, delete-orphan")

class BlogImage(Base):
    __tablename__ = "blog_images"
    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"))
    image_path = Column(String, nullable=False)
    
    blog = relationship("Blog", back_populates="images")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"))
    content = Column(Text)
    blog = relationship("Blog", back_populates="comments")
    user_id = Column(Integer, ForeignKey("users.id"))

class Shop(Base):
    __tablename__ = "shops"
    id = Column(Integer, primary_key=True, index=True)
    shop_name = Column(String)
    address = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    # Adding open time, close time, and is_open field
    open_time = Column(String, nullable=True)  # e.g., '09:00 AM'
    close_time = Column(String, nullable=True)  # e.g., '06:00 PM'
    is_open = Column(Boolean, default=False)  # Whether the shop is currently open or closed

    images = relationship("ShopImage", back_populates="shop", cascade="all, delete-orphan")
    workers = relationship("Worker", back_populates="shop", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="shop", cascade="all, delete-orphan")

class ShopImage(Base):
    __tablename__ = "shop_images"
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"))
    image_path = Column(String, nullable=False)
    shop = relationship("Shop", back_populates="images")


class Worker(Base):
    __tablename__ = "workers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    shop_id = Column(Integer, ForeignKey("shops.id"))
    
    user = relationship("User", backref="worker_shops")
    shop = relationship("Shop", back_populates="workers")
    # Many-to-Many Relationship with Services
    services = relationship("Service", secondary=worker_services, back_populates="workers")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    duration_minutes = Column(Integer, nullable=False)  # Time required for the service (in minutes)
    price = Column(Float, nullable=False)  # Cost of the service

    shop_id = Column(Integer, ForeignKey("shops.id"))
    shop = relationship("Shop", back_populates="services")
    workers = relationship("Worker", secondary=worker_services, back_populates="services")
    appointments = relationship("Appointment", secondary=appointment_services, back_populates="services")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"))
    shop_id = Column(Integer, ForeignKey("shops.id"))
    date = Column(String)
    time = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)  # ✅ Automatically set booking time
    total_price = Column(Float, nullable=False)  # ✅ Total payment amount
    payment_status = Column(String, default="Pending")  # Can be "Pending" or "Paid"
    
    user = relationship("User", backref="appointments")
    worker = relationship("Worker", backref="appointments")
    shop = relationship("Shop", backref="appointments")
    services = relationship("Service", secondary=appointment_services, back_populates="appointments")