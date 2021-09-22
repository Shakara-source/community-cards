from app import db
from models import User, Rooms, Message, Follows, Likes


db.drop_all()
db.create_all()

user1 = User(
            username = 'PokerFace1',
            email = '123@abc.com',
            bio = 'Cant beat the king',
            password= 'ABC123' ,
            image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Aachen_Domschatz_Bueste1.jpg/800px-Aachen_Domschatz_Bueste1.jpg'
)

db.session.add_all([user1])
db.session.commit()
