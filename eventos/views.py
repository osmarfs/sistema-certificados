from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from .forms import EventoForm, PerfilForm, AlunoPerfilForm
from django.utils import timezone
from .models import Evento, Inscricao, AlunoPerfil
import qrcode
import base64
from io import BytesIO
import locale
from datetime import datetime

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
    if request.method == 'POST':
        form_user = UserCreationForm(request.POST)
        form_perfil = AlunoPerfilForm(request.POST)
        
        if form_user.is_valid() and form_perfil.is_valid():
            user = form_user.save()
            # Salva o perfil atrelando-o ao usuário recém-criado
            perfil = form_perfil.save(commit=False)
            perfil.user = user
            perfil.save()
            
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('lista_eventos')
    else:
        form_user = UserCreationForm()
        form_perfil = AlunoPerfilForm()
        
    return render(request, 'eventos/cadastro.html', {'form_user': form_user, 'form_perfil': form_perfil})

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
    inscricao = get_object_or_404(Inscricao, id=inscricao_id, aluno=request.user, presenca_confirmada=True)
    evento = inscricao.evento

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificado_{evento.id}.pdf"'

    p = canvas.Canvas(response, pagesize=landscape(letter))
    width, height = landscape(letter)

    # 1. Imagem de fundo (Template limpo apenas com logos e bordas)
    if evento.template_certificado:
        caminho_imagem = evento.template_certificado.path
        p.drawImage(caminho_imagem, 0, 0, width=width, height=height)
    else:
        # Fallback de segurança
        p.setLineWidth(4)
        p.rect(20, 20, width - 40, height - 40)
        p.setFont("Helvetica-Bold", 32)
        p.drawCentredString(width / 2, height - 100, "CERTIFICADO")

    # 2. Resgate de dados dinâmicos do banco
    nome_aluno = f"{inscricao.aluno.first_name} {inscricao.aluno.last_name}".strip() or inscricao.aluno.username
    
    try:
        cpf_aluno = inscricao.aluno.alunoperfil.cpf
    except AlunoPerfil.DoesNotExist:
        cpf_aluno = ""

    # Formatação da data para o padrão por extenso (Ex: 07 de julho de 2026)
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
    except:
        pass
    
    data_formatada = evento.data_inicio.strftime('%d de %B de %Y')

    # 3. Renderização de todo o texto (Padrão Uninassau)
    
    # Linha 1
    p.setFont("Helvetica", 14)
    p.setFillColorRGB(0.4, 0.4, 0.4) # Cinza
    p.drawCentredString(width / 2, height - 190, "Este certificado é concedido a")

    # Linha 2: Nome
    p.setFont("Helvetica-BoldOblique", 32)
    p.setFillColorRGB(0.1, 0.2, 0.4) # Azul escuro
    p.drawCentredString(width / 2, height - 240, nome_aluno.title())

    # Linha 3: CPF
    if cpf_aluno:
        p.setFont("Helvetica", 12)
        p.setFillColorRGB(0.4, 0.4, 0.4)
        p.drawCentredString(width / 2, height - 260, f"CPF: {cpf_aluno}")

    # Linha 4: Texto de participação
    p.setFont("Helvetica", 14)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    texto_participacao = f"por sua participação no curso de extensão online com carga horária de {evento.carga_horaria}h em"
    p.drawCentredString(width / 2, height - 310, texto_participacao)

    # Linha 5: Nome do Evento
    p.setFont("Helvetica-Bold", 20)
    p.setFillColorRGB(0.1, 0.2, 0.4)
    p.drawCentredString(width / 2, height - 350, evento.titulo.upper())

    # Linha 6: Data
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawCentredString(width / 2, height - 420, data_formatada)

    # Código de Validação (Canto inferior direito)
    p.setFont("Helvetica", 8)
    p.setFillColorRGB(0.0, 0.0, 0.0) # Preto
    p.drawRightString(width - 40, 30, f"Código de Validação: {inscricao.ticket_hash}")

    p.showPage()
    p.save()
    
    return response


@login_required(login_url='/login/')
def perfil_usuario(request):
    # Garante que administradores antigos sem perfil não gerem erro ao acessar a tela
    perfil, created = AlunoPerfil.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form_user = PerfilForm(request.POST, instance=request.user)
        form_perfil = AlunoPerfilForm(request.POST, instance=perfil)
        
        if form_user.is_valid() and form_perfil.is_valid():
            form_user.save()
            form_perfil.save()
            messages.success(request, 'Dados atualizados com sucesso.')
            return redirect('perfil_usuario')
    else:
        form_user = PerfilForm(instance=request.user)
        form_perfil = AlunoPerfilForm(instance=perfil)
        
    return render(request, 'eventos/perfil.html', {'form_user': form_user, 'form_perfil': form_perfil})