from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    '''This form is for logins into the Poker Rooms'''
    
    username = StringField('Username', validators=[DataRequired()])
    
    password = PasswordField('Password', validators=[Length(min=6)])

class UserAddForm(FlaskForm):
    '''This form is for new users'''

    username= StringField('Username',validators=[DataRequired()])
    
    email =  StringField('E-mail', validators=[DataRequired()])
    
    password = PasswordField('Password', validators=[Length(min=6)])
    
    bio = TextAreaField('Optional - Tell us about yourself!')
    
    image_url = StringField('Optional - Upload profile picture')

class UserEditForm(FlaskForm):
    '''This form is to edit users in the Poker Rooms'''

    username = StringField('Username', validators=[DataRequired()])

    email = StringField('E-mail', validators=[DataRequired(), Email()])
    
    image_url = StringField('(Optional) Image URL')
    
    header_image_url = StringField('(Optional) Header Image URL')
    
    bio = TextAreaField('(Optional) Tell us about yourself')
    
    password = PasswordField('Password', validators=[Length(min=6)])

class MessageForm(FlaskForm):
    '''This form is to make messages in rooms'''

    text = TextAreaField('Share what you are up to...', validators=[DataRequired()])

class NewRoom(FlaskForm):

    room_name = StringField('Name the community', validators=[DataRequired()])

    room_description = TextAreaField('Describe the community', validators=[DataRequired()])

    profile_url = StringField('Optional - Upload community profile picture')

    header_image_url = StringField('Optional - Upload community cover picture')

class newGameRoom(FlaskForm):

    room_name = StringField('Game room name', validators=[DataRequired()])




