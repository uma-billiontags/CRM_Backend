from firebase_admin import messaging

from .models import FCMToken

def send_push_notification(title,body):

    tokens = FCMToken.objects.values_list('token',flat=True)

    for token in tokens:

        try:

            message = messaging.Message(

                notification=messaging.Notification(title=title,body=body),token=token)

            response = messaging.send(message)

            print("Notification Sent:",response)

        except Exception as e:

            print("FCM Error:",e)











