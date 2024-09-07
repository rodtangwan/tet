import logging

from webapp import db
from flask import url_for
from models.base_model import BaseModel
from models.user import User
from flask_login import current_user
# from models.order import Shipping
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean, Float
from _datetime import datetime

product_category = db.Table(
    "prod_category",
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id')))


# product category
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True, nullable=False, index=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)

    # One-to-many relationship with Product
    # products = db.relationship('Product', backref='category')

    def __repr__(self):
        return f"Category('{self.id}', '{self.category_name}')"

    def to_dict(self):
        return {
            'id': self.id,
            'category_name': self.category_name,
        }


# product description
class Description(db.Model):
    __tablename__ = 'descriptions'
    id = db.Column(db.Integer, primary_key=True)
    specifications = db.Column(db.Text, nullable=True)
    images = db.relationship('DescriptionImage', backref='descriptions', lazy=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'specifications': self.specifications,
            # 'images': [url_for("static", filename=f'descriptions/{image.to_dict()}') for image in self.images] or None
            'images': [image.to_dict() for image in self.images] or None

        }

    def __repr__(self):
        return f"Product Description('{self.id}', '{self.product_id}', '{self.specifications}', '{self.images}')"


# description images for more images for product description
class DescriptionImage(db.Model):
    __tablename__ = 'descriptionimages'
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(100), nullable=False)
    description_id = db.Column(db.Integer, db.ForeignKey('descriptions.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def to_dict(self):
        return {
            # 'id': self.id,
            'image_name': self.image_name
        }

    def __repr__(self):
        return f"Description Image ('{self.image_name}', '{self.description_id}')"


# product image table relationship with product
class ProductImage(db.Model):
    __tablename__ = 'productimages'
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def to_dict(self):
        return {
            # 'id': self.id,
            'image_name': self.image
        }

    def __repr__(self):
        return f"Product Image ('{self.image}', '{self.product_id}')"


# product colors
class ProductColor(db.Model):
    __tablename__ = 'product_colors'
    id = db.Column(db.Integer, primary_key=True)
    color = db.Column(db.String(100), nullable=True)
    number = db.Column(db.Integer, default=24)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'color': self.color
        }

    def __repr__(self):
        return f"Product Color ('{self.id}', '{self.color}', '{self.number}', '{self.product_id}')"


# product
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product_image = db.Column(db.String(50))
    regular_price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float, nullable=False)
    number_sold = db.Column(db.Integer)
    description = db.Column(db.String(300))
    # add description table and look into one to many relationship
    descriptions = db.relationship('Description', backref='products', lazy=True)

    # add images to each product
    images = db.relationship('ProductImage', backref='products', lazy=True)

    # add product colors available
    colors = db.relationship('ProductColor', backref='products', lazy=True)

    prod_cat = db.relationship('Category', secondary=product_category, backref=db.backref('products', lazy=True))
    reviews = db.relationship('Review', backref='products', lazy='dynamic')

    cart_items = db.relationship('CartItem', backref='products', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'description': self.description,
            # 'categoryid': self.categoryid,
            'image': self.product_image,
            'quantity': self.quantity,
            'regular_price': self.regular_price,
            'discounted_price': self.discounted_price,
            'product_image': [image.to_dict() for image in self.images]
        }

    # get product by product name
    def get_product_id_by_name(self, product_name):
        # query user table by email and get first result
        product = Product.query.filter_by(product_name=product_name).first()
        # if user is found return user ID
        if product:
            return product.id
        return None

    # assign category to a product
    def add_cat_to_prod(self, product_name, category_name):
        # get product id from product_name
        product_id = self.get_product_id_by_name(product_name)
        cat = Category.query.filter_by(category_name=category_name).first()
        # loaded product to assign category to
        product = Product.query.filter_by(id=product_id).first()
        product.prod_cat.append(cat)
        db.session.commit()

    def __repr__(self):
        return (f"Product('id: {self.id}','name: {self.product_name}', 'image': {self.product_image}, 'quantity: {self.quantity}', descriptions: '{self.descriptions}'\
         '{self.regular_price}', '{self.discounted_price}', '{self.prod_cat}', {self.cart_items}, {self.colors}, number_sold: {self.number_sold}")


# cart item for quantity
class CartItem(db.Model):
    __tablename__ = 'cart_item'
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    shipping = db.Column(db.Integer, nullable=False, default=2)
    color = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"Cart_id: {self.cart_id}, Product_id: {self.product_id}, Quantity: {self.quantity}, Shipping_method: {self.shipping}, product_color: {self.color}"


# shipping method available for products
class Shipping(db.Model):
    __tablename__ = 'shippings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    deliveryTime = db.Column(db.String(200))
    cost = db.Column(db.Float, nullable=False)

    def total_cost(self, name, quantity):
        method = Shipping.query.filter_by(name=name).first()
        logging.info(f'Method for total cost {method}')
        if quantity > 1:
            return (quantity * method.cost) * 0.55
        else:
            return "%.3f".format(method.cost)

    def __repr__(self):
        return (f"Shipping(id: '{self.id}' Name: '{self.name}', Cost: '{self.cost}' \
         deliveryTime: '{self.deliveryTime}'")


# product review
class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    product_rating = db.Column(db.Integer)
    product_review = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    productid = db.Column(db.Integer, db.ForeignKey('products.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    images = db.relationship('ReviewImage', backref='reviews', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'product_rating': self.product_rating,
            'product_review': self.product_review,
            'timestamp': self.timestamp,
            'productid': self.productid,
            'user_id': self.user_id,
            'images': [img.to_dict() for img in self.images]
        }

    def __repr__(self):
        return f"Review ('{self.id}',{self.product_review}', '{self.product_rating}', '{self.user_id}', '{self.productid}', '{self.images}')"


# review images
class ReviewImage(db.Model):
    __tablename__ = "review_images"
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(100), nullable=False)
    review_id = db.Column(db.String(100), db.ForeignKey('reviews.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def to_dict(self):
        return {
            # 'id': self.id,
            'image_name': self.image
            # 'review_id': self.review_id,
            # 'product_id': self.product_id
        }

    def __repr__(self):
        return f"Review Image ('{self.image}', '{self.review_id}', '{self.product_id}')"
