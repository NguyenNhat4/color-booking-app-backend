#!/usr/bin/env python
"""
Script to generate sample room images for testing purposes.
Creates simple color block images to represent rooms.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_sample_room_image(
    filename,
    width=1280,
    height=720,
    bg_color=(240, 240, 240),
    wall_color=(245, 245, 220),
    label=None
):
    """Create a simple room image with walls"""
    # Create base image with background color
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a wall rectangle
    wall_margin = int(width * 0.1)
    wall_height = int(height * 0.7)
    draw.rectangle(
        [(wall_margin, wall_margin), (width - wall_margin, wall_height)],
        fill=wall_color
    )
    
    # Add floor
    floor_points = [
        (wall_margin, wall_height),
        (width - wall_margin, wall_height),
        (width - int(wall_margin * 0.5), height - wall_margin),
        (int(wall_margin * 0.5), height - wall_margin)
    ]
    draw.polygon(floor_points, fill=(210, 180, 140))  # Tan color for floor
    
    # Add simple window or door
    filename_str = str(filename)
    if "living" in filename_str:
        # Add window for living room
        window_width = int(width * 0.2)
        window_height = int(height * 0.3)
        window_left = int(width * 0.6)
        window_top = int(height * 0.2)
        draw.rectangle(
            [(window_left, window_top), (window_left + window_width, window_top + window_height)],
            fill=(135, 206, 235)  # Sky blue
        )
    elif "bedroom" in filename_str:
        # Add bed outline for bedroom
        bed_width = int(width * 0.3)
        bed_height = int(height * 0.2)
        bed_left = int(width * 0.35)
        bed_top = int(height * 0.55)
        draw.rectangle(
            [(bed_left, bed_top), (bed_left + bed_width, bed_top + bed_height)],
            fill=(139, 69, 19),  # Brown
            outline=(101, 67, 33),
            width=2
        )
    elif "kitchen" in filename_str:
        # Add counter for kitchen
        counter_width = int(width * 0.5)
        counter_height = int(height * 0.1)
        counter_left = int(width * 0.25)
        counter_top = int(height * 0.5)
        draw.rectangle(
            [(counter_left, counter_top), (counter_left + counter_width, counter_top + counter_height)],
            fill=(220, 220, 220),  # Light gray
            outline=(200, 200, 200),
            width=2
        )
    
    # Add label if provided
    if label:
        # Try to find a font, use default if not available
        font_size = 30
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            # Use default font if Arial not available
            font = ImageFont.load_default()
        
        # Draw text at the bottom - newer Pillow versions use font.getbbox
        try:
            left, top, right, bottom = font.getbbox(label)
            text_width, text_height = right - left, bottom - top
        except AttributeError:
            # Fallback for older Pillow versions
            text_width, text_height = (300, 30) 
        text_position = ((width - text_width) // 2, height - wall_margin // 2)
        draw.text(text_position, label, fill=(0, 0, 0), font=font)
    
    # Save the image
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    img.save(filename, format="JPEG", quality=95)
    print(f"Created sample image: {filename}")
    return filename

def main():
    """Generate sample room images"""
    print("Generating sample room images...")
    
    # Define the output directory
    output_dir = Path("scripts") / "sample_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create living room image
    create_sample_room_image(
        filename=output_dir / "living_room_modern.jpg",
        bg_color=(200, 220, 240),  # Light blue background
        wall_color=(245, 245, 220),  # Beige wall
        label="Living Room Modern"
    )
    
    # Create bedroom image
    create_sample_room_image(
        filename=output_dir / "bedroom_classic.jpg",
        bg_color=(220, 240, 220),  # Light green background
        wall_color=(255, 248, 220),  # Cornsilk wall
        label="Bedroom Classic"
    )
    
    # Create kitchen image
    create_sample_room_image(
        filename=output_dir / "kitchen_contemporary.jpg",
        bg_color=(240, 230, 220),  # Light cream background
        wall_color=(255, 255, 240),  # Ivory wall
        label="Kitchen Contemporary"
    )
    
    print("Sample images generated successfully!")

if __name__ == "__main__":
    main() 