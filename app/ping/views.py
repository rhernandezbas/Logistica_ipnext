"""Module with ping endpoint."""

from flask import Blueprint

ping = Blueprint("ping", __name__)


@ping.route("/ping")
def main():
    """Ping endpoint, used to know if the app is up."""
    return "pong"
