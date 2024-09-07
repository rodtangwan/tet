import random
from webapp.email import send_coupon_email
from flask import render_template, url_for, flash, jsonify, redirect, request, make_response, session, send_from_directory
from models.product import Product, Category, Review, CartItem, Shipping, ProductColor, Description, ProductImage
from models.user import User, Cart
from webapp import db
from models.order import Order, OrderedProduct, Transaction, Coupon, Wallet
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from webapp.auth import has_role
from webapp.main import main
import logging
from sqlalchemy.exc import IntegrityError
import os

# Configure logging to display messages to the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])


# get all products
@main.route('/listproducts', methods=['GET'], strict_slashes=False)
def get_products():
    # Get the 'limit' and 'offset' query parameters from the request
    limit = request.args.get('limit', default=16, type=int)  # Default to 16 items per page
    offset = request.args.get('offset', default=0, type=int)  # Default to start from the first item

    # Query the products from the database with limit and offset
    products = Product.query.offset(offset).limit(limit).all()

    product_list = []

    for product in products:
        # Construct the URL for the product image
        if product.product_image:
            # Handle URL encoding of spaces and special characters if needed
            image_filename = product.product_image.replace(' ', '%20')
            image_url = f'{image_filename}'
        else:
            image_url = None

        product_list.append({
            'id': product.id,
            'Product name': product.product_name,
            'description': product.description,
            'quantity': product.quantity,
            'regular_price': product.regular_price,
            'product_image': image_url,
            'discounted_price': product.discounted_price
        })

    return jsonify(product_list), 200



# all product by category
@main.route('/categories', methods=['GET'], strict_slashes=False)
def view_categories():
    categories = Category.query.filter_by()
    all_cat = [category.to_dict() for category in categories]
    return jsonify(all_cat), 200


# view all products under a category
@main.route('/products/<category>', methods=['GET'], strict_slashes=False)
def products_category(category):
    all_products = Product.query.all()
    cat_prods = []
    for product in all_products:
        for cat in product.prod_cat:
            if category == cat.category_name:
                cat_prods.append(product)
            pass
    category_products = [{
        'name': prod.product_name,
        'image': prod.product_image,
        'price': prod.discounted_price,
        'id': prod.id
    } for prod in cat_prods]
    return jsonify(category_products), 200


# get a product
@main.route('/product/<int:product_id>', methods=['GET'], strict_slashes=False)
def view_product(product_id):
    product = Product.query.get(product_id) 
    
    if not product:
        return jsonify({'error': 'Product Not Found'}), 404

    # Convert the product object to a dictionary
    product_data = product.to_dict()

    base_url = '/static/products'  

    # Construct image URLs
    if 'images' in product_data:
        product_data['image_urls'] = [
            f'{base_url}/{img["image_name"]}' for img in product_data['images']
        ]

    return jsonify(product_data), 200


# view product description
@main.route('/product_desc/<int:product_id>', methods=['GET'], strict_slashes=False)
def view_product_desc(product_id):
    product = Product.query.get_or_404(product_id)
    if not product:
        return jsonify({'error': 'Product Not found'}), 404

    desc = Description.query.filter_by(product_id=product.id).first()
    if desc:
        return jsonify(desc.to_dict()), 200
 
    return jsonify({'error': 'Description Not found'}), 404


