import os
import random
import string
from config import Config
from flask import render_template, url_for, abort, redirect, request, flash, jsonify, current_app, render_template_string
from . import admin
from models.user import Role, User, Cart
from flask_login import login_required, current_user
from models.product import Product, Category, Review, Shipping, ReviewImage, ProductImage, ProductColor,\
    DescriptionImage, Description, CartItem
from models.order import Order, Coupon, Wallet
from webapp.auth import has_role
from webapp import db
import re
from datetime import datetime
from werkzeug.utils import secure_filename
import logging


# Configure logging to display messages to the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

# admin base route
# @login_required
@admin.route('/base', methods=["GET", "POST"], strict_slashes=False)
@has_role('administrator')
def base():
    users = User.query.all()
    roles = Role.query.all()
    products = Product.query.all()

    return jsonify({"Message": "Admin route success"}), 201


# create product category
@login_required
@admin.route('/create_category', methods=['POST'])
@has_role('administrator')
def create_category():
    data = request.json
    # # Check if category already exists
    categories = Category.query.filter_by(category_name=data['category_name']).first()
    if categories:
        return jsonify({'error': 'category_name exists parameter'}), 400
    new_category = Category(category_name=data['category_name'])
    db.session.add(new_category)
    db.session.commit()
    return jsonify({"Message": "create_category successful", "Data": new_category.category_name}), 201


# get category
@login_required
@admin.route('/category/<int:category_id>', methods=['POST'])
@has_role('administrator')
def category(category_id):
    cat = Category.query.filter_by(id=category_id).first()
    if cat:
        return jsonify({"Category": cat.category_name}), 200
    return jsonify({"error": "Category does not exist"}), 403


# assign a category
@login_required
@admin.route('/assign_category', methods=["PUT", "POST"], strict_slashes=False)
@has_role('administrator')
def assign_category():
    data = request.json
    all_cat = Category.query.all()
    all_prod = Product.query.all()
    product_name = data["product_name"]
    category_to_assign = data["category_to_assign"]
    product = Product.query.filter_by(product_name=data["product_name"]).first()
    if product is None:
        return {"error": "Product does not exist"}, 403

    category = Category.query.filter_by(category_name=data["category_to_assign"]).first()
    logging.info(f"Category: {category}")
    logging.info(f"Product: {product}")

    categories = product.prod_cat
    for cate in categories:
        if category_to_assign in cate.category_name:
            return {"error": "Category already exist for the Product"}, 403
    # for all_c in all_cat:
    if category_to_assign != category.category_name:
        return {"error": "Category does not exist"}, 403
    product.add_cat_to_prod(product_name, category_to_assign)
    db.session.commit()
    return {"Message": f"Category {category_to_assign} added to Product: {product.product_name} successfully"}, 201


@login_required
@admin.route('/delete_category/<id>', methods=['DELETE'], strict_slashes=False)
@has_role('administrator')
def delete_category(id):
    # get category by id
    cat = Category.query.filter_by(id=id).first()
    if cat:
        db.session.delete(cat)
        db.session.commit()
        return jsonify({"Message": "Delete_category successful", "Category": cat.category_name}), 201

    return {"Message": "Category does not exist"}, 400


# delete role from a particular user
@login_required
@admin.route('/delete_role/<id>', methods=["DELETE"], strict_slashes=False)
@has_role('administrator')
def admin_delete_role(id):
    roles = Role.query.all()
    delete_id = Role.query.get(id)
    if delete_id:
        db.session.delete(delete_id)
        db.session.commit()
        return {"Message": f"Role {delete_id.name} deleted"}, 200
    return {"Error": "No such role"}, 403


# create roles to users
@login_required
@admin.route('/create_role', methods=["GET", "POST"], strict_slashes=False)
@has_role('administrator')
def create_role():
    all_roles = Role.query.all()
    data = request.json
    if len(all_roles) <= 4:
        role_name = data['name']
        for i in all_roles:
            if i.name == role_name:
                return {"Message": "Role already exist!"}, 403
        new_role = Role(name=role_name)
        db.session.add(new_role)
        db.session.commit()
        return {"Message": "Role added successfully!"}, 201
    return {"Message": "Roles greater than 4"}, 401


