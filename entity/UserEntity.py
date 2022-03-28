from conn_db import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, unique=False, nullable=False)
    role = db.relationship("UserRole", backref="user", lazy="dynamic")

