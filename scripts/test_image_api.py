#!/usr/bin/env python
"""
Script to test the image processing API endpoints.
This will make HTTP requests to the API and verify responses.
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# API configuration
API_BASE_URL = "http://localhost:8001"
DEMO_ENDPOINT = f"{API_BASE_URL}/images/demo"
UPLOAD_ENDPOINT = f"{API_BASE_URL}/images/upload"
APPLY_COLOR_ENDPOINT_TEMPLATE = f"{API_BASE_URL}/images/{{image_id}}/apply-color"

# Test auth token - Replace with a real token for testing
TEST_AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzE4MDk2NTEyfQ.vj7dU5IGlrgCs0e3UzaaA3OTlFiOFuPpwGPK3wwQX0Y"

def test_demo_images_endpoint():
    """Test the demo images endpoint"""
    print("\n=== Testing Demo Images Endpoint ===")
    
    headers = {"Authorization": f"Bearer {TEST_AUTH_TOKEN}"}
    
    try:
        response = requests.get(DEMO_ENDPOINT, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"Response status: {response.status_code}")
        print(f"Success: {data.get('success', False)}")
        
        if 'data' in data and 'demo_images' in data['data']:
            print(f"Found {len(data['data']['demo_images'])} demo images")
            for i, demo in enumerate(data['data']['demo_images']):
                print(f"  {i+1}. {demo['name']} ({demo['room_type']})")
        else:
            print("No demo images found or unexpected response format")
            
    except requests.exceptions.RequestException as e:
        print(f"Error testing demo images endpoint: {e}")

def test_image_upload(test_image_path):
    """Test the image upload endpoint"""
    print("\n=== Testing Image Upload Endpoint ===")
    
    headers = {"Authorization": f"Bearer {TEST_AUTH_TOKEN}"}
    
    if not os.path.exists(test_image_path):
        print(f"Test image not found: {test_image_path}")
        return None
    
    try:
        with open(test_image_path, 'rb') as img_file:
            files = {'file': (os.path.basename(test_image_path), img_file, 'image/jpeg')}
            data = {'room_type': 'living_room', 'description': 'Test image upload'}
            
            response = requests.post(UPLOAD_ENDPOINT, headers=headers, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            print(f"Response status: {response.status_code}")
            print(f"Success: {result.get('success', False)}")
            
            if result.get('success') and 'data' in result:
                image_data = result['data']
                print(f"Uploaded image ID: {image_data.get('image_id')}")
                print(f"Original URL: {image_data.get('original_url')}")
                print(f"Thumbnail URL: {image_data.get('thumbnail_url')}")
                return image_data.get('image_id')
            else:
                print("Upload failed or unexpected response format")
                return None
                
    except requests.exceptions.RequestException as e:
        print(f"Error testing image upload endpoint: {e}")
        return None

def test_apply_color(image_id):
    """Test the apply color endpoint"""
    print("\n=== Testing Apply Color Endpoint ===")
    
    if not image_id:
        print("No image ID provided, skipping color application test")
        return
    
    headers = {
        "Authorization": f"Bearer {TEST_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Example color application data
    color_data = {
        "color_code": "#FFE4B5",
        "color_name": "Moccasin",
        "region": {
            "type": "polygon",
            "coordinates": [
                {"x": 100, "y": 150},
                {"x": 800, "y": 150},
                {"x": 800, "y": 600},
                {"x": 100, "y": 600}
            ]
        },
        "surface_type": "wall",
        "blend_mode": "normal",
        "opacity": 0.8
    }
    
    try:
        endpoint = APPLY_COLOR_ENDPOINT_TEMPLATE.format(image_id=image_id)
        response = requests.post(endpoint, headers=headers, json=color_data)
        response.raise_for_status()
        
        result = response.json()
        print(f"Response status: {response.status_code}")
        print(f"Success: {result.get('success', False)}")
        
        if result.get('success') and 'data' in result:
            processed_data = result['data']
            print(f"Processed image ID: {processed_data.get('processed_image_id')}")
            print(f"Processed URL: {processed_data.get('processed_url')}")
            print(f"Processing time: {processed_data.get('processing_time')} seconds")
            print(f"Applied color: {processed_data.get('applied_color', {}).get('color_name')}")
        else:
            print("Color application failed or unexpected response format")
            
    except requests.exceptions.RequestException as e:
        print(f"Error testing apply color endpoint: {e}")

def main():
    """Main test function"""
    print("=== Image API Test Script ===")
    
    # Test the demo images endpoint
    test_demo_images_endpoint()
    
    # Test image upload using a sample image
    test_image_path = Path("scripts") / "sample_images" / "living_room_modern.jpg"
    image_id = test_image_upload(test_image_path)
    
    # Test apply color if image upload was successful
    if image_id:
        test_apply_color(image_id)
        
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    main() 