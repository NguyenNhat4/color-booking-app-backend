from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Any, Dict, cast
import os

from database import get_db
from services.image_service import ImageService
from schemas.image_schemas import (
    ImageUploadResponse,
    ColorApplicationRequest,
    ColorApplicationResponse,
    DemoImagesResponse,
    StandardResponse,
    ImageDimensions,
    AppliedColorInfo,
    DemoImageInfo
)
from api.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/images", tags=["images"])

def get_image_service(db: Session = Depends(get_db)) -> ImageService:
    """Dependency to get ImageService instance"""
    return ImageService(db)

@router.post("/upload", response_model=StandardResponse)
async def upload_image(
    file: UploadFile = File(...),
    room_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Upload an image for color processing
    
    - **file**: Image file (JPEG, PNG, HEIC)
    - **room_type**: Type of room (living_room, bedroom, kitchen, bathroom)
    - **description**: Optional description of the image
    """
    try:
        # Upload image
        image = await image_service.upload_image(
            file=file,
            user_id=int(current_user.id),  # type: ignore
            room_type=room_type,
            description=description
        )
        
        # Generate URLs (for MVP, we'll use simple file paths)
        base_url = "http://localhost:8001"  # TODO: Get from config
        original_url = f"{base_url}/images/files/{os.path.basename(str(image.storage_path))}"
        thumbnail_url = f"{base_url}/images/thumbnails/{os.path.basename(str(image.storage_path)).replace('.', '_thumb.')}"
        
        response_data = ImageUploadResponse(
            image_id=str(image.id),
            original_url=original_url,
            thumbnail_url=thumbnail_url,
            upload_time=image.upload_time,  # type: ignore
            file_size=int(image.file_size),  # type: ignore
            dimensions=ImageDimensions(width=int(image.width), height=int(image.height))  # type: ignore
        )
        
        return StandardResponse(
            success=True,
            data=response_data.dict(),
            message="Image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "UPLOAD_FAILED",
                "message": "Failed to upload image",
                "details": str(e)
            }
        )

@router.post("/{image_id}/apply-color", response_model=StandardResponse)
async def apply_color_to_image(
    image_id: str,
    color_request: ColorApplicationRequest,
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Apply color to a specific region of an uploaded image
    
    - **image_id**: ID of the uploaded image
    - **color_request**: Color application parameters including region coordinates
    """
    try:
        # Apply color to image
        processed_image = await image_service.apply_color_to_image(
            image_id=image_id,
            user_id=str(current_user.id),
            region_data=color_request.region,
            color_code=color_request.color_code,
            color_name=color_request.color_name,
            surface_type=color_request.surface_type,
            blend_mode=color_request.blend_mode,
            opacity=color_request.opacity
        )
        
        # Generate URLs
        base_url = "http://localhost:8001"  # TODO: Get from config
        processed_url = f"{base_url}/images/processed/{os.path.basename(str(processed_image.storage_path))}"
        thumbnail_url = f"{base_url}/images/thumbnails/{os.path.basename(str(processed_image.storage_path)).replace('.', '_thumb.')}"
        
        response_data = ColorApplicationResponse(
            processed_image_id=str(processed_image.id),
            processed_url=processed_url,
            thumbnail_url=thumbnail_url,
            processing_time=float(processed_image.processing_time or 0.0),  # type: ignore
            applied_color=AppliedColorInfo(
                color_code=str(processed_image.color_code),
                color_name=str(processed_image.color_name),
                product_id=None  # TODO: Link to product when product catalog is implemented
            )
        )
        
        return StandardResponse(
            success=True,
            data=response_data.dict(),
            message="Color applied successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "COLOR_APPLICATION_FAILED",
                "message": "Failed to apply color to image",
                "details": str(e)
            }
        )

