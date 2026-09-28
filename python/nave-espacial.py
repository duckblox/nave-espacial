"""
NAVE ESPACIAL - um joguinho para o Andrew explorar o poder da programação!
------------------------------------------------------------------------
Como jogar:
  - Setas do teclado (ou W A S D) movem a nave
  - Espaço ou clique do mouse atira
  - Desvie dos inimigos, destrua-os e faça o maior score possível
  - Quando perder todas as vidas, pressione ENTER para jogar de novo

Como rodar:
  1) Instale a biblioteca do jogo (só precisa fazer isso uma vez):
        pip install pygame-ce
  2) Rode o jogo:
        python nave_espacial.py
"""

import pygame
import random
import math
import sys
import array
import json
import os

# ------------------------------------------------------------------
# CONFIGURAÇÃO BÁSICA
# ------------------------------------------------------------------
LARGURA, ALTURA = 900, 650
FPS = 60
TAXA_AMOSTRAGEM = 44100

PRETO = (5, 5, 15)
BRANCO = (240, 240, 250)
CIANO = (80, 220, 255)
AMARELO = (255, 210, 60)
VERMELHO = (255, 70, 70)
VERDE = (90, 255, 140)
ROXO = (190, 100, 255)
LARANJA = (255, 140, 40)
AZUL_ACO = (100, 150, 255)

# arquivo onde o recorde e a skin escolhida ficam salvos (na mesma pasta do jogo)
ARQUIVO_PROGRESSO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nave_progresso.json")

# skins da nave: cada uma é desbloqueada ao bater um recorde de pontos
SKINS = [
    {"nome": "Padrão",   "cor_nave": CIANO,          "cor_chama": LARANJA,        "recorde": 0},
    {"nome": "Fantasma", "cor_nave": (215, 215, 255), "cor_chama": (150, 170, 255), "recorde": 150},
    {"nome": "Fênix",    "cor_nave": LARANJA,         "cor_chama": VERMELHO,       "recorde": 400},
    {"nome": "Esmeralda","cor_nave": VERDE,           "cor_chama": (255, 255, 120), "recorde": 800},
]


