import os
import json
import functools

from flask import Flask, render_template, request, flash, redirect, session, g, abort, jsonify

from war_game_classes.players import Player
from war_game_classes.game import Game

# from game import Game
# from players import Player

from collections import defaultdict

from flask_login import (
    LoginManager,
    current_user,
    login_manager,
    login_required,
    login_user,
    logout_user,
)

from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from flask_sqlalchemy import SQLAlchemy

from flask_socketio import Namespace, SocketIO, join_room, leave_room, send, emit, disconnect



from forms import UserAddForm, UserEditForm, LoginForm, MessageForm, NewRoom, newGameRoom
from models import db, connect_db, User, Rooms, Message, Follows, Likes, GameRoom

from flask_cors import CORS

CURR_USER_KEY = "curr_user"

app = Flask(__name__, template_folder='front-end/templates')

CORS(app)

socketio = SocketIO()
socketio.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgres:///communityCards'))


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")



if __name__ == '__main__':
    socketio.run(app)


connect_db(app)



@login_manager.user_loader
def load_user(users_id):
    try:
        return User.query.get(int(users_id))
    except:
        return None


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

@app.route('/')
def land_page():
    if current_user.is_authenticated:
        return redirect('/main')
    else:
        return redirect('/login')

@app.route('/signup', methods=["GET", "POST"])
def signup():

    if current_user.is_authenticated:
        flash('You are already logged in!')
        return redirect('/')
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                bio = form.bio.data,
                image_url=form.image_url.data or User.image_url.default.arg,

            )
            
            db.session.add(user)
            db.session.commit()
        
        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('user-profiles/login.html', form=form)
        
        login_user(user)

        return redirect('/main')

    else:
        return render_template('user-profiles/login.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in!')
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        
        user = User.authenticate(form.username.data, form.password.data)
        
        if user:
            login_user(user)
            flash(f"Hello Honorable {user.username}!", "success")
            return redirect('/')
        
        flash('Login Failed, Try again!','danger')
    
    return render_template('user-profiles/login.html', form=form)



@app.route('/logout')

def logout():


    logout_user()


    flash("You have successfully logged out.", 'success')
    return redirect("/login")


@app.route('/main')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if current_user.is_authenticated:

       


        rooms = (Rooms
                     .query
                     .limit(20)
                     .all())
        
        users = (User.query.limit(20).all())

        

        return render_template('rooms/homepage.html', users =users, rooms=rooms)
    else:
        return render_template('home-anon.html')


@app.route('/rooms', methods=['GET'])
def get_rooms():

    if not current_user.is_authenticated:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    rooms = Rooms.query.all()
    

    return render_template('rooms/showAll.html', rooms=rooms)



@app.route('/rooms/new', methods=['GET','POST'])
def new_room():

    if not current_user.is_authenticated:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
        
    form = NewRoom()
    
    if form.validate_on_submit():
            
        room = Rooms(name=form.room_name.data, description=form.room_description.data, 
        image_url= form.profile_url.data, header_image_url = form.header_image_url.data)
        
        current_user.rooms.append(room)
        db.session.commit()
        
        return redirect(f"/rooms/{room.id}")
    
    return render_template('Rooms/new.html',form=form)

@app.route('/rooms/join/<int:rooms_id>',methods=['POST'])
def join_user(rooms_id):

    if not current_user.is_authenticated:
        flash('Acess Unauthorized', 'danger')
        return redirect('/')
    
    user_id = current_user.id

    room_id = Rooms.query.get_or_404(rooms_id)

    Rooms.join_user(user_id,room_id)


    return redirect(f'/rooms/{rooms.id}')


@app.route('/rooms/<int:rooms_id>', methods=['GET', 'POST'])
def room_view(rooms_id):

    if not current_user.is_authenticated:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    message_form = MessageForm()
    game_room_form = newGameRoom()
    
    room = Rooms.query.get_or_404(rooms_id)
    members = [Users.id for Users in room.users]
    gameRooms = [gameRoom.id for gameRoom in room.gameRoom]
   
  
    
    
    if message_form.validate_on_submit():
        
        message = Message(user_id= current_user.id, rooms_id= room.id, text= message_form.text.data) 
        current_user.messages.append(message)
        db.session.commit()

    elif game_room_form.validate_on_submit():
        
        new_game = GameRoom(name = game_room_form.room_name.data, rooms_id = room.id)
        room.gameRoom.append(new_game)
        
        db.session.commit()

        return redirect(f"/rooms/{room.id}")

    return render_template('Rooms/show.html', room=room, members=members, message_form= message_form, gameRooms=gameRooms, game_room_form=game_room_form)

