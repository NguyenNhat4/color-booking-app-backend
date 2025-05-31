#!/usr/bin/env python3
"""
Script to create a test user for API testing
"""
import requests
import json

API_BASE_URL = "http://localhost:8001"

def create_test_user():
    """Create a test user for API testing"""
    
    # Test user data
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123",
        "confirm_password": "TestPassword123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890"
    }
    
    print("Creating test user...")
    print(f"Email: {user_data['email']}")
    print(f"Username: {user_data['username']}")
    print(f"Password: {user_data['password']}")
    print("-" * 50)
    
    try:
        # Register the user
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            user_info = response.json()
            print("✅ Test user created successfully!")
            print(f"User ID: {user_info['id']}")
            print(f"Email: {user_info['email']}")
            print(f"Username: {user_info['username']}")
            
            # Now login to get a token
            print("\n" + "=" * 50)
            print("Logging in to get JWT token...")
            
            login_data = {
                "username_or_email": user_data["username"],
                "password": user_data["password"]
            }
            
            login_response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data["access_token"]
                
                print("✅ Login successful!")
                print(f"JWT Token: {token}")
                print("\n" + "=" * 50)
                print("🔑 COPY THIS TOKEN FOR SWAGGER UI:")
                print(f"{token}")
                print("=" * 50)
                
                # Test the token with a protected endpoint
                print("\nTesting token with /users/me endpoint...")
                
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                profile_response = requests.get(
                    f"{API_BASE_URL}/users/me",
                    headers=headers
                )
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print("✅ Token works! User profile retrieved:")
                    print(json.dumps(profile_data, indent=2))
                else:
                    print(f"❌ Token test failed: {profile_response.status_code}")
                    print(profile_response.text)
                    
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                print(login_response.text)
                
        elif response.status_code == 400:
            print("⚠️  User might already exist. Trying to login...")
            
            login_data = {
                "username_or_email": user_data["username"],
                "password": user_data["password"]
            }
            
            login_response = requests.post(
                f"{API_BASE_URL}/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data["access_token"]
                
                print("✅ Login successful with existing user!")
                print(f"JWT Token: {token}")
                print("\n" + "=" * 50)
                print("🔑 COPY THIS TOKEN FOR SWAGGER UI:")
                print(f"{token}")
                print("=" * 50)
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                print(login_response.text)
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure the backend is running on http://localhost:8001")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    create_test_user() 