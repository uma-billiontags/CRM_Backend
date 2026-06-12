from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import json
from .models import FCMToken

# Create your views here.

@api_view(['POST'])
@csrf_exempt
def save_fcm_token(request):
    try:
        data = json.loads(request.body)
        token = data.get("token")
        client_id = data.get("client_id")  # ← change from email to client_id

        if not token:
            return Response({"error": "Token Missing"}, status=400)

        #user = None
        client = None
        if client_id:
            try:
                # Find the User linked to this client_id
                from .models import Client  # adjust import to your app
                client = Client.objects.get(client_id=client_id)
                #user = User.objects.get(client=client)
            except (Client.DoesNotExist):
                pass

        FCMToken.objects.update_or_create(
            token=token,
            defaults={"client": client}
        )

        return Response({"message": "Token Saved Successfully"}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


