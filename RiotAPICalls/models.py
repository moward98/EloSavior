from tkinter import CASCADE
from django.db import models
from django.forms import CharField

# Create your models here.

class Summoner(models.Model):
    name = models.CharField(max_length=16)
    summoner_id = models.CharField(max_length=63)
    puuid = models.CharField(max_length=78, null=True)
    level = models.IntegerField()
    tier = models.CharField(max_length=3, null=True)
    rank = models.CharField(max_length=11, null=True)
    lp = models.IntegerField(null=True)
    hotstreak = models.BooleanField(null=True)
    divinity = models.BooleanField(null=True)

    def __str__(self):
        return self.name


