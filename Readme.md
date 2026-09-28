# 🚀 Nave Espacial

Um jogo de nave espacial feito com HTML, JavaScript e Canvas, criado para mostrar a uma criança o poder da programação. Roda direto no navegador, no computador ou no celular, sem instalar nada.

## ▶️ Jogue agora

**https://duckblox.github.io/nave-espacial/**

## 🎮 Controles

| Dispositivo | Ação |
|---|---|
| Teclado | Setas ou **W A S D** movem a nave |
| Teclado | **Barra de espaço** atira (segure para tiro contínuo) |
| Teclado | **F** liga/desliga o tiro automático |
| Teclado | **P** ou **Esc** pausa e continua |
| Mouse | Clique no botão ⏸ (no topo da tela) pausa; clique em qualquer lugar continua |
| Teclado | Teclas **1 a 4** trocam de nave (quando desbloqueada) |
| Mouse | Segure o botão esquerdo para tiro contínuo |
| Celular | Toque e arraste para mover; a nave atira sozinha |
| Celular | Toque no botão ⏸ (no topo) para pausar; toque na tela para continuar |
| Fim de jogo | **Enter** (ou toque na tela) para jogar de novo |

## ✨ Recursos

- Fundo estrelado com efeito de profundidade (parallax)
- Explosões com partículas e tremor de tela
- Efeitos sonoros gerados por código, sem arquivos de áudio
- **Fases:** a cada 200 pontos começa uma fase nova, com mais dificuldade
- **Três tipos de inimigos:** caçador, atirador e tanque (a partir da fase 3, aguenta 3 tiros)
- **Skins desbloqueáveis** por recorde de pontos:

| Tecla | Skin | Pontos necessários |
|---|---|---|
| 1 | Padrão | 0 |
| 2 | Fantasma | 150 |
| 3 | Fênix | 400 |
| 4 | Esmeralda | 800 |

- Recorde e skin escolhida ficam salvos no próprio navegador

## 🛠️ Tecnologias

- HTML5 + Canvas 2D
- JavaScript puro (sem bibliotecas)
- Web Audio API para os sons
- `localStorage` para salvar o progresso

## 📁 Estrutura

```
nave-espacial/
├── index.html            # versão web (HTML, CSS e JavaScript)
├── python/
│   └── nave_espacial.py  # versão em Python com pygame
├── .gitignore
└── README.md             # este arquivo
```

## 💻 Rodando a versão web localmente

Basta baixar o `index.html` e abri-lo no navegador. Não precisa de servidor nem de instalação.

## 🐍 Versão em Python

O jogo nasceu como um protótipo em Python com `pygame`, e a versão web foi convertida a partir dele. As duas têm as mesmas ideias: fases, inimigos, efeitos sonoros gerados por código e skins desbloqueáveis.

Para rodar:

```bash
pip install pygame-ce
python python/nave_espacial.py
```

Detalhes da versão Python:

- Controles: setas ou **W A S D** movem, **espaço** ou botão do mouse atira (segure para tiro contínuo), **F** liga/desliga o tiro automático, **P** (ou clique no botão ⏸) pausa e continua, **1 a 4** trocam de nave, **Enter** reinicia, **Esc** fecha o jogo
- O jogo também pausa sozinho quando a janela perde o foco
- O recorde e a skin escolhida ficam salvos no arquivo `nave_progresso.json`, criado na mesma pasta do script
- Usa `pygame-ce` (fork da comunidade, compatível com o código do `pygame`) porque tem pacotes prontos para versões mais novas do Python