from rest_framework.response import Response 
from rest_framework.decorators import api_view, parser_classes
from .models import User, TeamAccess
from .serializers import TeamAccessSerializer
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import status


# Create your views here.

@api_view(['POST'])
def login_view(request):
    email = request.data.get('email') # get the email and password from frontend request body
    password = request.data.get('password')

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=400) 

    # ── 1. Check TeamAccess table first (team members) ──────────────────────
    try:
        team_member = TeamAccess.objects.get(email=email)

        if team_member.status != 'Active':
            return Response({"error": "Your account is inactive. Contact your administrator."}, status=403)

        if team_member.password != password:
            return Response({"error": "Invalid password"}, status=401)
        
        role = team_member.role.lower().replace(" ", "_")
        
        return Response({
            "message": "Login successful",
            "user": {
                "id":        team_member.id,
                "username":  team_member.member,
                "email":     team_member.email,
                "role":      role,
                "client_id": None,
                "source":    "team",
            }
        }, status=200)

    except TeamAccess.DoesNotExist:
        pass  # not a team member, check user table next

    # ── 2. Check User table (clients + superadmin) ───────────────────────────
    try:
        user_obj = User.objects.get(email=email)   # searches the user in db using email
    except User.DoesNotExist:
        return Response({"error": "No account found with this email"}, status=401)

    user = authenticate(username=user_obj.username, password=password)   # verifies the password & username using django built-in authentication system
    if user is None:
        return Response({"error": "Invalid password"}, status=401)
    
    # UPDATE LAST LOGIN TIME    
    user.last_login = timezone.now()
    user.save()
    
    if user.role == 'client':   # check if the logged user is client
        if user.client is None or user.client.status != 'approved':      # check the client approvel status
            return Response({"error": "Your account is not approved yet"}, status=403)

    return Response({
        "message": "Login successful",
        "user": {
            "id":        user.id,
            "username":  user.username,
            "email":     user.email,
            "role":      user.role,
            "client_id": user.client.client_id if user.client else None,     # If user linked with client: return client id otherwise return None
            "client_name": user.client.name if user.client else None,  # ← ADD THIS
            "source":    "user",
        }
    }, status=200)


# ---------------------------
# TEAM MEMBER MANAGEMENT
# ---------------------------

# Create Team Member
@api_view(['POST'])
def create_team_member(request):

    serializer = TeamAccessSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get All Team Members
@api_view(['GET'])
def get_team_members(request):

    members = TeamAccess.objects.all().order_by('-id')
    serializer = TeamAccessSerializer(members, many=True)

    return Response(serializer.data)


# Edit Team Member
@api_view(['PUT'])
def edit_team_member(request, id):

    try:
        member = TeamAccess.objects.get(id=id)
    except TeamAccess.DoesNotExist:
        return Response(
            {"error": "Team member not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = TeamAccessSerializer(member, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Delete Team Member
@api_view(['DELETE'])
def delete_team_member(request, id):

    try:
        member = TeamAccess.objects.get(id=id)
    except TeamAccess.DoesNotExist:
        return Response(
            {"error": "Team member not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    member.delete()

    return Response(
        {"message": "Team member deleted successfully"},
        status=status.HTTP_200_OK
    )


# ---------------------------
# USER MANAGEMENT
# ---------------------------

# GET all client users
@api_view(['GET'])
def get_client_users(request):
    users = User.objects.filter(role='client').select_related('client')
    data = []
    for u in users:
        data.append({
            "id": u.id,
            "client_id": u.client.client_id if u.client else u.username,
            "email": u.email,
            "role": u.role,
            "status": getattr(u, 'status', 'Active'),  # once you add status field
            "last_active": u.last_login.isoformat() if u.last_login else u.date_joined.isoformat(),
        })
    return Response(data)



@api_view(['DELETE'])
def delete_client_user(request, id):

    # =====================================
    # FIND CLIENT USER
    # =====================================

    try:

        user = User.objects.select_related(
            'client'
        ).get(

            id=id,

            role='client'
        )

    except User.DoesNotExist:

        return Response({

            "error":
            "Client user not found"

        }, status=404)

    # =====================================
    # STORE DETAILS
    # =====================================

    client = user.client

    deleted_data = {

        "user_id": user.id,

        "email": user.email,

        "client_id": (

            client.client_id
            if client else None
        )
    }

    # =====================================
    # DELETE CLIENT TABLE
    # =====================================

    if client:

        client.delete()

    # =====================================
    # SUCCESS RESPONSE
    # =====================================

    return Response({

        "message":
        "Client and user deleted successfully",

        "deleted_data":
        deleted_data

    }, status=200)


@api_view(['PUT'])
def edit_client_user(request, id):
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    password = request.data.get('password')
    status = request.data.get('status')

    if password:
        user.set_password(password)
    if status:
        user.status = status   # add this field to User model first

    user.save()
    return Response({"message": "Updated successfully"}, status=200)


