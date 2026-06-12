from rest_framework import serializers
from .models import TeamAccess


class TeamAccessSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeamAccess
        fields = '__all__'

