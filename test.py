from pydantic import BaseModel, validator, ValidationError

class SimpleUser(BaseModel):
    nickname: str  # We expect a nickname, and it should be a string

    @validator('nickname') # This decorator says: "Hey, the function below is for checking 'nickname'!"
    def nickname_cannot_be_admin(cls, v_nickname):
        # 'cls' is the class (SimpleUser), v_nickname is the value of 'nickname' being checked.
        if v_nickname == "admin":
            raise ValueError("Nickname 'admin' is not allowed!") # If it's "admin", stop and raise an error.
        return v_nickname # If it's okay (not "admin"), return the value.

# --- Let's try it out ---

# 1. Try a good nickname
try:
    user_ok = SimpleUser(nickname="cool_user_123")
    print(f"SUCCESS: User created with nickname: {user_ok.nickname}")
except ValidationError as e:
    print(f"ERROR: {e}")

print("-" * 20)

# 2. Try the forbidden nickname
try:
    user_bad = SimpleUser(nickname="admin") # This should trigger the validator's error
    print(f"SUCCESS: User created with nickname: {user_bad.nickname}") # This line won't run
except ValidationError as e:
    print(f"ERROR AS EXPECTED: {e}")