from django.urls import  path
from . import views

urlpatterns = [
    path('<str:summoner_name>/', views.resp, name='get_summoner_info')
]