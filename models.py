from sqlalchemy import Column, Integer, String, ForeignKey, Text,Table
from sqlalchemy.orm import relationship
from database import Base

# Many-to-Many Relationship Table
worker_services = Table(
    "worker_services",
    Base.metadata,
    Column("worker_id", Integer, ForeignKey("workers.id"), primary_key=True),
    Column("service_id", Integer, ForeignKey("services.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

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
    # pin = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
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

    shop_id = Column(Integer, ForeignKey("shops.id"))
    shop = relationship("Shop", back_populates="services")
    workers = relationship("Worker", secondary=worker_services, back_populates="services")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"))
    shop_id = Column(Integer, ForeignKey("shops.id"))
    date = Column(String)
    time = Column(String)

    user = relationship("User", backref="appointments")
    worker = relationship("Worker", backref="appointments")
    shop = relationship("Shop", backref="appointments")