# users cart
@login_required
@main.route('/addToCart/<product_id>', methods=['GET', 'POST'], strict_slashes=False)
def add_to_cart(product_id):
    data = request.json
    # id = data['userId']
    id = current_user.id
    user = User.query.get(id)
    product_id = product_id
    product = Product.query.get(product_id)
    quantity = data.get('quantity', 1)
    shipping = data.get('shipping', 2)
    all_colors = ProductColor.query.filter_by(product_id=product_id).all()
    logging.info(f"all colors: {all_colors}")
    logging.info(f"len all colors: {len(all_colors)}")

    cs = len(all_colors)
    # color = data['color']
    # if not color:
    color = data.get('color')
    # color = data.get('color', f'{all_colors[random.choice(range(1, cs))].color}')
    logging.info(f"Quantity first {quantity}")
    logging.info(f"Data {data['quantity']}")

    # add or update shipping
    shipping_method = Shipping.query.filter_by(id=shipping).first()

    cart_len = 0
    try:
        if int(product.quantity) < int(quantity):
            return jsonify({"Message": "Not enough Product in stock reduce quantity"})
        # count = Cart.add_to_cart(cart_len=cart_len, quantity=quantity, product_id=product_id, shipping=int(shipping_method.method))
        # logging.info(f"items to add to cart: {count}")
        # cart = Cart.query.filter_by(user_id=current_user.id).first()
        cart = current_user.carts
        if not cart:
            add = Cart(user_id=current_user.id)
            db.session.add(add)
            db.session.commit()
        cart_item = CartItem.query.filter_by(cart_id=current_user.id, product_id=product.id).first()
        if cart_item:
            return jsonify({"Message": "Item already in cart"})
        else:
            add_cartitem = CartItem(cart_id=current_user.id, product_id=product.id, quantity=quantity, shipping=shipping, color=color)
            db.session.add(add_cartitem)
            db.session.commit()
        all_items = CartItem.query.filter_by(cart_id=current_user.id).all()
        cart_len += len(all_items)
    except IntegrityError as e:
        db.session.rollback()
        db.session.commit()
        cart = Cart.query.filter_by(user_id=user.id).first()
        return jsonify({"error": "Item already in cart", "Total Cart": cart_len})

    return jsonify({"Message": f"Product {product.product_name} added to User: {user.email} cart ,'total': {cart_len}"}), 200


# cart items
@login_required
@main.route('/cart', methods=['GET'], strict_slashes=False)
def cart():
    # user_id = current_user.id
    # user = Cart.query.filter_by(user_id=user_id).first()
    cart_items = CartItem.query.filter_by(cart_id=current_user.id).all()

    cart_details = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        shipping = Shipping.query.filter_by(id=item.shipping).first()
        cart_details.append({
            'id': product.id,
            'product_name': product.product_name,
            'product_image': product.product_image,
            'prod_quantity': item.quantity,
            'regular_price': product.regular_price,
            'discounted_price': product.discounted_price,
            'total_price': item.quantity * product.discounted_price,
            'shipping_method': shipping.name if shipping else None,
            'shipping_price': shipping.cost if shipping else None,
            'color': item.color,
            'delivery_date': shipping.deliveryTime if shipping else None
        })
    
    return jsonify({'cart_details': cart_details}), 200


# remove product from cart
@login_required
@main.route('/removeFromCart/<product_id>', methods=['DELETE'], strict_slashes=False)
def remove_from_cart(product_id):
    # data = request.json
    user_id = current_user.id
    # user_id = data['userId']
    product = Product.query.get(product_id)
    cart_item = CartItem.query.filter_by(
        cart_id=user_id, product_id=product_id
    ).first()

    # logging.info(f"Item quantity {add_quantity}")
    # logging.info(f"Cart details {cart_item.quantity}")
    if not cart_item:
        return jsonify({"error": "Item not found"}), 404
        # update total products
    # user = User.query.filter_by(id=user_id).first()
    # user.carts.remove(user.carts[-1])
    product.quantity += cart_item.quantity
    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"message": f"Item {product.product_name} deleted"}), 200


