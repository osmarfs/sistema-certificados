from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.lista_eventos, name='lista_eventos'),
    path('inscrever/<int:evento_id>/', views.inscrever_evento, name='inscrever_evento'),
    path('meus-eventos/', views.meus_eventos, name='meus_eventos'), # nova rota


    path('cadastro/', views.cadastro_aluno, name='cadastro'),
    path('login/', auth_views.LoginView.as_view(template_name='eventos/login.html', next_page='lista_eventos'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='lista_eventos'), name='logout'),
    path('criar-evento/', views.criar_evento, name='criar_evento'),
    path('certificado/<int:inscricao_id>/', views.gerar_certificado, name='gerar_certificado'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),




    path('checkin/', views.validar_checkin, name='validar_checkin'),
]
