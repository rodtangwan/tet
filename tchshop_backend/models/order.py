from webapp import db
from models.base_model import BaseModel
from models.user import User
# from models.product import Product
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean, Float


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, nullable=False)
    shipping_price = db.Column(db.Integer, nullable=False)
    billing_address = db.Column(db.String(90), nullable=False)
    contacts = db.Column(db.String(200), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ordered_products = db.relationship('OrderedProduct', backref='orders', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'order_date': self.order_date,
            'total_shipping': self.shipping_price,
            'billing_address': self.billing_address,
            'contacts': self.contacts,
            'userid': self.userid
        }

    def __repr__(self):
        return f"Order('{self.id}', '{self.order_date}','{self.contacts}','{self.shipping_price}','{self.billing_address}', '{self.userid}', '{self.ordered_products}')"


class OrderedProduct(db.Model):
    __tablename__ = "ordered_products"
    id = db.Column(db.Integer, primary_key=True)
    orderid = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    productid = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    shipping = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(15), default='pending')

    def to_dict(self):
        return {
            'id': self.id,
            'orderid': self.orderid,
            'productid': self.productid,
            'quantity': self.quantity,
            'shipping': self.shipping,
            'status': self.status
        }

    @staticmethod
    def clean_pending():
        all_pending = OrderedProduct.query.filter_by(status='pending').all()
        if all_pending:
            for i in all_pending:
                Order.query.filter_by(id=i.orderid).delete()
                # for j in corresponding_orders:
                db.session.delete(i)
            db.session.commit()

    def __repr__(self):
        return f"OrderedProduct('{self.id}', '{self.orderid}','{self.productid}','{self.quantity}', '{self.status}', '{self.shipping}')"


class Coupon(db.Model):
    __tablename__ = "coupons"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(15))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    percentage = db.Column(db.Integer, default=20)
    status = db.Column(db.String(10))

    def to_dict(self):
        return {
            "code": self.code,
            "user_id": self.user_id or None,
            "percentage": self.percentage or None,
            "status": self.status or None
        }


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False)
    # orderid = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    response = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "order_date": self.order_date,
            "userid": self.userid,
            "orderid": self.orderid,
            "amount": self.amount,
            "response": self.response
        }

    def __repr__(self):
        return f"SaleTransaction('{self.id}', '{self.amount}', '{self.response}')"


class Wallet(db.Model):
    __tablename__ = "wallets"
    id = db.Column(db.Integer, primary_key=True)
    currency_type = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(50), nullable=False, unique=True)

    def to_dict(self):
        return {
            "currency_type": self.currency_type,
            "address": self.address
        }

    def __repr__(self):
        return f"Wallets('{self.id}', '{self.currency_type}', '{self.address}')"




# CREATE TABLE coupons (
#    id INTEGER NOT NULL PRIMARY KEY,
#    code TEXT,
#    user_id INTEGER NOT NULL FOREIGNKEY,
#    percentage TEXT,
# status TEXT);