def carregar_progresso():
    padrao = {"recorde": 0, "skin_atual": 0}
    try:
        with open(ARQUIVO_PROGRESSO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            padrao["recorde"] = int(dados.get("recorde", 0))
            padrao["skin_atual"] = int(dados.get("skin_atual", 0))
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        pass
    return padrao


def salvar_progresso(progresso):
    try:
        with open(ARQUIVO_PROGRESSO, "w", encoding="utf-8") as arquivo:
            json.dump(progresso, arquivo)
    except OSError:
        pass  # se não conseguir salvar, o jogo continua funcionando normalmente


def skins_desbloqueadas(progresso):
    return [i for i, skin in enumerate(SKINS) if progresso["recorde"] >= skin["recorde"]]

pygame.init()

# tenta ligar o som; se a máquina não tiver placa de som, o jogo
# continua funcionando normalmente, só sem efeitos sonoros
try:
    pygame.mixer.init(frequency=TAXA_AMOSTRAGEM, size=-16, channels=1, buffer=256)
    SOM_ATIVO = True
except pygame.error:
    SOM_ATIVO = False

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Nave Espacial - feito em Python")
relogio = pygame.time.Clock()
fonte_grande = pygame.font.SysFont("arial", 60, bold=True)
fonte_media = pygame.font.SysFont("arial", 28, bold=True)
fonte_pequena = pygame.font.SysFont("arial", 20)


# ------------------------------------------------------------------
# SONS GERADOS POR CÓDIGO (nenhum arquivo de áudio é necessário)
# ------------------------------------------------------------------
def gerar_tom(frequencia, duracao_ms, volume=0.35, frequencia_final=None):
    """Cria uma onda quadrada simples (som 'chiptune', estilo 8-bit),
    com fade out no final para não estalar, e opção de variar o tom
    (glissando) para efeitos como explosão ou dano."""
    n_amostras = int(TAXA_AMOSTRAGEM * duracao_ms / 1000)
    amostras = array.array('h')
    if frequencia_final is None:
        frequencia_final = frequencia
    fase = 0.0
    for i in range(n_amostras):
        progresso = i / max(1, n_amostras)
        freq_atual = frequencia + (frequencia_final - frequencia) * progresso
        fase += freq_atual / TAXA_AMOSTRAGEM
        onda = 1.0 if math.sin(2 * math.pi * fase) >= 0 else -1.0
        fade = max(0.0, 1 - progresso)
        amostras.append(int(volume * fade * onda * 32767))
    return pygame.mixer.Sound(buffer=amostras.tobytes())


def gerar_ruido(duracao_ms, volume=0.35):
    """Cria ruído branco com fade out — bom para explosões."""
    n_amostras = int(TAXA_AMOSTRAGEM * duracao_ms / 1000)
    amostras = array.array('h')
    for i in range(n_amostras):
        fade = max(0.0, 1 - i / max(1, n_amostras))
        amostras.append(int(volume * fade * random.uniform(-1, 1) * 32767))
    return pygame.mixer.Sound(buffer=amostras.tobytes())


if SOM_ATIVO:
    SOM_TIRO = gerar_tom(880, 70, volume=0.18)
    SOM_EXPLOSAO = gerar_ruido(220, volume=0.30)
    SOM_DANO = gerar_tom(300, 220, volume=0.30, frequencia_final=120)
    SOM_FIM_DE_JOGO = gerar_tom(440, 700, volume=0.30, frequencia_final=80)
    SOM_FASE = gerar_tom(440, 350, volume=0.30, frequencia_final=1100)
    SOM_SKIN = gerar_tom(660, 450, volume=0.30, frequencia_final=1320)
else:
    SOM_TIRO = SOM_EXPLOSAO = SOM_DANO = SOM_FIM_DE_JOGO = SOM_FASE = SOM_SKIN = None


def tocar(som):
    if SOM_ATIVO and som is not None:
        som.play()


# ------------------------------------------------------------------
# FUNDO ESTRELADO COM PROFUNDIDADE (efeito parallax = sensação de 3D)
# ------------------------------------------------------------------
class CampoDeEstrelas:
    def __init__(self, quantidade=140):
        self.estrelas = []
        for _ in range(quantidade):
            camada = random.choice([1, 2, 3])  # 1 = longe/devagar, 3 = perto/rápido
            self.estrelas.append({
                "x": random.uniform(0, LARGURA),
                "y": random.uniform(0, ALTURA),
                "camada": camada,
                "raio": camada * 0.6,
                "vel": camada * 0.9,
            })

    def atualizar(self):
        for e in self.estrelas:
            e["y"] += e["vel"]
            if e["y"] > ALTURA:
                e["y"] = 0
                e["x"] = random.uniform(0, LARGURA)

    def desenhar(self, superficie):
        for e in self.estrelas:
            brilho = 120 + e["camada"] * 40
            cor = (brilho, brilho, min(255, brilho + 30))
            pygame.draw.circle(superficie, cor, (int(e["x"]), int(e["y"])), max(1, int(e["raio"])))


# ------------------------------------------------------------------
# PARTÍCULAS DE EXPLOSÃO (dão a sensação de impacto real)
# ------------------------------------------------------------------
class Particula:
    def __init__(self, x, y, cor):
        angulo = random.uniform(0, math.tau)
        velocidade = random.uniform(1.5, 6)
        self.x, self.y = x, y
        self.vx = math.cos(angulo) * velocidade
        self.vy = math.sin(angulo) * velocidade
        self.vida = random.uniform(20, 40)
        self.vida_max = self.vida
        self.cor = cor
        self.raio = random.uniform(2, 4)

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.vida -= 1

    def desenhar(self, superficie):
        if self.vida <= 0:
            return
        alfa = max(0, self.vida / self.vida_max)
        raio = max(1, int(self.raio * alfa * 2))
        cor = tuple(int(c * alfa) for c in self.cor)
        pygame.draw.circle(superficie, cor, (int(self.x), int(self.y)), raio)


def criar_explosao(lista_particulas, x, y, cor, quantidade=22):
    for _ in range(quantidade):
        lista_particulas.append(Particula(x, y, cor))


# ------------------------------------------------------------------
# NAVE DO JOGADOR
# ------------------------------------------------------------------
class Jogador:
    def __init__(self, skin_indice=0):
        self.x = LARGURA / 2
        self.y = ALTURA - 90
        self.vx = 0
        self.vy = 0
        self.raio_colisao = 16
        self.vidas = 3
        self.invencivel = 0
        self.tempo_tiro = 0
        self.chama = 0
        self.definir_skin(skin_indice)

    def definir_skin(self, skin_indice):
        self.skin_indice = skin_indice
        skin = SKINS[skin_indice]
        self.cor_nave = skin["cor_nave"]
        self.cor_chama = skin["cor_chama"]

    def atualizar(self, teclas):
        aceleracao = 0.6
        atrito = 0.90

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.vx -= aceleracao
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.vx += aceleracao
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.vy -= aceleracao
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.vy += aceleracao

        self.vx *= atrito
        self.vy *= atrito
        self.x += self.vx
        self.y += self.vy

        self.x = max(20, min(LARGURA - 20, self.x))
        self.y = max(20, min(ALTURA - 20, self.y))

        if self.tempo_tiro > 0:
            self.tempo_tiro -= 1
        if self.invencivel > 0:
            self.invencivel -= 1

        self.chama = (self.chama + 1) % 20

    def atirar(self, tiros):
        if self.tempo_tiro == 0:
            tiros.append(Tiro(self.x - 10, self.y - 10, -1))
            tiros.append(Tiro(self.x + 10, self.y - 10, -1))
            self.tempo_tiro = 10
            tocar(SOM_TIRO)

    def desenhar(self, superficie):
        # pisca quando está invencível (logo depois de tomar dano)
        if self.invencivel > 0 and self.invencivel % 6 < 3:
            return

        pontos = [
            (self.x, self.y - 22),
            (self.x - 16, self.y + 16),
            (self.x, self.y + 8),
            (self.x + 16, self.y + 16),
        ]
        pygame.draw.polygon(superficie, self.cor_nave, pontos)
        pygame.draw.polygon(superficie, BRANCO, pontos, width=2)

        # chama do propulsor, animada
        tamanho_chama = 10 + 6 * math.sin(self.chama * 0.6)
        chama_pontos = [
            (self.x - 8, self.y + 14),
            (self.x + 8, self.y + 14),
            (self.x, self.y + 14 + tamanho_chama),
        ]
        pygame.draw.polygon(superficie, self.cor_chama, chama_pontos)


# ------------------------------------------------------------------
# TIROS
# ------------------------------------------------------------------
class Tiro:
    def __init__(self, x, y, direcao):
        self.x = x
        self.y = y
        self.direcao = direcao  # -1 sobe (jogador), 1 desce (inimigo)
        self.velocidade = 11
        self.raio = 4
        self.cor = AMARELO if direcao == -1 else ROXO

    def atualizar(self):
        self.y += self.velocidade * self.direcao

    def fora_da_tela(self):
        return self.y < -10 or self.y > ALTURA + 10

    def desenhar(self, superficie):
        pygame.draw.circle(superficie, self.cor, (int(self.x), int(self.y)), self.raio)
        pygame.draw.circle(superficie, BRANCO, (int(self.x), int(self.y)), self.raio, width=1)


# ------------------------------------------------------------------
# INIMIGOS
# ------------------------------------------------------------------
class Inimigo:
    def __init__(self, dificuldade, fase_do_jogo):
        self.x = random.uniform(40, LARGURA - 40)
        self.y = -30
        sorteio = random.random()
        if fase_do_jogo >= 3 and sorteio < 0.2:
            self.tipo = "tanque"
            self.cor = AZUL_ACO
            self.velocidade = random.uniform(0.8, 1.3) + dificuldade * 0.05
            self.raio_colisao = 22
            self.pontos = 40
            self.vida = 3
        elif sorteio < 0.6:
            self.tipo = "caçador"
            self.cor = VERMELHO
            self.velocidade = random.uniform(2, 3) + dificuldade * 0.15
            self.raio_colisao = 14
            self.pontos = 10
            self.vida = 1
        else:
            self.tipo = "atirador"
            self.cor = ROXO
            self.velocidade = random.uniform(1.2, 2)
            self.raio_colisao = 16
            self.pontos = 20
            self.vida = 1
        self.vida_maxima = self.vida
        self.tempo_tiro = random.randint(40, 100)
        self.fase = random.uniform(0, math.tau)

    def atualizar(self, jogador, tiros_inimigos):
        self.fase += 0.05
        self.x += math.sin(self.fase) * 1.5
        self.y += self.velocidade

        if self.tipo in ("atirador", "tanque"):
            self.tempo_tiro -= 1
            if self.tempo_tiro <= 0 and 0 < self.y < ALTURA - 60:
                tiros_inimigos.append(Tiro(self.x, self.y + 10, 1))
                self.tempo_tiro = random.randint(70, 130) if self.tipo == "atirador" else random.randint(100, 160)

    def fora_da_tela(self):
        return self.y > ALTURA + 40

    def desenhar(self, superficie):
        if self.tipo == "tanque":
            pontos = [
                (self.x, self.y - 20),
                (self.x - 18, self.y - 4),
                (self.x - 18, self.y + 14),
                (self.x, self.y + 22),
                (self.x + 18, self.y + 14),
                (self.x + 18, self.y - 4),
            ]
        else:
            pontos = [
                (self.x, self.y - 16),
                (self.x - 14, self.y + 12),
                (self.x, self.y + 4),
                (self.x + 14, self.y + 12),
            ]
        pygame.draw.polygon(superficie, self.cor, pontos)
        pygame.draw.polygon(superficie, BRANCO, pontos, width=2)

        # barra de vida (só aparece em inimigos que aguentam mais de um tiro)
        if self.vida_maxima > 1:
            largura_barra = 34
            proporcao = max(0, self.vida / self.vida_maxima)
            topo = self.y - 32
            pygame.draw.rect(superficie, (60, 60, 60), (self.x - largura_barra / 2, topo, largura_barra, 5))
            pygame.draw.rect(superficie, VERDE, (self.x - largura_barra / 2, topo, largura_barra * proporcao, 5))


# ------------------------------------------------------------------
# TEXTO COM CONTORNO (fica mais legível sobre o fundo estrelado)
# ------------------------------------------------------------------
def desenhar_texto(superficie, texto, fonte, cor, x, y, centralizado=True):
    base = fonte.render(texto, True, cor)
    contorno = fonte.render(texto, True, PRETO)
    rect = base.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        superficie.blit(contorno, (rect.x + dx, rect.y + dy))
    superficie.blit(base, rect)


# ------------------------------------------------------------------
# LOOP PRINCIPAL DO JOGO
# ------------------------------------------------------------------
def novo_jogo(progresso):
    return {
        "jogador": Jogador(progresso["skin_atual"]),
        "tiros": [],
        "tiros_inimigos": [],
        "inimigos": [],
        "particulas": [],
        "pontuacao": 0,
        "tempo_spawn": 0,
        "fim_de_jogo": False,
        "tremor": 0,
        "fase": 1,
        "banner_fase_tempo": 0,
        "banner_skin_texto": "",
        "banner_skin_tempo": 0,
        "recorde_salvo": False,
    }


BOTAO_PAUSA = (LARGURA // 2, 32, 24)  # x, y, raio


def sobre_botao_pausa(pos):
    return math.hypot(pos[0] - BOTAO_PAUSA[0], pos[1] - BOTAO_PAUSA[1]) <= BOTAO_PAUSA[2] + 10


def desenhar_botao_pausa(superficie, pausado):
    x, y, r = BOTAO_PAUSA
    pygame.draw.circle(superficie, (15, 15, 30), (x, y), r)
    pygame.draw.circle(superficie, BRANCO, (x, y), r, width=2)
    if pausado:
        pygame.draw.polygon(superficie, BRANCO, [(x - 6, y - 10), (x + 11, y), (x - 6, y + 10)])
    else:
        pygame.draw.rect(superficie, BRANCO, (x - 9, y - 10, 6, 20))
        pygame.draw.rect(superficie, BRANCO, (x + 3, y - 10, 6, 20))


def main():
    estrelas = CampoDeEstrelas()
    progresso = carregar_progresso()
    estado = novo_jogo(progresso)

    auto_tiro = False  # liga/desliga com a tecla F
    pausado = False    # liga/desliga com a tecla P ou clicando no botão

    rodando = True
    while rodando:
        deslocamento_tremor = (0, 0)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            if evento.type == pygame.WINDOWFOCUSLOST and not estado["fim_de_jogo"]:
                pausado = True
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and not estado["fim_de_jogo"]:
                if pausado or sobre_botao_pausa(evento.pos):
                    pausado = not pausado
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                if evento.key == pygame.K_p and not estado["fim_de_jogo"]:
                    pausado = not pausado
                if evento.key == pygame.K_f:
                    auto_tiro = not auto_tiro
                if evento.key == pygame.K_RETURN and estado["fim_de_jogo"]:
                    estado = novo_jogo(progresso)
                for indice, tecla in enumerate([pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]):
                    if evento.key == tecla and indice in skins_desbloqueadas(progresso):
                        progresso["skin_atual"] = indice
                        estado["jogador"].definir_skin(indice)
                        salvar_progresso(progresso)

        teclas = pygame.key.get_pressed()
        if not pausado:
            estrelas.atualizar()

        if not estado["fim_de_jogo"] and not pausado:
            jogador = estado["jogador"]
            jogador.atualizar(teclas)

            # tiro contínuo: barra de espaço, botão esquerdo do mouse ou tiro automático (F)
            mouse_atirando = pygame.mouse.get_pressed()[0] and not sobre_botao_pausa(pygame.mouse.get_pos())
            if teclas[pygame.K_SPACE] or mouse_atirando or auto_tiro:
                jogador.atirar(estado["tiros"])

            # dificuldade aumenta com a pontuação
            dificuldade = estado["pontuacao"] / 150

            nova_fase = 1 + estado["pontuacao"] // 200
            if nova_fase != estado["fase"]:
                estado["fase"] = nova_fase
                estado["banner_fase_tempo"] = 100
                tocar(SOM_FASE)

            estado["tempo_spawn"] -= 1
            if estado["tempo_spawn"] <= 0:
                estado["inimigos"].append(Inimigo(dificuldade, estado["fase"]))
                estado["tempo_spawn"] = max(18, int(45 - dificuldade * 5))

            for tiro in estado["tiros"]:
                tiro.atualizar()
            estado["tiros"] = [t for t in estado["tiros"] if not t.fora_da_tela()]

            for tiro in estado["tiros_inimigos"]:
                tiro.atualizar()
            estado["tiros_inimigos"] = [t for t in estado["tiros_inimigos"] if not t.fora_da_tela()]

            for inimigo in estado["inimigos"]:
                inimigo.atualizar(jogador, estado["tiros_inimigos"])

            # colisão: tiro do jogador x inimigo
            inimigos_vivos = []
            recorde_anterior = progresso["recorde"]
            for inimigo in estado["inimigos"]:
                for tiro in estado["tiros"][:]:
                    dist = math.hypot(tiro.x - inimigo.x, tiro.y - inimigo.y)
                    if dist < inimigo.raio_colisao:
                        estado["tiros"].remove(tiro)
                        inimigo.vida -= 1
                        criar_explosao(estado["particulas"], tiro.x, tiro.y, BRANCO, 6)
                        break
                if inimigo.vida <= 0:
                    estado["pontuacao"] += inimigo.pontos
                    criar_explosao(estado["particulas"], inimigo.x, inimigo.y, inimigo.cor)
                    estado["tremor"] = 8
                    tocar(SOM_EXPLOSAO)
                    if estado["pontuacao"] > progresso["recorde"]:
                        progresso["recorde"] = estado["pontuacao"]
                elif inimigo.fora_da_tela():
                    pass
                else:
                    inimigos_vivos.append(inimigo)
            estado["inimigos"] = inimigos_vivos

            # se algum recorde novo acabou de desbloquear uma skin, avisa na hora
            if progresso["recorde"] > recorde_anterior:
                desbloqueadas_antes = {i for i, s in enumerate(SKINS) if recorde_anterior >= s["recorde"]}
                desbloqueadas_agora = set(skins_desbloqueadas(progresso))
                novas = desbloqueadas_agora - desbloqueadas_antes
                if novas:
                    nome_skin = SKINS[max(novas)]["nome"]
                    estado["banner_skin_texto"] = f"NOVA SKIN DESBLOQUEADA: {nome_skin}!"
                    estado["banner_skin_tempo"] = 150
                    tocar(SOM_SKIN)
                salvar_progresso(progresso)

            # colisão: inimigo x jogador
            if jogador.invencivel == 0:
                for inimigo in estado["inimigos"][:]:
                    dist = math.hypot(inimigo.x - jogador.x, inimigo.y - jogador.y)
                    if dist < inimigo.raio_colisao + jogador.raio_colisao:
                        estado["inimigos"].remove(inimigo)
                        criar_explosao(estado["particulas"], jogador.x, jogador.y, VERMELHO, 30)
                        jogador.vidas -= 1
                        jogador.invencivel = 90
                        estado["tremor"] = 16
                        if jogador.vidas <= 0:
                            estado["fim_de_jogo"] = True
                            tocar(SOM_FIM_DE_JOGO)
                        else:
                            tocar(SOM_DANO)

            # colisão: tiro inimigo x jogador
            if jogador.invencivel == 0:
                for tiro in estado["tiros_inimigos"][:]:
                    dist = math.hypot(tiro.x - jogador.x, tiro.y - jogador.y)
                    if dist < jogador.raio_colisao:
                        estado["tiros_inimigos"].remove(tiro)
                        criar_explosao(estado["particulas"], jogador.x, jogador.y, VERMELHO, 20)
                        jogador.vidas -= 1
                        jogador.invencivel = 90
                        estado["tremor"] = 14
                        if jogador.vidas <= 0:
                            estado["fim_de_jogo"] = True
                            tocar(SOM_FIM_DE_JOGO)
                        else:
                            tocar(SOM_DANO)

        if not pausado:
            for p in estado["particulas"]:
                p.atualizar()
            estado["particulas"] = [p for p in estado["particulas"] if p.vida > 0]

            if estado["banner_fase_tempo"] > 0:
                estado["banner_fase_tempo"] -= 1
            if estado["banner_skin_tempo"] > 0:
                estado["banner_skin_tempo"] -= 1

            if estado["tremor"] > 0:
                estado["tremor"] -= 1
                deslocamento_tremor = (random.randint(-6, 6), random.randint(-6, 6))

        # ---------------- DESENHO ----------------
        camada = pygame.Surface((LARGURA, ALTURA))
        camada.fill(PRETO)
        estrelas.desenhar(camada)

        if not estado["fim_de_jogo"]:
            estado["jogador"].desenhar(camada)
        for tiro in estado["tiros"]:
            tiro.desenhar(camada)
        for tiro in estado["tiros_inimigos"]:
            tiro.desenhar(camada)
        for inimigo in estado["inimigos"]:
            inimigo.desenhar(camada)
        for p in estado["particulas"]:
            p.desenhar(camada)

        desenhar_texto(camada, f"PONTOS: {estado['pontuacao']}", fonte_media, VERDE, 110, 30)
        desenhar_texto(camada, f"FASE {estado['fase']}", fonte_pequena, AMARELO, 110, 58)
        desenhar_texto(
            camada,
            f"Tiro automático [F]: {'LIGADO' if auto_tiro else 'desligado'}",
            fonte_pequena, CIANO if auto_tiro else BRANCO, 15, 76, centralizado=False,
        )
        vidas_txt = "❤" * max(0, estado["jogador"].vidas) if not estado["fim_de_jogo"] else ""
        desenhar_texto(camada, vidas_txt, fonte_media, VERMELHO, LARGURA - 90, 30)

        if estado["banner_fase_tempo"] > 0:
            desenhar_texto(camada, f"FASE {estado['fase']}!", fonte_grande, AMARELO, LARGURA / 2, ALTURA / 2 - 120)

        if estado["banner_skin_tempo"] > 0:
            desenhar_texto(camada, estado["banner_skin_texto"], fonte_media, VERDE, LARGURA / 2, 100)

        if estado["fim_de_jogo"]:
            desenhar_texto(camada, "FIM DE JOGO", fonte_grande, VERMELHO, LARGURA / 2, ALTURA / 2 - 40)
            desenhar_texto(camada, f"Pontuação final: {estado['pontuacao']}", fonte_media, BRANCO, LARGURA / 2, ALTURA / 2 + 20)
            desenhar_texto(camada, "Pressione ENTER para jogar de novo", fonte_pequena, CIANO, LARGURA / 2, ALTURA / 2 + 60)

            nome_skin_atual = SKINS[progresso["skin_atual"]]["nome"]
            desenhar_texto(camada, f"Nave atual: {nome_skin_atual}", fonte_pequena, BRANCO, LARGURA / 2, ALTURA / 2 + 95)
            desbloqueadas = skins_desbloqueadas(progresso)
            linha_skins = "  ".join(
                f"[{i + 1}] {s['nome']}" if i in desbloqueadas else f"[{i + 1}] ??? ({s['recorde']} pts)"
                for i, s in enumerate(SKINS)
            )
            desenhar_texto(camada, linha_skins, fonte_pequena, CIANO, LARGURA / 2, ALTURA / 2 + 125)
            desenhar_texto(camada, "Pressione 1-4 para trocar de nave", fonte_pequena, BRANCO, LARGURA / 2, ALTURA / 2 + 150)

        if not estado["fim_de_jogo"]:
            desenhar_botao_pausa(camada, pausado)

        if pausado:
            veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            veu.fill((5, 5, 15, 165))
            camada.blit(veu, (0, 0))
            desenhar_botao_pausa(camada, pausado)
            desenhar_texto(camada, "PAUSADO", fonte_grande, AMARELO, LARGURA / 2, ALTURA / 2 - 20)
            desenhar_texto(camada, "Clique ou aperte P para continuar", fonte_pequena, CIANO, LARGURA / 2, ALTURA / 2 + 30)

        tela.blit(camada, deslocamento_tremor)
        pygame.display.flip()
        relogio.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