@app.route('/gameroom/<int:gameRoom_id>')
def joinGame(gameRoom_id):

    if not current_user.is_authenticated:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = current_user
    room = GameRoom.query.get_or_404(gameRoom_id)


    return render_template('card-game/game.html', user=user, room=room)



games = []
connections = []

@socketio.on('lobby', namespace = '/war')
@authenticated_only
def lobby(data):

    user_id = current_user.id
    username = current_user.username
    user_image = current_user.image_url
    socket = request.sid
    room = int(data['room_id'])


    lobby =[]

    userHTML = {'id':user_id,'room':room,'profile':"<div id="+str(user_id)+"><img src="+str(user_image)+" width='100' height='100'><img><h1>"+str(username)+"</h1></div>"}

    connections.append(userHTML)
    
    for user in connections:
        
        if user['room'] == room:

            if user not in lobby:
    
                lobby.append(user)
    
    join_room(room)

    emit('enterLobby',{'user_id': user_id,'lobby': lobby}, to=room)

@socketio.on('exitLobby', namespace = '/war')
@authenticated_only
def leave_lobby(data):

    room = int(data['room_id'])
    
    user_id = current_user.id

    for user in connections:
        if user['room'] == room and user['id'] == user_id:
            connections.remove(user)
    
    lobby = []



    for user in connections:
        if user['room'] == room:
            if user not in lobby:
                lobby.append(user)
    
    print(lobby)

    leave_room(room)

    emit('enterLobby',{'lobby':lobby}, to=room)
    


    

    

@socketio.on('register', namespace = '/war')

@authenticated_only
def register_player(data):

    username = current_user.username
    user_image = current_user.image_url
    socket = socketio
    room_id = data['room_id']
    idx = None
     
    
    if len(rooms) > 0:
        for room in enumerate(rooms):
            if room[1].id == room_id:
                idx = room[0]
    
    if len(rooms) != 0:
        cur_game = rooms[idx]


    if len(rooms) == 0:

        print('11')
        game = Game(room_id)
        game.add_player(username, user_image, socket)
        rooms.append(game)
        player1 = game.players[0]
        
        emit('pending', {'username': player1.username,'image': player1.image})
        

    elif len(cur_game.players) == 1:

        print('P2','loading...')
        
        cur_game.add_player(username, user_image, socket)


        if len(cur_game.players) == 1:
            player1 = cur_game.players[1]
           
            emit('pending', {'username2': player1.username,'image2': player1.image})




# @socketio.on('start', namespace= '/war')
# def startgame(data):
    
#     user_id = current_user.id
#     username = current_user.username
#     user_image = current_user.image_url
#     room = int(data['room_id'])
#     socket = request.sid
#     player = Player(user_id,username,user_image,socket)
#     playerJson = player.toJson


    
    # username = current_user.username
    # user_image = current_user.image_url
    # room = int(data['room_id'])
    # idx = None

    # player = Player(user_id,username,user_image,socket)
    # playerJson = player.toJson

    # if len(rooms) > 0:
    #     for room in enumerate(rooms):
    #         if room[1].id == room_id:
    #             idx = room[0]
    
    # if len(rooms) != 0:
    #     cur_game = rooms[idx]


    # if len(rooms) == 0:

    #     print('11')
    #     game = Game(room_id)
    #     game.add_player(username, user_image, socket)
    #     rooms.append(game)
    #     player1 = game.players[0]
        
    #     emit('pending', {'username': player1.username,'image': player1.image})
    

    


    # game = rooms[data['idx']]
    # game.start_game()

# @socketio.on('deal', namespace= '/war')


# @socketio.on('end', namespace= '/war')



     














# @app.route('/game/new/<int:rooms_id>')
# def newGameRoom(rooms_id):
    
#     if not current_user.is_authenticated:
#         flash("Access unauthorized.", "danger")
#         return redirect("/")
    
#     form = newGameRoom()

#     if form.validate_on_submit():
        
#         game_room = GameRoom(room_name = form.room_name.data)
        
#         db.session.add(game_room)
#         db.session.commit()

#         return redirect('/game/<int:gameRoom_id>')
    
#     return render_template('Rooms/newGame.html', form=form)






# @app.route('/user/<int:user_id>')
# def pullup_user(user_id):
    
