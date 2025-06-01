from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class ImageDimensions(BaseModel):
    """Schema for image dimensions"""
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")

class RegionCoordinate(BaseModel):
    """Schema for region coordinate point"""
    x: int = Field(..., ge=0, description="X coordinate")
    y: int = Field(..., ge=0, description="Y coordinate")

class RegionData(BaseModel):
    """Schema for region selection data"""
    type: str = Field(..., description="Region type (polygon, rectangle, circle)")
    coordinates: List[RegionCoordinate] = Field(..., description="List of coordinates defining the region")
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if len(v) < 3:
            raise ValueError('At least 3 coordinates are required')
        return v

class ImageUploadResponse(BaseModel):
    """Response schema for image upload"""
    image_id: str = Field(..., description="Unique image identifier")
    original_url: str = Field(..., description="URL to access the original image")
    thumbnail_url: str = Field(..., description="URL to access the thumbnail")
    upload_time: datetime = Field(..., description="Upload timestamp")
    file_size: int = Field(..., description="File size in bytes")
    dimensions: ImageDimensions = Field(..., description="Image dimensions")

class ColorApplicationRequest(BaseModel):
    """Request schema for applying color to image"""
    color_code: str = Field(..., description="Hex color code")
    
    @validator('color_code')
    def validate_color_code(cls, v):
        import re
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError('Color code must be a valid hex color (e.g., #FF0000)')
        return v
    color_name: str = Field(..., min_length=1, max_length=100, description="Color name")
    region: RegionData = Field(..., description="Selected region data")
    surface_type: str = Field(default="wall", description="Surface type (wall, ceiling, floor)")
    blend_mode: str = Field(default="normal", description="Blend mode for color application")
    opacity: float = Field(default=0.8, ge=0.0, le=1.0, description="Color opacity (0.0 to 1.0)")

class AppliedColorInfo(BaseModel):
    """Schema for applied color information"""
    color_code: str = Field(..., description="Applied hex color code")
    color_name: str = Field(..., description="Applied color name")
    product_id: Optional[str] = Field(None, description="Associated product ID")

class ColorApplicationResponse(BaseModel):
    """Response schema for color application"""
    processed_image_id: str = Field(..., description="Processed image identifier")
    processed_url: str = Field(..., description="URL to access the processed image")
    thumbnail_url: str = Field(..., description="URL to access the processed thumbnail")
    processing_time: float = Field(..., description="Processing time in seconds")
    applied_color: AppliedColorInfo = Field(..., description="Applied color information")

class DemoImageInfo(BaseModel):
    """Schema for demo image information"""
    demo_id: str = Field(..., description="Demo image identifier")
    name: str = Field(..., description="Demo image name")
    description: Optional[str] = Field(None, description="Demo image description")
    image_url: str = Field(..., description="Demo image URL")
    thumbnail_url: str = Field(..., description="Demo thumbnail URL")
    room_type: str = Field(..., description="Room type")
    style: Optional[str] = Field(None, description="Style category")

class DemoImagesResponse(BaseModel):
    """Response schema for demo images list"""
    demo_images: List[DemoImageInfo] = Field(..., description="List of available demo images")

class ImageInfo(BaseModel):
    """Schema for basic image information"""
    image_id: str = Field(..., description="Image identifier")
    original_filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    dimensions: ImageDimensions = Field(..., description="Image dimensions")
    room_type: Optional[str] = Field(None, description="Room type")
    description: Optional[str] = Field(None, description="Image description")
    upload_time: datetime = Field(..., description="Upload timestamp")

class ProcessedImageInfo(BaseModel):
    """Schema for processed image information"""
    processed_image_id: str = Field(..., description="Processed image identifier")
    original_image_id: str = Field(..., description="Original image identifier")
    color_code: str = Field(..., description="Applied color code")
    color_name: str = Field(..., description="Applied color name")
    surface_type: str = Field(..., description="Surface type")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")

class ShareImageRequest(BaseModel):
    """Request schema for sharing processed image"""
    share_type: str = Field(default="public", description="Share type (public, private)")
    expiry_days: int = Field(default=30, ge=1, le=365, description="Expiry in days")
    include_product_info: bool = Field(default=True, description="Include product information")

class ShareImageResponse(BaseModel):
    """Response schema for image sharing"""
    share_id: str = Field(..., description="Share identifier")
    share_url: str = Field(..., description="Shareable URL")
    qr_code_url: str = Field(..., description="QR code URL")
    expires_at: datetime = Field(..., description="Expiry timestamp")
    view_count: int = Field(default=0, description="View count")
    created_at: datetime = Field(..., description="Creation timestamp")

class SaveImageRequest(BaseModel):
    """Request schema for saving processed image"""
    album_name: Optional[str] = Field(None, max_length=100, description="Album name")
    description: Optional[str] = Field(None, max_length=500, description="Image description")

class SaveImageResponse(BaseModel):
    """Response schema for saving image"""
    saved_image_id: str = Field(..., description="Saved image identifier")
    album_name: Optional[str] = Field(None, description="Album name")
    saved_at: datetime = Field(..., description="Save timestamp")

class StandardResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")

class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = Field(default=False, description="Operation success status")
    error: Dict[str, Any] = Field(..., description="Error details")

    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "INVALID_IMAGE_FORMAT",
                    "message": "Unsupported image format",
                    "details": "Only JPEG, PNG, and HEIC formats are supported"
                }
            }
        } 