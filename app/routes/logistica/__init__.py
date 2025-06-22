""" """

from flask import Blueprint

logistica_bp  = Blueprint('logistica', __name__)

from app.routes.logistica import routes_logistica