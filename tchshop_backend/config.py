#!/usr/bin/env python3
"""
Database engine and Config
"""
import os
from faker import Faker

faker = Faker()

basedir = os.path.abspath(os.path.dirname(__file__))
env = os.environ.get('WEBAPP_ENV')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'any complex string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 6144 * 6144
    UPLOAD_EXTENSIONS = ['.jpg', '.png', '.img', '.jpeg']
    DESCRIPTION_UPLOAD_EXTENSIONS = ['.jpg', '.png', '.img', '.jpeg', '.gif', '.pdf']
    REVIEW_UPLOAD_PATH = 'webapp/static/reviews/'
    PRODUCT_IMAGE_UPLOAD_PATH = 'webapp/static/products/'
    SINGLE_PRODUCT_UPLOAD_PATH = 'webapp/static/products/default_img/'
    DESCRIPTION_UPLOAD_PATH = 'webapp/static/descriptions/'

    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    ADMIN = os.environ.get('ADMIN') or "directhacktools@gmail.com"

    # email config
    MAIL_SERVER = "smtp.gmail.com"
    # MAIL_SERVER = 'smtp-mail.outlook.com'

    MAIL_PORT = 587
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    MAIL_USE_TLS = True
    # MAIL_USE_SSL = False

    MAIL_DEFAULT_SENDER = 'directhacktools@gmail.com'
    # MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    # MAIL_ASCII_ATTACHMENTS = False



class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, "{}.db").format(os.environ.get('WEBAPP_ENV'))
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'


class TestConfig(Config):
    pass


class ProdConfig(Config):
    pass

# from faker import Faker
# faker = Faker()
# for _ in range(20):
#      db.session.add(
#          Product(
#             product_name=faker.unique.first_name(),
#             quantity=faker.random_int(),
#             regular_price=faker.random_int(),
#             discounted_price=faker.random_int()
#         )
#     )
# db.session.commit()

# for _ in range(2):
#      db.session.add(
#          Category(
#             category_name='scripts',
#         )
#     )
# db.session.commit()

# create user
# from faker import Faker
# faker = Faker()
# for _ in range(10):
#     new_user = User(
#         firstname=faker.first_name(),
#         lastname=faker.last_name(),
#         email=faker.unique.email(),
#         agree=True,  # Example: Assuming agree is a boolean field
#         city=faker.city(),
#         state=faker.state(),
#         country=faker.country(),
#         zipcode=faker.zipcode(),
#         phone=faker.phone_number()
#     )
#     pw =  password='1234567'
#     print(pw)
#     new_user.set_password(password=pw)
#     db.session.add(new_user)