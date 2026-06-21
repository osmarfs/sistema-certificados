from PIL import Image, ImageDraw

# Dimensões exatas proporcionais ao formato landscape(letter) do ReportLab
largura = 1056
altura = 816

# Cria uma imagem de fundo branco
img = Image.new('RGB', (largura, altura), color='white')
draw = ImageDraw.Draw(img)

# Cores aproximadas da instituição
azul_escuro = (1, 32, 96)
dourado = (255, 192, 0)

# Desenhando as bordas do certificado
# Borda externa dourada
draw.rectangle([20, 20, largura-20, altura-20], outline=dourado, width=4)
# Borda interna azul
draw.rectangle([30, 30, largura-30, altura-30], outline=azul_escuro, width=8)

# Salva a imagem na sua pasta atual
img.save('template_branco.png')
print("Imagem 'template_branco.png' gerada com sucesso!")