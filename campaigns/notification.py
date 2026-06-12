from firebase_admin import messaging    # Firebase Admin SDK module
from notifications.models import FCMToken

# def send_push_notification(title,body):

#     tokens = FCMToken.objects.values_list('token',flat=True) # fetch the tokens from db

#     for token in tokens: # send each tokens

#         try:

#             message = messaging.Message(

#                 notification=messaging.Notification(title=title,body=body),token=token)

#             response = messaging.send(message)

#             print("Notification Sent:",response)

#         except Exception as e:

#             print("FCM Error:",e)
#             if "NotRegistered" in str(e) or "invalid-registration-token" in str(e):
#                 FCMToken.objects.filter(token=token).delete()  # auto cleanup




# claude 


from firebase_admin import messaging
from notifications.models import FCMToken

def send_push_notification(title, body):

    tokens = list(
        FCMToken.objects.values_list('token', flat=True).distinct()  # to reduce duplicate tokens
    )

    if not tokens:
        print("No FCM tokens found") # check empty token
        return

    for token in tokens:

        try:

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                token=token
            )

            response = messaging.send(message)
            print(f"Notification Sent: {response}")

        except Exception as e:

            print(f"FCM Error: {e}")

            # Invalid token → auto delete
            if "NotRegistered" in str(e) or "invalid-registration-token" in str(e):
                FCMToken.objects.filter(token=token).delete()
                print(f"Invalid token deleted: {token[:20]}...")


# # Send push notification to specific user

from firebase_admin import messaging
from notifications.models import FCMToken


def send_notification_to_client(
    client,
    title,
    body
):
    print("CLIENT =", client)
    print("CLIENT ID =", client.client_id)


    tokens = list(

        FCMToken.objects.filter(
            client=client
        ).values_list(
            "token",
            flat=True
        ).distinct()

    )

    if not tokens:

        print(
            f"No token found for {client.name}"
        )

        return

    for token in tokens:

        try:

            message = messaging.Message(

                notification=messaging.Notification(
                    title=title,
                    body=body
                ),

                token=token

            )

            response = messaging.send(
                message
            )

            print(
                f"Notification Sent: {response}"
            )

        except Exception as e:

            print(
                f"FCM Error: {e}"
            )




# user = models.ForeignKey(User)   model
# admin_tokens = FCMToken.objects.filter(user=admin)