# Update Quantity of a product in the cart
@login_required
@main.route('/updateQuantity/<int:product_id>', methods=['PUT'], strict_slashes=False)
def update_cart_item_quantity(product_id):
    id = current_user.id
    data = request.json
    # product = Product.query.get(product_id)

    if "quantity" not in data:
        return jsonify({"message": "Quantity not provided"}), 400

    cart_item = CartItem.query.filter_by(cart_id=id, product_id=product_id).first()
    if not cart_item:
        return jsonify({"message": "Item not found in cart"}), 404

    # update to real quantity in db
    # ini_quantity = product.quantity
    # logging.info(f"Initial Product quantity: {ini_quantity}")
    #
    # new_quantity = int(data.get('quantity'))
    # if (cart_item.quantity - new_quantity) <= 0:
    #     return jsonify({"error": "Not enough in Stock reduce quantity"}), 404
    # ini_quantity += cart_item.quantity
    # ini_quantity -= new_quantity
    # logging.info(f"Product quantity: {ini_quantity}")

    cart_item.quantity = data["quantity"]
    db.session.commit()

    return jsonify({"message": "Item quantity updated successfully"}), 200


# Update color of a product in the cart
@login_required
@main.route('/updateColor/<int:product_id>', methods=['PUT'], strict_slashes=False)
def update_cart_item_color(product_id):
    id = current_user.id
    data = request.json
    # product = Product.query.get(product_id)

    if "color" not in data:
        return jsonify({"message": "Color not provided"}), 400

    cart_item = CartItem.query.filter_by(cart_id=id, product_id=product_id).first()
    if not cart_item:
        return jsonify({"message": "Item not found in cart"}), 404

    # update to real quantity in db
    # ini_quantity = product.quantity
    # logging.info(f"Initial Product quantity: {ini_quantity}")
    #
    # new_quantity = int(data.get('quantity'))
    # if (cart_item.quantity - new_quantity) <= 0:
    #     return jsonify({"error": "Not enough in Stock reduce quantity"}), 404
    # ini_quantity += cart_item.quantity
    # ini_quantity -= new_quantity
    # logging.info(f"Product quantity: {ini_quantity}")

    cart_item.color = data["color"]
    db.session.commit()

    return jsonify({"message": "Item color updated successfully"}), 200


# get all shipping methods available
@login_required
@main.route('/shipping', methods=['GET'], strict_slashes=False)
def all_shipping():
    available_methods = Shipping.query.all()
    all_methods = [{"id": ship.id, "name": ship.name, "deliveryTime": ship.deliveryTime, "cost": ship.cost
                    } for ship in available_methods]
    return jsonify(all_methods), 200


# Update shipping method of a product in the cart
@login_required
@main.route('/updateShipping/<int:product_id>', methods=['PUT'], strict_slashes=False)
def update_cart_item_shipping(product_id):
    id = current_user.id
    data = request.json
    # product = Product.query.get(product_id)
    shipping = Shipping.query.filter_by(id=data["id"]).first_or_404()

    if "id" not in data:
        return jsonify({"message": "Shipping not provided"}), 401
    cart_item = CartItem.query.filter_by(cart_id=id, product_id=product_id).first()
    if not cart_item:
        return jsonify({"message": "Item not found in cart or Shipping method does not exist"}), 404

    cart_item.shipping = data["id"]
    db.session.commit()

    return jsonify({"message": "Item shipping updated successfully"}), 200


# Clear the cart
@login_required
@main.route('/clearCart', methods=['DELETE'])
def delete_all_items():
    CartItem.query.filter_by(cart_id=current_user.id).delete()
    db.session.commit()
    return jsonify(status="success", message="Cart cleared", data={}), 200


# reviews with code
@main.route('/reviews/<int:product_id>/<code>', methods=["GET"], strict_slashes=False)
def rev_sesh(product_id, code):
    # if its a new user, get the user that referred them. Save referrer in a cookie. Redirect to signup
    if code:
        try:
            user = Coupon.query.filter_by(code=code, status='minion').first()
            if user:
                session['coupon'] = code
        except:
            pass

    if current_user.is_authenticated:
        return redirect(url_for('main.view_reviews', product_id=product_id)), 200
    return redirect(url_for('auth_views.signup')), 200


