"""Flask app creation."""

import os

from flask import Flask

from app.dummy import dummy
from app.ping import ping
from app.routes.logistica import logistica_bp
from app.utils.logger import get_logger
from app.utils.config import load_secrets, db, marsmallow

logger = get_logger(__name__)

# Active endpoints noted as following:
# (url_prefix, blueprint_object)
ACTIVE_ENDPOINTS = (("/", ping), ("/dummy", dummy),("/logistica", logistica_bp))

def create_app():
    """Create Flask app."""
    app = Flask(__name__)

    # load secrets from environment variables
    app.config.update(load_secrets())
    
    # Comentamos la inicialización de la base de datos temporalmente
    # db.init_app(app)  # Initialize database

    # accepts both /endpoint and /endpoint/ as valid URLs
    app.url_map.strict_slashes = False

    # register each active blueprint
    for url, blueprint in ACTIVE_ENDPOINTS:
        app.register_blueprint(blueprint, url_prefix=url)

    return app