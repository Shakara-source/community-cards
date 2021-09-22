
from flask_socketio import SocketIO, Namespace, emit, join_room, leave_room, close_room, rooms, disconnect


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