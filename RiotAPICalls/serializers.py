from rest_framework import serializers
from .models import Summoner

class PlayerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Summoner
        fields = ('name',)