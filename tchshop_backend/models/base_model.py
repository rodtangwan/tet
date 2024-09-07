from webapp import db
from datetime import datetime
from uuid import uuid4, UUID


class BaseModel(db.Model):
    """
        attributes and functions for BaseModel class
        Attributes:
            * id, integer primary key
            * created_at, datetime
            * updated_at, datetime
    """
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    discriminator = db.Column('type', db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'base_model',
        'polymorphic_on': discriminator
    }

    def __init__(self, created_at, updated_at):
        """
            instantiation of new BaseModel class
        """
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"Created at: {self.created_at}  Updated at: {self.updated_at}"
