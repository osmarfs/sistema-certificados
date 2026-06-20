from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Evento, Inscricao
import qrcode
import base64
from io import BytesIO

def lista_eventos(request):
    #Busca todos os eventos cadastrados no banco de dados
    eventos = Evento.objects.all()

    # Envia esses eventos para um arquivo HTML que logo será criado
    return render(request, 'eventos/lista_eventos.html', {'eventos':eventos})

@login_required(login_url='/admin/login/')
def inscrever_evento(request, evento_id):
    # Captura o evento pela ID fornecido na URL
    evento = get_object_or_404(Evento, id=evento_id)

    # verifica se já ecxiste uma inscrição para este usuário neste evento
    inscricao_existe = Inscricao.objects.filter(aluno=request.user, evento=evento).exists()

    if not inscricao_existe:
        # Grava no banco. O ticket_hash (UUID) é gerado automaticamente pelo model    
        Inscricao.objects.create(aluno=request.user, evento=evento)

        messages.success(request, f'Incrição confirmada no evento: {evento.titulo}')
    else:

        messages.info(request, "Você já possui inscrição para este evento.")

    # Redireciona de volta para a tela principal
    return redirect('meus_eventos')

@login_required(login_url='admin/login/')
def meus_eventos(request):
    # Busca todas as inscrições do usuário logado
    inscricoes = Inscricao.objects.filter(aluno=request.user)

    ingressos = []

    for inscricao in inscricoes:
        # Pega o UUID único e transforma em imagem de QR Code
        qr = qrcode.make(str(inscricao.ticket_hash))
        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        # Converte a imagem para Base64 para exibir direto no HTML
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        ingressos.append({
            'inscricao': inscricao,
            'qr_code': img_str
        })

    return render(request, 'eventos/meus_eventos.html', {'ingressos': ingressos})

@login_required(login_url='/admin/login/')
def validar_checkin(request):

    if request.method == "POST":
        hash_lido = request.POST.get('ticket_hash')

        try:

            inscricao = Inscricao.objects.get(ticket_hash=hash_lido)

            if inscricao.presenca_confirmada:
                messages.warning(request, f'Alerta: Check-in já havia sido realizado para {inscricao.aluno.username}.')
            else:

                inscricao.presenca_confirmada = True
                inscricao.data_checkin = timezone.now() 
                inscricao.save()
                messages.sucess(request, f'Check-in confirmado com sucesso: {inscricao.aluno.username} no evento {inscricao.evento.titulo}.')

        except Inscricao.DoesNotExist:
            messages.error(request, 'Ingresso inválido. Nenhum registro encontrado para este QR Code')
        
        return redirect('validar_checkin')

    return render(request, 'eventos/checkin.html')