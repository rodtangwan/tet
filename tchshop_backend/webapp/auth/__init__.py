#!/usr/bin/env python3
""" Webapp authentication view
"""
from functools import wraps
from flask import Blueprint, abort, flash, jsonify
from models.user import User, AnonymousUser
from flask_login import LoginManager, current_user


# create blueprint for auth views
auth_views = Blueprint('auth_views',
                    __name__,
                    url_prefix="/auth"
                    )

login_manager = LoginManager()
login_manager.login_view = 'auth_views.signin'
login_manager.session_protection = "basic"
login_manager.login_message = "Please login to access this page"
login_manager.login_message_category = "info"
login_manager.anonymous_user = AnonymousUser


def create_module(app, **kwargs):
    login_manager.init_app(app)
    app.register_blueprint(auth_views)

# import views to prevent 404 error
from webapp.auth.views import *


def has_role(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if the user has all the required roles
            user_roles = current_user.roles  # Replace with your logic to get user roles
            for r in roles:
                if current_user.has_role(r):
                    return func(*args, **kwargs)
            # if all(role in user_roles for role in roles):
            #     return func(*args, **kwargs)
            else:
                return jsonify({'error': 'Unauthorized'}), 401
        return wrapper
    return decorator


@login_manager.user_loader
def load_user(id):
    return User.query.get(id)
