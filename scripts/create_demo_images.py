#!/usr/bin/env python
"""
Script to create demo images for the Color Swap application.
Adds demo images to the database and storage.
"""

import os
import sys
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PIL import Image

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.image import DemoImage
from database import Base

# Demo images data
DEMO_IMAGES = [
    {
        "name": "Phòng khách hiện đại",
        "description": "Phòng khách hiện đại với sofa xám",
        "filename": "living_room_modern.jpg",
        "room_type": "living_room",
        "style": "modern",
    },
    {
        "name": "Phòng ngủ cổ điển",
        "description": "Phòng ngủ phong cách cổ điển",
        "filename": "bedroom_classic.jpg",
        "room_type": "bedroom",
        "style": "classic",
    },
    {
        "name": "Nhà bếp đương đại",
        "description": "Không gian bếp hiện đại với kệ bếp trắng",
        "filename": "kitchen_contemporary.jpg",
        "room_type": "kitchen",
        "style": "contemporary",
    }
]

def create_demo_images(db_url):
    """Create demo images and add to database"""
    
    # Create engine and session
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Ensure storage directories exist
    storage_path = Path("storage")
    demo_path = storage_path / "demo"
    demo_thumbs_path = demo_path / "thumbnails"
    
    os.makedirs(demo_path, exist_ok=True)
    os.makedirs(demo_thumbs_path, exist_ok=True)
    
    # Path to sample images
    sample_images_path = Path("scripts") / "sample_images"
    
    try:
        for img_data in DEMO_IMAGES:
            # Source and destination paths
            source_path = sample_images_path / img_data["filename"]
            dest_path = demo_path / img_data["filename"]
            
            # Skip if source image doesn't exist
            if not source_path.exists():
                print(f"Warning: Sample image {source_path} not found, skipping")
                continue
            
            # Copy image to demo directory
            shutil.copy(source_path, dest_path)
            
            # Create thumbnail
            with Image.open(dest_path) as img:
                width, height = img.size
                
                # Create thumbnail
                img.thumbnail((300, 300))
                thumb_filename = f"thumb_{img_data['filename']}"
                thumb_path = demo_thumbs_path / thumb_filename
                img.save(thumb_path, "JPEG", quality=85)
                
                # Check if demo image already exists in database
                existing = session.query(DemoImage).filter_by(name=img_data["name"]).first()
                
                if existing:
                    print(f"Demo image '{img_data['name']}' already exists, skipping")
                    continue
                
                # Create demo image record
                demo_image = DemoImage(
                    name=img_data["name"],
                    description=img_data["description"],
                    storage_path=str(dest_path),
                    thumbnail_path=str(thumb_path),
                    room_type=img_data["room_type"],
                    style=img_data["style"],
                    width=width,
                    height=height,
                    is_active=1
                )
                
                session.add(demo_image)
                print(f"Added demo image: {img_data['name']}")
        
        # Commit changes
        session.commit()
        print("Demo images created successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error creating demo images: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # Default database URL
    db_url = os.environ.get(
        "DATABASE_URL", 
        "postgresql://colorswapuser_backend:colorswappass_backend@localhost:5433/colorswapdb_backend"
    )
    
    create_demo_images(db_url) 