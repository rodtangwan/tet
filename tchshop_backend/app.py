#!/usr/bin/env python3
"""
Route module for the app
"""
from webapp import create_app, db, mail
from flask import jsonify
import os
from models.base_model import BaseModel
from models.product import Product, Category, Review, CartItem, Description, DescriptionImage, ProductImage, Shipping, ReviewImage, ProductColor
from models.user import Role, User, Cart, Vcode
from models.order import Order, OrderedProduct, Transaction, Coupon, Wallet
from flask_cors import CORS


env = os.environ.get('WEBAPP_ENV')
# app = create_app(os.getenv('WEBAPP_ENV') or 'default')
app = create_app('config.%sConfig' % env.capitalize())
CORS(app, supports_credentials=True)
"""
    returns a dictionary that includes the database instance and the models in which 
    flask shell command will import these items automatically into the shell for user
    in flask terminal
"""


@app.shell_context_processor
def make_shell_context():
    # Base.metadata.create_all(bind=engine)
    return dict(db=db, BaseModel=BaseModel, Product=Product, Category=Category, Cart=Cart, CartItem=CartItem,
                User=User, Role=Role, Review=Review, Order=Order, OrderedProduct=OrderedProduct, Transaction=Transaction,
                Shipping=Shipping, Description=Description, DescriptionImage=DescriptionImage, ProductImage=ProductImage, ReviewImage=ReviewImage
                , ProductColor=ProductColor, Coupon=Coupon, Wallet=Wallet, Vcode=Vcode)


@app.errorhandler(404)
def not_found(error):
    """ Not found handler
    """
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(401)
def resource_not_found(e):
    """Unauthorized Handler Code: 401"""
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden_app(e):
    """Forbidden Handler Code:403"""
    return jsonify({"error": "Forbidden"}), 403


# @app.before_request
# def before_request():
#     """Before Request Flask"""
#     if auth is not None:
#         pathList = ['/api/v1/status/',
#                     '/api/v1/unauthorized/',
#                     '/api/v1/forbidden/']
#         if auth.require_auth(request.path, pathList) is False:
#             return
#         if auth.authorization_header(request) is None:
#             abort(401)
#         if auth.current_user(request) is None:
#             abort(403)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
