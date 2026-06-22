from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
import uuid

# Adicione esta classe logo abaixo das importações
class AlunoPerfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    data_inicio = models.DateTimeField()
    #data_fim = models.DateTimeField(null=True, blank=True)
    carga_horaria = models.IntegerField(help_text="Carga horária em horas")

    data_fim_inscricoes = models.DateTimeField(verbose_name="Fim das Inscrições", null=True, blank=True)
    
    # Esta linha DEVE estar aqui
    template_certificado = models.ImageField(upload_to='templates/', blank=True, null=True)

    def __str__(self):
        return self.titulo
    
    @property
    def inscricoes_abertas(self):
        return timezone.now() <= self.data_fim_inscricoes
    
class Inscricao(models.Model):
    #relaciona a inscrição ao usuário do sistema e ao evento
    aluno = models.ForeignKey(User, on_delete=models.CASCADE)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)

    # Gera uma string única impossivel de advinhar. Esse será o nosso QR Code.
    ticket_hash = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    presenca_confirmada = models.BooleanField(default=False)
    data_checkin = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.aluno.username} - {self.evento.titulo}"
