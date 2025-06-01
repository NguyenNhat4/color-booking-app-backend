import os
import uuid
import time
from typing import Optional, List, Tuple
from PIL import Image as PILImage, ImageDraw, ImageFilter
import aiofiles
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from models.image import Image, ProcessedImage, DemoImage
from schemas.image_schemas import RegionData, ImageDimensions

class ImageStorageService:
    """Service for handling image storage operations"""
    
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = storage_path
        self.images_path = os.path.join(storage_path, "images")
        self.thumbnails_path = os.path.join(storage_path, "thumbnails")
        self.processed_path = os.path.join(storage_path, "processed")
        self.demo_path = os.path.join(storage_path, "demo")
        
        # Create directories if they don't exist
        for path in [self.images_path, self.thumbnails_path, self.processed_path, self.demo_path]:
            os.makedirs(path, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile, user_id: str) -> Tuple[str, str]:
        """Save uploaded file and return file path and filename"""
        # Generate unique filename
        filename = file.filename or "unknown.jpg"
        file_extension = os.path.splitext(filename)[1].lower()
        unique_filename = f"{user_id}_{uuid.uuid4().hex[:12]}{file_extension}"
        file_path = os.path.join(self.images_path, unique_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path, unique_filename
    
    async def save_processed_image(self, image: PILImage.Image, processed_id: str) -> str:
        """Save processed image and return file path"""
        filename = f"{processed_id}.jpg"
        file_path = os.path.join(self.processed_path, filename)
        
        # Save as JPEG with high quality
        image.save(file_path, "JPEG", quality=90, optimize=True)
        return file_path
    
    async def create_thumbnail(self, image_path: str, thumbnail_size: Tuple[int, int] = (300, 300)) -> str:
        """Create thumbnail and return thumbnail path"""
        with PILImage.open(image_path) as img:
            img.thumbnail(thumbnail_size, PILImage.Resampling.LANCZOS)
            
            # Generate thumbnail filename
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            thumbnail_filename = f"{base_name}_thumb.jpg"
            thumbnail_path = os.path.join(self.thumbnails_path, thumbnail_filename)
            
            # Save thumbnail
            img.save(thumbnail_path, "JPEG", quality=85, optimize=True)
            return thumbnail_path

class ImageValidationService:
    """Service for validating uploaded images"""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSIONS = (4096, 4096)
    
    @classmethod
    def validate_file_format(cls, filename: str) -> bool:
        """Validate file format"""
        extension = os.path.splitext(filename)[1].lower()
        return extension in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> bool:
        """Validate file size"""
        return file_size <= cls.MAX_FILE_SIZE
    
    @classmethod
    def validate_image_dimensions(cls, image: PILImage.Image) -> bool:
        """Validate image dimensions"""
        width, height = image.size
        return width <= cls.MAX_DIMENSIONS[0] and height <= cls.MAX_DIMENSIONS[1]
    
    @classmethod
    async def validate_uploaded_file(cls, file: UploadFile) -> None:
        """Comprehensive validation of uploaded file"""
        # Check file format
        filename = file.filename or "unknown"
        if not cls.validate_file_format(filename):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_IMAGE_FORMAT",
                    "message": "Unsupported image format",
                    "details": f"Only {', '.join(cls.ALLOWED_EXTENSIONS)} formats are supported"
                }
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if not cls.validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "IMAGE_TOO_LARGE",
                    "message": "Image file is too large",
                    "details": f"Maximum file size is {cls.MAX_FILE_SIZE // (1024*1024)}MB"
                }
            )