# assign roles to users
@login_required
@admin.route('/assign_role', methods=["PUT"], strict_slashes=False)
@has_role('administrator')
def assign_role():
    data = request.json
    email = data["email"]
    role_to_assign = data["role_to_assign"]
    user = User.query.filter_by(email=data["email"]).first_or_404()
    roles = user.roles
    logging.info(f"Roles for the user: {roles}")
    for role in user.roles:
        if role_to_assign in role.name:
            return {"error": "rolename already exists"}, 403

    if email and role_to_assign:
        user.add_role_to_user(email, role_to_assign)
        return {"Message": f"Role {role_to_assign} added to User: {user.email} successfully"}, 201
    return {"error": "User or rolename does not exists"}, 403


# Product route
@login_required
@admin.route('/addproduct', methods=['POST'], strict_slashes=False)
@has_role('administrator')
def addproduct():
    new_product_data = request.form
    image = request.files['file']
    existing_product = Product.query.filter_by(product_name=new_product_data['product_name']).first()
    
    if existing_product:
        return jsonify({'error': 'Product with this name already exists'}), 403

    product_name = new_product_data['product_name']

    # Save the uploaded image with a unique filename
    name = secure_filename(image.filename)
    filename = f"{product_name}_{name}"
    logging.info(f"Saving image with filename: {filename}")

    if name != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        
        # Save the image file
        image.save(os.path.join(current_app.config['SINGLE_PRODUCT_UPLOAD_PATH'], filename))
        
        # Create a new Product instance
        new_product = Product(
            product_name=product_name,
            product_image=filename,
            quantity=new_product_data["quantity"],
            regular_price=new_product_data["regular_price"],
            discounted_price=new_product_data["discounted_price"],
            description=new_product_data["description"]
        )
        
        db.session.add(new_product)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to add product: {str(e)}'}), 500
        
        # Return a success response with the product ID
        return jsonify({
            "Message": "Product added successfully",
            "Product name": product_name,
            "id": new_product.id
        }), 201
    
    return jsonify({'error': 'Invalid image file'}), 400

# add description to a product
@login_required
@admin.route('/addProductDescription/<int:id>', methods=['POST'], strict_slashes=False)
@has_role('administrator')
def addDescription(id):
    data = request.form
    description_images = request.files.getlist('file')
    logging.info(f"len img description {len(description_images)}")

    # Find the product by ID
    product = Product.query.get(id)
    if product is None:
        return jsonify({'error': 'Product does not exist'}), 403

    # Retrieve the saved product description if it exists
    prod_description = Description.query.filter_by(product_id=product.id).first()
    if prod_description and len(description_images) == 0:
        prod_description.specifications = data['specifications']
        db.session.commit()
        return jsonify({'Message': 'Description specification updated successfully'})

    specifications = data['specifications']

    # Create and save the product description
    product_description = Description(specifications=specifications, product_id=product.id)
    db.session.add(product_description)
    db.session.commit()

    # Retrieve the saved product description
    prod_description = Description.query.filter_by(product_id=product.id).first()
    logging.info(f"description {prod_description}")

    # Handle the uploading of images if they are within the allowed range
    if (1 <= len(description_images)) and (len(description_images) <= 5):
        for uploaded_file in description_images:
            name = secure_filename(uploaded_file.filename)
            filename = f"{product.product_name}_{name}"

            if name != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in current_app.config['DESCRIPTION_UPLOAD_EXTENSIONS']:
                    abort(400)

                # Create and save the description image record
                des_img = DescriptionImage(image_name=filename, description_id=prod_description.id, product_id=product.id)
                db.session.add(des_img)
                db.session.commit()

                # Save the file to the specified path
                uploaded_file.save(os.path.join(current_app.config['DESCRIPTION_UPLOAD_PATH'], filename))

    return jsonify({'Message': f'Description successfully added for {product.product_name}'}), 201

