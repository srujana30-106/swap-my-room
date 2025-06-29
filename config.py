import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env into environment

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Database
    SQLALCHEMY_DATABASE_URI = (
        os.getenv('DATABASE_URL') or
        os.getenv('SQLALCHEMY_DATABASE_URI')
    )
    print('SQLALCHEMY_DATABASE_URI',SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
