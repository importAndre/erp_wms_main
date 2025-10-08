from passlib.context import CryptContext
from cryptography.fernet import Fernet

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

key = Fernet.generate_key()
cipher_suite = Fernet(key)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def encrypt(data: str) -> str:
    return cipher_suite.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt(data: str) -> str:
    return cipher_suite.decrypt(data.encode('utf-8')).decode('utf-8')