# delete description of a product
@login_required
@admin.route('/delete_product_description/<int:id>', methods=["DELETE"], strict_slashes=False)
@has_role('administrator')
def admin_delete_product_description_img(id):
    # Find the product by ID
    product = Product.query.get(id)

    if not product:
        return jsonify({'error': 'Product does not exist'}), 404

    if request.method == 'DELETE':
        # Retrieve all description images associated with the product
        product_description_images = DescriptionImage.query.filter_by(product_id=product.id).all()

        # Delete each image record
        for image in product_description_images:
            db.session.delete(image)
        db.session.commit()

        # Verify if any images are left after deletion
        remaining_images = DescriptionImage.query.filter_by(product_id=product.id).all()
        images = [image.to_dict() for image in remaining_images]

        return jsonify({
            'status': 'success',
            'product_name': product.product_name,
            'images_available': images
        }), 200

    return jsonify({'error': 'Delete failed'}), 400

# update product description detailed version
@login_required
@admin.route('/update_product_description/<int:id>', methods=["PUT"], strict_slashes=False)
@has_role('administrator')
def admin_update_product_description_img(id):
    # Retrieve the product using the product ID
    product = Product.query.get(id)
    data = request.json

    if product is None:
        return jsonify({'error': 'Product does not exist'}), 404

    if request.method == 'PUT':
        # Retrieve the existing product description
        product_description = Description.query.filter_by(product_id=product.id).first()
        
        if not product_description:
            return jsonify({'error': 'Description does not exist for this product'}), 404

        # Update the specifications field
        product_description.specifications = data.get('specifications')
        db.session.commit()

        # Fetch the updated product description
        updated_description = Description.query.filter_by(product_id=product.id).first()

        return jsonify({
            'status': 'success',
            'message': f'Description updated for {product.product_name}',
            'product_description': updated_description.to_dict()
        }), 200

    db.session.rollback()
    return jsonify({'error': 'Update failed'}), 400

# add images to a product
@login_required
@admin.route('/addProductImage/<int:id>', methods=['POST'], strict_slashes=False)
@has_role('administrator')
def addImage(id):
    product_images = request.files.getlist('file')
    logging.info(f"len img review {len(product_images)}")

    # Retrieve the product using the product ID
    product = Product.query.get(id)
    if product is None:
        return jsonify({'error': 'Product does not exist'}), 403

    if len(product_images) >= 1 and len(product_images) <= 7:
        logging.info(f"prod {product}")
        for uploaded_file in product_images:
            name = secure_filename(uploaded_file.filename)
            filename = product.product_name + '_' + name

            if name != '':
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
                    abort(400)
                
                # Create and save the product image record
                prod_img = ProductImage(image=filename, product_id=product.id)
                db.session.add(prod_img)
                db.session.commit()

                # Save the file to the specified path
                uploaded_file.save(os.path.join(current_app.config['PRODUCT_IMAGE_UPLOAD_PATH'], filename))

    # Query all images associated with the product
    product_images = ProductImage.query.filter_by(product_id=product.id).all()
    logging.info(f"prod images {product_images}")

    return jsonify({'Message': "Product Image(s) Successfully added"}), 200

# delete product images
@login_required
@admin.route('/delete_product_images/<int:id>', methods=["DELETE"], strict_slashes=False)
@has_role('administrator')
def admin_delete_product_images(id):
    product = Product.query.get(id)

    if product is None:
        return jsonify({'error': 'Product does not exist'}), 404

    if request.method == 'DELETE':
        # Retrieve and delete all product images associated with the product ID
        product_images = ProductImage.query.filter_by(product_id=product.id).all()
        for image in product_images:
            db.session.delete(image)
        db.session.commit()

        # Verify if any images still exist for the product
        product_images = ProductImage.query.filter_by(product_id=product.id).all()
        images = [image.to_dict() for image in product_images]

        return jsonify({'status': 'success', 'product_name': product.product_name, 'images_available': images})

    return jsonify({'error': 'Delete failed'}), 400

