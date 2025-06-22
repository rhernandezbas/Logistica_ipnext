"""This module contains configuration variables."""

import os
from typing import Dict
from dotenv import load_dotenv
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from app.utils.logger import get_logger

logger = get_logger(__name__)

db = SQLAlchemy()
marsmallow = Marshmallow()


def load_secrets() -> Dict[str, str]:
    """Load secrets to start the app"""
    load_dotenv()
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")  # Corregido de "goole_maps_api_key"
    hf_token = os.getenv("HF_TOKEN")
    bd_token = os.getenv("BD_TOKEN")

    secrets = {
        "GOOGLE_MAPS_API_KEY": google_maps_api_key,
        "HF_TOKEN": hf_token,
        "BD_TOKEN": bd_token
    }
    return secrets


class Config:
    """Configuration class for the application."""
    secret = load_secrets()

    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', secret.get("BD_TOKEN", "password"))
    DB_HOST = os.getenv('DB_HOST', 'host.docker.internal')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'ipnext')

    logger.info(f"Database configuration: Host={DB_HOST}, Port={DB_PORT}, DB={DB_NAME}, User={DB_USER}")

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 280, 'pool_pre_ping': True}