@router.get("/demo", response_model=StandardResponse)
async def get_demo_images(
    image_service: ImageService = Depends(get_image_service)
):
    """
    Get list of available demo images
    """
    try:
        demo_images = image_service.get_demo_images()
        
        base_url = "http://localhost:8001"  # TODO: Get from config
        demo_list = []
        
        for demo in demo_images:
            demo_info = DemoImageInfo(
                demo_id=str(demo.id),
                name=str(demo.name),
                description=str(demo.description) if demo.description else None,
                image_url=f"{base_url}/images/demo/{os.path.basename(str(demo.storage_path))}",
                thumbnail_url=f"{base_url}/images/demo/thumbnails/{os.path.basename(str(demo.thumbnail_path or demo.storage_path))}",
                room_type=str(demo.room_type),
                style=str(demo.style) if demo.style else None
            )
            demo_list.append(demo_info)
        
        response_data = DemoImagesResponse(demo_images=demo_list)
        
        return StandardResponse(
            success=True,
            data=response_data.dict(),
            message="Demo images retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DEMO_IMAGES_FAILED",
                "message": "Failed to retrieve demo images",
                "details": str(e)
            }
        )

@router.get("/files/{filename}")
async def get_image_file(filename: str):
    """Serve uploaded image files"""
    file_path = os.path.join("storage", "images", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

@router.get("/processed/{filename}")
async def get_processed_image_file(filename: str):
    """Serve processed image files"""
    file_path = os.path.join("storage", "processed", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Processed image not found")
    return FileResponse(file_path)

@router.get("/thumbnails/{filename}")
async def get_thumbnail_file(filename: str):
    """Serve thumbnail image files"""
    file_path = os.path.join("storage", "thumbnails", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(file_path)

@router.get("/demo/{filename}")
async def get_demo_image_file(filename: str):
    """Serve demo image files"""
    file_path = os.path.join("storage", "demo", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Demo image not found")
    return FileResponse(file_path)

@router.get("/my-images", response_model=StandardResponse)
async def get_my_images(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """Get current user's uploaded images"""
    try:
        images = image_service.get_user_images(str(current_user.id), skip, limit)
        
        base_url = "http://localhost:8001"  # TODO: Get from config
        image_list = []
        
        for image in images:
            image_info = {
                "image_id": str(image.id),
                "original_filename": str(image.original_filename),
                "file_size": int(image.file_size),
                "dimensions": {"width": int(image.width), "height": int(image.height)},
                "room_type": str(image.room_type) if image.room_type else None,
                "description": str(image.description) if image.description else None,
                "upload_time": image.upload_time,
                "image_url": f"{base_url}/images/files/{os.path.basename(str(image.storage_path))}"
            }
            image_list.append(image_info)
        
        return StandardResponse(
            success=True,
            data={"images": image_list},
            message="Images retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "GET_IMAGES_FAILED",
                "message": "Failed to retrieve images",
                "details": str(e)
            }
        )

@router.get("/my-processed", response_model=StandardResponse)
async def get_my_processed_images(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """Get current user's processed images"""
    try:
        processed_images = image_service.get_user_processed_images(str(current_user.id), skip, limit)
        
        base_url = "http://localhost:8001"  # TODO: Get from config
        processed_list = []
        
        for processed in processed_images:
            processed_info = {
                "processed_image_id": str(processed.id),
                "original_image_id": str(processed.original_image_id),
                "color_code": str(processed.color_code),
                "color_name": str(processed.color_name),
                "surface_type": str(processed.surface_type),
                "processing_time": float(processed.processing_time) if processed.processing_time else 0.0,
                "created_at": processed.created_at,
                "processed_url": f"{base_url}/images/processed/{os.path.basename(str(processed.storage_path))}"
            }
            processed_list.append(processed_info)
        
        return StandardResponse(
            success=True,
            data={"processed_images": processed_list},
            message="Processed images retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "GET_PROCESSED_IMAGES_FAILED",
                "message": "Failed to retrieve processed images",
                "details": str(e)
            }
        ) 