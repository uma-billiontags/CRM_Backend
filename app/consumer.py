# channels.generic.websocket → Django Channels module for WebSocket handling.
# AsyncWebsocketConsumer → a built-in class that helps create asynchronous WebSocket consumers.


# Claude

# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from .models import ChatRoom, Message, Campaign, User
# from .notification import send_push_notification
# import json


# class ChatConsumer(AsyncWebsocketConsumer):

#     # ==============================
#     # CONNECT
#     # ==============================

#     async def connect(self):   # websocket connect like ws://localhost:8000/ws/chat/CAMP001/

#         self.campaign_id = self.scope['url_route']['kwargs']['campaign_id']   # get the campaign_id from the URL route (ws/chat/CAMP001/)
#         self.room_group_name = f"chat_{self.campaign_id}"   # create a unique group name for the campaign (e.g., chat_CAMP001)

#         await self.channel_layer.group_add(  
#             self.room_group_name,
#             self.channel_name
#         )                                   # add group for current user to the campaign's group (e.g., chat_CAMP001) (client-admin both will join the same group)

        # await self.accept()   # connection accecpt 
        # print(f"WebSocket Connected → {self.campaign_id}")   # print connected 


#     # ==============================
#     # DISCONNECT
#     # ==============================

#     async def disconnect(self, close_code): # If user close the browser or navigate away, this method will be called.

#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         ) # remove the user from the campaign's group (e.g., chat_CAMP001) when they disconnect

#         print(f"WebSocket Disconnected → {self.campaign_id}") # print disconnected


#     # ==============================
#     # RECEIVE MESSAGE FROM FRONTEND
#     # ==============================

#     async def receive(self, text_data):  # receive message from frontend, the text_data is expected to be a JSON string containing content, sender_id, and sender_type (client or admin)

#         try:

#             data        = json.loads(text_data)
#             content     = data.get('content', '').strip() # split the data
#             sender_id   = data.get('sender_id')
#             sender_type = data.get('sender_type')

#             if not content or not sender_id:  # if content is empty or sender_id is missing, we ignore the message and return early
#                 return

#             # ==========================
#             # GET OR CREATE CHAT ROOM
#             # ==========================

#             room = await self.get_or_create_room(self.campaign_id)  # call get_or_create_room to get the chat room for the campaign, if it doesn't exist, it will be created. This is done asynchronously using database_sync_to_async to avoid blocking the event loop.

#             if room is None:
#                 return

#             # ==========================
#             # SAVE MESSAGE TO DB
#             # ==========================

#             message = await self.save_message(  # it calls  Message.objects.create(...)
#                 room=room,
#                 sender_id=sender_id,
#                 sender_type=sender_type,
#                 content=content
#             )

#             # ==========================
#             # BROADCAST TO ROOM GROUP
#             # ==========================

#             await self.channel_layer.group_send(  # it sends the message to all members of the campaign's group (e.g., chat_CAMP001) using group_send. The message includes the type 'chat_message' and the message details (id, content, sender_id, sender_type, timestamp).
#                 self.room_group_name,
#                 {
#                     'type':        'chat_message',     # the type is used to route the message to the appropriate handler method (chat_message) that will be called for all members of the group when a new message is sent. This allows real-time updates for both clients and admins in the campaign's chat.
#                     'message_id':  message.id,         # the message_id is included in the message so that clients can identify the message and use it for features like read receipts or message deletion in the future.
#                     'content':     content,            # the content of the message that will be broadcasted to all members of the campaign's group (client and admin) so that they can see the new message in real-time
#                     'sender_id':   sender_id,          # the sender_id is included in the message so that clients can identify who sent the message (client or admin)
#                     'sender_type': sender_type,        # the sender_type is included in the message so that clients can differentiate between messages sent by clients and admins, which can be used for styling or other UI purposes
#                     'timestamp':   message.timestamp.isoformat(),     # the timestamp of the message is included in ISO format so that clients can display the time the message was sent and use it for features like sorting messages or showing time indicators in the chat UI.
#                 }
#             )

#             # ==========================
#             # FIREBASE PUSH NOTIFICATION 
#             # (only when client sends)
#             # ==========================

#             if sender_type == 'client':                   # if the sender is a client, we want to send a push notification to the admin to notify them of the new message. If the sender is an admin, we don't need to send a notification because the admin is already aware of the new message they sent.
#                 await self.send_firebase_notification(    # it calls send_firebase_notification to send a push notification to the admin about the new message. This is done asynchronously using database_sync_to_async to avoid blocking the event loop.
#                     campaign_id=self.campaign_id,         # the campaign_id is included in the notification title to provide context about which campaign the new message is related to, which can help the admin prioritize their response if they are managing multiple campaigns.
#                     content=content                       # content of the message is included in the notification    
#                 )

