import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import secrets

# It's good practice to ensure the path allows importing from the Backend directory.
# This might require adding Backend to sys.path or configuring PYTHONPATH,
# or using relative imports if the test runner handles it.
# For now, assuming direct import works or will be configured.
from services.auth_service import AuthenticationService, UserService
from models.user import User, AccountType # Assuming AccountType is used
from config import settings # For JWT settings

# Helper to get a setting or a default if not found, to avoid test failures if settings are minimal
def get_setting(attr, default):
    return getattr(settings, attr, default)

class TestAuthenticationService(unittest.TestCase):

    def setUp(self):
        # Configure minimal settings for JWT if not fully defined in a test config
        self.SECRET_KEY = get_setting("SECRET_KEY", "test_secret_key_for_jwt")
        self.ALGORITHM = get_setting("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = get_setting("ACCESS_TOKEN_EXPIRE_MINUTES", 30)

        # Patch settings for consistency in tests
        self.settings_patcher = patch.multiple(
            'services.auth_service.settings',
            SECRET_KEY=self.SECRET_KEY,
            ALGORITHM=self.ALGORITHM,
            ACCESS_TOKEN_EXPIRE_MINUTES=self.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        self.mock_settings = self.settings_patcher.start()

    def tearDown(self):
        self.settings_patcher.stop()

    def test_hash_password(self):
        password = "plainpassword"
        hashed_password = AuthenticationService.hash_password(password)
        self.assertIsNotNone(hashed_password)
        self.assertNotEqual(password, hashed_password)
        # Check if it's a bcrypt hash (usually starts with $2b$)
        self.assertTrue(hashed_password.startswith("$2b$"))

    def test_verify_password(self):
        password = "plainpassword"
        hashed_password = AuthenticationService.hash_password(password)
        self.assertTrue(AuthenticationService.verify_password(password, hashed_password))
        self.assertFalse(AuthenticationService.verify_password("wrongpassword", hashed_password))

    def test_create_access_token(self):
        data = {"sub": "testuser"}
        token = AuthenticationService.create_access_token(data)
        self.assertIsNotNone(token)
        
        # Decode to verify content (using the same key and algorithm)
        payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        self.assertEqual(payload["sub"], data["sub"])
        self.assertIn("exp", payload)

    def test_create_access_token_with_expires_delta(self):
        data = {"sub": "testuser_delta"}
        expires_delta = timedelta(hours=1)
        token = AuthenticationService.create_access_token(data, expires_delta=expires_delta)
        self.assertIsNotNone(token)
        
        payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        self.assertEqual(payload["sub"], data["sub"])
        # Check if expiry is close to 1 hour from now
        expected_exp = datetime.utcnow() + expires_delta
        actual_exp = datetime.utcfromtimestamp(payload["exp"])
        self.assertAlmostEqual(expected_exp, actual_exp, delta=timedelta(seconds=5)) # Allow small delta

    def test_verify_token_valid(self):
        data = {"sub": "testuser_verify"}
        token = AuthenticationService.create_access_token(data)
        payload = AuthenticationService.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], data["sub"])

    def test_verify_token_invalid_signature(self):
        data = {"sub": "testuser_invalid_sig"}
        # Token created with correct key
        token = AuthenticationService.create_access_token(data)
        
        # Attempt to verify with a wrong key by temporarily overriding mock_settings
        original_secret_key = self.mock_settings.SECRET_KEY
        self.mock_settings.SECRET_KEY = "wrong_secret_key"
        try:
            payload = AuthenticationService.verify_token(token) # This verify_token call will use the wrong key due to patch
            self.assertIsNone(payload)
        finally:
            self.mock_settings.SECRET_KEY = original_secret_key # Restore for other tests


    def test_verify_token_expired(self):
        data = {"sub": "testuser_expired"}
        # Create a token that expires very quickly (e.g., 1 millisecond)
        token = AuthenticationService.create_access_token(data, expires_delta=timedelta(milliseconds=1))
        
        # Wait for slightly longer than the expiry
        import time
        time.sleep(0.01) # Sleep for 10 ms
        
        payload = AuthenticationService.verify_token(token)
        self.assertIsNone(payload)

    def test_verify_token_malformed(self):
        malformed_token = "this.is.not.a.valid.jwt.token"
        payload = AuthenticationService.verify_token(malformed_token)
        self.assertIsNone(payload)
        
    def test_generate_verification_token(self):
        token1 = AuthenticationService.generate_verification_token()
        token2 = AuthenticationService.generate_verification_token()
        self.assertIsNotNone(token1)
        self.assertIsInstance(token1, str)
        self.assertGreater(len(token1), 30) # Expect a reasonably long token
        self.assertNotEqual(token1, token2) # Tokens should be unique

