from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from passlib.context import CryptContext
import jwt
import datetime

app = FastAPI()

# Настройка схемы аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Хэширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Имитация базы данных пользователей
fake_users_db = {
    "john_doe": {
        "username": "john_doe",
        "hashed_password": pwd_context.hash("secret"),
        "email": "john@gmail.de",
        "age": 25,
        "role": "admin"  # Добавляем роль пользователя
    },

    "dave": {
        "username": "dave",
        "hashed_password": pwd_context.hash("secret11"),
        "email": "dave@gmail.de",
        "age": 25,
        "role": "user"  # Добавляем роль пользователя
    }
}

# Секретный ключ для JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Создаем pydantic модель
class User(BaseModel):
    username: str
    email: str
    age: int
    role: str  # Добавляем роль в модель

class ModelInput(BaseModel):
    input_data: str

class ModelOutput(BaseModel):
    result: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
    role: str  # Добавляем роль в данные токена



# Функция для проверки пользователя
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if user is None or not pwd_context.verify(password, user["hashed_password"]):
        return False
    return user

# Функция для создания JWT токена
def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Зависимость для получения текущего пользователя
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except jwt.PyJWTError:
        raise credentials_exception
    user_data = fake_users_db.get(token_data.username)
    if user_data is None:
        raise credentials_exception
    return User(**user_data)

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this user role"
        )
    return current_user

# Эндпоинт для получения токена
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Эндпоинт для получения текущего пользователя
@app.get("/users/me", response_model=User)
def read_current_user(current_admin: User = Depends(get_current_admin)):
    return current_admin

# Эндпоинт для создания пользователя
@app.post("/users/", response_model=User)
def create_user(user: User, current_admin: User = Depends(get_current_admin)):
    # Создаем нового пользователя с хэшированием пароля
    hashed_password = pwd_context.hash("secret")
    user_data = user.dict()
    user_data["hashed_password"] = hashed_password
    fake_users_db[user.username] = user_data
    return user
    

@app.post("/model/", response_model=ModelOutput)
def run_model(input: ModelInput, current_admin: User = Depends(get_current_admin)):
    result = f"Processed input: {input.input_data}"
    return ModelOutput(result=result)