#         except Exception as e:                            # if any error occurs during the message processing (e.g., database errors, JSON parsing errors, etc.), we catch the exception and print an error message to the console. This helps with debugging and ensures that the WebSocket connection remains stable even if there are issues with processing a particular message.
#             print(f"Receive Error: {e}")                  # print the error message


#     # ==============================
#     # BROADCAST HANDLER
#     # ==============================

#     async def chat_message(self, event):                  # this method is called when a message is broadcasted to the campaign's group (e.g., chat_CAMP001) using group_send. The event parameter contains the message details that were sent in the group_send call. This method is responsible for sending the message to the WebSocket client that is connected to this consumer.

#         await self.send(text_data=json.dumps({            # it sends the message to the WebSocket client as a JSON string. The message includes the message_id, content, sender_id, sender_type, and timestamp that were included in the event when it was broadcasted. This allows the client to receive real-time updates about new messages in the campaign's chat.
#             'message_id':  event['message_id'],
#             'content':     event['content'],
#             'sender_id':   event['sender_id'],
#             'sender_type': event['sender_type'],
#             'timestamp':   event['timestamp'],
#         }))


#     # ==============================
#     # DB HELPERS
#     # ==============================

#     @database_sync_to_async                        # To run synchronous database operations in an asynchronous context, we use the @database_sync_to_async decorator provided by Django Channels. This allows us to call synchronous Django ORM methods without blocking the event loop, ensuring that our WebSocket consumer remains responsive while performing database operations.
#     def get_or_create_room(self, campaign_id):     # this method is responsible for retrieving the chat room associated with the given campaign_id. If the chat room does not exist, it will create a new one. This ensures that there is always a chat room available for each campaign when clients and admins connect to the WebSocket.

#         try:
#             campaign = Campaign.objects.get(       # Find the campaign associated with the given campaign_id using Campaign.objects.get(). If the campaign does not exist, it will raise a Campaign.DoesNotExist exception, which we catch to handle the case where an invalid campaign_id is provided.
#                 campaign_id=campaign_id
#             )

#             room, _ = ChatRoom.objects.get_or_create(   
#                 campaign=campaign,                       
#                 defaults={'client': campaign.client}    # if a new chat room is created, we set the client field to the campaign's client to establish the relationship between the chat room and the client. If the chat room already exists, we simply retrieve it without modifying the client field.
#             )

#             return room

#         except Campaign.DoesNotExist:
#             print(f"Campaign not found: {campaign_id}")
#             return None


#     @database_sync_to_async
#     def save_message(self, room, sender_id, sender_type, content):  

#         sender = User.objects.get(id=sender_id)          

#         message = Message.objects.create(      # it creates a new message in the database using Message.objects.create() with the provided room, sender, sender_type, and content. This saves the message to the database and returns the created message instance, which includes the generated message ID and timestamp that can be used for broadcasting to clients.
#             room=room,                         
#             sender=sender,                     
#             sender_type=sender_type,          
#             content=content                   # the content of the message that will be saved in the database and later broadcasted to clients. This allows us to persist the chat history for each campaign and retrieve it when needed (e.g., when a client or admin reconnects to the WebSocket).
#         )

#         return message                        


#     # ==============================
#     # FIREBASE NOTIFICATION
#     # ==============================

#     @database_sync_to_async
#     def send_firebase_notification(self, campaign_id, content):  # this method is responsible for sending a push notification to the admin when a new message is sent by a client. It uses the send_push_notification function defined in the notification module to send the notification. The notification includes a title that indicates there is a new message related to the specific campaign and a body that contains a preview of the message content (first 100 characters). This helps keep the admin informed about new messages in real-time, even if they are not actively monitoring the chat interface. If there is an error while sending the notification (e.g., issues with Firebase), we catch the exception and print an error message to the console for debugging purposes.

#         try:

#             send_push_notification(
#                 title=f"New message — {campaign_id}",
#                 body=content[:100]                               # the body of the notification includes a preview of the message content (first 100 characters) to give the admin a quick overview of the new message without needing to open the chat interface. This can help the admin prioritize their response and stay informed about new messages in real-time.
#             )

#         except Exception as e:
#             print(f"Firebase Error: {e}")                        # if there is an error while sending the notification (e.g., issues with Firebase), we catch the exception and print an error message to the console for debugging purposes. This helps us identify and resolve any issues with the notification system without affecting the overall functionality of the WebSocket consumer.

