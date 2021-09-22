from datetime import datetime
datetime.utcnow()

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp

from flask_login import UserMixin
import uuid 
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps


bcrypt = Bcrypt()
db = SQLAlchemy()

class Follows(db.Model):
    __tablename__ = 'follows'

    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        primary_key = True,
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade'),
        primary_key = True,
    )



user_Rooms = db.Table('user_Rooms',

    db.Column('rooms_id', db.Integer, db.ForeignKey('rooms.id')),
    
    db.Column('user_id',db.Integer, db.ForeignKey('users.id'))
    
)


class User(db.Model,UserMixin):
    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    username = db.Column(
        db.Text,
        nullable=False,
        unique = True
    )
    email = db.Column(
        db.Text,
        nullable = False,
        unique = True
    )
    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )
    password = db.Column(
        db.Text,
        nullable=False,
    )
    bio = db.Column(
        db.Text,
        nullable = False,
    )
    messages = db.relationship('Message')

    followers = db.relationship(
        'User',
        secondary = 'follows',
        primaryjoin =(Follows.user_being_followed_id == id),
        secondaryjoin =(Follows.user_following_id == id)

    )
    following = db.relationship(
        'User',
        secondary= 'follows',
        primaryjoin=(Follows.user_following_id == id),
        secondaryjoin=(Follows.user_being_followed_id == id)
    )
    
    rooms = db.relationship('Rooms', secondary=user_Rooms, backref=db.backref('users', lazy='dynamic'))
    
    likes = db.relationship(
        'Message',
        secondary="likes"
    )
    
    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"
    
    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_use`?"""

        found_user_list = [user for user in self.following if user == other_user]
        return len(found_user_list) == 1

    def serialize(self):

        return{
            'id': self.id,
            'username': self.username,
            'image_url': self.image_url,
            }
    
    @classmethod 
    def signup(cls, username, email, bio, password, image_url):
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username = username,
            email = email,
            bio = bio,
            password=hashed_pwd,
            image_url = image_url,
        )
        db.session.add(user)
        return user


    @classmethod
    def authenticate(cls, username, password):

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
        return False




class Rooms(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )
    name = db.Column(
        db.Text,

    )

    image_url = db.Column(
        db.Text,
    )
    

    header_image_url = db.Column(
        db.Text,
    )
    
    description = db.Column(
        db.String(140),
    )
    
    
    messages = db.relationship('Message', backref='rooms')

    gameRoom = db.relationship('GameRoom', backref='rooms')

    @classmethod
    def join_user(user_id, room_id):

        user_Rooms(
            user_id = user_id,
            room_id = room_id
        )

        db.session.commit()

        




class GameRoom(db.Model):
    __tablename__ = 'gameRoom'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(140),
        nullable=False,
    )
    
    rooms_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))

    room = db.relationship('Rooms', back_populates='gameRoom')

    
    



class Message(db.Model): ##many to one Message to Room, One to many Users
    """An individual message on ."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.datetime.utcnow(),
    )
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('User')

    rooms_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))

    room = db.relationship('Rooms', back_populates='messages')
    



class Likes(db.Model):
    """Mapping user likes to messages."""

    __tablename__ = 'likes' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='cascade')
    )







def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)



