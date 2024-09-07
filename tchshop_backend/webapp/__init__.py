from flask import Flask, Blueprint
from config import DevConfig
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from faker import Faker
from flask_mail import Mail
from flask_session import Session


db = SQLAlchemy()
migrate = Migrate()
faker = Faker()
mail = Mail()
# session = Session()


def create_app(object_name):
    """
        An flask application factory, as explained here:
        http://flask.pocoo.org/docs/patterns/appfactories/

        Arguments:
            object_name: the python path of the config object,
            e.g. Patient-Information-System.config.DevConfig
    """
    app = Flask(__name__)
    app.secret_key = 'qwertyuiop'
    app.config.from_object(object_name)

    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    CORS(app, supports_credentials=True)  # Enable CORS for all origins

    # auth module  init creation
    from webapp.auth import create_module as auth_create_module
    auth_create_module(app)

    # admin module  init creation
    from webapp.admin import create_module as admin_create_module
    admin_create_module(app)

    # views module  init creation
    from webapp.main import create_module as main_create_module
    main_create_module(app)

    return app