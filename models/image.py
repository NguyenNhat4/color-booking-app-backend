from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base

class Image(Base):
    """Model for storing original uploaded images"""
    __tablename__ = "images"
    
    id = Column(String, primary_key=True, default=lambda: f"img_{uuid.uuid4().hex[:12]}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    room_type = Column(String(50), nullable=True)  # living_room, bedroom, kitchen, bathroom
    description = Column(Text, nullable=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="images")
    processed_images = relationship("ProcessedImage", back_populates="original_image", cascade="all, delete-orphan")

class ProcessedImage(Base):
    """Model for storing processed images with color applications"""
    __tablename__ = "processed_images"
    
    id = Column(String, primary_key=True, default=lambda: f"proc_{uuid.uuid4().hex[:12]}")
    original_image_id = Column(String, ForeignKey("images.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    color_code = Column(String(7), nullable=False)  # hex color code
    color_name = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    processing_time = Column(Float, nullable=True)  # in seconds
    region_data = Column(JSON, nullable=False)  # coordinates of the selected region
    surface_type = Column(String(50), default="wall")  # wall, ceiling, floor
    blend_mode = Column(String(20), default="normal")
    opacity = Column(Float, default=0.8)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    original_image = relationship("Image", back_populates="processed_images")
    user = relationship("User", back_populates="processed_images")

class DemoImage(Base):
    """Model for storing demo images"""
    __tablename__ = "demo_images"
    
    id = Column(String, primary_key=True, default=lambda: f"demo_{uuid.uuid4().hex[:12]}")
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    storage_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    room_type = Column(String(50), nullable=False)
    style = Column(String(50), nullable=True)  # modern, classic, minimalist
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    created_at = Column(DateTime, default=datetime.utcnow) 