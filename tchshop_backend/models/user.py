#!/usr/bin/env python3
"""
User and Role Model: create a SQLAlchemy model User
"""
from webapp import db
from models.base_model import BaseModel
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean, Float
from flask import current_app, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import AnonymousUserMixin, current_user
from uuid import uuid4, UUID
import logging
import random
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

cart_product = db.Table(
    'cart_product',
    db.Column('cart_id', db.Integer, db.ForeignKey('carts.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True)
)

user_roles = db.Table(
    'role_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id')),
)


# product cart
class Cart(db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True, index=True)
    productid = db.relationship('Product', secondary=cart_product, backref=db.backref('carts', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cart_items = db.relationship('CartItem', backref='carts', uselist=True, lazy=True)

    # cart count
    def total_cart(self, user_id):
        from models.product import Product, CartItem
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        return len(cart.cart_items)

    def __repr__(self):
        return f"Cart('{self.id}', '{self.productid}, 'user_id: {self.user_id}, 'Cart_items: {self.cart_items})"


class User(db.Model):
    """Class User
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    firstname = db.Column(db.String(64), unique=False, index=True)
    lastname = db.Column(db.String(64), unique=False, index=True)
    agree = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(128))
    city = db.Column(db.String(50), unique=False)
    state = db.Column(db.String(30), unique=False)
    country = db.Column(db.String(50), unique=False)
    zipcode = db.Column(db.Integer, unique=False)
    street = db.Column(db.String(70))
    phone = db.Column(db.String(20), nullable=False)

    coupons_count = db.Column(db.Integer, default=0)
    coupons = db.relationship("Coupon", backref="users", lazy=True)

    roles = db.relationship("Role", secondary=user_roles, backref=db.backref('users', lazy=True))
    carts = db.relationship('Cart', backref='users', lazy=True)
    reviews = db.relationship('Review', backref='users', lazy=True)
    orders = db.relationship('Order', backref='users', lazy=True)
    transactions = db.relationship('Transaction', backref='users', lazy=True)

    def __init__(self, email, firstname, lastname, agree, city, state, country, zipcode, street, phone):
        self.email = email
        default = Role.query.filter_by(name="default").one()
        self.roles.append(default)
        self.firstname = firstname
        self.lastname = lastname
        self.agree = agree
        self.roles.append(default)
        self.city = city
        self.state = state
        self.country = country
        self.zipcode = zipcode
        self.street = street
        self.phone = phone

    def serialize(self):
        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'agree': self.agree,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'zipcode': self.zipcode,
            'street': self.street,
            'phone': self.phone,
            # Add more fields as needed
        }

        # add administrator
        # if self.email == current_app.config['ADMIN']:
        #     admin = Role(name='administrator')
        #     db.session.add(admin)
        #     db.session.commit()
        #     self.roles.append(admin)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *name):
        for role in self.roles:
            if role.name in name:
                return True
        return False

    # get current user roles
    # def get_user_role(self):
    #     return self.roles
    # for i in name:
    #     if i in self.roles:
    #         return True
    # return False

    @staticmethod
    def generate_confirmation_token():
        """Generate a unique 6-digit code."""
        return f"{random.randint(100000, 999999):06d}"

    def store_generated_code(self):
        token = self.generate_confirmation_token()
        expiration_time = datetime.now() + timedelta(minutes=40)
        users_code = Vcode(user_id=self.id, code=token, expires_at=expiration_time)
        db.session.add(users_code)
        db.session.commit()
        return token

    def revoke_token(self):
        users_code = Vcode.query.filter_by(user_id=self.id).first()
        db.session.delete(users_code)
        db.session.commit()

    def confirm(self, token):
        users_code = Vcode.query.filter_by(user_id=self.id).first()
        try:
            if users_code:
                code = users_code.code
                expires_at = datetime.fromisoformat(str(users_code.expires_at))
                if token == code and datetime.now() < expires_at:
                    return True
                self.revoke_token()
                return False
        except Exception as e:
            return f"{e}"

    # @staticmethod
    # def get_reset_password_token():
    #     """Generate a unique 6-digit code."""
    #     return f"{random.randint(100000, 999999):06d}"

    @staticmethod
    def verify_reset_password_token(self, token):
        users_code = Vcode.query.filter_by(user_id=current_user.id).first()
        try:
            if users_code:
                code = users_code.code
                expires_at = datetime.fromisoformat(str(users_code.expires_at))
                if token == code and datetime.now() < expires_at:
                    return True
                self.revoke_token()
                return False
        except Exception as e:
            return f"{e}"

    # get user by email
    def get_user_id_by_email(self, email):
        # query user table by email and get first result
        user = User.query.filter_by(email=email).first()
        # if user is found return user ID
        if user:
            return user.id
        return None

    # add role to a user
    def add_role_to_user(self, email, role_name):
        # get user id from email
        # user = self.get_user_id_by_email(email)
        role = Role.query.filter_by(name=role_name).first()
        user_id = self.get_user_id_by_email(email)
        user = User.query.filter_by(id=user_id).first()

        if not user:
            return {"error": "User does not exists"}, 403
        if not role:
            role = Role(name=role_name)
            db.session.add(role)
        if role_name not in user.roles:

            user.roles.append(role)
            db.session.commit()
        return {"Message": f"Role {role_name} added to User: {user.email} successfully"}, 201

    # delete a role from user
    def delete_user_role(self, id):
        # get user id from email
        user = self.get(id)
        # loaded user to delete role from
        role_delete = User.query.filter_by(id=user).one()
        users_roles = role_delete.roles
        if user:
            if len(users_roles) > 0:
                users_roles.pop()
                # role_delete.roles.pop()
                db.session.commit()
            flash(f"User has no role at the moment")

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    # fixes user signin route not redirecting if you're not using the UserMixin class
    def get_id(self):
        return (self.id)

    def __repr__(self):
        return f"User('{self.id}', '{self.firstname}', '{self.lastname}'), '{self.roles}', '{self.coupons_count}', '{self.coupons}'"\
               f"'{self.city}', '{self.state}', '{self.country}', '{self.zipcode}', '{self.street}','{self.email}', '{self.carts}'"


class Role(db.Model):
    """Class Role: Database table named role
    Attributes:
    * id, integer primary key
    * name, non-nullable string

    - roles available = [<Role 'default'>, <Role 'doctor'>, <Role 'record_officer'>, <Role 'administrator'>]
    """
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {
            'role': self.name
        }

    def __repr__(self):
        return '<Role %r>' % self.name


class AnonymousUser(AnonymousUserMixin):
    def has_role(self, name='default'):
        return False

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    @property
    def is_anonymous(self):
        return True


class Vcode(db.Model):
    __tablename__ = "vcodes"
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.String(), nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'code': self.code,
            'expires_at': self.expires_at
        }