# view product reviews
@main.route('/reviews/<int:product_id>', methods=["GET"], strict_slashes=False)
def view_reviews(product_id):
    product = Product.query.get_or_404(product_id)
    if product:
        all_reviews = Review.query.filter_by(productid=product_id).all()
        base_url = '/static/reviews'

        reviews = []
        for review in all_reviews:
            image_urls = [
                f'{img["image_name"]}' for img in [image.to_dict() for image in review.images]
            ]
            logging.info(f"Image URLs for review {review.id}: {image_urls}")

            reviews.append({
                "Rating": review.product_rating,
                "Review": review.product_review,
                "Timestamp": review.timestamp,
                "Image": image_urls,
                "id": review.id,
                "user_id": review.user_id
            })

        return jsonify(reviews), 200
    return jsonify({"error": "Item not found"}), 404


@login_required
@main.route('/shippingAddress', methods=["GET", "POST"], strict_slashes=False)
def address():
    user = User.query.get(current_user.id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'GET':
        if not all([user.zipcode, user.street, user.city, user.state, user.country]):
            return jsonify({'error': 'Shipping address not complete or missing. Please add a shipping address.'}), 400

        address_parts = [str(part) for part in [user.zipcode, user.street, user.state, user.city, user.country] if part]
        formatted_address = ', '.join(address_parts)

        return jsonify({"shipping_address": formatted_address}), 200

    if request.method == 'POST':
        data = request.json
        
<<<<<<< HEAD
        required_fields = ['country', 'state', 'city', 'street', 'zipcode', 'firstname', 'lastname', 'phone']
=======
        required_fields = ['country', 'state', 'city', 'street', 'zipcode']
>>>>>>> a451a55d35c592577f6ad4ccfbeeca733c9f5e7e
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({'error': 'All fields (country, state, city, street, zipcode) are required.'}), 400

        user.firstname = data.get('firstname')
        user.lastname = data.get('lastname')
        user.phone = data.get('phone')
        user.country = data.get('country')
        user.state = data.get('state')
        user.city = data.get('city')
        user.street = data.get('street')
        user.zipcode = data.get('zipcode')

        db.session.commit()
        return jsonify(status="success", message="Shipping address added successfully"), 201


# view product colors available
@login_required
@main.route('/view_product_color/<int:product_id>', methods=["GET"], strict_slashes=False)
def view_product_colors(product_id):
    product = Product.query.get_or_404(product_id)
    if product is None:
        return jsonify({'error': 'Product does not exist'}), 404
    
    if request.method == 'GET':
        product_colors = ProductColor.query.filter_by(product_id=product.id).all()
        colors = [color.to_dict() for color in product_colors]
        return jsonify(colors), 200


@login_required
@main.route('/checkout', methods=["GET", "POST"], strict_slashes=False)
def checkout():

    cart_items = CartItem.query.filter_by(cart_id=current_user.id).all()

    if not cart_items:
        return jsonify(status="error", message="Your cart is empty"), 400
    user = User.query.get(current_user.id)

    if not all([user.zipcode, user.street, user.city]):
        return jsonify(status="error", error_type="missing_data",
                       message="Update shipping"), 400

    # check if same order with status pending exist and remove them
    users_orders = Order.query.filter_by(userid=current_user.id).all()
    logging.info(f'toatal price: {users_orders}')

    if users_orders:
        for i in users_orders:
            for j in i.ordered_products:

                if j.status == 'pending':
                    db.session.delete(i)
        db.session.commit()
    else:
        pass

    total_price = 0
    total_shipping = 0
    # Update the product's available quantity
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        product.quantity -= cart_item.quantity
        method = Shipping.query.filter_by(id=cart_item.shipping).first()
        total_price += product.discounted_price * cart_item.quantity
        if cart_item.quantity >= 2:
            total_shipping += (method.cost * cart_item.quantity) * 0.85
        else:
            total_shipping += (method.cost * cart_item.quantity)

        billing_address = f"{user.zipcode},{user.street}, {user.city}, {user.state}, {user.country}"
        contacts = f"{user.email}, {user.phone}"
        new_order = Order(order_date=datetime.utcnow(), shipping_price=method.cost, billing_address=billing_address,\
                          contacts=contacts, userid=user.id)
        db.session.add(new_order)
        db.session.commit()

        items = OrderedProduct(orderid=new_order.id, productid=cart_item.product_id, quantity=cart_item.quantity, shipping=cart_item.shipping, status='pending')
        db.session.add(items)
    try:
        db.session.commit()

        session["total_price"] = round(total_price, 3)
        session["total_shipping"] = round(total_shipping, 3)

        total_price = session["total_price"]
        total_shipping = session["total_shipping"]

        logging.info(f'toatal price: {session["total_price"]}')
        return jsonify({"total_price": round(total_price, 3), "total_shipping": round(total_shipping, 3)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": e}), 400


# each users coupon code
# @login_required
@main.route('/coupon', methods=["GET"], strict_slashes=False)
def coupon():
    user = current_user
    user = Coupon.query.filter_by(user_id=current_user.id).first()
    if not user:
        return jsonify({"error": "no coupon for this user"}), 400
    return jsonify({"users_coupon": user.code}), 200


# each users coupon code
# @login_required
@main.route('/coupon/<code>', methods=["GET"], strict_slashes=False)
def coupon_sesh(code):
    #if its a new user, get the user that referred them. Save referrer in a cookie. Redirect to signup
    if code:
        try:
            user = Coupon.query.filter_by(code=code, status='minion').first()
            if user:
                session['coupon'] = code
        except:
            pass

    return redirect(url_for('auth_views.signup')), 200


# use users coupon code
@login_required
@main.route('/useCoupon', methods=["POST"], strict_slashes=False)
def use_coupon():
    data = request.json
    code = data["code"]
    coupon_user = Coupon.query.filter_by(code=code, percentage=20).first()
    if not coupon_user:
        return jsonify({"error": "Invalid coupon code"}), 400

    # session.pop("total_price", None)
    # session.pop("total_shipping", None)
    # total_price = 0
    # total_shipping = 0
    total_price = session["total_price"]
    total_shipping = session["total_shipping"]
    coupon_price = total_price - (total_price * 0.07)

    cart_items = CartItem.query.filter_by(cart_id=current_user.id).all()
    # Update the product's available quantity
    users_c = Coupon.query.filter_by(code=code, user_id=current_user.id).first()
    if users_c is None:
        user_coupon = Coupon(code=code, user_id=current_user.id, percentage='', status="pending")
        db.session.add(user_coupon)
    db.session.commit()

    session["total_price"] = round(coupon_price, 3)
    session["total_shipping"] = round(total_shipping, 3)
    # logging.info(f'toatal price: {session["total_price"]}')

    return jsonify({"coupon_price": coupon_price, "total_shipping": round(total_shipping, 3)}), 200

    # all_order = Order.query.filter_by(userid=coupon_user.id).all()



# select payment method
@login_required
@main.route('/paymentMethods', methods=["POST"], strict_slashes=False)
def select_method():
    data = request.json
    method = data.get("method").upper()

    if not method:
        return jsonify({"error": "No payment method provided"}), 400

    session["method"] = method

    check = Wallet.query.filter_by(currency_type=method).first()
    logging.info(f'toatal price: {check}')

    if not check:
        return jsonify({"error": "Payment method not available, consider another option"}), 400

    if method.upper() == "USDT":
        usdt_addresses = Wallet.query.filter_by(currency_type=method).all()
        selected_address = random.choice(usdt_addresses).address
        session["address"] = selected_address
        
        return jsonify({
            "success": True,
            "message": "Payment method selected successfully",
        }), 200

    # return jsonify({"success": True, "message": "Payment method selected successfully"}), 200
# @login_required
# @main.route('/paymentMethods', methods=["POST"], strict_slashes=False)
# def select_method():
#     data = request.json
#     method = data["method"]
#     session["method"] = method

#     check = Wallet.query.filter_by(currency_type=method).first()
#     if not check:
#         return jsonify({"error": "not available consider another payment method"}), 400
#     if method.upper() == "USDT":
#         usdt_address = Wallet.query.filter_by(currency_type=method).all()
#         add = random.choice(usdt_address)
#         address = add.address
#         session["address"] = address
#         return redirect(url_for("main.pay")), 200 
    

        # return jsonify({"address": address, "crypto": method}), 200
    # elif method.upper() == "USDC":
    #     usdc_address = Wallet.query.filter_by(currency_type=method).all()
    #     add = random.choice(usdc_address)
    #     address = add.address
    #     session["address"] = address
    #     session["method"] = method
    #     return redirect(url_for("main.pay")), 200
        # return jsonify({"address": address, "crypto": method}), 200

<<<<<<< HEAD
# proceed to payment
# @login_required
# @main.route('/proceed', methods=["GET"], strict_slashes=False)
# def proceed():
#     total_price = session["total_price"]
#     total_shipping = session["total_shipping"]
#     session["tax"] = 5.6
#     tax = session["tax"]
#     grand_total = round(float(total_price) + float(total_shipping) + float(tax), 3)
#     session["grand_total"] = grand_total
#     return jsonify({'total_price': total_price, 'total_shipping': total_shipping, 'tax': tax, 'grand_total': grand_total})




=======
>>>>>>> a451a55d35c592577f6ad4ccfbeeca733c9f5e7e
"""
    the appropriate random address selected from the above is passed here with the amount to be paid
"""
@login_required
@main.route('/pay', methods=["GET"], strict_slashes=False)
def pay():
    if current_user:
        address = session["address"]
        method = session["method"]
        total_price = session["total_price"]
        total_shipping = session["total_shipping"]
        session["tax"] = 5.6
        tax = session["tax"]
        grand_total = round(float(total_price) + float(total_shipping) + float(tax), 3)
        session["grand_total"] = grand_total
        grand_total = session["grand_total"]

        return jsonify({'address': address, 'type': method, 'total_price': total_price, 'tax': tax, 'grand_total': grand_total})


# confirm pay
@login_required
@main.route('/confirmation', methods=["POST"], strict_slashes=False)
def confirm_payment():
    user = current_user
    if request.method == "POST" and current_user:
        if "grand_total" not in session:
            return jsonify({'pending': 'payment already processing'}), 200
        grand_total = session["grand_total"]
        
        # user_order = Order.query.filter_by(userid=current_user.id).all()
        # for order in user_order
        new_transaction = Transaction(order_date=datetime.utcnow(), userid=current_user.id, amount=grand_total, response='pending')
        db.session.add(new_transaction)
        try:
            cart_items = CartItem.query.filter_by(cart_id=current_user.id).all()
            for cart_item in cart_items:
                db.session.delete(cart_item)

            users_c = Coupon.query.filter_by(user_id=current_user.id).first()
            if users_c:
                users_c.status = 'success'

            # update order status to processing
            users_orders = Order.query.filter_by(userid=current_user.id).all()
            logging.info(f'toatal price: {users_orders}')
            if users_orders:
                for i in users_orders:
                    for j in i.ordered_products:

                        if j.status == 'pending':
                            j.status = 'processing'
                # db.session.commit()
            else:
                pass
            db.session.commit()

            send_coupon_email(user, grand_total)

            # session.pop("grand_total", None)
            session.clear()
            return jsonify({'success': 'payment processing'}), 201
        except Exception as e:
            j = e
            # logging.info(f'key error{j}')
            # # session.pop("grand_total", None)
            # if e:
            #     return jsonify({'message': f'payment processing'}), 400

            db.session.rollback()
            return jsonify({'error': f'{e}payment not successful'}), 400


# view users ordered product
@login_required
@main.route('/orders', methods=["GET"], strict_slashes=False)
def orders():
    id = current_user.id
    OrderedProduct.clean_pending()

    users_orders = Order.query.filter_by(userid=id).order_by(Order.order_date.desc()).all()

    # logging.info(f'toatal price: {users_orders}')

    if not users_orders:
        return jsonify({'message': 'you have no orders yet'}), 400
    all_orders = []

    for order in users_orders:
        # for ordered in all_ordered:
        all_ordered = OrderedProduct.query.filter_by(orderid=order.id).first()
        if order.id:
            method = Shipping.query.filter_by(id=all_ordered.shipping).first()
            product = Product.query.filter_by(id=all_ordered.productid).first()

            # logging.info(f'{product}')
            if product.product_image:
                # Handle URL encoding of spaces and special characters if needed
                image_filename = product.product_image.replace(' ', '%20')
                image_url = f'{image_filename}'
            else:
                image_url = None
            all_orders.append(
                {
                    "product_id": product.id,
                    "product_name": product.product_name,
                    "product_image": image_url,
                    "order_date": order.order_date,
                    "status": all_ordered.status,
                    "shipping": method.name,
                    "delivery": method.deliveryTime,
                    "quantity": all_ordered.quantity
                })

<<<<<<< HEAD
    return jsonify({all_orders}), 200
=======
    return jsonify(all_orders), 200
>>>>>>> a451a55d35c592577f6ad4ccfbeeca733c9f5e7e


# check ordered product status
@login_required
@main.route('/shipment/<product_id>', methods=["PUT"], strict_slashes=False)
def shipment(product_id):
    users_orders = Order.query.filter_by(userid=current_user.id).order_by(Order.order_date.desc()).all()
    if not users_orders:
        return jsonify({"message": "you have no orders"}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "product does not exist"}), 400

    if users_orders:
        for i in users_orders:
            logging.info(f'order day {i.ordered_products}')
            ordered_products = i.ordered_products
            try:
                # for j in range(len(ordered_products)):
                for j, item in enumerate(ordered_products):
                    logging.info(f'enumerate {j} item{item.status}')
                    logging.info(f'enumerate {j} item{item.productid}')

                    if item.productid == int(product_id) and item.status == 'processing':
                        logging.info(f'order day {i.order_date}')

                        # logging.info(f'product id{j.productid}')
                        # logging.info(f'product shipping {j.shipping}')
                        # logging.info(f'product status {j.status}')
                        # dispatch times comes between 24 and 48 hours
                        today_time = datetime.utcnow()

                        shipping_dispatch = i.order_date + timedelta(hours=random.choice(range(20, 50)))
                        # shipping_dispatch = i.order_date + timedelta(minutes=random.choice(range(1, 5)))

                        logging.info(f'shipping_dispatch {shipping_dispatch}')

                        # update status to shipped if current time is greater than shipping_dispatch
                        # dispatch = datetime.fromisoformat(str(shipping_dispatch))
                        logging.info(f'today {today_time}')
                        if today_time >= shipping_dispatch:
                            item.status = 'Product has been shipped'
                            logging.info(f'product shipping {item.shipping}')
                            db.session.commit()
                            return jsonify({"message": "Your order has been shipped"}), 201
                        elif today_time < shipping_dispatch:
                            return jsonify({"message": "order ships in 1 - 2 days time"}), 200
                    if item.productid == int(product_id) and item.status == 'Product has been shipped':
                        return jsonify({"error": "order already shipped"}), 400
                    # else:
                    #     pass
                    # return jsonify({"error": "you did not order this"}), 400
            except Exception as e:
                return jsonify({"error": f"{e}"}), 400

    return jsonify({"error": "you did not order this"}), 400



