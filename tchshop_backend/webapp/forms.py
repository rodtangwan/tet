from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, TelField, IntegerField, EmailField, SelectField, DateField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError
from models.user import User


class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 40), Email()])
    # username = StringField('Username', validators=[DataRequired(), Length(1, 40),
    #                                                Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
    #            'Usernames must have only letters, numbers, dots or '
    #            'underscores')])
    firstname = StringField('Firstname', validators=[DataRequired(), Length(1, 40)])
    lastname = StringField('Lastname', validators=[DataRequired(), Length(1, 40)])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    agree = BooleanField('I agree')
    submit = SubmitField('Sign Up')


    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Email already exist, try another')


class SigninForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log In')


class UpdateProfileForm(FlaskForm):
    firstname = StringField( 'First Name' )#,default=User.firstname
    lastname = StringField( 'Last Name' )#,default=User.lastname
    city = StringField( 'City', validators=[])
    email = EmailField( 'Email', validators=[])
    phone = TelField( 'Phone Number', validators=[])
    state = StringField( 'State', validators=[])
    Country = StringField( 'Country', validators=[])
    zipcode = StringField( 'Zipcode', validators=[])

    submit = SubmitField('Update')


# class AddProductForm(FlaskForm):