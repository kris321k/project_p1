from datetime import datetime
from config.database import db

class User(db.Model) :

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key = True
    )
    username = db.Column(
        db.String(100),
        unique = True,
        nullable = False
    )
    email = db.Column(
        db.String(150),
        unique = True,
        nullable = False
    )
    password_hash = db.Column(
    db.String(255),
    nullable=False
    )
    role = db.Column(
        db.String(20),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # One User -> One Employee
    employee = db.relationship(
        "Employee",
        back_populates="user",
        uselist=False
    )
