from django.urls import path
from . import views

urlpatterns = [
    path('', view.lista_eventos, name='lista_eventos'),
]
