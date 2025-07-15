import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import random
import os
import time
import requests
import platform
import string
import json
import sys
import pygame.mixer
import logging
import unicodedata
from bs4 import BeautifulSoup, Tag
import webbrowser

# --- Configuração do Logging ---
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_log.txt")
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.info("--- INÍCIO DA EXECUÇÃO DO JOGO ---")

# --- Classe de Configurações do Usuário ---
class ConfiguracoesUsuario:
    def __init__(self):
        self.arquivo_config = "configuracoes.json"
        self.configuracoes_padrao = {
            "audio": {
                "volume_geral": 0.7,
                "volume_musica": 0.5,
                "volume_efeitos": 0.7,
                "som_ativado": True,
                "musica_ativada": True
            },
            "interface": {
                "tema": "escuro",  # escuro, claro
                "tamanho_fonte": "normal",  # pequeno, normal, grande
                "animacoes_ativadas": True,
                "tooltips_ativados": True
            },
            "jogo": {
                "dificuldade_padrao": "Médio",
                "penalidade_erro": 3.0,
                "tempo_limite": 0,  # 0 = sem limite
                "mostrar_dicas": True,
                "usar_palavras_comuns": True
            },
            "ranking": {
                "manter_historico": True,
                "max_entradas_ranking": 10,
                "mostrar_ranking_apos_jogo": True
            },
            "perfil": {
                "nome_padrao": "JOGADOR"
            }
        }
        self.configuracoes = self.carregar_configuracoes()
    
    def carregar_configuracoes(self):
        """Carrega as configurações do arquivo JSON ou cria com valores padrão"""
        try:
            if os.path.exists(self.arquivo_config):
                with open(self.arquivo_config, "r", encoding="utf-8") as f:
                    config_carregada = json.load(f)
                    logging.info("Configurações carregadas com sucesso.")
                    return self.merge_configuracoes(self.configuracoes_padrao, config_carregada)
            else:
                logging.info("Arquivo de configurações não encontrado. Criando com valores padrão.")
                self.salvar_configuracoes(self.configuracoes_padrao)
                return self.configuracoes_padrao
        except Exception as e:
            logging.error(f"Erro ao carregar configurações: {e}")
            return self.configuracoes_padrao
    
    def merge_configuracoes(self, config_padrao, config_carregada):
        """Mescla configurações carregadas com padrões, garantindo compatibilidade"""
        config_final = config_padrao.copy()
        
        for secao in config_carregada:
            if secao in config_final:
                if isinstance(config_final[secao], dict):
                    config_final[secao].update(config_carregada[secao])
                else:
                    config_final[secao] = config_carregada[secao]
            else:
                config_final[secao] = config_carregada[secao]
        
        return config_final
    
    def salvar_configuracoes(self, config=None):
        """Salva as configurações no arquivo JSON"""
        if config is None:
            config = self.configuracoes
        
        try:
            with open(self.arquivo_config, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logging.info("Configurações salvas com sucesso.")
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar configurações: {e}")
            return False
    
    def obter_config(self, secao, chave, valor_padrao=None):
        """Obtém um valor específico das configurações"""
        try:
            return self.configuracoes[secao][chave]
        except KeyError:
            if valor_padrao is not None:
                return valor_padrao
            return self.configuracoes_padrao[secao][chave]
    
    def definir_config(self, secao, chave, valor):
        """Define um valor específico nas configurações"""
        if secao not in self.configuracoes:
            self.configuracoes[secao] = {}
        self.configuracoes[secao][chave] = valor
        self.salvar_configuracoes()
        logging.info(f"Configuração atualizada: {secao}.{chave} = {valor}")
    
    def resetar_configuracoes(self):
        """Reseta todas as configurações para os valores padrão"""
        self.configuracoes = self.configuracoes_padrao.copy()
        self.salvar_configuracoes()
        logging.info("Configurações resetadas para valores padrão.")

# ============================================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================================

# --- CORES ---
# =========================================================================
# NOVA PALETA DE CORES (SUGESTÃO DO USUÁRIO)
# =========================================================================
# #5F6F52 (verde escuro), #A9B388 (verde claro), #FEFAE0 (bege claro),
# #F9EBC7 (amarelo pastel), #B99470 (marrom claro), #C4661F (laranja), #783D19 (marrom escuro)
COR_FUNDO_PRINCIPAL = "#F9EBC7"      # Amarelo pastel confortável
COR_FUNDO_SECUNDARIO = "#F9EBC7"      # Amarelo pastel
COR_TEXTO_CLARO = "#5F6F52"           # Verde escuro
COR_TEXTO_CLARO_DESTACADO = "#C4661F" # Laranja
COR_AZUL_SUAVE_BOTOES = "#A9B388"     # Verde claro (usado para botões)
COR_VERDE_ACERTO = "#A9B388"          # Verde claro
COR_VERDE_ACERTO_CLARO = "#B99470"    # Marrom claro (destaque)
COR_VERMELHO_ERRO = "#C4661F"         # Laranja (erro)
COR_AMARELO_AVISO = "#F9EBC7"         # Amarelo pastel
COR_BOTAO_PRESSIONADO = "#B99470"     # Marrom claro
COR_FUNDO_ESCURO_INPUT = "#E6E2C3"    # Bege escuro suave
COR_ROSA_PASTEL = "#F9EBC7"           # Amarelo pastel (não usado)
COR_LILAS_PASTEL = "#A9B388"          # Verde claro (não usado)
COR_BORDA = "#783D19"                 # Marrom escuro

# --- CONFIGURAÇÕES DO JOGO ---
ARQUIVO_RANKING = "ranking_solo.json"
ARQUIVO_DICIONARIO = "palavras.txt"
URL_DICIONARIO_ONLINE = "https://raw.githubusercontent.com/uefs/dic-ptbr-latex/master/pt_BR.dic"
URL_DICIONARIO_COMUM = "https://raw.githubusercontent.com/dwyl/english-words/master/words.txt"

# NOVA OPÇÃO: verificar definição online ao sortear do pt_BR.dic
VERIFICAR_DEFINICAO_ONLINE = True  # Pode ser alterado em configurações futuramente

# ============================================================================
# REGRAS DE DIFICULDADE CENTRALIZADAS
# =========================================================================
REGRAS_DIFICULDADE = {
    "Fácil":    {"min": 4, "max": 5,  "descricao": "Palavras de 4 ou 5 letras"},
    "Médio":    {"min": 6, "max": 7,  "descricao": "Palavras de 6 ou 7 letras"},
    "Difícil":  {"min": 8, "max": 20, "descricao": "Palavras de 8 ou mais letras"},
}

# ============================================================================
# CLASSE PRINCIPAL DO JOGO
# =========================================================================

class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JOGO DE ADIVINHAÇÃO DE PALAVRAS - DESAFIO DE RIVAIS")
        self.root.config(bg=COR_FUNDO_PRINCIPAL)
        
        # Inicializa o sistema de configurações
        self.config = ConfiguracoesUsuario()

        # Sempre fullscreen
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', self.mostrar_opcoes_esc)

        self.centralizar_janela(self.root)

        # ============================================================================
        # INICIALIZAÇÃO DAS VARIÁVEIS DE ESTADO
        # ============================================================================
        
        # --- Estado do Jogo Atual ---
        self.palavra_secreta = ""
        self.letras_embaralhadas = ""
        self.palavra_adivinhada_entries = []
        self.entry_vars_adivinhacao = []
        self.erros_rodada_atual = 0
        self.letras_ja_tentadas_exibicao = set()
        self.letras_erradas_exibicao = set()
        self.letras_erradas_desde_ultimo_acerto = set()  # NOVO: letras erradas desde o último acerto
        self.indice_atual = 0
        self.partida_desistida = False

        # --- Controle de Tempo ---
        self.tempo_inicio_rodada = 0
        self.timer_id = None
        self.tempo_total_jogador_atual = 0.0
        self.tempo_penalidade_acumulada = 0.0

        # --- Sistema de Jogadores ---
        self.jogadores = []
        self.jogador_atual_idx = 0
        self.jogador_definidor_idx = 0
        self.num_jogadores_total = 0
        self.entry_nomes_jogadores = []

        # --- Interface ---
        self.botoes_letras_embaralhadas = []

        # --- Variáveis Tkinter ---
        self.dificuldade_selecionada = tk.StringVar(root)
        self.dificuldade_selecionada.set(self.config.obter_config("jogo", "dificuldade_padrao"))
        self.modo_jogo_selecionado = tk.StringVar(root)
        self.modo_jogo_selecionado.set("")
        self.palavra_secreta_var = tk.StringVar(root)
        self.num_jogadores_multiplayer = tk.IntVar(root)
        self.num_jogadores_multiplayer.set(2)

        # --- Sistema de Ranking ---
        self.ranking_solo = {
            'comum_on': {'Fácil': [], 'Médio': [], 'Difícil': []},
            'comum_off': {'Fácil': [], 'Médio': [], 'Difícil': []}
        }
        self.ARQUIVO_RANKING = ARQUIVO_RANKING

        # --- Sistema de Dicionário ---
        self.dicionario_palavras = set()
        self.URL_DICIONARIO_ONLINE = URL_DICIONARIO_ONLINE
        self.URL_DICIONARIO_COMUM = URL_DICIONARIO_COMUM
        self.ARQUIVO_LOCAL_DICIONARIO = ARQUIVO_DICIONARIO
        
        # Palavras comuns educativas do dia a dia (filtradas para conteúdo apropriado)
        self.PALAVRAS_COMUNS = {
            # Objetos da casa
            "casa", "carro", "livro", "mesa", "porta", "janela", "cama", "sopa", "pão", "água",
            "café", "leite", "fruta", "carne", "peixe", "arroz", "feijão", "sal", "açúcar",
            "copo", "prato", "garfo", "faca", "colher", "panela", "fogão", "geladeira",
            "toalha", "sabão", "escova", "pasta", "papel", "caneta", "lápis", "borracha",
            "mala", "mochila", "carteira", "chave", "lâmpada", "tela", "corda", "fita",
            
            # Natureza e clima
            "tempo", "sol", "lua", "estrela", "nuvem", "chuva", "vento", "frio", "quente",
            "árvore", "flor", "grama", "terra", "pedra", "areia", "mar", "rio", "montanha",
            "nuvem", "neve", "gelo", "fogo", "fumaça", "vapor", "poeira", "lama",
            
            # Família e pessoas
            "amigo", "família", "pai", "mãe", "filho", "filha", "irmão", "irmã", "tio", "tia",
            "avô", "avó", "primo", "prima", "namorado", "namorada", "marido", "esposa",
            "vizinho", "professor", "médico", "enfermeiro", "policial", "bombeiro",
            "aluno", "estudante", "criança", "adulto", "idoso", "jovem", "senhor", "senhora",
            
            # Lugares e locais
            "escola", "trabalho", "cidade", "rua", "praça", "parque", "loja", "banco", "hospital",
            "padaria", "farmácia", "posto", "mercado", "shopping", "cinema", "teatro", "museu",
            "igreja", "templo", "estação", "aeroporto", "porto", "ponte", "túnel", "biblioteca",
            "restaurante", "hotel", "pousada", "sala", "cozinha", "banheiro", "quarto", "escritório",
            
            # Tecnologia e comunicação
            "telefone", "computador", "televisão", "rádio", "jornal", "revista", "música", "filme",
            "internet", "email", "mensagem", "foto", "câmera", "bateria", "carregador",
            "tela", "teclado", "mouse", "impressora", "scanner", "tablet", "celular",
            
            # Cores e características
            "cor", "vermelho", "azul", "verde", "amarelo", "preto", "branco", "rosa", "roxo",
            "laranja", "marrom", "cinza", "dourado", "prateado", "transparente", "colorido",
            "claro", "escuro", "brilhante", "fosco", "liso", "áspero", "macio", "duro",
            
            # Linguagem e comunicação
            "número", "letra", "palavra", "frase", "texto", "história", "conto", "poema",
            "nome", "sobrenome", "endereço", "telefone", "email", "senha", "código",
            "língua", "idioma", "conversa", "pergunta", "resposta", "explicação",
            
            # Atividades e esportes
            "bola", "jogo", "brincar", "correr", "andar", "sentar", "dormir", "acordar",
            "nadar", "pular", "dançar", "cantar", "pintar", "desenhar", "fotografar",
            "futebol", "basquete", "vôlei", "tênis", "natação", "ciclismo", "caminhada",
            "corrida", "saltar", "girar", "balançar", "escorregar", "subir", "descer",
            
            # Ações do dia a dia
            "comer", "beber", "lavar", "limpar", "cozinhar", "estudar", "ler", "escrever",
            "pensar", "falar", "ouvir", "ver", "tocar", "cheirar", "provar", "sentir",
            "trabalhar", "estudar", "aprender", "ensinar", "ajudar", "cuidar", "proteger",
            "guardar", "procurar", "encontrar", "perder", "ganhar", "dar", "receber",
            
            # Emoções e sentimentos
            "feliz", "triste", "bravo", "calmo", "rápido", "lento", "grande", "pequeno",
            "alegre", "sério", "nervoso", "tranquilo", "ansioso", "relaxado", "cansado",
            "energético", "preguiçoso", "inteligente", "esperto", "bonito", "feio",
            "amoroso", "carinhoso", "gentil", "educado", "respeitoso", "honesto",
            
            # Espaço e posição
            "alto", "baixo", "longe", "perto", "dentro", "fora", "cima", "baixo",
            "esquerda", "direita", "frente", "trás", "centro", "lado", "meio",
            "largo", "estreito", "curto", "comprido", "redondo", "quadrado", "triangular",
            
            # Tempo e datas
            "manhã", "tarde", "noite", "hoje", "ontem", "amanhã", "semana", "mês", "ano",
            "verão", "inverno", "primavera", "outono", "segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo",
            "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
            
            # Alimentos e bebidas
            "banana", "maçã", "laranja", "uva", "morango", "abacaxi", "manga", "pera",
            "batata", "cenoura", "tomate", "cebola", "alho", "pimenta", "azeite",
            "suco", "refrigerante", "chocolate", "bolo", "biscoito", "sorvete", "pizza",
            "queijo", "manteiga", "mel", "limão", "abacate", "kiwi", "framboesa",
            
            # Animais
            "cachorro", "gato", "cavalo", "vaca", "porco", "galinha", "pato", "pássaro",
            "peixe", "abelha", "formiga", "borboleta", "mosca", "mosquito", "aranha",
            "coelho", "ovelha", "cabra", "porco", "pato", "ganso", "pombo", "coruja",
            
            # Roupas e acessórios
            "camisa", "calça", "vestido", "saia", "sapato", "tênis", "sandália", "meia",
            "boné", "chapéu", "óculos", "relógio", "anel", "colar", "pulseira", "cinto",
            "casaco", "blusa", "short", "bermuda", "jaqueta", "suéter", "cachecol",
            
            # Transporte
            "ônibus", "trem", "avião", "barco", "bicicleta", "moto", "caminhão", "táxi",
            "metrô", "tram", "helicóptero", "navio", "lancha", "canoa", "patinete",
            "carroça", "trator", "ambulância", "carro", "van", "furgão", "carreta"
        }

        # Lista de palavras difíceis para o modo difícil
        self.PALAVRAS_DIFICEIS = {
            # Palavras complexas e menos comuns
            "abduzir", "acrimônia", "adstrito", "alarido", "alcunha", "âmago", "ardiloso", "arroubo", "atoleimado",
            "beneplácito", "cacofonia", "candente", "cáustico", "cizânia", "concomitante", "consubstanciar", "contumaz",
            "deleter", "desídia", "dilapidar", "dissonância", "efêmero", "elucubrar", "empírico", "enclausurar",
            "escrúpulo", "estulto", "eufemismo", "exíguo", "fúlgido", "galvanizar", "hegemonizar", "hermético",
            "idílico", "impertérrito", "incólume", "indolente", "inefável", "inócuo", "insólito", "intrínseco",
            "lacônico", "lúgubre", "magnânimo", "mendaz", "mísero", "nefando", "obstinado", "oprobrio",
            "perfunctório", "pernicioso", "pertinaz", "pífio", "precário", "probo", "pródigo", "prudente",
            "quimérico", "rebuscado", "recíproco", "redentor", "refinado", "relutante", "remoto", "resiliente",
            "sagaz", "sórdido", "sucinto", "sutil", "tenaz", "tímido", "tranquilo", "ubíquo",
            "vacilante", "veraz", "verossímil", "vigoroso", "virtuoso", "volátil", "voraz", "zeloso"
        }

        # Lista de palavras inadequadas para filtrar
        self.PALAVRAS_INADEQUADAS = {
            # Palavrões e termos ofensivos
            "porra", "caralho", "puta", "merda", "foda", "cacete", "buceta", "pau", "pinto",
            "carai", "porcaria", "bosta", "merdoso", "fodido", "puto", "caralhudo",
            
            # Termos sexuais inadequados
            "sexo", "pênis", "vagina", "pornô", "porno", "erótico", "sexual", "intimo",
            "nudez", "pelado", "nu", "nua", "transar", "foder", "meter", "comer",
            
            # Termos violentos ou inadequados
            "morte", "matar", "assassinar", "sangue", "violência", "briga", "luta",
            "droga", "cigarro", "álcool", "bebida", "embriagado", "drogado",
            
            # Outros termos inadequados
            "idiota", "imbecil", "estúpido", "burro", "retardado", "deficiente"
        }

        # Variáveis para Sons
        self.som_acerto = None
        self.som_erro = None
        self.som_vitoria_palavra = None
        self.musica_menu = None
        self.som_teclado = None
        self.som_fim_jogo = None
        self.som_iniciar_rodada = None

        # --- Inicialização do Pygame Mixer ---
        try:
            pygame.mixer.init()
            logging.info("Pygame mixer inicializado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao inicializar Pygame mixer: {e}")
            messagebox.showerror("Erro Crítico", f"Não foi possível inicializar o módulo de áudio (Pygame Mixer).\nO jogo pode não funcionar corretamente. Erro: {e}")
            sys.exit(1)

        # Inicializa o objeto style aqui, tornando-o um atributo da instância
        self.style = ttk.Style()
        self.aplicar_estilos_ttk()
        self.root.protocol("WM_DELETE_WINDOW", self.confirmar_saida)

        # Carrega o dicionário e o ranking antes de carregar os sons
        self.carregar_dicionario()
        self.carregar_ranking()
        self.carregar_sons() # Carrega os sons na inicialização do jogo
        
        # Cria os frames iniciais uma única vez na inicialização
        self._criar_frames_iniciais() 
        self.iniciar_selecao_modo() # Sempre inicia na tela de seleção de modo

        # Persistência de palavras já sorteadas
        self.arquivo_palavras_usadas = "palavras_usadas.json"
        self.palavras_usadas = self.carregar_palavras_usadas()
        # Persistência de palavras usadas no multiplayer
        self.arquivo_palavras_multiplayer = "palavras_multiplayer.json"
        self.palavras_multiplayer = self.carregar_palavras_multiplayer()
        self.ordem_palavra_multiplayer = self.palavras_multiplayer.get("__ordem__", 0)

    # ============================================================================
    # MÉTODOS DE CONFIGURAÇÃO E INICIALIZAÇÃO
    # ============================================================================

    def centralizar_janela(self, janela):
        janela.update_idletasks()
        largura = janela.winfo_width()
        altura = janela.winfo_height()
        x = (janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (janela.winfo_screenheight() // 2) - (altura // 2)
        janela.geometry(f'+{x}+{y}')
        logging.info(f"Janela centralizada: {largura}x{altura} em {x},{y}")

    def aplicar_estilos_ttk(self):
        self.style.theme_use('clam')
        # Botão padrão
        self.style.configure("TButton",
            font=("Segoe UI", 13, "bold"),
            foreground=COR_TEXTO_CLARO,
            background=COR_AZUL_SUAVE_BOTOES,
            borderwidth=0,
            padding=10,
            relief="flat",
            focusthickness=2,
            focuscolor=COR_BORDA,
            bordercolor=COR_BORDA,
            lightcolor=COR_BOTAO_PRESSIONADO,
            darkcolor=COR_BORDA,
            highlightthickness=0)
        self.style.map("TButton",
            background=[('active', COR_BOTAO_PRESSIONADO), ('pressed', COR_BOTAO_PRESSIONADO)],
            foreground=[('disabled', '#B5B5B5')])
        # Botão de letra
        self.style.configure("Letter.TButton",
            font=("Segoe UI", 16, "bold"),
            foreground=COR_TEXTO_CLARO,
            background=COR_AZUL_SUAVE_BOTOES,
            borderwidth=0,
            padding=8,
            width=3,
            relief="raised",
            focusthickness=2,
            focuscolor=COR_BORDA,
            bordercolor=COR_BORDA,
            highlightthickness=0)
        self.style.map("Letter.TButton",
            background=[('active', COR_BOTAO_PRESSIONADO)],
            foreground=[('disabled', '#B5B5B5')])
        self.style.configure("LetterPressed.TButton",
            font=("Segoe UI", 16, "bold"),
            foreground=COR_TEXTO_CLARO,
            background=COR_VERDE_ACERTO,
            borderwidth=0,
            padding=8,
            width=3,
            relief="sunken",
            bordercolor=COR_BORDA)
        # RadioButton
        self.style.configure("TRadiobutton",
            font=("Segoe UI", 13),
            foreground=COR_TEXTO_CLARO,
            background=COR_FUNDO_SECUNDARIO)
        self.style.map("TRadiobutton",
            background=[('active', COR_FUNDO_PRINCIPAL)],
            foreground=[('disabled', '#B5B5B5')])
        # Spinbox
        self.style.configure("TSpinbox",
            font=("Segoe UI", 15),
            background=COR_FUNDO_ESCURO_INPUT,
            foreground=COR_TEXTO_CLARO,
            fieldbackground=COR_FUNDO_ESCURO_INPUT,
            arrowsize=16,
            borderwidth=0)
        self.style.map("TSpinbox",
            background=[('readonly', COR_FUNDO_ESCURO_INPUT)],
            fieldbackground=[('readonly', COR_FUNDO_ESCURO_INPUT)],
            foreground=[('readonly', COR_TEXTO_CLARO)])
        # Títulos
        self.style.configure("Title.TLabel",
            font=("Segoe UI", 32, "bold"),
            foreground=COR_TEXTO_CLARO_DESTACADO,
            background=COR_FUNDO_PRINCIPAL)
        self.style.configure("SubTitle.TLabel",
            font=("Segoe UI", 20, "bold"),
            foreground=COR_BORDA,
            background=COR_FUNDO_PRINCIPAL)
        # Treeview (placar)
        self.style.configure("Treeview",
            background=COR_FUNDO_SECUNDARIO,
            foreground=COR_TEXTO_CLARO,
            fieldbackground=COR_FUNDO_SECUNDARIO,
            borderwidth=0)
        self.style.map("Treeview",
            background=[('selected', COR_AZUL_SUAVE_BOTOES)])
        self.style.configure("Treeview.Heading",
            font=("Segoe UI", 13, "bold"),
            background=COR_BOTAO_PRESSIONADO,
            foreground=COR_TEXTO_CLARO)
        # Botões arredondados (simulação)
        self.style.layout("TButton", [
            ("Button.border", {'sticky': 'nswe', 'children': [
                ("Button.focus", {'sticky': 'nswe', 'children': [
                    ("Button.padding", {'sticky': 'nswe', 'children': [
                        ("Button.label", {'sticky': 'nswe'})
                    ]})
                ]})
            ]})
        ])

    def encontrar_arquivo_som(self, nome_arquivo):
        """Procura um arquivo de som em diferentes locais possíveis"""
        # Lista de possíveis locais para os arquivos de som
        possiveis_caminhos = [
            nome_arquivo,  # Arquivo na mesma pasta do jogo
            f"sons/{nome_arquivo}",  # Pasta sons
            f"../sons/{nome_arquivo}",  # Pasta sons um nível acima
            f"../../sons/{nome_arquivo}",  # Pasta sons dois níveis acima
        ]
        
        for caminho in possiveis_caminhos:
            if os.path.exists(caminho):
                return caminho
        
        return None

    def carregar_sons(self):
        """Carrega todos os arquivos de som de forma otimizada"""
        # Lista de arquivos de som necessários com prioridades
        arquivos_som = {
            'acerto_letra.wav': 'som_acerto',
            'erro_letra.wav': 'som_erro', 
            'vitoria_palavra.wav': 'som_vitoria_palavra',
            'musica_menu.wav': 'musica_menu',
            'teclado.wav': 'som_teclado',
            'fim_jogo.wav': 'som_fim_jogo',
            'iniciar_rodada.wav': 'som_iniciar_rodada'
        }
        
        sons_carregados = 0
        total_sons = len(arquivos_som)
        
        # Cache de volumes para otimização
        volume_efeitos = self.config.obter_config("audio", "volume_efeitos")
        volume_musica = self.config.obter_config("audio", "volume_musica")
        
        try:
            # Carregamento otimizado com tratamento de erro individual
            for nome_arquivo, atributo in arquivos_som.items():
                try:
                    caminho_arquivo = self.encontrar_arquivo_som(nome_arquivo)
                    
                    if caminho_arquivo:
                        som = pygame.mixer.Sound(caminho_arquivo)
                        setattr(self, atributo, som)
                        sons_carregados += 1
                        logging.info(f"Som carregado: {caminho_arquivo}")
                        
                        # Aplica volume imediatamente para evitar recálculos
                        if atributo in ['som_acerto', 'som_erro', 'som_vitoria_palavra', 'som_fim_jogo', 'som_iniciar_rodada']:
                            som.set_volume(volume_efeitos)
                        elif atributo == 'musica_menu':
                            som.set_volume(volume_musica)
                        elif atributo == 'som_teclado':
                            som.set_volume(volume_efeitos * 0.4)  # Volume menor para teclado
                    else:
                        setattr(self, atributo, None)
                        logging.warning(f"Arquivo de som não encontrado: {nome_arquivo}")
                        
                except Exception as e:
                    logging.warning(f"Erro ao carregar {nome_arquivo}: {e}")
                    setattr(self, atributo, None)

            # Feedback otimizado baseado no resultado
            if sons_carregados == total_sons:
                logging.info("Todos os sons carregados com sucesso.")
            elif sons_carregados > 0:
                logging.info(f"{sons_carregados}/{total_sons} sons carregados com sucesso.")
                if sons_carregados >= 3:  # Se carregou pelo menos os sons essenciais
                    logging.info("Sons essenciais carregados. Jogo funcionará normalmente.")
                else:
                    messagebox.showinfo("Sons Parciais", f"Carregados {sons_carregados}/{total_sons} arquivos de som.\nO jogo funcionará normalmente.")
            else:
                logging.warning("Nenhum arquivo de som encontrado.")
                messagebox.showwarning("Sons Ausentes", "Nenhum arquivo de som foi encontrado.\nO jogo funcionará sem sons.")
                
        except pygame.error as e:
            messagebox.showwarning("Erro de Áudio", f"Erro ao carregar sons: {e}\nO jogo continuará sem eles.")
            logging.warning(f"Erro ao carregar sons: {e}")
            # Inicializa todos como None em caso de erro
            for atributo in arquivos_som.values():
                setattr(self, atributo, None)

    # ============================================================================
    # MÉTODOS DE ÁUDIO
    # ============================================================================

    def baixar_dicionario(self):
        logging.info(f"Tentando baixar dicionário de: {self.URL_DICIONARIO_ONLINE}")
        try:
            response = requests.get(self.URL_DICIONARIO_ONLINE, timeout=10)
            response.raise_for_status()

            with open(self.ARQUIVO_LOCAL_DICIONARIO, "wb") as f:
                f.write(response.content)
            messagebox.showinfo("DOWNLOAD CONCLUÍDO", "DICIONÁRIO DE PALAVRAS BAIXADO COM SUCESSO!")
            logging.info("Dicionário baixado com sucesso.")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao baixar dicionário: {e}", exc_info=True)
            messagebox.showwarning("ERRO DE CONEXÃO",
                                   f"NÃO FOI POSSÍVEL BAIXAR o DICIONÁRIO ONLINE. "
                                   "Verifique sua conexão com a internet.\n"
                                   f"Detalhes do erro: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado no download do dicionário: {e}", exc_info=True)
            messagebox.showerror("ERRO NO DOWNLOAD",
                                 f"Ocorreu um erro inesperado ao baixar o dicionário: {e}")
            return False

    def remover_acentos(self, txt):
        return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')

    def carregar_dicionario(self):
        self.dicionario_palavras.clear()
        self.dicionario_palavras_sem_acento = set()
        logging.info("Iniciando carregamento do dicionário.")
        # Carregamento separado para solo e multiplayer
        ptbr_dic = "pt_BR.dic"
        palavras_txt = self.ARQUIVO_LOCAL_DICIONARIO
        palavras_set = set()
        # Carrega pt_BR.dic se existir
        if os.path.exists(ptbr_dic) and os.stat(ptbr_dic).st_size > 0:
            try:
                with open(ptbr_dic, "r", encoding="utf-8") as f:
                    primeira_linha = True
                    for linha in f:
                        if primeira_linha:
                            primeira_linha = False
                            if linha.strip().isdigit():
                                continue
                        palavra = linha.strip().lower()
                        if not palavra:
                            continue
                        if '/' in palavra:
                            palavra = palavra.split('/')[0]
                        if palavra.isalpha():
                            palavras_set.add(palavra)
            except UnicodeDecodeError:
                with open(ptbr_dic, "r", encoding="latin-1") as f:
                    primeira_linha = True
                    for linha in f:
                        if primeira_linha:
                            primeira_linha = False
                            if linha.strip().isdigit():
                                continue
                        palavra = linha.strip().lower()
                        if not palavra:
                            continue
                        if '/' in palavra:
                            palavra = palavra.split('/')[0]
                        if palavra.isalpha():
                            palavras_set.add(palavra)
        # Se for multiplayer, também carrega palavras.txt
        if self.modo_jogo_selecionado.get() == 'multiplayer' and os.path.exists(palavras_txt) and os.stat(palavras_txt).st_size > 0:
            try:
                with open(palavras_txt, "r", encoding="utf-8") as f:
                    for linha in f:
                        palavra = linha.strip().lower()
                        if not palavra:
                            continue
                        if '/' in palavra:
                            palavra = palavra.split('/')[0]
                        if palavra.isalpha():
                            palavras_set.add(palavra)
            except UnicodeDecodeError:
                with open(palavras_txt, "r", encoding="latin-1") as f:
                    for linha in f:
                        palavra = linha.strip().lower()
                        if not palavra:
                            continue
                        if '/' in palavra:
                            palavra = palavra.split('/')[0]
                        if palavra.isalpha():
                            palavras_set.add(palavra)
        # Atualiza os sets do objeto
        for palavra in palavras_set:
            self.dicionario_palavras.add(palavra)
            self.dicionario_palavras_sem_acento.add(self.remover_acentos(palavra))
        logging.info(f"Dicionário carregado com {len(self.dicionario_palavras)} palavras.")
        return True

    # ============================================================================
    # MÉTODOS DE DICIONÁRIO E PALAVRAS
    # ============================================================================

    def filtrar_palavra_inadequada(self, palavra):
        """Verifica se uma palavra contém conteúdo inadequado"""
        palavra_lower = palavra.lower()
        
        # Verifica se a palavra está na lista de palavras inadequadas
        if palavra_lower in self.PALAVRAS_INADEQUADAS:
            return True
        
        # Verifica se contém substrings inadequadas
        for termo_inadequado in self.PALAVRAS_INADEQUADAS:
            if termo_inadequado in palavra_lower:
                return True
        
        return False

    def filtrar_palavras_adequadas(self, lista_palavras):
        """Filtra uma lista de palavras removendo as inadequadas"""
        palavras_filtradas = []
        for palavra in lista_palavras:
            if not self.filtrar_palavra_inadequada(palavra):
                palavras_filtradas.append(palavra)
        
        logging.info(f"Filtradas {len(lista_palavras) - len(palavras_filtradas)} palavras inadequadas.")
        return palavras_filtradas

    def levenshtein_distance(self, s1, s2):
        # Early exit para casos óbvios
        if s1 == s2:
            return 0
        if len(s1) == 0:
            return len(s2)
        if len(s2) == 0:
            return len(s1)
        
        # Se a diferença de tamanho é maior que o limite, não vale a pena calcular
        if abs(len(s1) - len(s2)) > 3:
            return 999  # Valor alto para indicar que não é uma boa sugestão
        
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def sugerir_palavras(self, palavra_digitada, limite_distancia=2):
        logging.info(f"Gerando sugestões para '{palavra_digitada}' com limite de distância {limite_distancia}.")
        
        # Otimização: primeiro filtra por tamanho similar
        len_palavra = len(palavra_digitada)
        palavras_candidatas = []
        
        # Busca apenas em palavras com tamanho similar (±2 letras)
        for palavra_dic in self.dicionario_palavras:
            if abs(len(palavra_dic) - len_palavra) <= 2:
                palavras_candidatas.append(palavra_dic)
        
        # Se não encontrou candidatos, expande a busca
        if len(palavras_candidatas) < 10:
            for palavra_dic in self.dicionario_palavras:
                if abs(len(palavra_dic) - len_palavra) <= 3:
                    if palavra_dic not in palavras_candidatas:
                        palavras_candidatas.append(palavra_dic)
        
        # Limita a busca para não ficar muito lento
        if len(palavras_candidatas) > 1000:
            # Prioriza palavras comuns se disponíveis
            palavras_comuns_candidatas = [p for p in palavras_candidatas if p in self.PALAVRAS_COMUNS]
            if palavras_comuns_candidatas:
                palavras_candidatas = palavras_comuns_candidatas[:500]
            else:
                palavras_candidatas = palavras_candidatas[:500]
        
        sugestoes = []
        palavra_lower = palavra_digitada.lower()
        
        # Primeiro tenta encontrar palavras que começam com as mesmas letras
        for palavra_dic in palavras_candidatas:
            if palavra_dic.startswith(palavra_lower[:2]) or palavra_lower.startswith(palavra_dic[:2]):
                dist = self.levenshtein_distance(palavra_lower, palavra_dic)
                if dist <= limite_distancia:
                    sugestoes.append((palavra_dic, dist))
                    if len(sugestoes) >= 5:  # Limita a 5 sugestões
                        break
        
        # Se não encontrou sugestões, busca em todas as candidatas
        if len(sugestoes) < 3:
            for palavra_dic in palavras_candidatas:
                if palavra_dic not in [s[0] for s in sugestoes]:
                    dist = self.levenshtein_distance(palavra_lower, palavra_dic)
                    if dist <= limite_distancia:
                        sugestoes.append((palavra_dic, dist))
                        if len(sugestoes) >= 5:
                            break
        
        # Ordena por distância e depois alfabeticamente
        sugestoes.sort(key=lambda x: (x[1], x[0]))
        
        # Retorna apenas as 5 melhores sugestões
        resultado = [s[0] for s in sugestoes[:5]]
        logging.info(f"Sugestões encontradas: {resultado}")
        return resultado

    def mostrar_sugestoes(self, palavra_errada, sugestoes_similares=None, equivalentes_sem_acento=None):
        logging.info(f"Exibindo sugestões para a palavra inválida: '{palavra_errada}'")
        janela_sugestao = tk.Toplevel(self.root)
        janela_sugestao.title("PALAVRA INVÁLIDA - SUGESTÕES")
        largura, altura = 540, 460  # Altura aumentada para garantir espaço para o botão
        x = (self.root.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.root.winfo_screenheight() // 2) - (altura // 2)
        janela_sugestao.geometry(f"{largura}x{altura}+{x}+{y}")
        janela_sugestao.resizable(False, False)
        janela_sugestao.transient(self.root)
        janela_sugestao.grab_set()
        janela_sugestao.config(bg=COR_FUNDO_SECUNDARIO)

        tk.Label(janela_sugestao, text=f"A PALAVRA '{palavra_errada.upper()}' NÃO É VÁLIDA.",
                 font=("Arial", 14, "bold"), fg=COR_VERMELHO_ERRO, bg=COR_FUNDO_SECUNDARIO).pack(pady=10)
        tk.Label(janela_sugestao, text="VOCÊ QUIS DIZER ALGUMA DESTA?",
                 font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack(pady=5)

        # Junta equivalentes sem acento e sugestões similares, sem duplicar
        sugestoes_exibir = []
        if equivalentes_sem_acento:
            sugestoes_exibir.extend([p for p in equivalentes_sem_acento if p not in sugestoes_exibir])
        if sugestoes_similares:
            sugestoes_exibir.extend([p for p in sugestoes_similares if p not in sugestoes_exibir])
        sugestoes_exibir = sugestoes_exibir[:10]  # até 10 sugestões

        listbox_sugestoes = tk.Listbox(janela_sugestao, font=("Arial", 13), height=10, width=32,
                                       bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO,
                                       selectbackground=COR_AZUL_SUAVE_BOTOES, selectforeground="white")
        listbox_sugestoes.pack(pady=10, padx=20, fill=tk.BOTH, expand=False)

        if not sugestoes_exibir:
            listbox_sugestoes.insert(tk.END, "NENHUMA SUGESTÃO ENCONTRADA.")
        else:
            for s in sugestoes_exibir:
                listbox_sugestoes.insert(tk.END, s.upper())

        # Frame para os botões principais (lado a lado)
        botoes_frame = tk.Frame(janela_sugestao, bg=COR_FUNDO_SECUNDARIO)
        botoes_frame.pack(pady=(10, 0), fill=tk.X)

        # Frame para o botão de adicionar (abaixo, centralizado)
        frame_adicionar = tk.Frame(janela_sugestao, bg=COR_FUNDO_SECUNDARIO)
        frame_adicionar.pack(pady=(8, 10), fill=tk.X)

        def usar_sugestao():
            selecionado_idx = listbox_sugestoes.curselection()
            if selecionado_idx:
                palavra_selecionada = listbox_sugestoes.get(selecionado_idx[0]).lower()
                if palavra_selecionada == "nenhuma sugestão encontrada.":
                    return
                self.palavra_secreta_var.set(palavra_selecionada.upper())
                janela_sugestao.destroy()
                # Foco volta para o campo de entrada para permitir confirmação manual
                self.entry_palavra_secreta.focus_set()
                # Não chama processar_palavra_secreta automaticamente
                logging.info(f"Sugestão '{palavra_selecionada.upper()}' usada e foco devolvido ao campo de entrada.")
            else:
                messagebox.showwarning("NENHUMA SELEÇÃO", "POR FAVOR, SELECIONE UMA PALAVRA OU CLIQUE EM 'DIGITAR NOVAMENTE'.")
                logging.warning("Tentativa de usar sugestão sem seleção.")

        def digitar_novamente():
            self.palavra_secreta_var.set("")
            self.entry_palavra_secreta.focus_set()
            janela_sugestao.destroy()
            logging.info("Usuário optou por digitar a palavra novamente.")

        def adicionar_ao_dicionario():
            palavra_nova = palavra_errada.lower()
            if not palavra_nova.isalpha():
                messagebox.showwarning("PALAVRA INVÁLIDA", "Só é possível adicionar palavras com letras.")
                return
            if palavra_nova in self.dicionario_palavras:
                messagebox.showinfo("JÁ EXISTE", "Esta palavra já está no dicionário.")
                return
            self.dicionario_palavras.add(palavra_nova)
            self.dicionario_palavras_sem_acento.add(self.remover_acentos(palavra_nova))
            # Salva no arquivo palavras.txt
            try:
                with open(self.ARQUIVO_LOCAL_DICIONARIO, "a", encoding="utf-8") as f:
                    f.write(f"{palavra_nova}\n")
                messagebox.showinfo("ADICIONADO!", f"A palavra '{palavra_nova.upper()}' foi adicionada ao dicionário!")
                logging.info(f"Palavra '{palavra_nova}' adicionada ao dicionário e salva em '{self.ARQUIVO_LOCAL_DICIONARIO}'.")
            except Exception as e:
                messagebox.showerror("ERRO AO SALVAR", f"Não foi possível salvar a palavra no arquivo: {e}")
                logging.error(f"Erro ao salvar palavra no dicionário: {e}")
            # Fecha a janela ANTES de processar a palavra
            janela_sugestao.destroy()
            self.root.update()  # Garante atualização da interface
            # Após adicionar, já aceita a palavra
            self.palavra_secreta_var.set(palavra_nova.upper())
            self.processar_palavra_secreta()

        # Botões lado a lado
        btn_usar_sugestao = ttk.Button(botoes_frame, text="USAR SELECIONADA",
                                       command=usar_sugestao,
                                       style="TButton")
        btn_usar_sugestao.pack(side=tk.LEFT, padx=10, ipadx=6, ipady=3, expand=True)

        btn_digitar_novamente = ttk.Button(botoes_frame, text="DIGITAR NOVAMENTE",
                                           command=digitar_novamente,
                                           style="TButton")
        btn_digitar_novamente.pack(side=tk.LEFT, padx=10, ipadx=6, ipady=3, expand=True)

        # Botão adicionar centralizado abaixo
        btn_adicionar_dic = ttk.Button(frame_adicionar, text="ADICIONAR AO DICIONÁRIO",
                                       command=adicionar_ao_dicionario,
                                       style="TButton")
        btn_adicionar_dic.pack(pady=0, ipadx=30, ipady=4)

        self.root.wait_window(janela_sugestao)

    def embaralhar_palavra(self, palavra):
        letras_base = list(palavra)
        logging.info(f"Embaralhando palavra '{palavra}' para dificuldade: {self.dificuldade_selecionada.get()}")

        # Agora todas as dificuldades usam apenas as letras da palavra original
        letras_para_embaralhar = letras_base 

        random.shuffle(letras_para_embaralhar)
        embaralhada = ''.join(letras_para_embaralhar)
        logging.info(f"Palavra embaralhada: {embaralhada}")
        return embaralhada

    def gerar_palavra_sistema(self):
        dificuldade = self.dificuldade_selecionada.get()
        if self.modo_jogo_selecionado.get() == 'solo':
            regras = REGRAS_DIFICULDADE.get(dificuldade, {"min": 4, "max": 20})
            min_len = regras["min"]
            max_len = regras["max"]
        else:
            min_len = 4
            max_len = 20
        logging.info(f"Gerando palavra do sistema para dificuldade: {dificuldade} no modo {self.modo_jogo_selecionado.get()}.")

        def tem_definicao_online(palavra):
            if not VERIFICAR_DEFINICAO_ONLINE:
                return True
            try:
                url = f'https://dicio-api.vercel.app/v2/{palavra.lower()}'
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    return True
            except Exception:
                pass
            try:
                url_wikt = f'https://pt.wiktionary.org/wiki/{palavra.lower()}'
                resp = requests.get(url_wikt, timeout=3)
                if resp.status_code == 200 and 'pt.wiktionary.org' in resp.url:
                    return True
            except Exception:
                pass
            return False

        if not self.dicionario_palavras:
            logging.error("Dicionário de palavras vazio. Não é possível gerar palavra do sistema.")
            messagebox.showerror("Dicionário não carregado", "Não há palavras no dicionário para o sistema escolher. Verifique o arquivo 'palavras.txt' ou 'pt_BR.dic'.")
            return None

        priorizar_comuns = self.config.obter_config("jogo", "usar_palavras_comuns", False)
        palavras_usadas = set(self.palavras_usadas.get(dificuldade, []))
        # Sempre filtra pelo tamanho da dificuldade
        if priorizar_comuns:
            palavras_base = [p for p in self.PALAVRAS_COMUNS if min_len <= len(p) <= max_len and p not in palavras_usadas]
            if not palavras_base:
                palavras_base = [p for p in self.dicionario_palavras if min_len <= len(p) <= max_len and p not in palavras_usadas]
        else:
            palavras_base = [p for p in self.dicionario_palavras if min_len <= len(p) <= max_len and p not in palavras_usadas]
        if not palavras_base:
            self.palavras_usadas[dificuldade] = []
            self.salvar_palavras_usadas()
            if priorizar_comuns:
                palavras_base = [p for p in self.PALAVRAS_COMUNS if min_len <= len(p) <= max_len]
                if not palavras_base:
                    palavras_base = [p for p in self.dicionario_palavras if min_len <= len(p) <= max_len]
            else:
                palavras_base = [p for p in self.dicionario_palavras if min_len <= len(p) <= max_len]
        # Filtro de definição online (apenas modo solo)
        if self.modo_jogo_selecionado.get() == 'solo' and VERIFICAR_DEFINICAO_ONLINE:
            palavras_validas = []
            tentativas = 0
            random.shuffle(palavras_base)
            for palavra in palavras_base:
                if tentativas >= 10:
                    break
                if tem_definicao_online(palavra):
                    palavras_validas.append(palavra)
                    break
                tentativas += 1
            if palavras_validas:
                palavra_escolhida = palavras_validas[0].upper()
                self.palavras_usadas.setdefault(dificuldade, []).append(palavra_escolhida.lower())
                self.salvar_palavras_usadas()
                logging.info(f"Palavra sorteada com definição online: {palavra_escolhida} (Dificuldade: {dificuldade})")
                return palavra_escolhida
        # Fallback: ainda assim, só sorteia palavra do tamanho correto
        if not palavras_base:
            palavras_base = [p for p in self.dicionario_palavras if min_len <= len(p) <= max_len]
        if not palavras_base:
            # Se ainda assim não houver, sorteia qualquer palavra do dicionário
            palavras_base = list(self.dicionario_palavras)
        palavra_escolhida = random.choice(palavras_base).upper()
        self.palavras_usadas.setdefault(dificuldade, []).append(palavra_escolhida.lower())
        self.salvar_palavras_usadas()
        logging.info(f"Palavra do sistema escolhida: {palavra_escolhida} (Dificuldade: {dificuldade})")
        return palavra_escolhida

    def mostrar_carregando_palavra(self):
        self.janela_carregando = tk.Toplevel(self.root)
        self.janela_carregando.title("Carregando palavra...")
        largura, altura = 320, 120
        x = (self.root.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.root.winfo_screenheight() // 2) - (altura // 2)
        self.janela_carregando.geometry(f"{largura}x{altura}+{x}+{y}")
        self.janela_carregando.resizable(False, False)
        self.janela_carregando.transient(self.root)
        self.janela_carregando.grab_set()
        self.janela_carregando.config(bg=COR_FUNDO_PRINCIPAL)
        label = tk.Label(self.janela_carregando, text="Carregando palavra...", font=("Arial", 16, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)
        label.pack(expand=True, pady=30)
        self._carregando_animar = True
        def animar():
            if not self._carregando_animar:
                return
            texto = label.cget("text")
            if texto.endswith("......"):
                label.config(text="Carregando palavra...")
            else:
                label.config(text=texto + ".")
            self.janela_carregando.after(400, animar)
        animar()
        self.root.update()

    def fechar_carregando_palavra(self):
        self._carregando_animar = False
        if hasattr(self, 'janela_carregando') and self.janela_carregando.winfo_exists():
            self.janela_carregando.destroy()

    def iniciar_fase_definicao_palavra(self):
        logging.info(f"Iniciando fase de definição de palavra. Modo: {self.modo_jogo_selecionado.get()}")
        self.partida_desistida = False
        if self.modo_jogo_selecionado.get() == 'solo':
            logging.info("Modo SOLO selecionado. Gerando palavra do sistema.")
            self.mostrar_carregando_palavra()
            self.root.after(100, self._sortear_palavra_solo)
            return

        jogador_que_vai_adivinhar = (self.jogador_definidor_idx + 1) % len(self.jogadores)

        definidor_da_vez = self.jogadores[self.jogador_definidor_idx]['nome']
        adivinhador_desta_palavra = self.jogadores[jogador_que_vai_adivinhar]['nome']
        logging.info(f"Modo MULTIPLAYER. Definidor: {definidor_da_vez}, Adivinhador: {adivinhador_desta_palavra}.")

        self.palavra_secreta_var.set("")
        
        self.limpar_tela()
        self._criar_frames_iniciais()
        self.label_jogador1.config(text=f"{definidor_da_vez.upper()}, DEFINA A PALAVRA SECRETA PARA {adivinhador_desta_palavra.upper()}:")
        self.label_jogador1.pack(pady=20)
        self.entry_palavra_secreta.pack(pady=20, ipadx=10, ipady=10)
        ttk.Button(self.frame_jogador1, text="CONFIRMAR PALAVRA", command=self.processar_palavra_secreta, style="TButton").pack(pady=10)
        self.frame_jogador1.pack(expand=True, fill='both', pady=20)

        self.root.after(100, self.entry_palavra_secreta.focus_set)
        logging.info("Exibindo tela de definição de palavra para o definidor.")

    

    # ============================================================================
    # MÉTODOS DE INTERFACE E INTERAÇÃO
    # ============================================================================

    def on_entry_uppercase(self, var, event=None):
        current_value = var.get()
        new_value = current_value.upper()
        if current_value != new_value:
            var.set(new_value)
        
        if self.som_teclado and self.config.obter_config("audio", "som_ativado", True) and event and event.char and event.keysym not in ('BackSpace', 'Return', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Caps_Lock', 'Tab'):
            self.som_teclado.play()
            logging.debug(f"Som de teclado acionado por {event.keysym} em on_entry_uppercase.")
        
        pass

    def on_entry_uppercase_and_verify(self, var, event=None):
        """Converte para maiúsculas E verifica nomes preenchidos"""
        # Converte para maiúsculas
        current_value = var.get()
        new_value = current_value.upper()
        if current_value != new_value:
            var.set(new_value)
        
        # Toca som de teclado se disponível
        if self.som_teclado and self.config.obter_config("audio", "som_ativado", True) and event and event.char and event.keysym not in ('BackSpace', 'Return', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Caps_Lock', 'Tab'):
            self.som_teclado.play()
            logging.debug(f"Som de teclado acionado por {event.keysym} em on_entry_uppercase_and_verify.")
        
        # Verifica nomes preenchidos
        self.verificar_nomes_preenchidos()

    # ============================================================================
    # MÉTODOS DE LÓGICA DO JOGO
    # ============================================================================

    def processar_palavra_secreta(self):
        palavra_digitada = self.palavra_secreta_var.get().strip()
        dificuldade_atual = self.dificuldade_selecionada.get()
        # Só aplica as regras de dificuldade no modo solo
        if self.modo_jogo_selecionado.get() == 'solo':
            regras = REGRAS_DIFICULDADE.get(dificuldade_atual, {"min": 4, "max": 20})
            min_len = regras["min"]
            max_len = regras["max"]
        else:
            min_len = 4
            max_len = 20
        logging.info(f"Processando palavra secreta digitada: '{palavra_digitada}' (Dificuldade: {dificuldade_atual})")
        if not palavra_digitada:
            messagebox.showwarning("ENTRADA VAZIA", "POR FAVOR, DIGITE UMA PALAVRA.")
            self.entry_palavra_secreta.focus_set()
            logging.warning("Tentativa de processar palavra vazia.")
            return
        if not palavra_digitada.isalpha():
            messagebox.showwarning("ENTRADA INVÁLIDA", "POR FAVOR, DIGITE UMA PALAVRA VÁLIDA (APENAS LETRAS).")
            self.palavra_secreta_var.set("")
            self.entry_palavra_secreta.focus_set()
            logging.warning(f"Tentativa de processar palavra com caracteres inválidos: '{palavra_digitada}'")
            return
        if len(palavra_digitada) < min_len:
            messagebox.showwarning("ENTRADA INVÁLIDA", f"A PALAVRA DEVE TER NO MÍNIMO {min_len} LETRAS.")
            self.palavra_secreta_var.set("")
            self.entry_palavra_secreta.focus_set()
            logging.warning(f"Palavra digitada muito curta: '{palavra_digitada}'")
            return
        if len(palavra_digitada) > max_len:
            messagebox.showwarning("PALAVRA MUITO LONGA", f"A PALAVRA DEVE TER NO MÁXIMO {max_len} LETRAS.")
            self.palavra_secreta_var.set("")
            self.entry_palavra_secreta.focus_set()
            logging.warning(f"Palavra '{palavra_digitada}' muito longa.")
            return
        # Verificação exata
        palavra_digitada_lower = palavra_digitada.lower()
        equivalentes = [p for p in self.dicionario_palavras if self.remover_acentos(p) == self.remover_acentos(palavra_digitada_lower)]
        sugestoes = []
        if palavra_digitada_lower not in self.dicionario_palavras:
            if equivalentes:
                logging.info(f"Palavra '{palavra_digitada}' não encontrada, mas existe equivalente com acento: {equivalentes}")
            else:
                logging.info(f"Palavra '{palavra_digitada}' não encontrada no dicionário. Gerando sugestões por similaridade.")
            sugestoes = self.sugerir_palavras(palavra_digitada_lower)
            self.mostrar_sugestoes(palavra_digitada_lower, sugestoes_similares=sugestoes, equivalentes_sem_acento=equivalentes)
            return
        # ... restante do código original ...
        # Se chegou até aqui, a palavra é válida e está no dicionário
        if self.modo_jogo_selecionado.get() == 'solo':
            self.jogadores[0]['palavra_a_adivinhar'] = palavra_digitada.upper()
            self.jogadores[0]['dificuldade_rodada'] = self.dificuldade_selecionada.get()
            self.jogador_atual_idx = 0
            self.iniciar_rodada_adivinhacao()
        else:
            # Multiplayer: salva a palavra para o adivinhador e avança
            idx_adivinhador = (self.jogador_definidor_idx + 1) % len(self.jogadores)
            self.jogadores[idx_adivinhador]['palavra_a_adivinhar'] = palavra_digitada.upper()
            self.jogadores[idx_adivinhador]['dificuldade_rodada'] = self.dificuldade_selecionada.get()
            self.jogador_atual_idx = idx_adivinhador
            self.iniciar_rodada_adivinhacao()
        return

    def desistir_partida(self):
        logging.info(f"Jogador {self.jogadores[self.jogador_atual_idx]['nome']} solicitou desistência.")

        resposta = messagebox.askyesno("DESISTIR?", "TEM CERTEZA QUE DESEJA DESISTIR DA PARTIDA? O TEMPO NÃO SERÁ CONTABILIZADO E SEU RESULTADO NÃO ENTRARÁ NO RANKING (MODO SOLO).")
        if not resposta:
            logging.info("Desistência cancelada pelo usuário.")
            return

        self.partida_desistida = True
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            logging.info("Timer cancelado devido à desistência.")

        for btn in self.botoes_letras_embaralhadas:
            btn.config(state='disabled')

        self.btn_desistir.pack_forget()

        self.jogadores[self.jogador_atual_idx]['tempo_rodada'] = float('inf')
        self.jogadores[self.jogador_atual_idx]['erros_rodada'] = "DESISTIU"
        
        self.label_instrucao_jogador2.config(text=f"{self.jogadores[self.jogador_atual_idx]['nome'].upper()} DESISTIU! A PALAVRA ERA: {self.palavra_secreta.upper()}", fg=COR_VERMELHO_ERRO)
        self.label_tempo.config(text="TEMPO: DESISTIDO")
        self.label_erros.config(text="ERROS: DESISTIDO")
        logging.info(f"Rodada para {self.jogadores[self.jogador_atual_idx]['nome']} encerrada: DESISTIU. Palavra: {self.palavra_secreta}.")
        
        for i, char in enumerate(self.palavra_secreta):
            if i < len(self.palavra_adivinhada_entries):
                self.palavra_adivinhada_entries[i].config(state='normal', bg=COR_VERMELHO_ERRO, fg="white")
                self.palavra_adivinhada_entries[i].delete(0, tk.END)
                self.palavra_adivinhada_entries[i].insert(0, char)
                self.palavra_adivinhada_entries[i].config(state='disabled')

        self.verificar_fim_de_rodada()

    # ============================================================================
    # MÉTODOS DE INTERFACE E NAVEGAÇÃO
    # ============================================================================

    def iniciar_rodada_adivinhacao(self):
        logging.info(f"Iniciando rodada de adivinhação para o jogador: {self.jogadores[self.jogador_atual_idx]['nome']}")

        if self.timer_id:
            self.root.after_cancel(self.timer_id)

        self.partida_desistida = False

        self.palavra_secreta = self.jogadores[self.jogador_atual_idx]['palavra_a_adivinhar']
        if not self.palavra_secreta:
            logging.error(f"Jogador {self.jogadores[self.jogador_atual_idx]['nome']} não tem palavra para adivinhar. Retornando ao menu.")
            messagebox.showerror("ERRO DE SEQUÊNCIA", f"O JOGADOR {self.jogadores[self.jogador_atual_idx]['nome'].upper()} AINDA NÃO TEM UMA PALAVRA PARA ADIVINHAR. O JOGO TENTARÁ REDEFINIR.")
            self.iniciar_selecao_modo()
            return

        self.letras_embaralhadas = self.embaralhar_palavra(self.palavra_secreta)

        self.erros_rodada_atual = 0
        self.letras_ja_tentadas_exibicao.clear()
        self.letras_erradas_exibicao.clear()
        self.letras_erradas_desde_ultimo_acerto = set()  # NOVO: letras erradas desde o último acerto
        self.indice_atual = 0
        self.tempo_total_jogador_atual = 0.0
        self.tempo_penalidade_acumulada = 0.0

        self.limpar_tela()
        self._criar_frames_iniciais()

        for widget in self.frame_palavra_adivinhada.winfo_children():
            widget.destroy()
        self.palavra_adivinhada_entries.clear()
        self.entry_vars_adivinhacao.clear()

        for i in range(len(self.palavra_secreta)):
            entry_var = tk.StringVar(self.root)
            entry = tk.Entry(self.frame_palavra_adivinhada, width=3, font=("Arial", 24, "bold"),
                             justify='center', bd=2, relief="solid",
                             bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO,
                             textvariable=entry_var)
            entry.pack(side=tk.LEFT, padx=2)
            entry.bind("<KeyRelease>", lambda event, idx=i: self.on_key_release_adivinhacao(event, idx))
            entry.config(state='disabled')
            self.palavra_adivinhada_entries.append(entry)
            self.entry_vars_adivinhacao.append(entry_var)

        for widget in self.frame_letras_embaralhadas_botoes.winfo_children():
            widget.destroy()
        self.botoes_letras_embaralhadas.clear()

        max_cols = 10
        for i, letra in enumerate(self.letras_embaralhadas):
            row = i // max_cols
            col = i % max_cols
            btn = ttk.Button(self.frame_letras_embaralhadas_botoes, text=letra,
                             style="Letter.TButton",
                             command=lambda l=letra, current_btn_idx=i: self.inserir_letra_clicada(l, current_btn_idx))
            btn.grid(row=row, column=col, padx=2, pady=5)
            btn.config(state='disabled')
            self.botoes_letras_embaralhadas.append(btn)

        self.frame_jogador2.pack(expand=True, fill='both', pady=20) 

        # Garantir que os labels estejam visíveis e na ordem correta
        self.label_instrucao_jogador2.pack(pady=10)
        self.label_tempo.pack(pady=5)
        self.label_erros.pack(pady=5)
        self.label_letras_tentadas.pack(pady=5)
        self.label_letras_erradas.pack(pady=5)
        self.frame_palavra_adivinhada.pack(pady=15)
        self.label_letras_embaralhadas.pack(pady=5)
        self.frame_letras_embaralhadas_botoes.pack(pady=10)

        self.revelar_palavra_adivinhada_apenas()
        self.esconder_letras_embaralhadas_apenas()

        self.botao_iniciar_jogador2.pack_forget()
        self.botao_iniciar_jogador2.pack(pady=20)
        self.botao_iniciar_jogador2.config(state='normal')

        self.btn_desistir.pack(side=tk.BOTTOM, pady=10)
        self.btn_desistir.config(state='normal')

        if self.modo_jogo_selecionado.get() == 'solo':
            dificuldade = self.dificuldade_selecionada.get()
            priorizar_comuns = self.config.obter_config("jogo", "usar_palavras_comuns", False)
            texto_comuns = "(Prioriza Palavras Comuns)" if priorizar_comuns else "(Dicionário Completo)"
            self.label_instrucao_jogador2.config(text=f"DIFICULDADE: {dificuldade.upper()} {texto_comuns}\nVEZ DE: {self.jogadores[self.jogador_atual_idx]['nome'].upper()}. CLIQUE EM 'INICIAR RODADA' PARA COMEÇAR!", fg=COR_TEXTO_CLARO)
        else:
            self.label_instrucao_jogador2.config(text=f"VEZ DE: {self.jogadores[self.jogador_atual_idx]['nome'].upper()}. CLIQUE EM 'INICIAR RODADA' PARA COMEÇAR!", fg=COR_TEXTO_CLARO)

        self.label_letras_embaralhadas.config(text="LETRAS DISPONÍVEIS:", fg=COR_TEXTO_CLARO_DESTACADO)
        self.label_erros.config(text="")
        self.label_letras_tentadas.config(text="")
        self.label_letras_erradas.config(text="")
        self.label_tempo.config(text="TEMPO: 0.00S")

        logging.info("Interface da rodada de adivinhação preparada.")

    # ============================================================================
    # MÉTODOS DE CONTROLE DE TEMPO
    # ============================================================================

    def on_key_release_adivinhacao(self, event, idx):
        if self.partida_desistida:
            logging.info("KeyRelease ignorado: partida desistida.")
            return "break"

        if self.som_teclado:
            if event.char.isalpha() or event.keysym == 'BackSpace':
                self.som_teclado.play()
                logging.debug(f"Som de teclado acionado por {event.keysym} no Entry de adivinhação.")

        if not self.palavra_adivinhada_entries or idx >= len(self.palavra_adivinhada_entries):
            logging.error(f"Erro: Tentativa de key release em Entry inválido. idx={idx}, len(palavra_adivinhada_entries)={len(self.palavra_adivinhada_entries)}")
            return "break"

        current_entry = self.palavra_adivinhada_entries[idx]

        if event.keysym in ('BackSpace', 'Delete'):
            logging.debug(f"Tecla de navegação/exclusão pressionada: {event.keysym} na posição {idx}")
            if idx == self.indice_atual:
                current_entry.delete(0, tk.END)
                current_entry.focus_set() 
            else:
                current_entry.delete(0, tk.END)
                if self.indice_atual < len(self.palavra_adivinhada_entries):
                    self.palavra_adivinhada_entries[self.indice_atual].focus_set()
            return "break"

        if event.char.isalpha():
            letra_maiuscula = event.char.upper()
            logging.debug(f"Letra '{letra_maiuscula}' digitada na posição {idx}.")
            
            if idx == self.indice_atual:
                current_entry.delete(0, tk.END)
                current_entry.insert(0, letra_maiuscula)
                self.verificar_letra(letra_maiuscula, idx)
            else:
                current_entry.delete(0, tk.END)
                if self.indice_atual < len(self.palavra_adivinhada_entries):
                     self.palavra_adivinhada_entries[self.indice_atual].focus_set()
                logging.warning(f"Caractere não-alfabético '{event.char}' digitado na posição {idx}. Ignorado.")
        else:
            current_entry.delete(0, tk.END)
            if self.indice_atual < len(self.palavra_adivinhada_entries):
                 self.palavra_adivinhada_entries[self.indice_atual].focus_set()
            logging.warning(f"Caractere não-alfabético '{event.char}' digitado na posição {idx}. Ignorado.")
        return "break"

    def inserir_letra_clicada(self, letra, original_btn_idx):
        if self.partida_desistida:
            logging.info("Clique em letra ignorado: partida desistida.")
            return

        if self.som_teclado and self.config.obter_config("audio", "som_ativado", True):
            self.som_teclado.play()
            logging.debug(f"Som de teclado acionado por botão virtual: {letra}")

        if self.indice_atual < len(self.palavra_adivinhada_entries):
            current_entry = self.palavra_adivinhada_entries[self.indice_atual]
            clicked_btn = self.botoes_letras_embaralhadas[original_btn_idx]

            logging.info(f"Letra '{letra}' clicada (botão {original_btn_idx}). Inserindo na posição {self.indice_atual}.")

            original_style = clicked_btn.cget("style")
            clicked_btn.config(style="LetterPressed.TButton")
            self.root.after(100, lambda: clicked_btn.config(style=original_style))

            self.entry_vars_adivinhacao[self.indice_atual].set(letra.upper())
            
            self.verificar_letra(letra.upper(), self.indice_atual)
        else:
            messagebox.showwarning("PALAVRA COMPLETA", "A PALAVRA JÁ ESTÁ COMPLETA!")
            logging.warning("Tentativa de inserir letra em palavra já completa.")

    def iniciar_partida_jogador(self):
        logging.info(f"iniciar_partida_jogador() chamada para o jogador: {self.jogadores[self.jogador_atual_idx]['nome']}")
        logging.info(f"Iniciando partida para o jogador: {self.jogadores[self.jogador_atual_idx]['nome']}")

        if self.musica_menu and pygame.mixer.get_busy():
            self.musica_menu.stop()
            logging.info("Música do menu parada ao iniciar a rodada de adivinhação.")

        if self.som_iniciar_rodada:
            self.som_iniciar_rodada.play()
            logging.info("Som 'iniciar_rodada' acionado.")

        self.botao_iniciar_jogador2.pack_forget()

        for btn in self.botoes_letras_embaralhadas:
            btn.config(state='normal')

        self.indice_atual = 0
        if self.palavra_adivinhada_entries:
            self.palavra_adivinhada_entries[self.indice_atual].config(state='normal', bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO)
            self.palavra_adivinhada_entries[self.indice_atual].focus_set()
            logging.info(f"Foco inicial na Entry da posição {self.indice_atual}.")
        else:
            logging.error("As caixas de entrada da palavra não foram criadas corretamente.")
            messagebox.showerror("ERRO DE INICIALIZAÇÃO", "AS CAIXAS DE ENTRADA DA PALAVRA NÃO FORAM CRIADAS CORRETAMENTE.")
            self.iniciar_selecao_modo()
            return

        self.revelar_letras_embaralhadas_apenas()

        self.tempo_inicio_rodada = time.time()
        self.iniciar_timer_progressivo()
        self.atualizar_interface_jogador2()

    def esconder_letras_embaralhadas_apenas(self):
        self.label_letras_embaralhadas.pack_forget()
        self.frame_letras_embaralhadas_botoes.pack_forget()
        for btn in self.botoes_letras_embaralhadas:
            btn.config(state='disabled')
        logging.info("Letras embaralhadas e botões escondidos.")

    def revelar_letras_embaralhadas_apenas(self):
        self.label_letras_embaralhadas.pack(pady=5)
        self.frame_letras_embaralhadas_botoes.pack(pady=10)
        for btn in self.botoes_letras_embaralhadas:
            btn.config(state='normal')
        logging.info("Letras embaralhadas e botões revelados.")

    def revelar_palavra_adivinhada_apenas(self):
        self.frame_palavra_adivinhada.pack(pady=15)
        for entry in self.palavra_adivinhada_entries:
            entry.pack(side=tk.LEFT, padx=2)
            entry.delete(0, tk.END)
            entry.config(state='disabled', bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO)
        logging.info("Caixas da palavra adivinhada reveladas (em branco).")

    def atualizar_interface_jogador2(self):
        self.label_erros.config(text=f"ERROS: {self.erros_rodada_atual}")
        letras_exibicao_tentadas = sorted(list(self.letras_ja_tentadas_exibicao))
        self.label_letras_tentadas.config(text="LETRAS TENTADAS (GERAL): " + ", ".join(letras_exibicao_tentadas).upper())

        # NOVO: letras erradas desde o último acerto
        letras_exibicao_erradas = sorted(list(getattr(self, 'letras_erradas_desde_ultimo_acerto', set())))
        self.label_letras_erradas.config(text="LETRAS ERRADAS: " + ", ".join(letras_exibicao_erradas).upper(), fg=COR_VERMELHO_ERRO)

        if self.indice_atual < len(self.palavra_secreta):
            self.label_instrucao_jogador2.config(text=f"VEZ DE: {self.jogadores[self.jogador_atual_idx]['nome'].upper()} - ADIVINHE A LETRA DA POSIÇÃO {self.indice_atual + 1}:")
        else:
            self.label_instrucao_jogador2.config(text=f"VEZ DE: {self.jogadores[self.jogador_atual_idx]['nome'].upper()} - PALAVRA COMPLETA!")

        self.label_tempo.config(text=f"TEMPO: {self.tempo_total_jogador_atual:.2f}S")
        logging.debug(f"Interface atualizada. Erros: {self.erros_rodada_atual}, Tempo: {self.tempo_total_jogador_atual:.2f}s.")

    def iniciar_timer_progressivo(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)

        if self.indice_atual >= len(self.palavra_secreta):
            logging.info("Timer não iniciado: palavra já completa.")
            return

        self.contar_tempo_progressivo()

    def contar_tempo_progressivo(self):
        if self.partida_desistida:
            logging.debug("Contagem de tempo interrompida: partida desistida.")
            return

        self.tempo_total_jogador_atual = (time.time() - self.tempo_inicio_rodada) + self.tempo_penalidade_acumulada

        self.atualizar_interface_jogador2()
        self.timer_id = self.root.after(100, self.contar_tempo_progressivo)

    def verificar_letra(self, letra_input, idx):
        if self.partida_desistida:
            logging.info("Verificação de letra ignorada: partida desistida.")
            return

        if not self.palavra_adivinhada_entries or idx >= len(self.palavra_adivinhada_entries):
            logging.error(f"ERRO: Tentativa de acessar entry inválida. idx={idx}, len(palavra_adivinhada_entries)={len(self.palavra_adivinhada_entries)}")
            return

        current_entry = self.palavra_adivinhada_entries[idx]
        letra_digitada = letra_input.upper()
        letra_correta = self.palavra_secreta[self.indice_atual]

        self.letras_ja_tentadas_exibicao.add(letra_digitada)

        # NOVO: aceita equivalentes sem acento
        if (letra_digitada == letra_correta) or (self.remover_acentos(letra_digitada) == self.remover_acentos(letra_correta)):
            # Se digitou sem acento mas a correta tem acento, corrige no campo
            current_entry.delete(0, tk.END)
            current_entry.insert(0, letra_correta)
            current_entry.config(state='disabled', bg=COR_VERDE_ACERTO_CLARO, fg="white")
            logging.info(f"Acertou a letra '{letra_digitada}' (comparada como '{letra_correta}') na posição {self.indice_atual}.")
            
            is_last_letter_of_word = (self.indice_atual + 1) == len(self.palavra_secreta)
            
            if self.som_acerto and self.config.obter_config("audio", "som_ativado", True) and (not is_last_letter_of_word or self.modo_jogo_selecionado.get() == 'multiplayer'):
                self.som_acerto.play()
                logging.info(f"Som de acerto acionado para a letra '{letra_digitada}'.")
            elif is_last_letter_of_word and self.modo_jogo_selecionado.get() == 'solo':
                logging.info(f"Última letra '{letra_digitada}' acertada no modo solo. Som de acerto suprimido para priorizar som final.")

            if letra_digitada in self.letras_erradas_exibicao:
                self.letras_erradas_exibicao.remove(letra_digitada)
                logging.info(f"Letra '{letra_digitada}' removida das letras erradas (acertou em outra posição).")

            self.indice_atual += 1

            # NOVO: limpa as letras erradas desde o último acerto
            self.letras_erradas_desde_ultimo_acerto = set()

            if self.indice_atual < len(self.palavra_secreta):
                self.palavra_adivinhada_entries[self.indice_atual-1].config(state='disabled')
                self.palavra_adivinhada_entries[self.indice_atual].config(state='normal', bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO)
                self.palavra_adivinhada_entries[self.indice_atual].focus_set()
                logging.debug(f"Foco movido para a próxima posição: {self.indice_atual}.")
            else:
                logging.info("Palavra completa. Verificando fim de rodada.")
                if self.palavra_secreta:
                    self.palavra_adivinhada_entries[len(self.palavra_secreta)-1].config(state='disabled')
                self.verificar_fim_de_rodada()
        else:
            self.erros_rodada_atual += 1
            self.letras_erradas_exibicao.add(letra_digitada)
            # NOVO: adiciona à lista de erradas desde o último acerto
            if not hasattr(self, 'letras_erradas_desde_ultimo_acerto'):
                self.letras_erradas_desde_ultimo_acerto = set()
            self.letras_erradas_desde_ultimo_acerto.add(letra_digitada)
            penalidade_erro = self.config.obter_config("jogo", "penalidade_erro", 3.0)
            self.tempo_penalidade_acumulada += penalidade_erro
            logging.info(f"Errou a letra '{letra_digitada}' na posição {self.indice_atual}. Erros: {self.erros_rodada_atual}, Penalidade: {self.tempo_penalidade_acumulada}s.")
            if self.som_erro and self.config.obter_config("audio", "som_ativado", True):
                self.som_erro.play()
                logging.info(f"Som de erro acionado para a letra '{letra_digitada}'.")

            original_bg = current_entry.cget("bg")
            current_entry.config(bg=COR_VERMELHO_ERRO, fg="white")
            self.root.after(200, lambda: current_entry.config(bg=original_bg, fg=COR_TEXTO_CLARO))
            
            self.entry_vars_adivinhacao[self.indice_atual].set("")
            current_entry.focus_set()
            logging.debug(f"Foco mantido na posição {self.indice_atual} após erro.")

        self.atualizar_interface_jogador2()

    def verificar_fim_de_rodada(self):
        logging.info("Verificando fim de rodada.")

        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            logging.info("Timer da rodada cancelado.")

        palavra_adivinhada_str = "".join([var.get() for var in self.entry_vars_adivinhacao]).upper()

        for btn in self.botoes_letras_embaralhadas:
            btn.config(state='disabled')
        for entry in self.palavra_adivinhada_entries:
            entry.config(state='disabled')

        if self.partida_desistida:
            resultado_rodada = "DESISTIU"
            tempo_final = float('inf')
            erros_final = "DESISTIU"
            logging.info(f"Rodada para {self.jogadores[self.jogador_atual_idx]['nome']} encerrada: DESISTIU.")
        elif palavra_adivinhada_str == self.palavra_secreta:
            resultado_rodada = "ADIVINHOU"
            tempo_final = self.tempo_total_jogador_atual
            erros_final = self.erros_rodada_atual
            messagebox.showinfo("PARABÉNS!", f"VOCÊ ADIVINHOU A PALAVRA '{self.palavra_secreta.upper()}' EM {tempo_final:.2f} SEGUNDOS!")
            
            is_last_multiplayer_word = False
            if self.modo_jogo_selecionado.get() == 'multiplayer':
                is_last_multiplayer_word = ((self.jogador_definidor_idx + 1) % len(self.jogadores)) == 0

            if self.som_vitoria_palavra and (self.modo_jogo_selecionado.get() == 'solo' or not is_last_multiplayer_word):
                self.som_vitoria_palavra.play()
                logging.info(f"Som de vitória de palavra acionado para '{self.palavra_secreta}'.")
            elif is_last_multiplayer_word and self.som_fim_jogo:
                logging.info(f"Última palavra multiplayer acertada. Som de vitória de palavra suprimido para priorizar som de fim de jogo.")

            logging.info(f"Rodada para {self.jogadores[self.jogador_atual_idx]['nome']} encerrada: ADIVINHOU. Tempo: {tempo_final:.2f}s, Erros: {erros_final}.")
        else:
            resultado_rodada = "INCOMPLETA"
            tempo_final = self.tempo_total_jogador_atual
            erros_final = self.erros_rodada_atual
            logging.warning(f"Rodada para {self.jogadores[self.jogador_atual_idx]['nome']} encerrada: INCOMPLETA. Palavra era '{self.palavra_secreta}'. Tempo: {tempo_final:.2f}s, Erros: {erros_final}.")
            for i, char in enumerate(self.palavra_secreta):
                if i < len(self.palavra_adivinhada_entries):
                    self.palavra_adivinhada_entries[i].config(state='normal', bg=COR_VERMELHO_ERRO, fg="white")
                    self.entry_vars_adivinhacao[i].set(char)
                    self.palavra_adivinhada_entries[i].config(state='disabled')

        self.jogadores[self.jogador_atual_idx]['erros_rodada'] = erros_final
        self.jogadores[self.jogador_atual_idx]['tempo_rodada'] = tempo_final
        self.jogadores[self.jogador_atual_idx]['palavra_adivinhada_rodada'] = self.palavra_secreta
        self.jogadores[self.jogador_atual_idx]['status_rodada'] = resultado_rodada

        if self.modo_jogo_selecionado.get() == 'solo':
            self.jogadores[self.jogador_atual_idx]['tempo_total'] = tempo_final
            self.jogadores[self.jogador_atual_idx]['erros_acumulados'] = erros_final

            if resultado_rodada == "ADIVINHOU" and tempo_final != float('inf'):
                self.adicionar_ao_ranking(
                    self.jogadores[self.jogador_atual_idx]['nome'],
                    self.jogadores[self.jogador_atual_idx]['tempo_total'],
                    self.jogadores[self.jogador_atual_idx]['erros_acumulados'],
                    self.jogadores[self.jogador_atual_idx]['dificuldade_rodada'],
                    self.jogadores[self.jogador_atual_idx]['palavra_adivinhada_rodada']
                )
                self.salvar_ranking()
                logging.info(f"Resultado solo salvo para ranking: {self.jogadores[self.jogador_atual_idx]['nome']}, {tempo_final:.2f}s, {erros_final} erros, Dificuldade: {self.jogadores[self.jogador_atual_idx]['dificuldade_rodada']}, Palavra: {self.jogadores[self.jogador_atual_idx]['palavra_adivinhada_rodada']}.")
            else:
                logging.info(f"Resultado solo não salvo no ranking: {self.jogadores[self.jogador_atual_idx]['nome']} (Status: {resultado_rodada}).")

            self.root.after(100, self.mostrar_placar_final_solo)

        else:
            self.jogador_definidor_idx = (self.jogador_definidor_idx + 1) % len(self.jogadores)
            logging.info(f"Definidor avançou para o índice: {self.jogador_definidor_idx}. Agora {self.jogadores[self.jogador_definidor_idx]['nome']} é o definidor.")
            
            if self.jogador_definidor_idx == 0:
                logging.info("Partida multiplayer finalizada. Todos os jogadores definiram e adivinharam uma palavra.")
                self.root.after(100, self.mostrar_placar_final_multiplayer)
            else:
                logging.info(f"Rodada concluída. Próxima rodada: {self.jogadores[self.jogador_definidor_idx]['nome']} definirá a palavra.")
                self.root.after(100, self.iniciar_fase_definicao_palavra)

    # ============================================================================
    # MÉTODOS DE RANKING
    # ============================================================================

    def carregar_ranking(self):
        if os.path.exists(self.ARQUIVO_RANKING):
            try:
                with open(self.ARQUIVO_RANKING, "r", encoding="utf-8") as f:
                    ranking_data = json.load(f)
                    for modo in ['comum_on', 'comum_off']:
                        for diff in ["Fácil", "Médio", "Difícil"]:
                            self.ranking_solo[modo][diff] = ranking_data.get(modo, {}).get(diff, [])
                            self.ranking_solo[modo][diff].sort(key=lambda x: (x.get('tempo', float('inf')), x.get('erros', 9999)))
                            self.ranking_solo[modo][diff] = self.ranking_solo[modo][diff][:10]
                logging.info("Ranking carregado com sucesso.")
            except json.JSONDecodeError:
                logging.error("Arquivo de ranking corrompido (JSONDecodeError). Criando um novo.", exc_info=True)
                messagebox.showwarning("ERRO DE RANKING", "ARQUIVO DE RANKING CORROMPIDO. CRIANDO UM NOVO.")
                self.ranking_solo = {'comum_on': {'Fácil': [], 'Médio': [], 'Difícil': []}, 'comum_off': {'Fácil': [], 'Médio': [], 'Difícil': []}}
            except Exception as e:
                logging.error(f"Ocorreu um erro ao carregar o ranking: {e}. Criando um novo.", exc_info=True)
                messagebox.showerror("ERRO AO CARREGAR RANKING", f"Ocorreu um erro ao carregar o ranking: {e}. Criando um novo.")
                self.ranking_solo = {'comum_on': {'Fácil': [], 'Médio': [], 'Difícil': []}, 'comum_off': {'Fácil': [], 'Médio': [], 'Difícil': []}}
        else:
            logging.info("Arquivo de ranking não encontrado. Inicializando ranking vazio.")
            self.ranking_solo = {'comum_on': {'Fácil': [], 'Médio': [], 'Difícil': []}, 'comum_off': {'Fácil': [], 'Médio': [], 'Difícil': []}}

    def salvar_ranking(self):
        logging.info("Tentando salvar ranking.")
        try:
            with open(self.ARQUIVO_RANKING, "w", encoding="utf-8") as f:
                json.dump(self.ranking_solo, f, indent=4)
            logging.info("Ranking salvo com sucesso.")
        except IOError as e:
            logging.error(f"NÃO FOI POSSÍVEL SALVAR O RANKING: {e}", exc_info=True)
            messagebox.showerror("ERRO DE SALVAMENTO", f"NÃO FOI POSSÍVEL SALVAR O RANKING: {e}")

    def adicionar_ao_ranking(self, nome, tempo, erros, dificuldade, palavra):
        priorizar_comuns = self.config.obter_config("jogo", "usar_palavras_comuns", False)
        modo = 'comum_on' if priorizar_comuns else 'comum_off'
        logging.info(f"Adicionando ao ranking ({modo}): {nome}, Tempo: {tempo}, Erros: {erros}, Dificuldade: {dificuldade}, Palavra: {palavra}")
        if dificuldade not in self.ranking_solo[modo]:
            self.ranking_solo[modo][dificuldade] = []
        self.ranking_solo[modo][dificuldade].append({
            "nome": nome,
            "tempo": tempo,
            "erros": erros,
            "palavra": palavra
        })
        self.ranking_solo[modo][dificuldade].sort(key=lambda x: (x['tempo'], x['erros']))
        self.ranking_solo[modo][dificuldade] = self.ranking_solo[modo][dificuldade][:10]
        logging.info(f"Ranking atualizado para {dificuldade} ({modo}): {self.ranking_solo[modo][dificuldade]}.")

    # ============================================================================
    # MÉTODOS DE INTERFACE DE USUÁRIO
    # ============================================================================

    def limpar_tela(self):
        logging.info("Limpando a tela (destruindo todos os widgets filhos de root).")
        for widget in self.root.winfo_children():
            widget.destroy()

    def parar_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
            logging.info("Timer parado.")

    def iniciar_selecao_modo(self):
        self.jogadores.clear()
        self.jogador_definidor_idx = 0
        self.limpar_tela()

        self._criar_frames_iniciais()

        if self.musica_menu and self.config.obter_config("audio", "musica_ativada", True) and not pygame.mixer.get_busy():
            self.musica_menu.play(-1)
            logging.info("Música do menu iniciada.")

        # Título do jogo com emoji
        tk.Label(self.frame_selecao_modo, text="🎲 JOGO DE ADIVINHAÇÃO DE PALAVRAS", 
                font=("Segoe UI", 32, "bold"), fg=COR_TEXTO_CLARO_DESTACADO, bg=COR_FUNDO_PRINCIPAL).pack(pady=30)
        tk.Label(self.frame_selecao_modo, text="✨ DESAFIO DE RIVAIS ✨", 
                font=("Segoe UI", 20, "bold"), fg=COR_LILAS_PASTEL, bg=COR_FUNDO_PRINCIPAL).pack(pady=10)
        # Botões principais com emojis
        ttk.Button(self.frame_selecao_modo, text="🧑‍💻 INICIAR JOGO SOLO", 
                  command=lambda: self.iniciar_jogo_solo(), style="TButton").pack(pady=15)
        ttk.Button(self.frame_selecao_modo, text="👥 INICIAR JOGO MULTIPLAYER", 
                  command=lambda: self.iniciar_jogo_multiplayer(), style="TButton").pack(pady=15)
        # Botões secundários
        ttk.Button(self.frame_selecao_modo, text="⚙️ CONFIGURAÇÕES", 
                  command=self.mostrar_configuracoes, style="TButton").pack(pady=10)
        ttk.Button(self.frame_selecao_modo, text="❓ COMO JOGAR?", 
                  command=self.mostrar_instrucoes, style="TButton").pack(pady=10)
        ttk.Button(self.frame_selecao_modo, text="🚪 SAIR DO JOGO", 
                  command=self.confirmar_saida, style="TButton").pack(pady=10)
        self.frame_selecao_modo.pack(expand=True, fill='both', pady=20)
        logging.info("Tela inicial organizada exibida.")

    def iniciar_jogo_solo(self):
        """Inicia o jogo no modo solo"""
        logging.info("Iniciando jogo solo.")
        self.modo_jogo_selecionado.set("solo")
        # Sempre garantir que a dificuldade selecionada seja a salva nas configurações
        self.dificuldade_selecionada.set(self.config.obter_config("jogo", "dificuldade_padrao"))
        self.mostrar_opcoes_multiplayer_e_nomes_e_dificuldade()

    def iniciar_jogo_multiplayer(self):
        """Inicia o jogo no modo multiplayer"""
        logging.info("Iniciando jogo multiplayer.")
        self.modo_jogo_selecionado.set("multiplayer")
        self.mostrar_opcoes_multiplayer_e_nomes_e_dificuldade()

    def _esconder_opcoes_nomes_multiplayer_e_botoes(self):
        logging.info("Escondendo opções de nomes e botões de iniciar jogo.")
        if hasattr(self, 'label_num_jogadores_multiplayer') and self.label_num_jogadores_multiplayer.winfo_exists():
            self.label_num_jogadores_multiplayer.pack_forget()
        if hasattr(self, 'spinbox_num_jogadores') and self.spinbox_num_jogadores.winfo_exists():
            self.spinbox_num_jogadores.pack_forget()
        if hasattr(self, 'frame_entry_nomes') and self.frame_entry_nomes.winfo_exists():
            self.frame_entry_nomes.pack_forget()
        if hasattr(self, 'btn_iniciar_jogo_principal') and self.btn_iniciar_jogo_principal.winfo_exists():
            self.btn_iniciar_jogo_principal.pack_forget()
        if hasattr(self, 'btn_voltar_nomes') and self.btn_voltar_nomes.winfo_exists():
            self.btn_voltar_nomes.pack_forget()
        logging.info("Opções de nomes e botões de iniciar jogo escondidos.")

    def mostrar_opcoes_multiplayer_e_nomes_e_dificuldade(self):
        logging.info(f"Exibindo opções para o modo: {self.modo_jogo_selecionado.get()}")

        self.jogadores.clear()
        self.entry_nomes_jogadores.clear()

        for widget in self.frame_entry_nomes.winfo_children():
            widget.destroy()

        self.limpar_tela()
        self._criar_frames_iniciais()

        self.label_nomes_multiplayer.pack(pady=20)
        
        if self.modo_jogo_selecionado.get() == 'solo':
            self.num_jogadores_total = 1
            logging.info("Preparando entrada de nome para o modo SOLO.")
            
            self._esconder_opcoes_nomes_multiplayer_e_botoes()

            tk.Label(self.frame_entry_nomes, text="SEU NOME:", font=("Arial", 14), bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO).pack(pady=5)
            name_var = tk.StringVar(self.root)
            # Deixar o campo em branco para o jogador digitar
            name_var.set("")
            name_entry = tk.Entry(self.frame_entry_nomes, font=("Arial", 16), bd=2, relief="solid", bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO, textvariable=name_var)
            name_entry.pack(pady=5)
            self.entry_nomes_jogadores.append(name_entry)
            name_entry.bind("<KeyRelease>", lambda event, var=name_var: self.on_entry_uppercase_and_verify(var, event))
            name_entry.bind("<Return>", lambda event: self.finalizar_cadastro_jogadores())

            self.frame_entry_nomes.pack(pady=10)
            self.btn_iniciar_jogo_principal.config(command=self.finalizar_cadastro_jogadores)
            self.btn_iniciar_jogo_principal.pack(pady=10)
            self.btn_iniciar_jogo_principal.config(state='normal')
            self.btn_voltar_nomes.pack(side=tk.BOTTOM, pady=5)
            name_entry.focus_set()
        else:
            logging.info("Preparando seleção de quantidade para o modo MULTIPLAYER.")
            self.frame_entry_nomes.pack_forget()
            self.btn_iniciar_jogo_principal.pack_forget()
            
            self.label_num_jogadores_multiplayer.pack(pady=5)
            self.spinbox_num_jogadores.pack(pady=5)
            
            # Ao selecionar o número de jogadores, já vai para a tela de nomes
            self.spinbox_num_jogadores.bind("<Return>", lambda event: self._ir_para_inserir_nomes())
            self.spinbox_num_jogadores.bind("<FocusOut>", lambda event: self._ir_para_inserir_nomes())
            ttk.Button(self.frame_nomes_jogadores, text="CONTINUAR", command=self._ir_para_inserir_nomes, style="TButton").pack(pady=10)
            self.btn_voltar_nomes.pack(side=tk.BOTTOM, pady=5)

        self.frame_nomes_jogadores.pack(expand=True, fill='both', pady=20)
        self.root.after(100, lambda: self.spinbox_num_jogadores.focus_set() if self.modo_jogo_selecionado.get() == 'multiplayer' else self.entry_nomes_jogadores[0].focus_set())

    def _ir_para_inserir_nomes(self):
        logging.info(f"Confirmando número de jogadores: {self.num_jogadores_multiplayer.get()}")
        self.label_num_jogadores_multiplayer.pack_forget()
        self.spinbox_num_jogadores.pack_forget()
        for widget in self.frame_nomes_jogadores.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget('text') == 'CONTINUAR':
                widget.pack_forget()
        self.num_jogadores_total = self.num_jogadores_multiplayer.get()
        self._criar_entradas_nomes_dinamico()

    def _criar_entradas_nomes_dinamico(self):
        logging.info(f"Criando {self.num_jogadores_total} entradas de nome dinamicamente para multiplayer.")
        for widget in self.frame_entry_nomes.winfo_children():
            widget.destroy()
        self.entry_nomes_jogadores.clear()
        self.label_nomes_multiplayer.config(text="INSIRA OS NOMES DOS JOGADORES:")
        for i in range(self.num_jogadores_total):
            tk.Label(self.frame_entry_nomes, text=f"JOGADOR {i+1}:", font=("Arial", 14), bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO).pack(pady=5)
            name_var = tk.StringVar(self.root)
            name_entry = tk.Entry(self.frame_entry_nomes, font=("Arial", 16), bd=2, relief="solid", bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO, textvariable=name_var)
            name_entry.pack(pady=5)
            self.entry_nomes_jogadores.append(name_entry)
            name_entry.bind("<KeyRelease>", lambda event, var=name_var: self.on_entry_uppercase_and_verify(var, event))
            name_entry.bind("<Return>", lambda event, idx=i: self.navegar_proximo_jogador(idx))
        self.frame_entry_nomes.pack(pady=10)
        self.btn_iniciar_jogo_principal.config(command=self.finalizar_cadastro_jogadores)
        self.btn_iniciar_jogo_principal.pack(pady=10)
        self.btn_iniciar_jogo_principal.config(state='normal')
        if self.entry_nomes_jogadores:
            self.root.after(200, self.entry_nomes_jogadores[0].focus_set)
        self.verificar_nomes_preenchidos()
        # Botão VOLTAR fica por último, abaixo de tudo
        self.btn_voltar_nomes.pack(side=tk.BOTTOM, pady=5)

    def navegar_proximo_jogador(self, current_idx):
        """Navega para o próximo jogador ou finaliza se for o último"""
        if not self.entry_nomes_jogadores[current_idx].get().strip():
            messagebox.showwarning("NOME INVÁLIDO", "POR FAVOR, INSIRA UM NOME ANTES DE CONTINUAR.")
            self.entry_nomes_jogadores[current_idx].focus_set()
            return
        
        if current_idx + 1 < len(self.entry_nomes_jogadores):
            # Vai para o próximo jogador
            self.entry_nomes_jogadores[current_idx + 1].focus_set()
        else:
            # É o último jogador, verifica se pode finalizar
            self.verificar_nomes_preenchidos()
            if self.todos_nomes_preenchidos():
                self.finalizar_cadastro_jogadores()
            else:
                messagebox.showwarning("NOMES INCOMPLETOS", "POR FAVOR, PREENCHA O NOME DE TODOS OS JOGADORES.")

    def todos_nomes_preenchidos(self):
        """Verifica se todos os nomes estão preenchidos"""
        for entry in self.entry_nomes_jogadores:
            if not entry.get().strip():
                return False
        return True

    def verificar_nomes_preenchidos(self):
        todos_preenchidos = self.todos_nomes_preenchidos()
        # O botão fica sempre ativo, mas só avança se todos preenchidos
        if todos_preenchidos:
            self.btn_iniciar_jogo_principal.config(command=self.finalizar_cadastro_jogadores)
        else:
            self.btn_iniciar_jogo_principal.config(command=lambda: messagebox.showwarning("NOMES INCOMPLETOS", "POR FAVOR, PREENCHA O NOME DE TODOS OS JOGADORES."))

    def finalizar_cadastro_jogadores(self):
        logging.info("Finalizando cadastro de jogadores.")

        todos_preenchidos = True
        for entry in self.entry_nomes_jogadores:
            if not entry.get().strip():
                todos_preenchidos = False
                break
        
        if not todos_preenchidos:
            messagebox.showwarning("NOMES INCOMPLETOS", "POR FAVOR, PREENCHA O NOME DE TODOS OS JOGADORES.")
            logging.warning("Tentativa de finalizar cadastro com nomes incompletos.")
            return

        self.jogadores.clear()
        for entry in self.entry_nomes_jogadores:
            self.jogadores.append({
                'nome': entry.get().strip(),
                'erros_rodada': 0,
                'tempo_rodada': 0.0,
                'palavra_a_adivinhar': '',
                'dificuldade_rodada': '',
                'tempo_total_partida': 0.0,
                'erros_total_partida': 0,
                'palavra_definida_por_mim': '' # Inicializa o campo para a palavra definida
            })
        logging.info(f"Jogadores cadastrados: {[j['nome'] for j in self.jogadores]}. Prosseguindo para fase de definição de palavra.")
        self.iniciar_fase_definicao_palavra()

    # ============================================================================
    # MÉTODOS DE TELAS E PLACARES
    # ============================================================================

    def mostrar_placar_final_solo(self):
        logging.info("Exibindo placar final (Solo).")
        self.limpar_tela()
        self._criar_frames_iniciais()
        
        for widget in self.frame_placar_solo.winfo_children():
            widget.destroy()

        # Exibir o frame principal do placar
        self.frame_placar_solo.pack(expand=True, fill='both', pady=20)
        
        # Frame centralizado simples
        content_frame = tk.Frame(self.frame_placar_solo, bg=COR_FUNDO_PRINCIPAL)
        content_frame.pack(expand=True, fill='both', padx=100)
        
        # Conteúdo do placar centralizado
        tk.Label(content_frame, text="RESULTADO DA PARTIDA SOLO", font=("Arial", 20, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=15)
        
        jogador = self.jogadores[0]
        tempo_str = f"{jogador['tempo_rodada']:.2f} segundos" if isinstance(jogador['tempo_rodada'], float) else str(jogador['tempo_rodada'])
        erros_str = str(jogador['erros_rodada']) if isinstance(jogador['erros_rodada'], int) else str(jogador['erros_rodada'])

        tk.Label(content_frame, text=f"JOGADOR: {jogador['nome'].upper()}", font=("Arial", 14), fg=COR_TEXTO_CLARO).pack(pady=3)
        tk.Label(content_frame, text=f"PALAVRA: {jogador['palavra_a_adivinhar'].upper()}", font=("Arial", 14), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=3)
        tk.Label(content_frame, text=f"DIFICULDADE: {jogador['dificuldade_rodada'].upper()}", font=("Arial", 14), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=3)
        tk.Label(content_frame, text=f"TEMPO FINAL: {tempo_str}", font=("Arial", 14), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=3)
        tk.Label(content_frame, text=f"ERROS: {erros_str}", font=("Arial", 14), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=3)

        # Botão para ver definição da palavra
        def mostrar_definicao():
            palavra = jogador['palavra_a_adivinhar']
            import webbrowser
            url = f"https://pt.wiktionary.org/wiki/{palavra.lower()}"
            webbrowser.open(url)
        ttk.Button(content_frame, text='Ver definição', command=mostrar_definicao, style='TButton').pack(pady=5)

        # Exibe apenas o ranking da dificuldade jogada
        priorizar_comuns = self.config.obter_config("jogo", "usar_palavras_comuns", False)
        modo = 'comum_on' if priorizar_comuns else 'comum_off'
        dificuldade_atual = jogador['dificuldade_rodada']
        texto_comuns = "(Prioriza Palavras Comuns)" if priorizar_comuns else "(Dicionário Completo)"
        tk.Label(content_frame, text=f"RANKING TOP 10 {texto_comuns} - {dificuldade_atual.upper()}", font=("Arial", 16, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=15)
        top_10 = self.ranking_solo[modo].get(dificuldade_atual, [])[:10]
        if top_10:
            ranking_texto = ""
            for i, entrada in enumerate(top_10):
                tempo_rank = f"{entrada['tempo']:.2f}s" if isinstance(entrada['tempo'], float) else str(entrada['tempo'])
                erros_rank = str(entrada['erros']) if isinstance(entrada['erros'], int) else str(entrada['erros'])
                palavra_rank = entrada.get('palavra', 'N/A').upper()
                ranking_texto += f"{i+1}. {entrada['nome']} - {palavra_rank} - {tempo_rank} - {erros_rank} erros\n"
            tk.Label(content_frame, text=ranking_texto, font=("Arial", 10), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO, justify=tk.CENTER).pack(pady=3)
        else:
            tk.Label(content_frame, text="NENHUM REGISTRO AINDA.", font=("Arial", 10), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=3)

        # Frame para os botões centralizados na parte inferior
        botoes_frame = tk.Frame(self.frame_placar_solo, bg=COR_FUNDO_PRINCIPAL)
        botoes_frame.pack(side=tk.BOTTOM, pady=10)

        def tentar_novamente_solo():
            """Gera uma nova palavra para o mesmo jogador e dificuldade"""
            logging.info(f"Tentando novamente para {self.jogadores[0]['nome']} na dificuldade {self.dificuldade_selecionada.get()}")
            
            # Limpa os dados da rodada anterior
            self.jogadores[0]['erros_rodada'] = 0
            self.jogadores[0]['tempo_rodada'] = 0.0
            self.jogadores[0]['palavra_a_adivinhar'] = ''
            self.jogadores[0]['dificuldade_rodada'] = ''
            self.jogadores[0]['status_rodada'] = ''
            
            # Gera nova palavra e inicia nova rodada
            self.iniciar_fase_definicao_palavra()

        ttk.Button(botoes_frame, text="TENTAR NOVAMENTE", command=tentar_novamente_solo, style="TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(botoes_frame, text="NOVO JOGO", command=self.iniciar_selecao_modo, style="TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(botoes_frame, text="SAIR DO JOGO", command=self.confirmar_saida, style="TButton").pack(side=tk.LEFT, padx=10)
        
        if jogador['status_rodada'] == "INCOMPLETA" and self.som_fim_jogo:
            self.som_fim_jogo.play()
            logging.info("Som de fim de jogo acionado (derrota solo).")

        logging.info("Placar final solo exibido com Top 10 da dificuldade jogada.")

    def mostrar_placar_final_multiplayer(self):
        logging.info("Exibindo placar final (Multiplayer).")
        self.limpar_tela()
        self._criar_frames_iniciais()
        self.frame_placar_multiplayer.pack(expand=True, fill='both', pady=20)

        if self.som_fim_jogo:
            self.som_fim_jogo.play()
            logging.info("Som de fim de jogo acionado para o placar final multiplayer.")

        tk.Label(self.frame_placar_multiplayer, text="RESULTADO FINAL DA PARTIDA MULTIPLAYER", font=("Arial", 28, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=28)
        
        colunas = ('Jogador', 'Palavra Adivinhada', 'Dificuldade', 'Tempo Adivinhando', 'Erros Adivinhando', 'Status')
        tree = ttk.Treeview(self.frame_placar_multiplayer, columns=colunas, show='headings', style="Treeview")
        
        for col in colunas:
            tree.heading(col, text=col, anchor='center')
            if col == 'Jogador':
                tree.column(col, anchor='center', width=120)
            elif col == 'Palavra Adivinhada':
                tree.column(col, anchor='center', width=180)
            elif col == 'Dificuldade':
                tree.column(col, anchor='center', width=110)
            elif col == 'Tempo Adivinhando':
                tree.column(col, anchor='center', width=160)
            elif col == 'Erros Adivinhando':
                tree.column(col, anchor='center', width=130)
            elif col == 'Status':
                tree.column(col, anchor='center', width=110)
            else:
                tree.column(col, anchor='center', width=100)
        
        self.style.configure("Treeview", background=COR_FUNDO_SECUNDARIO, foreground=COR_TEXTO_CLARO, fieldbackground=COR_FUNDO_SECUNDARIO, font=("Arial", 14))
        self.style.map("Treeview", background=[('selected', COR_AZUL_SUAVE_BOTOES)])
        self.style.configure("Treeview.Heading", font=("Arial", 15, "bold"), background=COR_AZUL_SUAVE_BOTOES, foreground="white")

        for jogador in self.jogadores:
            jogador['tempo_total_partida'] = 0.0
            jogador['erros_total_partida'] = 0
            if jogador['status_rodada'] == "ADIVINHOU" and jogador['tempo_rodada'] != float('inf'):
                jogador['tempo_total_partida'] += jogador['tempo_rodada']
                jogador['erros_total_partida'] += jogador['erros_rodada']
            elif jogador['status_rodada'] == "INCOMPLETA":
                jogador['tempo_total_partida'] = float('inf')
                jogador['erros_total_partida'] = 9999

        # REGISTRA PALAVRAS USADAS NO MULTIPLAYER
        for jogador in self.jogadores:
            palavra_definida = jogador.get('palavra_definida_por_mim', '')
            if palavra_definida:
                self.registrar_palavra_multiplayer(palavra_definida)

        jogadores_ordenados = sorted(
            [j for j in self.jogadores if j['status_rodada'] == "ADIVINHOU" and j['tempo_rodada'] != float('inf')], 
            key=lambda x: (x['tempo_total_partida'], x['erros_total_partida'])
        )

        jogadores_incompletos_desistentes = sorted(
            [j for j in self.jogadores if j['status_rodada'] != "ADIVINHOU" or j['tempo_rodada'] == float('inf')],
            key=lambda x: x['nome']
        )
        jogadores_para_exibir = jogadores_ordenados + jogadores_incompletos_desistentes

        for i, jogador in enumerate(jogadores_para_exibir):
            tempo_str = f"{jogador['tempo_rodada']:.2f}s" if isinstance(jogador['tempo_rodada'], float) else str(jogador['tempo_rodada'])
            erros_str = str(jogador['erros_rodada']) if isinstance(jogador['erros_rodada'], int) else str(jogador['erros_rodada'])
            palavra_adivinhada_exibicao = jogador.get('palavra_a_adivinhar', 'N/A')
            tree.insert('', tk.END, values=(
                jogador['nome'].upper(),
                palavra_adivinhada_exibicao.upper() if palavra_adivinhada_exibicao != 'N/A' else 'N/A',
                jogador['dificuldade_rodada'].upper() if jogador['dificuldade_rodada'] else "N/A",
                tempo_str,
                erros_str,
                jogador['status_rodada'].upper()
            ))
        
        tree.pack(pady=28, padx=28, fill='both', expand=True)

        campeao = None
        if jogadores_ordenados:
            campeao = jogadores_ordenados[0]
            tempo_campeao_str = f"{campeao['tempo_total_partida']:.2f}s" if isinstance(campeao['tempo_total_partida'], float) else str(campeao['tempo_total_partida'])
            erros_campeao_str = str(campeao['erros_total_partida']) if isinstance(campeao['erros_total_partida'], int) else str(campeao['erros_total_partida'])
            tk.Label(self.frame_placar_multiplayer, text=f"\nCAMPEÃO: {campeao['nome'].upper()}!", font=("Arial", 26, "bold"), fg=COR_VERDE_ACERTO, bg=COR_FUNDO_PRINCIPAL).pack(pady=14)
            tk.Label(self.frame_placar_multiplayer, text=f"TEMPO TOTAL: {tempo_campeao_str} - ERROS: {erros_campeao_str}", font=("Arial", 20), fg=COR_VERDE_ACERTO_CLARO, bg=COR_FUNDO_PRINCIPAL).pack(pady=7)
        else:
            tk.Label(self.frame_placar_multiplayer, text="\nNÃO FOUI POSSÍVEL DETERMINAR UM CAMPEÃO.", font=("Arial", 20, "bold"), fg=COR_AMARELO_AVISO, bg=COR_FUNDO_PRINCIPAL).pack(pady=14)
            tk.Label(self.frame_placar_multiplayer, text="Nenhum jogador conseguiu adivinhar a palavra.", font=("Arial", 16), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL).pack(pady=7)

        # Novo frame para os botões na parte inferior
        button_frame = tk.Frame(self.frame_placar_multiplayer, bg=COR_FUNDO_PRINCIPAL)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        # Botão para abrir ranking de palavras mais usadas no multiplayer
        def mostrar_palavras_mais_usadas():
            top_palavras = [(palavra, dados["contador"], dados["ordem"]) for palavra, dados in self.palavras_multiplayer.items() if palavra != "__ordem__"]
            # Ordena por contador decrescente, depois ordem crescente
            top_palavras.sort(key=lambda x: (-x[1], x[2]))
            top_10 = top_palavras[:10]
            popup = tk.Toplevel(self.root)
            popup.title("Palavras mais usadas no multiplayer")
            popup.geometry('420x340')
            popup.resizable(False, False)
            popup.config(bg=COR_FUNDO_PRINCIPAL)
            tk.Label(popup, text='TOP 10 PALAVRAS MAIS USADAS', font=("Arial", 16, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=(18, 10))
            if top_10:
                for i, (palavra, contador, ordem) in enumerate(top_10):
                    tk.Label(popup, text=f"{i+1}. {palavra.upper()} - {contador} vez(es)", font=("Arial", 13), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=2)
            else:
                tk.Label(popup, text="Nenhuma palavra registrada ainda.", font=("Arial", 12), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=10)
            ttk.Button(popup, text="Fechar", command=popup.destroy, style="TButton").pack(pady=18, ipadx=8, ipady=3)
            popup.transient(self.root)
            popup.grab_set()
            self.root.wait_window(popup)

        ttk.Button(button_frame, text="PALAVRAS MAIS USADAS NO MULTIPLAYER", command=mostrar_palavras_mais_usadas, style="TButton").pack(side=tk.LEFT, padx=10, expand=True)
        ttk.Button(button_frame, text="JOGAR NOVAMENTE", command=self.iniciar_selecao_modo, style="TButton").pack(side=tk.LEFT, padx=10, expand=True)
        ttk.Button(button_frame, text="SAIR DO JOGO", command=self.confirmar_saida, style="TButton").pack(side=tk.RIGHT, padx=10, expand=True)
        logging.info("Placar final multiplayer exibido.")

    def mostrar_configuracoes(self):
        logging.info("Exibindo tela de configurações.")
        self.limpar_tela()
        self._criar_frames_iniciais()
        self.frame_configuracoes.pack(expand=True, fill='both', pady=20)

        tk.Label(self.frame_configuracoes, text="CONFIGURAÇÕES DO JOGO", font=("Arial", 24, "bold"), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL).pack(pady=20)

        # Frame para as configurações
        config_frame = tk.Frame(self.frame_configuracoes, bg=COR_FUNDO_SECUNDARIO, bd=2, relief="groove")
        config_frame.pack(pady=20, padx=50, fill='both', expand=True)

        # Seção Áudio
        tk.Label(config_frame, text="CONFIGURAÇÕES DE ÁUDIO", font=("Arial", 16, "bold"), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack(pady=10)

        # Volume de efeitos
        tk.Label(config_frame, text="Volume de Efeitos:", font=("Arial", 12), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack()
        volume_efeitos_var = tk.DoubleVar(value=self.config.obter_config("audio", "volume_efeitos"))
        volume_efeitos_scale = tk.Scale(config_frame, from_=0.0, to=1.0, resolution=0.1, 
                                       variable=volume_efeitos_var, orient=tk.HORIZONTAL,
                                       bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO,
                                       highlightbackground=COR_FUNDO_SECUNDARIO)
        volume_efeitos_scale.pack(pady=5)

        # Volume de música
        tk.Label(config_frame, text="Volume de Música:", font=("Arial", 12), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack()
        volume_musica_var = tk.DoubleVar(value=self.config.obter_config("audio", "volume_musica"))
        volume_musica_scale = tk.Scale(config_frame, from_=0.0, to=1.0, resolution=0.1, 
                                      variable=volume_musica_var, orient=tk.HORIZONTAL,
                                      bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO,
                                      highlightbackground=COR_FUNDO_SECUNDARIO)
        volume_musica_scale.pack(pady=5)

        # Som ativado
        som_ativado_var = tk.BooleanVar(value=self.config.obter_config("audio", "som_ativado"))
        tk.Checkbutton(config_frame, text="Ativar Sons", variable=som_ativado_var,
                      font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO,
                      selectcolor=COR_FUNDO_ESCURO_INPUT).pack(pady=5)

        # Música ativada
        musica_ativada_var = tk.BooleanVar(value=self.config.obter_config("audio", "musica_ativada"))
        tk.Checkbutton(config_frame, text="Ativar Música", variable=musica_ativada_var,
                      font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO,
                      selectcolor=COR_FUNDO_ESCURO_INPUT).pack(pady=5)

        # Seção Jogo
        tk.Label(config_frame, text="CONFIGURAÇÕES DE JOGO", font=("Arial", 16, "bold"), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack(pady=10)

        # Dificuldade padrão
        tk.Label(config_frame, text="Dificuldade Padrão:", font=("Arial", 12), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack()
        dificuldade_padrao_var = tk.StringVar(value=self.config.obter_config("jogo", "dificuldade_padrao"))
        dificuldade_combo = ttk.Combobox(config_frame, textvariable=dificuldade_padrao_var,
                                        values=["Fácil", "Médio", "Difícil"], state="readonly",
                                        font=("Arial", 12))
        dificuldade_combo.pack(pady=5)



        # Penalidade por erro
        tk.Label(config_frame, text="Penalidade por Erro (segundos):", font=("Arial", 12), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack()
        penalidade_var = tk.DoubleVar(value=self.config.obter_config("jogo", "penalidade_erro"))
        penalidade_scale = tk.Scale(config_frame, from_=0.0, to=10.0, resolution=0.5, 
                                   variable=penalidade_var, orient=tk.HORIZONTAL,
                                   bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO,
                                   highlightbackground=COR_FUNDO_SECUNDARIO)
        penalidade_scale.pack(pady=5)

        # Mostrar dicas
        mostrar_dicas_var = tk.BooleanVar(value=self.config.obter_config("jogo", "mostrar_dicas"))
        tk.Checkbutton(config_frame, text="Mostrar Dicas", variable=mostrar_dicas_var,
                      font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO,
                      selectcolor=COR_FUNDO_ESCURO_INPUT).pack(pady=5)

        # Seção Dicionário
        tk.Label(config_frame, text="CONFIGURAÇÕES DE DICIONÁRIO", font=("Arial", 16, "bold"), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack(pady=10)
        # Priorizar palavras comuns
        usar_palavras_comuns_var = tk.BooleanVar(value=self.config.obter_config("jogo", "usar_palavras_comuns", False))
        tk.Checkbutton(config_frame, text="Priorizar Palavras Comuns (mais fáceis)", variable=usar_palavras_comuns_var,
                      font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO,
                      selectcolor=COR_FUNDO_ESCURO_INPUT).pack(pady=5)

        # Botões para baixar dicionários
        tk.Label(config_frame, text="Gerenciar Dicionários:", font=("Arial", 12, "bold"), 
                fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack(pady=5)

        def baixar_dicionario_principal():
            if self.baixar_dicionario():
                messagebox.showinfo("SUCESSO", "Dicionário principal baixado com sucesso!")
            else:
                messagebox.showwarning("ERRO", "Não foi possível baixar o dicionário principal.")

        botoes_dicionario_frame = tk.Frame(config_frame, bg=COR_FUNDO_SECUNDARIO)
        botoes_dicionario_frame.pack(pady=5)

        ttk.Button(botoes_dicionario_frame, text="BAIXAR DICIONÁRIO PRINCIPAL", 
                  command=baixar_dicionario_principal, style="TButton").pack(padx=5)

        # Botões de ação
        botoes_frame = tk.Frame(config_frame, bg=COR_FUNDO_SECUNDARIO)
        botoes_frame.pack(pady=20)

        def salvar_configuracoes():
            # Salva as configurações
            self.config.definir_config("audio", "volume_efeitos", volume_efeitos_var.get())
            self.config.definir_config("audio", "volume_musica", volume_musica_var.get())
            self.config.definir_config("audio", "som_ativado", som_ativado_var.get())
            self.config.definir_config("audio", "musica_ativada", musica_ativada_var.get())
            self.config.definir_config("jogo", "dificuldade_padrao", dificuldade_padrao_var.get())
            self.config.definir_config("jogo", "penalidade_erro", penalidade_var.get())
            self.config.definir_config("jogo", "mostrar_dicas", mostrar_dicas_var.get())
            self.config.definir_config("jogo", "usar_palavras_comuns", usar_palavras_comuns_var.get())
            # Troca a paleta e reaplica estilos (não há mais tema)
            self.aplicar_estilos_ttk()
            self.root.config(bg=COR_FUNDO_PRINCIPAL)
            for frame in [getattr(self, attr) for attr in dir(self) if attr.startswith('frame_')]:
                try:
                    frame.config(bg=COR_FUNDO_PRINCIPAL)
                except Exception:
                    pass
            self.iniciar_selecao_modo()

        # Guardar valores originais para detectar alterações
        valores_originais = {
            "volume_efeitos": self.config.obter_config("audio", "volume_efeitos"),
            "volume_musica": self.config.obter_config("audio", "volume_musica"),
            "som_ativado": self.config.obter_config("audio", "som_ativado"),
            "musica_ativada": self.config.obter_config("audio", "musica_ativada"),
            "dificuldade_padrao": self.config.obter_config("jogo", "dificuldade_padrao"),
            "penalidade_erro": self.config.obter_config("jogo", "penalidade_erro"),
            "mostrar_dicas": self.config.obter_config("jogo", "mostrar_dicas"),
            "usar_palavras_comuns": self.config.obter_config("jogo", "usar_palavras_comuns", False)
        }

        def houve_modificacao():
            return (
                volume_efeitos_var.get() != valores_originais["volume_efeitos"] or
                volume_musica_var.get() != valores_originais["volume_musica"] or
                som_ativado_var.get() != valores_originais["som_ativado"] or
                musica_ativada_var.get() != valores_originais["musica_ativada"] or
                dificuldade_padrao_var.get() != valores_originais["dificuldade_padrao"] or
                penalidade_var.get() != valores_originais["penalidade_erro"] or
                mostrar_dicas_var.get() != valores_originais["mostrar_dicas"] or
                usar_palavras_comuns_var.get() != valores_originais["usar_palavras_comuns"]
            )

        def resetar_configuracoes():
            self.config.resetar_configuracoes()
            self.config.definir_config("perfil", "nome_padrao", "JOGADOR")
            # Atualizar os campos na tela para os valores padrão
            volume_efeitos_var.set(self.config.obter_config("audio", "volume_efeitos"))
            volume_musica_var.set(self.config.obter_config("audio", "volume_musica"))
            som_ativado_var.set(self.config.obter_config("audio", "som_ativado"))
            musica_ativada_var.set(self.config.obter_config("audio", "musica_ativada"))
            dificuldade_padrao_var.set(self.config.obter_config("jogo", "dificuldade_padrao"))
            penalidade_var.set(self.config.obter_config("jogo", "penalidade_erro"))
            mostrar_dicas_var.set(self.config.obter_config("jogo", "mostrar_dicas"))
            usar_palavras_comuns_var.set(self.config.obter_config("jogo", "usar_palavras_comuns", False))
            # Não mostra mensagem, não volta ao menu

        def voltar_configuracoes():
            if houve_modificacao():
                if messagebox.askyesno("ALTERAÇÕES NÃO SALVAS", "Você fez alterações que não foram salvas. Deseja sair sem salvar?"):
                    self.iniciar_selecao_modo()
            else:
                self.iniciar_selecao_modo()

        ttk.Button(botoes_frame, text="SALVAR CONFIGURAÇÕES", command=salvar_configuracoes, 
                  style="TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(botoes_frame, text="RESETAR CONFIGURAÇÕES", command=resetar_configuracoes, 
                  style="TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(botoes_frame, text="VOLTAR", command=voltar_configuracoes, 
                  style="TButton").pack(side=tk.RIGHT, padx=10)

        # Botão de depuração do dicionário
        def depurar_dicionario():
            palavra_teste = 'pato'
            total = len(self.dicionario_palavras)
            primeiras = sorted(list(self.dicionario_palavras))[:10]
            contem_pato = 'SIM' if palavra_teste in self.dicionario_palavras else 'NÃO'
            msg = f"Total de palavras carregadas: {total}\n"
            msg += f"Primeiras palavras: {', '.join(primeiras)}\n"
            msg += f"A palavra '{palavra_teste}' está no dicionário: {contem_pato}"
            messagebox.showinfo("Depuração do Dicionário", msg)

        ttk.Button(self.frame_configuracoes, text="Depurar Dicionário", command=depurar_dicionario, style="TButton").pack(pady=10)

    def mostrar_instrucoes(self):
        logging.info("Exibindo tela de instruções.")
        self.limpar_tela()
        self._criar_frames_iniciais()
        self.frame_instrucoes.pack(expand=True, fill='both', pady=20)

        tk.Label(self.frame_instrucoes, text="COMO JOGAR?", font=("Arial", 24, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL).pack(pady=20)

        instrucoes_texto = """
        BEM-VINDO(A) AO JOGO DE ADIVINHAÇÃO DE PALAVRAS - DESAFIO DE RIVAIS!
        
        MODO SOLO:
        1. O sistema escolherá uma palavra aleatória com base na dificuldade selecionada.
        2. As letras da palavra serão embaralhadas e exibidas.
        3. Seu objetivo é digitar a palavra correta, letra por letra, na ordem certa.
        4. Cada letra incorreta adicionará 3 segundos ao seu tempo final.
        5. O tempo é crucial para o ranking! Tente adivinhar o mais rápido possível.
        
        MODO MULTIPLAYER:
        1. Os jogadores se revezam. O primeiro jogador (definidor) escolhe uma palavra.
        2. O próximo jogador (adivinhador) tenta adivinhar a palavra.
        3. As mesmas regras de tempo e erros do Modo Solo se aplicam a cada rodada de adivinhação.
        4. Ao final da partida (quando todos definiram uma palavra), o jogador com o MENOR TEMPO acumulado nas rodadas em que ADIVINHOU (e menos erros em caso de empate) será o CAMPEÃO!
        
        DIFICULDADES:
        - FÁCIL: Palavras de 4 a 5 letras (ex: casa, livro, mesa, porta)
        - MÉDIO: Palavras de 4 a 10 letras (ex: computador, televisão, chocolate)
        - DIFÍCIL: Palavras complexas de 6+ letras (ex: abduzir, acrimônia, ardiloso)
        
        MULTIPLAYER:
        - Os jogadores definem suas próprias palavras
        - Mínimo de 4 letras para qualquer palavra
        - Sem interferência da dificuldade selecionada
        
        CONFIGURAÇÕES:
        - "Priorizar Palavras Comuns": Ativa para usar palavras do dia a dia em todas as dificuldades
        - O jogo filtra automaticamente palavras inadequadas para manter o conteúdo educativo
        
        DICAS:
        - Use as letras embaralhadas para te ajudar!
        - Errar aumenta seu tempo, então pense bem antes de digitar.
        - No multiplayer, escolha palavras que seus amigos conheçam!
        - Divirta-se e desafie seus rivais!
        """

        tk.Label(self.frame_instrucoes, text=instrucoes_texto, font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO, justify=tk.LEFT, wraplength=self.root.winfo_width() - 100).pack(pady=10, padx=50, fill=tk.BOTH, expand=True)

        ttk.Button(self.frame_instrucoes, text="VOLTAR AO INÍCIO", command=self.iniciar_selecao_modo, style="TButton").pack(pady=20)

    def confirmar_saida(self, forcar=False):
        logging.info("Usuário tentou fechar a janela. Confirmando saída.")
        if forcar or messagebox.askyesno("SAIR DO JOGO", "TEM CERTEZA QUE DESEJA SAIR?"):
            if pygame.mixer.get_init():
                pygame.mixer.quit()
                logging.info("Pygame mixer encerrado.")
            self.root.destroy()
            logging.info("Confirmação de saída aceita. Encerrando aplicação.")
        else:
            logging.info("Saída cancelada pelo usuário.")

    def _criar_frames_iniciais(self):
        # Frame de Seleção de Modo
        self.frame_selecao_modo = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)
        self.label_selecao_modo = tk.Label(self.frame_selecao_modo, text="SELECIONE O MODO DE JOGO:", font=("Arial", 20, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)



        # Frame de Nomes dos Jogadores (Dinâmico para Solo/Multi)
        self.frame_nomes_jogadores = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)
        self.label_nomes_multiplayer = tk.Label(self.frame_nomes_jogadores, text="SELECIONE A QUANTIDADE DE JOGADORES:", font=("Arial", 20, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)

        self.label_num_jogadores_multiplayer = tk.Label(self.frame_nomes_jogadores, text="QUANTOS JOGADORES?", font=("Arial", 14), bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO)
        self.spinbox_num_jogadores = ttk.Spinbox(self.frame_nomes_jogadores, from_=2, to=5, textvariable=self.num_jogadores_multiplayer, width=5, font=("Arial", 14), state='readonly')

        self.frame_entry_nomes = tk.Frame(self.frame_nomes_jogadores, bg=COR_FUNDO_PRINCIPAL)

        self.btn_iniciar_jogo_principal = ttk.Button(self.frame_nomes_jogadores, text="INICIAR JOGO", command=self.finalizar_cadastro_jogadores, style="TButton", state='disabled')
        self.btn_voltar_nomes = ttk.Button(self.frame_nomes_jogadores, text="VOLTAR", command=self.iniciar_selecao_modo, style="TButton")



        # Frame Jogador 1 (Definidor da Palavra Secreta - Multiplayer)
        self.frame_jogador1 = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)
        self.label_jogador1 = tk.Label(self.frame_jogador1, text="DEFINA A PALAVRA SECRETA:", font=("Arial", 20, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)

        self.entry_palavra_secreta = tk.Entry(self.frame_jogador1, textvariable=self.palavra_secreta_var, font=("Arial", 24), bd=2, relief="solid", bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO, justify='center')
        self.entry_palavra_secreta.bind("<KeyRelease>", lambda event, var=self.palavra_secreta_var: self.on_entry_uppercase(var, event))
        self.entry_palavra_secreta.bind("<Return>", lambda event: self.processar_palavra_secreta())

        # Frame Jogador 2 (Adivinhador da Palavra)
        self.frame_jogador2 = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)

        self.label_instrucao_jogador2 = tk.Label(self.frame_jogador2, text="", font=("Arial", 20, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)

        self.label_tempo = tk.Label(self.frame_jogador2, text="TEMPO: 0.00S", font=("Arial", 16), fg=COR_TEXTO_CLARO_DESTACADO, bg=COR_FUNDO_PRINCIPAL)

        self.label_erros = tk.Label(self.frame_jogador2, text="ERROS: 0", font=("Arial", 16), fg=COR_TEXTO_CLARO_DESTACADO, bg=COR_FUNDO_PRINCIPAL)

        self.label_letras_tentadas = tk.Label(self.frame_jogador2, text="LETRAS TENTADAS (GERAL):", font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)

        self.label_letras_erradas = tk.Label(self.frame_jogador2, text="LETRAS ERRADAS:", font=("Arial", 12), fg=COR_VERMELHO_ERRO, bg=COR_FUNDO_PRINCIPAL)

        self.frame_palavra_adivinhada = tk.Frame(self.frame_jogador2, bg=COR_FUNDO_SECUNDARIO, bd=2, relief="sunken")

        self.label_letras_embaralhadas = tk.Label(self.frame_jogador2, text="LETRAS DISPONÍVEIS:", font=("Arial", 16, "bold"), fg=COR_TEXTO_CLARO_DESTACADO, bg=COR_FUNDO_PRINCIPAL)

        self.frame_letras_embaralhadas_botoes = tk.Frame(self.frame_jogador2, bg=COR_FUNDO_PRINCIPAL)

        self.botao_iniciar_jogador2 = ttk.Button(self.frame_jogador2, text="INICIAR RODADA", command=self.iniciar_partida_jogador, style="TButton")

        self.btn_desistir = ttk.Button(self.frame_jogador2, text="DESISTIR DA PARTIDA", command=self.desistir_partida, style="TButton")

        # Frame do Placar Final (Solo)
        self.frame_placar_solo = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)

        # Frame do Placar Final (Multiplayer)
        self.frame_placar_multiplayer = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)

        # Frame de Instruções
        self.frame_instrucoes = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)

        # Frame de Configurações
        self.frame_configuracoes = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)

    def buscar_definicao_dicio(self, palavra):
        import requests
        try:
            url = f'https://dicio-api.vercel.app/v2/{palavra.lower()}'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and 'meanings' in data[0]:
                    significados = data[0]['meanings']
                    definicao = '\n'.join(significados)
                    return definicao
        except Exception:
            pass  # Ignora erro e tenta Wiktionary
        # Tenta Wiktionary
        try:
            url_wikt = f'https://pt.wiktionary.org/wiki/{palavra.lower()}'
            response = requests.get(url_wikt, timeout=5)
            if response.status_code == 200:
                from bs4 import BeautifulSoup, Tag
                soup = BeautifulSoup(response.text, 'html.parser')
                # Procura a primeira definição em <ol><li> dentro da seção 'Português'
                secao_pt = soup.find('span', {'id': 'Português'})
                if secao_pt:
                    # Primeiro tenta <ol><li>
                    ol = secao_pt.find_next('ol')
                    if isinstance(ol, Tag):
                        lis = ol.find_all('li', recursive=False)
                        if lis:
                            definicao = lis[0].get_text(strip=True)
                            return f'Definição (Wiktionary):\n{definicao}'
                    # Se não achou <ol><li>, pega o primeiro <p> após a seção
                    p = secao_pt.find_next('p')
                    if isinstance(p, Tag):
                        texto = p.get_text(strip=True)
                        if texto:
                            return f'Definição (Wiktionary):\n{texto}'
        except Exception:
            pass
        return None

    def mostrar_opcoes_esc(self, event=None):
        # Popup centralizado com confirmação de saída
        popup = tk.Toplevel(self.root)
        popup.title("Sair do Jogo")
        popup.geometry('340x140')
        popup.resizable(False, False)
        popup.config(bg=COR_FUNDO_PRINCIPAL)
        self.centralizar_janela(popup)
        
        tk.Label(popup, text="Você deseja realmente sair?", font=("Segoe UI", 15, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL).pack(pady=(28, 18))
        
        botoes_frame = tk.Frame(popup, bg=COR_FUNDO_PRINCIPAL)
        botoes_frame.pack(pady=0)
        
        def sair():
            popup.destroy()
            self.confirmar_saida(forcar=True)
        def cancelar():
            popup.destroy()
        
        ttk.Button(botoes_frame, text="Sim", command=sair, style="TButton").pack(side=tk.LEFT, padx=16, ipadx=10, ipady=2)
        ttk.Button(botoes_frame, text="Não", command=cancelar, style="TButton").pack(side=tk.LEFT, padx=16, ipadx=10, ipady=2)
        
        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)

    @staticmethod
    def aplicar_paleta(tema):
        global COR_FUNDO_PRINCIPAL, COR_FUNDO_SECUNDARIO, COR_TEXTO_CLARO, COR_TEXTO_CLARO_DESTACADO, COR_AZUL_SUAVE_BOTOES, COR_VERDE_ACERTO, COR_VERDE_ACERTO_CLARO, COR_VERMELHO_ERRO, COR_AMARELO_AVISO, COR_BOTAO_PRESSIONADO, COR_FUNDO_ESCURO_INPUT, COR_BORDA
        if tema == 'escuro':
            paleta = PALETA_ESCURO
        else:
            paleta = PALETA_CLARA
        COR_FUNDO_PRINCIPAL = paleta['COR_FUNDO_PRINCIPAL']
        COR_FUNDO_SECUNDARIO = paleta['COR_FUNDO_SECUNDARIO']
        COR_TEXTO_CLARO = paleta['COR_TEXTO_CLARO']
        COR_TEXTO_CLARO_DESTACADO = paleta['COR_TEXTO_CLARO_DESTACADO']
        COR_AZUL_SUAVE_BOTOES = paleta['COR_AZUL_SUAVE_BOTOES']
        COR_VERDE_ACERTO = paleta['COR_VERDE_ACERTO']
        COR_VERDE_ACERTO_CLARO = paleta['COR_VERDE_ACERTO_CLARO']
        COR_VERMELHO_ERRO = paleta['COR_VERMELHO_ERRO']
        COR_AMARELO_AVISO = paleta['COR_AMARELO_AVISO']
        COR_BOTAO_PRESSIONADO = paleta['COR_BOTAO_PRESSIONADO']
        COR_FUNDO_ESCURO_INPUT = paleta['COR_FUNDO_ESCURO_INPUT']
        COR_BORDA = paleta['COR_BORDA']

    def carregar_palavras_usadas(self):
        if os.path.exists(self.arquivo_palavras_usadas):
            try:
                with open(self.arquivo_palavras_usadas, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"Fácil": [], "Médio": [], "Difícil": []}
        else:
            return {"Fácil": [], "Médio": [], "Difícil": []}

    def salvar_palavras_usadas(self):
        try:
            with open(self.arquivo_palavras_usadas, "w", encoding="utf-8") as f:
                json.dump(self.palavras_usadas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Erro ao salvar palavras usadas: {e}")

    def carregar_palavras_multiplayer(self):
        if os.path.exists(self.arquivo_palavras_multiplayer):
            try:
                with open(self.arquivo_palavras_multiplayer, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        else:
            return {}

    def salvar_palavras_multiplayer(self):
        try:
            with open(self.arquivo_palavras_multiplayer, "w", encoding="utf-8") as f:
                json.dump(self.palavras_multiplayer, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Erro ao salvar palavras multiplayer: {e}")

    def registrar_palavra_multiplayer(self, palavra):
        palavra_lower = palavra.lower()
        if palavra_lower not in self.palavras_multiplayer:
            # Salva ordem incremental para desempate
            ordem = self.palavras_multiplayer.get("__ordem__", 0) + 1
            self.palavras_multiplayer[palavra_lower] = {"contador": 1, "ordem": ordem}
            self.palavras_multiplayer["__ordem__"] = ordem
        else:
            self.palavras_multiplayer[palavra_lower]["contador"] += 1
        self.salvar_palavras_multiplayer()

    def _sortear_palavra_solo(self):
        palavra_secreta_gerada = self.gerar_palavra_sistema()
        self.fechar_carregando_palavra()
        if palavra_secreta_gerada:
            self.jogadores[0]['palavra_a_adivinhar'] = palavra_secreta_gerada
            self.jogadores[0]['dificuldade_rodada'] = self.dificuldade_selecionada.get()
            self.jogador_atual_idx = 0
            logging.info(f"Palavra solo '{palavra_secreta_gerada}' atribuída ao jogador {self.jogadores[0]['nome']}.")
            self.iniciar_rodada_adivinhacao()
        else:
            logging.error("Falha ao gerar palavra para o jogo solo. Voltando ao menu.")
            messagebox.showerror("Erro na Geração da Palavra", "Não foi possível gerar uma palavra para o jogo solo. Voltando ao menu.")
            self.iniciar_selecao_modo()

# --- Tratamento de Erros Geral ---
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Ocorreu um erro inesperado na aplicação!", exc_info=(exc_type, exc_value, exc_traceback))
    messagebox.showerror("ERRO FATAL",
                         f"Ocorreu um erro inesperado e o jogo precisa ser fechado.\n"
                         f"Detalhes: {exc_value}\n"
                         f"Verifique o arquivo '{log_file_path}' para mais informações.")
    # Não chame root.destroy() aqui, pois o GameApp já faz isso no confirmar_saida se for o caso
    # Ou, se for um erro realmente fatal que impede o Tkinter de continuar, sys.exit() é mais adequado.

sys.excepthook = handle_exception

# --- Início do Programa Principal ---
if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root) # Cria uma instância da classe GameApp
    
    logging.info("Entering root.mainloop()..")
    try:
        root.mainloop()
    except Exception as e:
        handle_exception(type(e), e, e.__traceback__)
    finally:
        logging.info("--- FIM DA EXECUÇÃO DO JOGO ---")
        sys.exit()

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def centralizar_janela(janela):
    """Centraliza uma janela na tela"""
    janela.update_idletasks()
    largura = janela.winfo_width()
    altura = janela.winfo_height()
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f'+{x}+{y}')
    logging.info(f"Janela centralizada: {largura}x{altura} em {x},{y}")

def embaralhar_palavra(palavra):
    """Embaralha as letras de uma palavra"""
    letras = list(palavra)
    random.shuffle(letras)
    return ''.join(letras)

def validar_palavra(palavra, min_len=4, max_len=20):
    """Valida se uma palavra é adequada para o jogo"""
    if not palavra or not palavra.isalpha():
        return False, "A palavra deve conter apenas letras."
    
    if len(palavra) < min_len:
        return False, f"A palavra deve ter no mínimo {min_len} letras."
    
    if len(palavra) > max_len:
        return False, f"A palavra deve ter no máximo {max_len} letras."
    
    return True, ""

def filtrar_palavra_inadequada(palavra, palavras_inadequadas):
    """Verifica se uma palavra contém conteúdo inadequado"""
    palavra_lower = palavra.lower()
    
    # Verifica se a palavra está na lista de palavras inadequadas
    if palavra_lower in palavras_inadequadas:
        return True
    
    # Verifica se contém substrings inadequadas
    for termo_inadequado in palavras_inadequadas:
        if termo_inadequado in palavra_lower:
            return True
    
    return False

def levenshtein_distance(s1, s2):
    """Calcula a distância de Levenshtein entre duas strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

# Função sugerir_palavras removida - versão otimizada está na classe GameApp

def criar_botao_estilo(parent, texto, comando, **kwargs):
    """Cria um botão com estilo padrão"""
    return ttk.Button(parent, text=texto, command=comando, style="TButton", **kwargs)

def criar_label_estilo(parent, texto, **kwargs):
    """Cria um label com estilo padrão"""
    return tk.Label(parent, text=texto, bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO, **kwargs)

# ============================================================================
# ESTRUTURA DO CÓDIGO OTIMIZADO
# ============================================================================
# 
# O código foi organizado em seções lógicas para facilitar manutenção:
# 
# 1. CONFIGURAÇÕES E CONSTANTES - Cores, URLs, arquivos
# 2. CLASSE PRINCIPAL DO JOGO (GameApp)
#   2.1 MÉTODOS DE CONFIGURAÇÃO E INICIALIZAÇÃO
#   2.2 MÉTODOS DE ÁUDIO
#   2.3 MÉTODOS DE DICIONÁRIO E PALAVRAS
#   2.4 MÉTODOS DE INTERFACE E INTERAÇÃO
#   2.5 MÉTODOS DE LÓGICA DO JOGO
#   2.6 MÉTODOS DE INTERFACE E NAVEGAÇÃO
#   2.7 MÉTODOS DE CONTROLE DE TEMPO
#   2.8 MÉTODOS DE RANKING
#   2.9 MÉTODOS DE INTERFACE DE USUÁRIO
#   2.10 MÉTODOS DE TELAS E PLACARES
# 3. FUNÇÕES UTILITÁRIAS - Funções auxiliares reutilizáveis
# 
# Melhorias implementadas:
# - Organização em seções lógicas com comentários claros
# - Otimização do carregamento de sons
# - Funções utilitárias extraídas
# - Melhor tratamento de erros
# - Código mais legível e manutenível
# ============================================================================

# =========================================================================
# PALETAS DE CORES: CLARO (PADRÃO) E ESCURO
# =========================================================================
PALETA_CLARA = {
    'COR_FUNDO_PRINCIPAL': "#FEFAE0",
    'COR_FUNDO_SECUNDARIO': "#F9EBC7",
    'COR_TEXTO_CLARO': "#5F6F52",
    'COR_TEXTO_CLARO_DESTACADO': "#C4661F",
    'COR_AZUL_SUAVE_BOTOES': "#A9B388",
    'COR_VERDE_ACERTO': "#A9B388",
    'COR_VERDE_ACERTO_CLARO': "#B99470",
    'COR_VERMELHO_ERRO': "#C4661F",
    'COR_AMARELO_AVISO': "#F9EBC7",
    'COR_BOTAO_PRESSIONADO': "#B99470",
    'COR_FUNDO_ESCURO_INPUT': "#E6E2C3",
    'COR_BORDA': "#783D19"
}
PALETA_ESCURO = {
    'COR_FUNDO_PRINCIPAL': "#232323",
    'COR_FUNDO_SECUNDARIO': "#2D2D2D",
    'COR_TEXTO_CLARO': "#F2F2F2",
    'COR_TEXTO_CLARO_DESTACADO': "#B5B5B5",
    'COR_AZUL_SUAVE_BOTOES': "#444444",
    'COR_VERDE_ACERTO': "#444444",
    'COR_VERDE_ACERTO_CLARO': "#3A3A3A",
    'COR_VERMELHO_ERRO': "#C4661F",
    'COR_AMARELO_AVISO': "#444444",
    'COR_BOTAO_PRESSIONADO': "#3A3A3A",
    'COR_FUNDO_ESCURO_INPUT': "#232323",
    'COR_BORDA': "#888888"
}
