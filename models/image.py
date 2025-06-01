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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    storage_path = Column(String(500), nullable=False)
    room_type = Column(String(50))
    description = Column(Text)
    upload_time = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="images")
    processed_images = relationship("ProcessedImage", back_populates="original_image", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Image(id={self.id}, user_id={self.user_id}, filename={self.original_filename})>"

class ProcessedImage(Base):
    """Model for storing processed images with color applied"""
    __tablename__ = "processed_images"
    
    id = Column(String, primary_key=True, default=lambda: f"proc_{uuid.uuid4().hex[:12]}")
    original_image_id = Column(String, ForeignKey("images.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    color_code = Column(String(7), nullable=False)  # Hex color code
    color_name = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    processing_time = Column(Float)  # in seconds
    region_data = Column(JSON, nullable=False)  # Coordinates and region type
    surface_type = Column(String(50))  # wall, ceiling, floor, etc.
    blend_mode = Column(String(20), default="normal")
    opacity = Column(Float, default=0.8)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="processed_images")
    original_image = relationship("Image", back_populates="processed_images")
    
    def __repr__(self):
        return f"<ProcessedImage(id={self.id}, original_image_id={self.original_image_id}, color={self.color_code})>"

class DemoImage(Base):
    """Model for storing demo room images"""
    __tablename__ = "demo_images"
    
    id = Column(String, primary_key=True, default=lambda: f"demo_{uuid.uuid4().hex[:12]}")
    name = Column(String(100), nullable=False)
    description = Column(Text)
    storage_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    room_type = Column(String(50), nullable=False)  # living_room, bedroom, etc.
    style = Column(String(50))  # modern, classic, etc.
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DemoImage(id={self.id}, name={self.name}, room_type={self.room_type})>" 