# add product color
@login_required
@admin.route('/addProductColor/<int:id>', methods=['POST'], strict_slashes=False)
@has_role('administrator')
def colors_available(id):
    data = request.get_json()
    colors = data.get("name")
    logging.info(f'{colors}, type{type(colors)}')

    product = Product.query.get(id)

    if product is None:
        return jsonify({'error': 'Product does not exist'}), 404

    # Check the number of existing colors for this product
    present_colors = ProductColor.query.filter_by(product_id=product.id).all()
    if len(present_colors) >= 6:
        return jsonify({"error": "Consider clearing all previous colors for this product"}), 400

    # Validate the colors input
    if not colors or not isinstance(colors, list):
        return jsonify({"error": "Invalid JSON data; 'name' should be a list of colors"}), 400

    # Add new colors to the product
    for name in colors:
        product_color = ProductColor(color=name, number=random.choice(range(20)), product_id=product.id)
        db.session.add(product_color)

    try:
        db.session.commit()
        return jsonify({'message': 'Colors added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# view products colors
@login_required
@admin.route('/view_product_color/<int:id>', methods=["GET"], strict_slashes=False)
@has_role('administrator')
def admin_view_product_colors(id):
    # Find the product by ID
    product = Product.query.get(id)
    
    if product is None:
        return jsonify({'error': 'Product does not exist'}), 404
    
    if request.method == 'GET':
        # Retrieve colors for the product
        product_colors = ProductColor.query.filter_by(product_id=product.id).all()
        colors = [color.to_dict() for color in product_colors]
        
        return jsonify({
            'product_name': product.product_name,
            'product_id': product.id,
            'colors_available': colors
        }), 200

# delete product colors
@login_required
@admin.route('/delete_product_color/<int:id>', methods=["DELETE"], strict_slashes=False)
@has_role('administrator')
def admin_delete_product_colors(id):
    # Find the product by ID
    product = Product.query.get(id)

    if product is None:
        return jsonify({'error': 'Product does not exist'}), 404

    if request.method == 'DELETE':
        # Retrieve and delete colors for the product
        product_colors = ProductColor.query.filter_by(product_id=product.id).all()
        for color in product_colors:
            db.session.delete(color)
        db.session.commit()

        # Verify colors have been deleted
        product_colors = ProductColor.query.filter_by(product_id=product.id).all()
        
        return jsonify({
            'status': 'success',
            'product_id': product.id,
            'product_name': product.product_name,
            'colors_available': [color.to_dict() for color in product_colors]  # Ensure to_dict() is defined
        }), 200

    return jsonify({'error': 'delete failed'}), 400

# delete product
@login_required
@admin.route('/delete_product/<id>', methods=["DELETE"], strict_slashes=False)
@has_role('administrator')
def admin_delete_product(id):
    cart_item = CartItem.query.filter_by(product_id=id).all()
    # colors = ProductColor.query.filter_by(product_id=id).delete()

    delete_id = Product.query.get(id)
    if delete_id:
        for prod in cart_item:
            db.session.delete(prod)
        # for col in colors:
        #     db.session.delete(col)
        admin_delete_product_description_img(delete_id.product_name)
        admin_delete_product_colors(delete_id.id)
        admin_delete_product_images(delete_id.product_name)
        # delete_id.delete_user_role(id=delete_id)
        db.session.delete(delete_id)
        db.session.commit()
        flash(f"User {delete_id.product_name}'s Product deleted")
        return jsonify({"message": f"User {delete_id.product_name}'s Product deleted"})
    return jsonify({"error": "Product not found"})

# shipping
# add_shipping methods and price
@login_required
@admin.route('/addShipping', methods=['POST'], strict_slashes=False)
@has_role('administrator')
def add_shipping():
    data = request.json
    cost = data.get('cost')
    name = data.get('name')
    deliveryTime = data.get('deliveryTime')
    shipping = Shipping.query.filter_by(name=name).first()
    if shipping:
        return jsonify({"message": f"Shipping method already exist"})
    elif cost and name:
        shipping_name = Shipping(name=name, cost=cost, deliveryTime=deliveryTime)
        db.session.add(shipping_name)
        db.session.commit()
        return jsonify({"message": f"Shipping method added"})
    db.session.rollback()
    return jsonify({"error": f"Failed to add fill all fields correctly"})


# delete shipping method
@login_required
@admin.route('/delete_shipping/<name>', methods=["DELETE"], strict_slashes=False)
@has_role('administrator')
def admin_delete_shipping(name):
    delete_id = Shipping.query.filter_by(name=name).first()
    if delete_id:
        db.session.delete(delete_id)
        db.session.commit()
        return {"Message": f"Shipping {delete_id.name} deleted"}, 200
    return {"Error": "No such shipping"}, 403


# update shipping cost
@login_required
@admin.route('/update_shipping_cost/<id>', methods=["PUT"], strict_slashes=False)
@has_role('administrator')
def admin_update_shipping_cost(id):
    shipping = Shipping.query.filter_by(id=id).first()
    data = request.json
    if request.method == "PUT":
        if shipping:
            shipping.cost = data["cost"]
            db.session.commit()
            return {"Message": f"Shipping cost for {shipping.name} updated"}, 201

    return {"Error": "No such shipping"}, 403


# get shippings with product id arg
@login_required
@admin.route('/shipping', methods=['GET'], strict_slashes=False)
@has_role('administrator')
def all_shipping():
    available_methods = Shipping.query.all()
    all_methods = [{"id": ship.id, "deliveryTime": ship.deliveryTime, "cost": ship.cost
                    , "name": ship.name} for ship in available_methods]
    return jsonify(all_methods), 200


# add reviews
@login_required
@admin.route('/addReview/<int:product_id>', methods=['GET', 'POST'], strict_slashes=False)
@has_role('administrator')
def add_review(product_id):
    data = request.form
    review_images = request.files.getlist('file')
    logging.info(f"len img review {len(review_images)}")

    user = current_user.id
    product = Product.query.get_or_404(product_id)
    rating = data['rating']
    review = data['review']

    if current_user:
        product_review = Review(product_rating=rating, product_review=review, timestamp=datetime.utcnow())
        product_review.productid = product.id
        product_review.user_id = user
        db.session.add(product_review)
        db.session.commit()
        prod_reviews = Review.query.filter_by(productid=product.id).first()
        # logging.info(f"review {prod_reviews}")
        # return jsonify({'Message': "Successfully reviewed"}), 200

        if len(review_images) >= 1 and (len(review_images) <= 5):
            # prod_reviews = Review.query.filter_by(productid=product.id).first()
            logging.info(f"prod review {prod_reviews}")

            for uploaded_file in review_images:
                name = secure_filename(uploaded_file.filename)
                filename = product.product_name + '_' + name

                if name != '':
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext not in current_app.config['UPLOAD_EXTENSIONS']:
                        abort(400)
                    prod_reviews_img = Review.query.order_by(Review.timestamp.desc()).first()

                    rev_img = ReviewImage(image=filename, review_id=prod_reviews_img.id, product_id=product_id)
                    db.session.add(rev_img)
                    db.session.commit()
                    # image.append(filename)
                    # logging.info(f"all images: {image}")
                uploaded_file.save(os.path.join(current_app.config['REVIEW_UPLOAD_PATH'], filename))
        #     image.append(filename)
        # u = ReviewImage.query.filter_by(review_id=prod_reviews.id)
        return jsonify({'Message': "Successfully reviewed"}), 200
    db.session.rollback()
    return jsonify({'error': 'review failed'}), 404



# update reviews times
@login_required
@admin.route('/addReviewDates/<id>', methods=['GET', 'POST'], strict_slashes=False)
@has_role('administrator')
def update_review_dates(id):
    # data = request.get_json()
    # prod_reviews = Review.query.all()
    product = Product.query.get(id)
    if product:
        # Read the datetime values from the file
        datetime_list = []
        try:
            BASEDIR = os.path.dirname(os.path.abspath(__file__))
            FILEPATH = os.path.join(BASEDIR, 'rev.txt')
            # logging.info(f'{FILEPATH}')
          
            with open(FILEPATH, 'r') as file:
                content = file.readlines()
                # strip each newline from each line
                new_list = [line.strip() for line in content]
                datetime_list = new_list
                # logging.info(f'{new_list}')
            all_reviews = Review.query.filter_by(productid=id).all()
            rev_len = len(datetime_list)
            for review in all_reviews:
                try:
                    for i in range(len(all_reviews)):
                        logging.info(f'{type(datetime.strptime(datetime_list[i], "%Y-%m-%d %H:%M:%S"))}')

                        review.timestamp = datetime.strptime(datetime_list[random.choice(range(rev_len))], "%Y-%m-%d %H:%M:%S")
                        return jsonify({"success": "Time updated successfully"}), 200
                except Exception as e:
                    return jsonify({"error": f"{e}"}), 404
            db.session.commit()
    
            

        except FileNotFoundError:
            return "File not found.", 404
        # reviews = []     
    # return render_template_string('{{content}}', content=content), 200
    
    
        
@login_required
@admin.route('/generateCoupon', methods=['GET', 'POST'], strict_slashes=False)
@has_role('administrator')
def generate():
    data = request.json
    email = data["email"]
    percentage = data.get('percentage', 20)
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "user does not exist"}), 404
    if_user = Coupon.query.filter_by(user_id=user.id).first()
    if if_user:
        return jsonify({"message": "user already has a coupon"}), 404

    def gen(length=6):
        character = string.ascii_uppercase + string.digits
        return ''.join(random.choice(character) for _ in range(length))
    coupon = gen()
    user_coupon = Coupon(code=coupon, user_id=user.id, percentage=percentage, status="minion")
    db.session.add(user_coupon)
    logging.info(f"coupon {type(coupon)}")
    # user.coupons = coupon
    db.session.commit()
    users_coupon = Coupon.query.filter_by(user_id=user.id).first()
    return jsonify({"success": f"{users_coupon.code}"}), 201


