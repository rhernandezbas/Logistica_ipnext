"""Cliente model module."""

from datetime import datetime
from app.utils.config import db

class Cliente(db.Model):
    """Cliente model."""
    
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    localidad = db.Column(db.String(100), nullable=False)  # Campo localidad para agrupar clientes
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    telefono = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.String(100))
    updated_at = db.Column(db.String(100))
    
    def __repr__(self):
        """Return string representation of Cliente."""
        return f"<Cliente {self.id}: {self.nombre}>"
    
    def to_dict(self):
        """Return dictionary representation of Cliente."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'direccion': self.direccion,
            'localidad': self.localidad,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'telefono': self.telefono,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