#     user = User.query.get_or_404(user_id)

#     RoomsJoined = (User
#                      .query
#                      .filter()
#                      .all())
    
#     return render_template('users/userpage.html', user=user RoomsJoined = RoomsJoined )




#





# @app.route('/rooms')
# def rooms_in_system():

#     rooms = (Rooms.query.all())

#     return render_template('rooms/<int:rooms.id' rooms=rooms)
    





# @app.route('/user')

# @socketio.on('join')
# def on_join(data):
#     username = data['username']
#     room = data['room']
#     join_room(room)
#     send(username + ' has entered the room.', room=room)

# @socketio.on('leave')
# def on_leave(data):
#     username = data['username']
#     room = data['room']
#     leave_room(room)
#     send(username + ' has left the room.', room=room)

# @socketio.on('my event')
# def handle_my_custom_event(data):
#     emit('my response', data, broadcast=True)



# @app.route('/
# def homepage():

#     if g.user:
#         following_ids = [f.id for f in g.user.following] + [g.user.id]

#         rooms = (Room
#                 .query
#                 .filter()
#                 .order_by(Room.timestamp.desc())
#                 .limit(100)
#                 .all())
        
#         return render_template('homepage.html' rooms = rooms)

#     else:

#         return render_template('home-anon.html')

# @app.route('/users/<int:user_id>')
# def show_users(user_id):

#     user = User.query.get_or_404(user_id)

#     rooms = (Rooms
#             .query
#             .filter(Room.user_id == user_id)
#             .order_by(Room.timestamp.desc())
#             .limit(100)
#             .all())
    
#     return render_template('')

# @app.route('/users/<int:user_id>/following')
# def users_following(user_id):

#     if not g.user:
#         flash('Nope. Try again','danger')
#         return redirect('/')
    
#     user = User.query.get_or_404(user_id)
#     return render_template('')

# @app.route("/users/follow/<int:user.id>")

# @app.route("/users/stop-following/<int:user.id>")

# @app.route("/rooms/<int:rooms.id>")

# @app.route('/logout'
#  















# socket.on('connection', function(socket){
    
#     socket.on('join', function(data){
        
#         var game;
        
#         if(rooms.length === 0){
            
#             game = new Game()
#             rooms.push(game)
#         }

#         game.addPlayer(data.username, socket)
#     })
# })


# @socketio.on('register', namespace = '/war')
# @authenticated_only
# def register_player(socket):

#     user = current_user
#     print(socket)
#     print(user)

#     game = Game.add_player(user, socket)

#     rooms.append(game)

#     emit('connected', {'data': user})

#     ##Figure out how to get user into EXACT requested room 
#     ## make sure room has 2 players 

# @socketio.on('d',namespace='/war')







# class WarGame(Namespace):
    
  
#     @authenticated_only
#     def on_join(self):
       
#        username = current_user
       
#        emit('connection', {username})
    

#     @authenticated_only
#     def on_join_room(self, data):

#         username = current_user
#         gameRoom_id = data['gameRoom_id']
        
#         users[gameRoom_id].append(username)

       
#         if len(users[gameRoom_id]) == 2:
        

#             room = GameRoom.query.filter_by(gameRoom_id = gameRoom_id).first()
            
#             join_room(room)
            
#             emit('join_game', {'users': users[gameRoom_id], 'gameRoom_id': gameRoom_id}, to=room)
            
    
    
#     @authenticated_only
#     def on_play(self,data):
    
    
#     @authenticated_only 
#     def on_play(self,data):

#         data['card1']
#         data['card2']
    
    
#     @authenticated_only
#     def win(self, data):
#         message = data['message_body']
#         sender = data['sender']
#         room = data['room']
#         room_id = data['room_id']
#         current_user = data['current_user']
#         message_object = Messages(message=message,sender=sender,room_id=room_id)
#         db.session.add(message_object)
#         db.session.commit()
#         emit('chat',{'message':message, 'sender': sender, 'current_user':current_user}, room=room, broadcast=True)
    
# socketio.on_namespace(WarGame('/war'))
    
    
    
#     @authenticated_only
#     def play_card(self,data):


        
        



# # @socketio.on('start')
# # @authenticated_only
# # def start_game():



# # @socketio.on('leave')
# # @authenticated_only
# # def on_leave(data):
# #     username = data['username']
# #     room = data['room']
# #     leave_room(room)
# #     send(username + ' has left the room.', to=room)


