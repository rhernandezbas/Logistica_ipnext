"""This module contains configuration variables."""

import os
import time
from typing import Dict

from dotenv import load_dotenv
from flask import current_app
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

from app.utils.logger import get_logger

logger = get_logger(__name__)

db = SQLAlchemy()
marsmallow = Marshmallow()


def load_secrets() -> Dict[str, str]:
    """Load secrets to start the app"""
    load_dotenv()
    goole_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    hf_token = os.getenv("HF_TOKEN")

    secrets = {
        "GOOGLE_MAPS_API_KEY": goole_maps_api_key,
        "HF_TOKEN": hf_token
    }
    return secrets


def get_secrets(secret_name: str) -> str:
    """Get secrets from the app.config or from load_secrets"""
    try:
        secret = current_app.config.get(secret_name, '')
        if not secret:
            logger.info('[get_secrets]: not secret from config, proceed to load_secrets')
            secrets = load_secrets()
            current_app.config.update(secrets)
            return secrets.get(secret_name, '')
        logger.info(f'[get_secrets]: Success {secret_name}')
        return secret
    except Exception as err:
        logger.error(f'[get_secrets]: Exception {type(err).__name__}: {str(err)}')
        return ''

"""class Config:
    SCOPE = os.getenv('SCOPE', 'local')
    secrets = load_secrets()

    if  "prod" in SCOPE.lower():
        logger.info(f'[get_secrets]: Scope {SCOPE}')
        db_user = secrets.get('db_user', '')
        db_pass = secrets.get('db_pass', '')
        db_endpoint = os.getenv('DB_MYSQL_NOCREPORTHUBA00_REPORTHUBPROD_REPORTHUBPROD_ENDPOINT', '')
        db_schema = "reporthubprod"
    else:
        logger.info(f'[get_secrets]: Scope {SCOPE}')
        db_user = secrets.get('db_user_test', '')
        db_pass = secrets.get('db_pass_test', '')
        db_endpoint = os.getenv('DB_MYSQL_DESAENV10_REPORTHUBTEST_REPORTHUBTEST_ENDPOINT', '')
        db_schema = "reporthubtest"

    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{db_user}:{db_pass}@{db_endpoint}/{db_schema}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 280, 'pool_pre_ping': True}"""