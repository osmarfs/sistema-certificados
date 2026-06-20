from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('inscrever/<int:evento_id>/', views.inscrever_evento, name='inscrever_evento'),
    path('meus-eventos/', views.meus_eventos, name='meus_eventos'), # nova rota
    path('checkin/', views.validar_checkin, name='validar_checkin'),
]