# delete user coupon
@login_required
@admin.route('/deleteCoupon/<email>', methods=['DELETE'], strict_slashes=False)
@has_role('administrator')
def delete_user_coupon(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "user does not exist"}), 404

    users_coupon = Coupon.query.filter_by(user_id=user.id, status='minion').first()
    if not users_coupon:
        return jsonify({"error": "user not minion"}), 404

    logging.info(f"users coup {users_coupon.to_dict()}")
    db.session.delete(users_coupon)
    db.session.commit()
    return jsonify({"success": "all coupons deleted"}), 200


# delete all coupons
@login_required
@admin.route('/deleteCoupon', methods=['DELETE'], strict_slashes=False)
@has_role('administrator')
def delete_all_coupons():
    coupons = Coupon.query.delete()
    return jsonify({"success": "all coupons deleted"}), 200


# view all coupons
@login_required
@admin.route('/viewCoupons', methods=['GET'], strict_slashes=False)
@has_role('administrator')
def view_all_coupons():
    coupons = Coupon.query.all()
    c = [coup.to_dict() for coup in coupons]
    return jsonify(c), 200


# add wallet addresses
@login_required
@admin.route('/addWallet', methods=['POST'], strict_slashes=False)
@has_role('administrator')
def add_wallet():
    data = request.json
    currency_type = data['currency_type']
    address = data['address']
    logging.info(f"{currency_type.upper()}")
    if currency_type.upper() != "USDT" and currency_type.upper() != "USDC":
        return jsonify({"error": "only USDT or USDC accepted"}), 400
    if not isinstance(address, str) or len(address) < 12:
        return jsonify({"error": "provide a valid address"}), 400
    try:
        new_wallet = Wallet(currency_type=currency_type, address=address)
        db.session.add(new_wallet)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "addresses must be unique"}), 400
    return jsonify({"success": f"{currency_type} wallet added"}), 200


@login_required
@admin.route('/viewWallets', methods=['GET'], strict_slashes=False)
@has_role('administrator')
def list_wallets():
    wallets = Wallet.query.all()
    all = [wallet.to_dict() for wallet in wallets]
    return jsonify(all), 200



# START CART MODULE
# Gets products in the cart
# def getusercartdetails():
#     userId = User.query.with_entities(User.userid).filter(User.email == session['email']).first()
#
#     productsincart = Product.query.join(Cart, Product.productid == Cart.productid) \
#         .add_columns(Product.productid, Product.product_name, Product.discounted_price, Cart.quantity, Product.image) \
#         .add_columns(Product.discounted_price * Cart.quantity).filter(
#         Cart.userid == userId)
#     totalsum = 0
#
#     for row in productsincart:
#         totalsum += row[6]
#
#     tax = ("%.2f" % (.06 * float(totalsum)))
#
#     totalsum = float("%.2f" % (1.06 * float(totalsum)))
#     return (productsincart, totalsum, tax)

