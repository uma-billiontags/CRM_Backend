from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from accounts.models import User
from clients.models import Client
from .serializers import ClientSerializer
from .notification import send_push_notification
import json

# Create your views here.


@api_view(["POST"])
def create_client(request):

    try:

        # ==========================
        # GET SIGNATURE FILES
        # ==========================

        signatures = {
            key: request.FILES[key]
            for key in request.FILES
            if key.startswith("contact_signature_")
        }

        # ==========================
        # GET FORM DATA
        # ==========================

        raw = request.data.get("data")

        if raw:

            parsed = json.loads(raw)

            data = parsed

        else:

            data = request.data

        # ==========================
        # CHECK DUPLICATE EMAIL
        # ==========================

        email = data.get("email")

        if Client.objects.filter(email=email).exists():

            return Response({"error": "This email is already registered"}, status=400)

        # ==========================
        # SERIALIZER VALIDATION
        # ==========================

        serializer = ClientSerializer(data=data, context={"signatures": signatures})

        if serializer.is_valid():

            # ==========================
            # SAVE CLIENT
            # ==========================

            client = serializer.save()

            # ==========================
            # CREATE LOGIN USER
            # ==========================

            if email and not User.objects.filter(email=email).exists():

                User.objects.create(
                    username=email, email=email, role="client", client=client
                )

            # ==========================
            # SEND FIREBASE PUSH NOTIFICATION
            # ==========================

            send_push_notification(
                "New Client Request", f"New Client Submitted: {client.name}"
            )

            # ==========================
            # SUCCESS RESPONSE
            # ==========================

            return Response({"message": "Client created successfully"}, status=201)

        # ==========================
        # SERIALIZER ERROR RESPONSE
        # ==========================

        return Response(serializer.errors, status=400)

    except Exception as e:

        # ==========================
        # EXCEPTION ERROR RESPONSE
        # ==========================

        return Response({"error": str(e)}, status=500)


# To update the client function for approvel
@api_view(["PATCH"])
def update_client_status(request, client_id):
    try:
        client = Client.objects.get(client_id=client_id)
    except Client.DoesNotExist:
        return Response({"error": "Client not found"}, status=404)

    status = request.data.get("status")
    if status not in ["pending", "approved", "rejected"]:
        return Response({"error": "Invalid status"}, status=400)

    client.status = status
    client.save()
    return Response({"message": f"Client status updated to {status}"}, status=200)


# ==============================
# GET SINGLE CLIENT
# ==============================
@api_view(["GET"])
def get_client(request, client_id):
    try:
        client = (
            Client.objects.select_related(
                "billing", "ownership", "classification"  #  FIXED  #  FIXED  #  FIXED
            )
            .prefetch_related("addresses", "contacts")  # correct  # correct
            .get(client_id=client_id)
        )

    except Client.DoesNotExist:
        return Response({"error": "Client not found"}, status=404)

    serializer = ClientSerializer(client)
    return Response(serializer.data)


# ==============================
# GET ALL CLIENTS
# ==============================


@api_view(["GET"])
def get_all_clients(request):

    clients = (
        Client.objects.select_related(
            "billing", "ownership", "classification"  # FIXED  #  FIXED  #  FIXED
        )
        .prefetch_related("addresses", "contacts")  #  correct  #  correct
        .all()
    )

    serializer = ClientSerializer(clients, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def approve_client(request):

    # =====================================
    # GET DATA FROM FRONTEND
    # =====================================

    client_id = request.data.get("client_id")

    password = request.data.get("password")

    # =====================================
    # VALIDATION
    # =====================================

    if not client_id or not password:

        return Response({"error": "client_id and password required"}, status=400)

    # =====================================
    # GET CLIENT
    # =====================================
    try:

        client = Client.objects.get(client_id=client_id)

    except Client.DoesNotExist:

        return Response({"error": "Client not found"}, status=404)

    # =====================================
    # CREATE USER IF NOT EXISTS
    # =====================================

    user, created = User.objects.get_or_create(
        email=client.email,
        defaults={
            "username": client.client_id,
            "email": client.email,
            "role": "client",
            "client": client,
        },
    )

    # =====================================
    # UPDATE USER DETAILS
    # =====================================

    user.username = client.email  # client.email  (or) client.client_id

    user.email = client.email

    user.role = "client"

    user.client = client

    # SET PASSWORD (HASH PASSWORD)
    user.set_password(password)

    # SAVE USER
    user.save()

    # =====================================
    # UPDATE CLIENT STATUS
    # =====================================

    client.status = "approved"

    client.save()

    # =====================================
    # SEND LOGIN EMAIL
    # =====================================

    send_mail(
        subject="CRM Login Credentials",
        message=f"""
Hello {client.name},

Your account has been approved.

Login Email:
{client.email}

Password:
{password}

You can now login and create campaigns.
Thank You
""",
        from_email="yourgmail@gmail.com",
        recipient_list=[client.email],
        fail_silently=False,
    )

    # =====================================
    # SUCCESS RESPONSE
    # =====================================

    return Response(
        {
            "message": "Client approved successfully",
            "client_id": client.client_id,
            "email": client.email,
            "status": client.status,
        },
        status=200,
    )


# ---------------------------
# USER MANAGEMENT
# ---------------------------


# GET all client users
@api_view(["GET"])
def get_client_users(request):
    users = User.objects.filter(role="client").select_related("client")
    data = []
    for u in users:
        data.append(
            {
                "id": u.id,
                "client_id": u.client.client_id if u.client else u.username,
                "email": u.email,
                "role": u.role,
                "status": getattr(u, "status", "Active"),  # once you add status field
                "last_active": (
                    u.last_login.isoformat()
                    if u.last_login
                    else u.date_joined.isoformat()
                ),
            }
        )
    return Response(data)


@api_view(["DELETE"])
def delete_client_user(request, id):

    # =====================================
    # FIND CLIENT USER
    # =====================================

    try:

        user = User.objects.select_related("client").get(id=id, role="client")

    except User.DoesNotExist:

        return Response({"error": "Client user not found"}, status=404)

    # =====================================
    # STORE DETAILS
    # =====================================

    client = user.client

    deleted_data = {
        "user_id": user.id,
        "email": user.email,
        "client_id": (client.client_id if client else None),
    }

    # =====================================
    # DELETE CLIENT TABLE
    # =====================================

    if client:

        client.delete()

    # =====================================
    # SUCCESS RESPONSE
    # =====================================

    return Response(
        {
            "message": "Client and user deleted successfully",
            "deleted_data": deleted_data,
        },
        status=200,
    )


@api_view(["PUT"])
def edit_client_user(request, id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    password = request.data.get("password")
    status = request.data.get("status")

    if password:
        user.set_password(password)
    if status:
        user.status = status  # add this field to User model first

    user.save()
    return Response({"message": "Updated successfully"}, status=200)