class ImageProcessingService:
    """Service for image processing operations"""
    
    def __init__(self, storage_service: ImageStorageService):
        self.storage_service = storage_service
    
    async def compress_image(self, image_path: str, quality: int = 85) -> PILImage.Image:
        """Compress image while maintaining quality"""
        with PILImage.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            max_size = (1920, 1080)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
            
            return img.copy()
    
    async def apply_color_overlay(
        self, 
        image_path: str, 
        region_data: RegionData, 
        color_code: str, 
        opacity: float = 0.8
    ) -> Tuple[PILImage.Image, float]:
        """Apply color overlay to specified region"""
        start_time = time.time()
        
        with PILImage.open(image_path) as base_img:
            # Convert to RGBA for transparency support
            if base_img.mode != 'RGBA':
                base_img = base_img.convert('RGBA')
            
            # Create overlay layer
            overlay = PILImage.new('RGBA', base_img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Convert hex color to RGB
            color_rgb = self._hex_to_rgb(color_code)
            color_with_alpha = (*color_rgb, int(255 * opacity))
            
            # Draw the region based on type
            if region_data.type == "polygon":
                points = [(coord.x, coord.y) for coord in region_data.coordinates]
                draw.polygon(points, fill=color_with_alpha)
            elif region_data.type == "rectangle":
                if len(region_data.coordinates) >= 2:
                    x1, y1 = region_data.coordinates[0].x, region_data.coordinates[0].y
                    x2, y2 = region_data.coordinates[1].x, region_data.coordinates[1].y
                    draw.rectangle([x1, y1, x2, y2], fill=color_with_alpha)
            
            # Blend overlay with base image
            result = PILImage.alpha_composite(base_img, overlay)
            
            # Convert back to RGB for saving
            result = result.convert('RGB')
            
            processing_time = time.time() - start_time
            return result, processing_time
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError("Invalid hex color format")
        return (
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
    
    async def get_image_metadata(self, image_path: str) -> dict:
        """Extract image metadata"""
        with PILImage.open(image_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "file_size": os.path.getsize(image_path)
            }

class ImageService:
    """Main service for image operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_service = ImageStorageService()
        self.validation_service = ImageValidationService()
        self.processing_service = ImageProcessingService(self.storage_service)
    
    async def upload_image(
        self, 
        file: UploadFile, 
        user_id: str, 
        room_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Image:
        """Upload and process image"""
        # Validate file
        await self.validation_service.validate_uploaded_file(file)
        
        try:
            # Save uploaded file
            file_path, filename = await self.storage_service.save_uploaded_file(file, user_id)
            
            # Get image metadata
            metadata = await self.processing_service.get_image_metadata(file_path)
            
            # Create thumbnail
            thumbnail_path = await self.storage_service.create_thumbnail(file_path)
            
            # Create database record
            image = Image(
                user_id=user_id,
                original_filename=file.filename or "unknown.jpg",
                file_size=metadata["file_size"],
                width=metadata["width"],
                height=metadata["height"],
                storage_path=file_path,
                room_type=room_type,
                description=description
            )
            
            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)
            
            return image
            
        except Exception as e:
            # Clean up files if database operation fails
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            if 'thumbnail_path' in locals() and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "PROCESSING_FAILED",
                    "message": "Image processing failed",
                    "details": str(e)
                }
            )
    
    async def apply_color_to_image(
        self,
        image_id: str,
        user_id: str,
        region_data: RegionData,
        color_code: str,
        color_name: str,
        surface_type: str = "wall",
        blend_mode: str = "normal",
        opacity: float = 0.8
    ) -> ProcessedImage:
        """Apply color to image region"""
        # Get original image
        image = self.db.query(Image).filter(
            Image.id == image_id,
            Image.user_id == user_id
        ).first()
        
        if not image:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "IMAGE_NOT_FOUND",
                    "message": "Image not found",
                    "details": "The specified image does not exist or you don't have permission to access it"
                }
            )
        
        try:
            # Apply color overlay
            processed_img, processing_time = await self.processing_service.apply_color_overlay(
                image.storage_path, region_data, color_code, opacity
            )
            
            # Save processed image
            processed_id = f"proc_{uuid.uuid4().hex[:12]}"
            processed_path = await self.storage_service.save_processed_image(processed_img, processed_id)
            
            # Create thumbnail for processed image
            thumbnail_path = await self.storage_service.create_thumbnail(processed_path)
            
            # Create database record
            processed_image = ProcessedImage(
                id=processed_id,
                original_image_id=image_id,
                user_id=user_id,
                color_code=color_code,
                color_name=color_name,
                storage_path=processed_path,
                processing_time=processing_time,
                region_data=region_data.dict(),
                surface_type=surface_type,
                blend_mode=blend_mode,
                opacity=opacity
            )
            
            self.db.add(processed_image)
            self.db.commit()
            self.db.refresh(processed_image)
            
            return processed_image
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "PROCESSING_FAILED",
                    "message": "Color application failed",
                    "details": str(e)
                }
            )
    
    def get_demo_images(self) -> List[DemoImage]:
        """Get list of available demo images"""
        return self.db.query(DemoImage).filter(DemoImage.is_active == 1).all()
    
    def get_user_images(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Image]:
        """Get user's uploaded images"""
        return self.db.query(Image).filter(
            Image.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_user_processed_images(self, user_id: str, skip: int = 0, limit: int = 20) -> List[ProcessedImage]:
        """Get user's processed images"""
        return self.db.query(ProcessedImage).filter(
            ProcessedImage.user_id == user_id
        ).offset(skip).limit(limit).all() 