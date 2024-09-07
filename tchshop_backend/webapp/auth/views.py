import logging

from flask import Flask, render_template, url_for, flash, redirect, request, make_response, jsonify, session
from webapp.auth import auth_views
from webapp.forms import SigninForm, SignupForm
from flask_login import current_user
from datetime import datetime
from flask_login import login_user, logout_user, login_required
from models.user import User, Vcode
from webapp import db
from models.order import Coupon
from webapp.email import send_async_email, send_password_reset_code


@login_required
@auth_views.route('/@me')
def get_current_user():
    user_id = session.get("userId")
    if user_id:
        user = User.query.get(user_id)
        if user:
            return jsonify({
                "id": user.id,
                "username": user.firstname,
                "roles": len([role.to_dict() for role in user.roles]),
                "email": user.email
            }), 200
    return jsonify({"error": "User not authenticated"}), 401


@auth_views.route('/signup/<coupon>', methods=['POST'], strict_slashes=False)
def signup_coupon(coupon):
    data = request.json
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:

        return jsonify({'message': 'Username or email already exists'}), 400

    else:
        # Create new user
        new_user = User(
            firstname=data.get('firstname', ''),
            lastname=data.get('lastname', ''),
            email=data['email'],
            agree=True,  # Example: Assuming agree is a boolean field
            city=data.get('city', ''),
            state=data.get('state', ''),
            country=data.get('country', ''),
            street=data.get('street', ''),
            zipcode=data.get('zipcode', ''),
            phone=data.get('phone', '')
        )
        new_user.set_password(password=data['password'])
        # users.append(new_user)
        db.session.add(new_user)
        db.session.commit()

        if coupon:
            code = coupon
            user = User.query.filter_by(email=data['email']).first()
            new_coupon = Coupon(code=code, user_id=user.id, percentage='', status="pending")
            db.session.add(new_coupon)
            coupon_owner = Coupon.query.filter_by(code=code, status='minion').first()
            count = User.query.filter_by(id=coupon_owner.user_id).first()

            # all pending refs of a user
            owners_coupons = Coupon.query.filter_by(code=code, status='pending').all()
            # each minions count updated
            count.coupons_count = len(owners_coupons)
            db.session.commit()
        else:
            pass
            
        return jsonify({'message': 'User created successfully with coupon', 'user': new_user.email}), 201


@auth_views.route('/signup', methods=['POST'], strict_slashes=False)
def signup():
    data = request.json
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:

        return jsonify({'message': 'Username or email already exists'}), 400

    else:
        # Create new user
        new_user = User(
            firstname=data.get('firstname', ''),
            lastname=data.get('lastname', ''),
            email=data['email'],
            agree=True,  # Example: Assuming agree is a boolean field
            city=data.get('city', ''),
            state=data.get('state', ''),
            country=data.get('country', ''),
            street=data.get('street', ''),
            zipcode=data.get('zipcode', ''),
            phone=data.get('phone', '')
        )
        new_user.set_password(password=data['password'])
        # users.append(new_user)
        db.session.add(new_user)
        db.session.commit()

        if 'coupon' in session:
            code = session['coupon']
            user = User.query.filter_by(email=data['email']).first()
            new_coupon = Coupon(code=code, user_id=user.id, percentage='', status="pending")
            db.session.add(new_coupon)
            coupon_owner = Coupon.query.filter_by(code=code, status='minion').first()
            count = User.query.filter_by(id=coupon_owner.user_id).first()

            # all pending refs of a user
            owners_coupons = Coupon.query.filter_by(code=code, status='pending').all()
            # each minions count updated
            count.coupons_count = len(owners_coupons)
            db.session.commit()
        else:
            pass
            
        return jsonify({'message': 'User created successfully', 'user': new_user.firstname}), 201


@auth_views.route('/signin', methods=['GET', 'POST'], strict_slashes=False)
def signin():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    password = data['password']
    if user:
        if user.verify_password(password):
            login_user(user, remember=data.get('remember', True))

            # token = request.cookies
            logging.info(f"token:{user}")
            session["userId"] = user.id

            return jsonify({"Message": "Login Successful", "username": user.firstname, "email": user.email, "id": user.id, "roles": len([role.to_dict() for role in user.roles])}), 200
        return {"error": "Login failed Wrong password"}, 401
    return jsonify({"error": "Login failed"}), 401

@auth_views.route('/logout', strict_slashes=False, methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    session.clear()

    response = jsonify({"message": "User logged out"})
    response.set_cookie('session', '', expires=0)
    
    return response

@auth_views.route('/reset_password_request', methods=['GET'], strict_slashes=False)
def reset_password_request():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for('main.get_products'))
        return redirect(url_for('auth_views.reset_password_email')), 200

# enter email address to get reset code
@auth_views.route('/reset_password_email', methods=['POST'], strict_slashes=False)
def reset_password_email():
    if request.method == "POST":
        data = request.json
        email = data['email']
        if email:
            user = User.query.filter_by(email=email).first()
            check = Vcode.query.filter_by(user_id=user.id).first()
            if check:
                user.revoke_token()
            else:
                pass
            if user:
                session['u_email'] = email
                send_password_reset_code(user)
                # return jsonify({'success': 'code sent via email'}), 200
                return redirect(url_for('auth_views.confirm_vcode')), 201
            db.session.rollback()
            # return jsonify({"error": "failed to send code"}), 401

    return jsonify({"error": "provide a registered email for password reset"}), 404


# enter and verify code sent to email
@auth_views.route('/confirm_vcode', methods=['POST'], strict_slashes=False)
def confirm_vcode():
    data = request.json
    code = data['code']
    email = session['u_email']

    try:
        user = User.query.filter_by(email=email).first()
        reset_code = Vcode.query.filter_by(code=code).first()
        if user and reset_code:
            confirm = user.confirm(token=code)
            if confirm:
                user.revoke_token()
                # return jsonify({'success': 'enter new password'}), 200
                return redirect(url_for('auth_views.reset_password')), 200

        user.revoke_token()
        return jsonify({'error': 'code expired'}), 400

    except Exception as e:
        return jsonify({'error': f'{e}'}), 500


# enter new password
@auth_views.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    data = request.json
    password1 = data['password']
    password2 = data['confirm']
    email = session['u_email']
    user = User.query.filter_by(email=email).first()

    if password1 == password2:
        user.set_password(password1)
        db.session.commit()
        return redirect(url_for('auth_views.signin')), 201
    return jsonify({'error': 'password reset failed try again'}), 401

