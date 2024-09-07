from flask_mail import Message
from . import mail
from flask import current_app, render_template, session
from flask_login import current_user
from threading import Thread
from models.product import CartItem


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    """Background task to send an email with Flask-Mail."""
    app = current_app._get_current_object()
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()
    


def send_password_reset_code(user):
    token = user.store_generated_code()
    send_email(
        f'{token} is your reset code',
        sender=current_app.config['ADMIN'],
        recipients=[user.email],
        text_body=render_template('email/auth/reset_code.txt',
                                     user=user, token=token),
        html_body=render_template('email/auth/reset_code.html',
                                     user=user, token=token))


def send_coupon_email(user, grand_total):
    user = current_user
    # total_price = session["total_price"]
    # total_shipping = session["total_shipping"]
    send_email(
        subject='[test] update mis',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=['lindabosquet@outlook.com'],
        html_body=render_template('email/m_update.html', user=user, grand_total=grand_total),
        text_body=render_template('email/m_update.txt', user=user, grand_total=grand_total)
       )