# Placeholder for UserService tests - to be implemented
class TestUserService(unittest.TestCase):
    def setUp(self):
        # Mock the database session for all tests in this class
        self.mock_db_session = MagicMock()

        # It's good practice to also mock settings if UserService relies on them
        self.SECRET_KEY = get_setting("SECRET_KEY", "test_secret_key_for_jwt_user_service")
        self.ALGORITHM = get_setting("ALGORITHM", "HS256_user_service")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = get_setting("ACCESS_TOKEN_EXPIRE_MINUTES_user_service", 15)

        self.settings_patcher_user = patch.multiple(
            'services.auth_service.settings', # Assuming UserService also imports settings from here
            SECRET_KEY=self.SECRET_KEY,
            ALGORITHM=self.ALGORITHM,
            ACCESS_TOKEN_EXPIRE_MINUTES=self.ACCESS_TOKEN_EXPIRE_MINUTES,
            create=True # Create if not exists, good for flexibility
        )
        self.mock_settings_user = self.settings_patcher_user.start()

        self.user_service = UserService(database_session=self.mock_db_session)

    def tearDown(self):
        self.settings_patcher_user.stop()
        
    # Example: Test get_user_by_email
    def test_get_user_by_email_found(self):
        mock_user = User(id=1, email="test@example.com", username="testuser", hashed_password="hashed_password")
        self.mock_db_session.query(User).filter(User.email == "test@example.com").first.return_value = mock_user
        
        user = self.user_service.get_user_by_email("test@example.com")
        self.assertEqual(user, mock_user)
        self.mock_db_session.query(User).filter(User.email == "test@example.com").first.assert_called_once()

    def test_get_user_by_email_not_found(self):
        self.mock_db_session.query(User).filter(User.email == "nonexistent@example.com").first.return_value = None
        
        user = self.user_service.get_user_by_email("nonexistent@example.com")
        self.assertIsNone(user)
        self.mock_db_session.query(User).filter(User.email == "nonexistent@example.com").first.assert_called_once()

    def test_get_user_by_username_found(self):
        mock_user = User(id=1, email="test@example.com", username="testuser", hashed_password="hashed")
        self.mock_db_session.query(User).filter(User.username == "testuser").first.return_value = mock_user
        user = self.user_service.get_user_by_username("testuser")
        self.assertEqual(user, mock_user)
        self.mock_db_session.query(User).filter(User.username == "testuser").first.assert_called_once()

    def test_get_user_by_username_not_found(self):
        self.mock_db_session.query(User).filter(User.username == "nonexistentuser").first.return_value = None
        user = self.user_service.get_user_by_username("nonexistentuser")
        self.assertIsNone(user)
        self.mock_db_session.query(User).filter(User.username == "nonexistentuser").first.assert_called_once()

    def test_get_user_by_id_found(self):
        mock_user = User(id=1, email="test@example.com", username="testuser", hashed_password="hashed")
        self.mock_db_session.query(User).filter(User.id == 1).first.return_value = mock_user
        user = self.user_service.get_user_by_id(1)
        self.assertEqual(user, mock_user)
        self.mock_db_session.query(User).filter(User.id == 1).first.assert_called_once()

    def test_get_user_by_id_not_found(self):
        self.mock_db_session.query(User).filter(User.id == 999).first.return_value = None
        user = self.user_service.get_user_by_id(999)
        self.assertIsNone(user)
        self.mock_db_session.query(User).filter(User.id == 999).first.assert_called_once()

    @patch('services.auth_service.AuthenticationService.hash_password')
    @patch('services.auth_service.AuthenticationService.generate_verification_token')
    def test_create_user_success(self, mock_generate_token, mock_hash_password):
        mock_hash_password.return_value = "hashed_password"
        mock_generate_token.return_value = "test_verification_token"
        
        # Mock that user does not exist
        self.user_service.get_user_by_email = MagicMock(return_value=None)
        self.user_service.get_user_by_username = MagicMock(return_value=None)
        
        created_user = self.user_service.create_user(
            email="newuser@example.com", 
            username="newuser", 
            password="password123",
            first_name="New",
            last_name="User"
        )
        
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.email, "newuser@example.com")
        self.assertEqual(created_user.username, "newuser")
        self.assertEqual(created_user.hashed_password, "hashed_password")
        self.assertEqual(created_user.verification_token, "test_verification_token")
        self.assertFalse(created_user.is_verified)
        self.assertEqual(created_user.first_name, "New")

        self.mock_db_session.add.assert_called_once_with(created_user)
        self.mock_db_session.commit.assert_called_once()
        self.mock_db_session.refresh.assert_called_once_with(created_user)
        mock_hash_password.assert_called_once_with("password123")
        mock_generate_token.assert_called_once()

    @patch('services.auth_service.AuthenticationService.hash_password')
    def test_create_user_email_exists(self, mock_hash_password):
        # Mock that user with this email already exists
        self.user_service.get_user_by_email = MagicMock(return_value=User(email="existing@example.com"))
        self.user_service.get_user_by_username = MagicMock(return_value=None)
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as context:
            self.user_service.create_user(
                email="existing@example.com", 
                username="newuser", 
                password="password123"
            )
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Email already registered")
        mock_hash_password.assert_not_called() # Should not proceed to hash password
        self.mock_db_session.add.assert_not_called()

    @patch('services.auth_service.AuthenticationService.hash_password')
    def test_create_user_username_exists(self, mock_hash_password):
        self.user_service.get_user_by_email = MagicMock(return_value=None)
        self.user_service.get_user_by_username = MagicMock(return_value=User(username="existinguser"))

        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as context:
            self.user_service.create_user(
                email="new@example.com", 
                username="existinguser", 
                password="password123"
            )
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Username already taken")
        mock_hash_password.assert_not_called()
        self.mock_db_session.add.assert_not_called()

    @patch('services.auth_service.AuthenticationService.verify_password')
    def test_authenticate_user_success(self, mock_verify_password):
        mock_user = User(
            id=1, email="test@example.com", username="testuser", 
            hashed_password="hashed_pw", is_active=True
        )
        self.user_service.get_user_by_username_or_email = MagicMock(return_value=mock_user)
        mock_verify_password.return_value = True
        
        authenticated_user = self.user_service.authenticate_user("testuser", "password123")
        
        self.assertEqual(authenticated_user, mock_user)
        self.assertIsNotNone(authenticated_user.last_login) # Check last_login is updated
        self.user_service.get_user_by_username_or_email.assert_called_once_with("testuser")
        mock_verify_password.assert_called_once_with("password123", "hashed_pw")
        self.mock_db_session.commit.assert_called_once() # For updating last_login

    def test_authenticate_user_not_found(self):
        self.user_service.get_user_by_username_or_email = MagicMock(return_value=None)
        
        authenticated_user = self.user_service.authenticate_user("nouser", "password123")
        self.assertIsNone(authenticated_user)
        self.user_service.get_user_by_username_or_email.assert_called_once_with("nouser")

    @patch('services.auth_service.AuthenticationService.verify_password')
    def test_authenticate_user_wrong_password(self, mock_verify_password):
        mock_user = User(id=1, email="test@example.com", username="testuser", hashed_password="hashed_pw", is_active=True)
        self.user_service.get_user_by_username_or_email = MagicMock(return_value=mock_user)
        mock_verify_password.return_value = False # Password verification fails
        
        authenticated_user = self.user_service.authenticate_user("testuser", "wrongpassword")
        self.assertIsNone(authenticated_user)
        mock_verify_password.assert_called_once_with("wrongpassword", "hashed_pw")

    def test_authenticate_user_inactive(self):
        mock_user = User(id=1, email="test@example.com", username="inactiveuser", hashed_password="hashed_pw", is_active=False)
        self.user_service.get_user_by_username_or_email = MagicMock(return_value=mock_user)
        # verify_password will be true for this case, but is_active is false
        # We need to ensure AuthenticationService.verify_password is also patched if not testing its internal logic here directly
        # For this specific test, we assume AuthenticationService.verify_password would return True if called.

        from fastapi import HTTPException
        with patch('services.auth_service.AuthenticationService.verify_password', return_value=True):
            with self.assertRaises(HTTPException) as context:
                self.user_service.authenticate_user("inactiveuser", "password123")
        
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Account is deactivated")
        self.user_service.get_user_by_username_or_email.assert_called_once_with("inactiveuser")
        
    def test_update_account_type_success(self):
        mock_user = User(id=1, account_type=AccountType.INDIVIDUAL)
        self.user_service.get_user_by_id = MagicMock(return_value=mock_user)
        
        updated_user = self.user_service.update_account_type(1, AccountType.CONTRACTOR)
        
        self.assertEqual(updated_user.account_type, AccountType.CONTRACTOR)
        self.mock_db_session.commit.assert_called_once()
        self.mock_db_session.refresh.assert_called_once_with(mock_user)
        self.user_service.get_user_by_id.assert_called_once_with(1)

    def test_update_account_type_user_not_found(self):
        self.user_service.get_user_by_id = MagicMock(return_value=None)
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as context:
            self.user_service.update_account_type(999, AccountType.CONTRACTOR)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User not found")
        self.mock_db_session.commit.assert_not_called()

    def test_update_user_profile_success(self):
        mock_user = User(id=1, first_name="OldName", email="old@example.com")
        self.user_service.get_user_by_id = MagicMock(return_value=mock_user)
        profile_data = {"first_name": "NewName", "email": "new@example.com", "phone_number": "1234567890"}
        
        updated_user = self.user_service.update_user_profile(1, profile_data)
        
        self.assertEqual(updated_user.first_name, "NewName")
        self.assertEqual(updated_user.email, "new@example.com")
        self.assertEqual(updated_user.phone_number, "1234567890")
        self.assertIsNotNone(updated_user.updated_at)
        self.mock_db_session.commit.assert_called_once()
        self.mock_db_session.refresh.assert_called_once_with(mock_user)

    def test_update_user_profile_user_not_found(self):
        self.user_service.get_user_by_id = MagicMock(return_value=None)
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as context:
            self.user_service.update_user_profile(999, {"first_name": "NewName"})
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "User not found")

    def test_verify_user_email_success(self):
        mock_user = User(id=1, verification_token="valid_token", is_verified=False)
        self.mock_db_session.query(User).filter(User.verification_token == "valid_token").first.return_value = mock_user
        
        result = self.user_service.verify_user_email("valid_token")
        
        self.assertTrue(result)
        self.assertTrue(mock_user.is_verified)
        self.assertIsNone(mock_user.verification_token)
        self.mock_db_session.commit.assert_called_once()

    def test_verify_user_email_invalid_token(self):
        self.mock_db_session.query(User).filter(User.verification_token == "invalid_token").first.return_value = None
        
        result = self.user_service.verify_user_email("invalid_token")
        self.assertFalse(result)
        self.mock_db_session.commit.assert_not_called()

    @patch('services.auth_service.AuthenticationService.generate_verification_token')
    def test_initiate_password_reset_success(self, mock_generate_token):
        mock_user = User(id=1, email="user@example.com")
        self.user_service.get_user_by_email = MagicMock(return_value=mock_user)
        mock_generate_token.return_value = "new_reset_token"
        
        token = self.user_service.initiate_password_reset("user@example.com")
        
        self.assertEqual(token, "new_reset_token")
        self.assertEqual(mock_user.verification_token, "new_reset_token")
        self.mock_db_session.commit.assert_called_once()
        mock_generate_token.assert_called_once()

    def test_initiate_password_reset_user_not_found(self):
        self.user_service.get_user_by_email = MagicMock(return_value=None)
        # generate_verification_token should not be called if user not found
        with patch('services.auth_service.AuthenticationService.generate_verification_token') as mock_generate_token:
            token = self.user_service.initiate_password_reset("nouser@example.com")
            self.assertIsNone(token)
            mock_generate_token.assert_not_called()
        self.mock_db_session.commit.assert_not_called()

    @patch('services.auth_service.AuthenticationService.hash_password')
    def test_reset_password_success(self, mock_hash_password):
        mock_user = User(id=1, verification_token="reset_token")
        self.mock_db_session.query(User).filter(User.verification_token == "reset_token").first.return_value = mock_user
        mock_hash_password.return_value = "new_hashed_password"
        
        result = self.user_service.reset_password("reset_token", "new_password123")
        
        self.assertTrue(result)
        self.assertEqual(mock_user.hashed_password, "new_hashed_password")
        self.assertIsNone(mock_user.verification_token)
        self.mock_db_session.commit.assert_called_once()
        mock_hash_password.assert_called_once_with("new_password123")

    def test_reset_password_invalid_token(self):
        self.mock_db_session.query(User).filter(User.verification_token == "invalid_token").first.return_value = None
        with patch('services.auth_service.AuthenticationService.hash_password') as mock_hash_password:
            result = self.user_service.reset_password("invalid_token", "new_password123")
            self.assertFalse(result)
            mock_hash_password.assert_not_called()
        self.mock_db_session.commit.assert_not_called()

if __name__ == '__main__':
    unittest.main()