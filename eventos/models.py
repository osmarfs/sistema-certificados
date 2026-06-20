from django.db import models
from django.contrib.auth.models import User
import uuid

class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    carga_horaria = models.IntegerField(help_text="Carga horaria em horas")
    template_certificados = models.ImageField(upload_to='templates/', blank=True, null=True)

    def __str__(self):
        return self.titulo
    
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
