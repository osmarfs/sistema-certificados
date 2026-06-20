from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from .forms import EventoForm, PerfilForm
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

@login_required(login_url='/login/')
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

@login_required(login_url='login/')
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

@login_required(login_url='/login/')
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

def cadastro_aluno(request):
    # Se o aluno preencheu o formulário e clicou em enviar
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Salva o usuário no banco
            login(request, user) # Faz o login automático
            messages.success(request, 'Cadastro realizado com sucesso! Bem-vindo(a).')
            return redirect('lista_eventos')
    else:
        # Se ele apenas abriu a página, carrega o formulário vazio
        form = UserCreationForm()
        
    return render(request, 'eventos/cadastro.html', {'form': form})

# Exige a permissão nativa de adicionar eventos. Se não tiver, levanta erro de acesso negado.
@permission_required('eventos.add_evento', raise_exception=True)
def criar_evento(request):
    if request.method == 'POST':
        # request.FILES é necessário pois o formulário contém upload de imagem
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Novo evento publicado com sucesso.')
            return redirect('lista_eventos')
    else:
        form = EventoForm()
        
    return render(request, 'eventos/criar_evento.html', {'form': form})

@login_required(login_url='/login/')
def gerar_certificado(request, inscricao_id):
    # Garante que a inscrição pertence ao aluno logado e que a presença foi confirmada
    inscricao = get_object_or_404(Inscricao, id=inscricao_id, aluno=request.user, presenca_confirmada=True)
    evento = inscricao.evento

    # Configura a resposta do Django para retornar um arquivo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificado_{evento.id}.pdf"'

    # Cria o arquivo PDF usando orientação de paisagem (landscape)
    p = canvas.Canvas(response, pagesize=landscape(letter))
    width, height = landscape(letter)

    # --- Desenho do Layout do Certificado ---
    # Borda externa
    p.setLineWidth(4)
    p.rect(20, 20, width - 40, height - 40)
    
    # Borda interna fina
    p.setLineWidth(1)
    p.rect(25, 25, width - 50, height - 50)

    # Título Principal
    p.setFont("Helvetica-Bold", 32)
    p.drawCentredString(width / 2, height - 100, "CERTIFICADO DE PARTICIPAÇÃO")

    # Texto de Conclusão
    p.setFont("Helvetica", 18)
    # Pega o nome completo, ou usa o username caso o aluno não tenha preenchido o perfil
    nome_aluno = f"{inscricao.aluno.first_name} {inscricao.aluno.last_name}".strip()
    if not nome_aluno:
        nome_aluno = inscricao.aluno.username

    texto = f"Certificamos que {nome_aluno.upper()} participou do evento"
    p.drawCentredString(width / 2, height - 180, texto)

    # Nome do Evento
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width / 2, height - 230, f"'{evento.titulo}'")

    # Detalhes de Carga Horária
    p.setFont("Helvetica", 14)
    detalhes = f"Realizado em {evento.data_inicio.strftime('%d/%m/%Y')} com carga horária total de {evento.carga_horaria} horas."
    p.drawCentredString(width / 2, height - 300, detalhes)

    # Linha e espaço para assinatura da coordenação
    p.setLineWidth(1)
    p.line(width / 2 - 150, 100, width / 2 + 150, 100)
    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2, 80, "Coordenação de Extensão")
    
    # Código de autenticidade (UUID gerado no check-in)
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(40, 40, f"Código de Autenticação: {inscricao.ticket_hash}")

    # Finaliza o PDF
    p.showPage()
    p.save()
    
    return response


@login_required(login_url='/login/')
def perfil_usuario(request):
    if request.method == 'POST':
        # Passamos 'instance=request.user' para que o Django saiba que estamos ATUALIZANDO o usuário atual
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso.')
            return redirect('perfil_usuario')
    else:
        # Carrega o formulário já preenchido com os dados atuais do banco
        form = PerfilForm(instance=request.user)
        
    return render(request, 'eventos/perfil.html', {'form': form})