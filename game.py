import os
import sys
import time
import random
import string
import json
import platform
import logging

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import requests
import pygame.mixer

# --- Configuração do Logging ---
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game_log.txt")
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.info("--- INÍCIO DA EXECUÇÃO DO JOGO ---")

# --- CORES ---
COR_FUNDO_PRINCIPAL = "#2C3E50"
COR_FUNDO_SECUNDARIO = "#34495E"
COR_TEXTO_CLARO = "#ECF0F1"
COR_TEXTO_CLARO_DESTACADO = "#BDC3C7"
COR_AZUL_SUAVE_BOTOES = "#3498DB"
COR_VERDE_ACERTO = "#2ECC71"
COR_VERDE_ACERTO_CLARO = "#27AE60"
COR_VERMELHO_ERRO = "#E74C3C"
COR_AMARELO_AVISO = "#F1C40F"
COR_BOTAO_PRESSIONADO = "#2980B9"
COR_FUNDO_ESCURO_INPUT = "#1C2833"

# --- Constantes de Penalidade ---
PENALIDADE_ERRO = 3  # Penalidade em segundos por erro

# --- Classe Principal do Jogo ---
class GameApp:
    # Constantes
    MAX_SUGESTOES = 5
    
    def __init__(self, root):
        self.root = root
        self.root.title("JOGO DE ADIVINHAÇÃO DE PALAVRAS - DESAFIO DE RIVAIS")
        self.root.config(bg=COR_FUNDO_PRINCIPAL)

        # Configuração da janela (maximizada ou tela cheia)
        if platform.system() == "Windows":
            self.root.state('zoomed')
            logging.info("Janela maximizada (Windows).")
        else:
            try:
                self.root.attributes('-fullscreen', True)
                logging.info("Janela em tela cheia (outros OS).")
            except tk.TclError:
                logging.warning("Aviso: Tela cheia não suportada ou houve um erro ao aplicar. A janela será maximizada.")
                self.root.state('zoomed')

        self.centralizar_janela(self.root)

        # --- Variáveis de Estado do Jogo (agora atributos da instância) ---
        self.palavra_secreta = ""
        self.letras_embaralhadas = ""
        self.palavra_adivinhada_entries = []
        self.entry_vars_adivinhacao = []
        self.erros_rodada_atual = 0
        self.letras_ja_tentadas_exibicao = set()
        self.letras_erradas_exibicao = set()
        self.indice_atual = 0

        self.jogadores = []
        self.jogador_atual_idx = 0
        self.jogador_definidor_idx = 0

        self.tempo_inicio_rodada = 0
        self.timer_id = None
        self.tempo_total_jogador_atual = 0.0
        self.tempo_penalidade_acumulada = 0.0
        self.partida_desistida = False

        self.num_jogadores_total = 0
        self.entry_nomes_jogadores = []

        self.botoes_letras_embaralhadas = []

        self.dificuldade_selecionada = tk.StringVar(root)
        self.dificuldade_selecionada.set("Médio")

        self.modo_jogo_selecionado = tk.StringVar(root)
        self.modo_jogo_selecionado.set("")

        self.palavra_secreta_var = tk.StringVar(root)

        self.num_jogadores_multiplayer = tk.IntVar(root)
        self.num_jogadores_multiplayer.set(2)

        self.ranking_solo = {
            "Fácil": [],
            "Médio": [],
            "Difícil": []
        }
        self.ARQUIVO_RANKING = "ranking_solo.json"

        self.dicionario_palavras = set()
        self.URL_DICIONARIO_ONLINE = "https://raw.githubusercontent.com/pythonprobr/palavras/master/palavras.txt"
        self.ARQUIVO_LOCAL_DICIONARIO = "palavras.txt"

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

        self.style.configure("TButton",
                        font=("Arial", 12, "bold"),
                        foreground=COR_TEXTO_CLARO,
                        background=COR_AZUL_SUAVE_BOTOES,
                        padding=10,
                        relief="flat")
        self.style.map("TButton",
                  background=[('active', COR_BOTAO_PRESSIONADO)],
                  foreground=[('disabled', '#6C7A89')])

        self.style.configure("TRadiobutton",
                        font=("Arial", 12),
                        foreground=COR_TEXTO_CLARO,
                        background=COR_FUNDO_SECUNDARIO)
        self.style.map("TRadiobutton",
                  background=[('active', COR_FUNDO_PRINCIPAL)],
                  foreground=[('disabled', '#6C7A89')])

        self.style.configure("TSpinbox",
                        font=("Arial", 14),
                        background=COR_FUNDO_ESCURO_INPUT,
                        foreground=COR_TEXTO_CLARO,
                        fieldbackground=COR_FUNDO_ESCURO_INPUT,
                        arrowsize=15)
        self.style.map("TSpinbox",
                  background=[('readonly', COR_FUNDO_ESCURO_INPUT)],
                  fieldbackground=[('readonly', COR_FUNDO_ESCURO_INPUT)],
                  foreground=[('readonly', COR_TEXTO_CLARO)])

        self.style.configure("Letter.TButton",
                        font=("Arial", 18, "bold"),
                        foreground="white",
                        background=COR_AZUL_SUAVE_BOTOES,
                        padding=8,
                        width=3,
                        relief="raised")
        self.style.map("Letter.TButton",
                  background=[('active', COR_BOTAO_PRESSIONADO)],
                  foreground=[('disabled', '#6C7A89')])

        self.style.configure("LetterPressed.TButton",
                        font=("Arial", 18, "bold"),
                        foreground="white",
                        background=COR_VERDE_ACERTO,
                        padding=8,
                        width=3,
                        relief="sunken")

        self.style.configure("Title.TLabel",
                        font=("Arial", 28, "bold"),
                        foreground=COR_TEXTO_CLARO,
                        background=COR_FUNDO_PRINCIPAL)
        self.style.configure("SubTitle.TLabel",
                        font=("Arial", 20, "bold"),
                        foreground=COR_TEXTO_CLARO,
                        background=COR_FUNDO_PRINCIPAL)

    def carregar_sons(self):
        try:
            sons = {
                "som_acerto": "sons/acerto_letra.wav",
                "som_erro": "sons/erro_letra.wav",
                "som_vitoria_palavra": "sons/vitoria_palavra.wav",
                "musica_menu": "sons/musica_menu.wav",
                "som_teclado": "sons/teclado.wav",
                "som_fim_jogo": "sons/fim_jogo.wav",
                "som_iniciar_rodada": "sons/iniciar_rodada.wav"
            }
            for nome, caminho in sons.items():
                try:
                    setattr(self, nome, pygame.mixer.Sound(caminho))
                except pygame.error as e:
                    setattr(self, nome, None)
                    logging.warning(f"Erro ao carregar {caminho}: {e}")
            # Volumes
            if self.som_acerto: self.som_acerto.set_volume(0.7)
            if self.som_erro: self.som_erro.set_volume(0.7)
            if self.som_vitoria_palavra: self.som_vitoria_palavra.set_volume(0.8)
            if self.musica_menu: self.musica_menu.set_volume(0.5)
            if self.som_teclado: self.som_teclado.set_volume(0.3)
            if self.som_fim_jogo: self.som_fim_jogo.set_volume(0.9)
            if self.som_iniciar_rodada: self.som_iniciar_rodada.set_volume(0.7)

            logging.info("Sons carregados com sucesso.")
        except Exception as e:
            messagebox.showwarning("Erro de Áudio", f"Não foi possível carregar alguns sons: {e}\nVerifique se os arquivos .wav existem na pasta 'sons/'. O jogo continuará sem eles.")
            logging.warning(f"Erro ao carregar sons: {e}")

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

    def carregar_dicionario(self):
        logging.info("Tentando carregar dicionário local.")
        
        if os.path.exists(self.ARQUIVO_LOCAL_DICIONARIO) and os.stat(self.ARQUIVO_LOCAL_DICIONARIO).st_size > 0:
            try:
                with open(self.ARQUIVO_LOCAL_DICIONARIO, "r", encoding="utf-8") as f:
                    palavras = set(palavra.strip().lower() for palavra in f.readlines() if palavra.strip())
                self.dicionario_palavras = palavras
                logging.info(f"Dicionário local carregado com sucesso. Total de palavras: {len(self.dicionario_palavras)}")
                return True
            except Exception as e:
                logging.error(f"Erro ao carregar dicionário local: {e}", exc_info=True)
                messagebox.showerror("ERRO NO DICIONÁRIO", f"ERRO AO CARREGAR O DICIONÁRIO LOCAL: {e}")
                return False
        else:
            logging.warning("Dicionário local não encontrado ou vazio. Tentando baixar.")
            if self.baixar_dicionario():
                return self.carregar_dicionario()
            return False

        if not self.dicionario_palavras:
            logging.error("ERRO CRÍTICO: Dicionário não pôde ser carregado.")
            messagebox.showerror("ERRO CRÍTICO", "O DICIONÁRIO DE PALAVRAS NÃO PÔDE SER CARREGADO.\nO JOGO NÃO PODE FUNCIONAR SEM UM DICIONÁRIO.")
            return False
        
        return True

    def levenshtein_distance(self, s1, s2):
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

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

    def sugerir_palavras(self, palavra_digitada, limite_distancia=2):
        logging.info(f"Gerando sugestões para '{palavra_digitada}' com limite de distância {limite_distancia}.")
        sugestoes = []
        for palavra_dic in self.dicionario_palavras:
            if abs(len(palavra_dic) - len(palavra_digitada)) > limite_distancia:
                continue

            dist = self.levenshtein_distance(palavra_digitada, palavra_dic)

            if dist <= limite_distancia:
                sugestoes.append((palavra_dic, dist))

        sugestoes.sort(key=lambda x: (x[1], x[0]))
        logging.info(f"Sugestões encontradas: {[s[0] for s in sugestoes[:self.MAX_SUGESTOES]]}")
        return [s[0] for s in sugestoes[:self.MAX_SUGGESTIONS]]

    def mostrar_sugestoes(self, palavra_errada, sugestoes):
        logging.info(f"Exibindo sugestões para a palavra inválida: '{palavra_errada}'")
        janela_sugestao = tk.Toplevel(self.root)
        janela_sugestao.title("PALAVRA INVÁLIDA - SUGESTÕES")
        janela_sugestao.geometry("400x300")
        janela_sugestao.transient(self.root)
        janela_sugestao.grab_set()
        janela_sugestao.config(bg=COR_FUNDO_SECUNDARIO)

        tk.Label(janela_sugestao, text=f"A PALAVRA '{palavra_errada.upper()}' NÃO É VÁLIDA.",
                 font=("Arial", 14, "bold"), fg=COR_VERMELHO_ERRO, bg=COR_FUNDO_SECUNDARIO).pack(pady=10)
        tk.Label(janela_sugestao, text="VOCÊ QUIS DIZER ALGUMA DESTA?",
                 font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO).pack(pady=5)

        listbox_sugestoes = tk.Listbox(janela_sugestao, font=("Arial", 12), height=min(len(sugestoes), 5), width=30,
                                       bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO,
                                       selectbackground=COR_AZUL_SUAVE_BOTOES, selectforeground="white")
        listbox_sugestoes.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        if not sugestoes:
            listbox_sugestoes.insert(tk.END, "NENHUMA SUGESTÃO ENCONTRADA.")
            btn_ok_sem_sugestao = ttk.Button(janela_sugestao, text="OK",
                                             command=janela_sugestao.destroy,
                                             style="TButton")
            btn_ok_sem_sugestao.pack(pady=10)
        else:
            for sugestao in sugestoes:
                listbox_sugestoes.insert(tk.END, sugestao.upper())

            def usar_sugestao():
                selecionado_idx = listbox_sugestoes.curselection()
                if selecionado_idx:
                    palavra_selecionada = listbox_sugestoes.get(selecionado_idx[0]).lower()
                    self.palavra_secreta_var.set(palavra_selecionada.upper())
                    janela_sugestao.destroy()
                    self.processar_palavra_secreta()
                    logging.info(f"Sugestão '{palavra_selecionada.upper()}' usada.")
                else:
                    messagebox.showwarning("NENHUMA SELEÇÃO", "POR FAVOR, SELECIONE UMA PALAVRA OU CLIQUE EM 'DIGITAR NOVAMENTE'.")
                    logging.warning("Tentativa de usar sugestão sem seleção.")

            def digitar_novamente():
                self.palavra_secreta_var.set("")
                self.entry_palavra_secreta.focus_set()
                janela_sugestao.destroy()
                logging.info("Usuário optou por digitar a palavra novamente.")

            btn_usar_sugestao = ttk.Button(janela_sugestao, text="USAR SELECIONADA",
                                           command=usar_sugestao,
                                           style="TButton")
            btn_usar_sugestao.pack(side=tk.LEFT, padx=10, pady=5)

            btn_digitar_novamente = ttk.Button(janela_sugestao, text="DIGITAR NOVAMENTE",
                                               command=digitar_novamente,
                                               style="TButton")
            btn_digitar_novamente.pack(side=tk.RIGHT, padx=10, pady=5)

        self.root.wait_window(janela_sugestao)

    def embaralhar_palavra(self, palavra):
        """
        Embaralha a palavra de acordo com a dificuldade selecionada.
        Para 'Difícil', adiciona letras extras.
        """
        letras_base = list(palavra)
        logging.info(f"Embaralhando palavra '{palavra}' para dificuldade: {self.dificuldade_selecionada.get()}")

        if self.dificuldade_selecionada.get() == "Difícil":
            letras_unicas = sorted(list(set(letras_base)))

            letras_adicionais = []
            todas_as_letras_alfabeto = list(string.ascii_uppercase)
            letras_disponiveis = [l for l in todas_as_letras_alfabeto if l not in letras_unicas]

            for _ in range(3):
                if letras_disponiveis:
                    letra_aleatoria = random.choice(letras_disponiveis)
                    letras_adicionais.append(letra_aleatoria)
                    letras_disponiveis.remove(letra_aleatoria)
                else:
                    break

            letras_para_embaralhar = letras_unicas + letras_adicionais
        else:
            letras_para_embaralhar = letras_base 

        random.shuffle(letras_para_embaralhar)
        embaralhada = ''.join(letras_para_embaralhar)
        logging.info(f"Palavra embaralhada: {embaralhada}")
        return embaralhada

    def gerar_palavra_sistema(self):
        dificuldade = self.dificuldade_selecionada.get()
        palavras_filtradas = []
        logging.info(f"Gerando palavra do sistema para dificuldade: {dificuldade} no modo {self.modo_jogo_selecionado.get()}.")

        if not self.dicionario_palavras:
            logging.error("Dicionário de palavras vazio. Não é possível gerar palavra do sistema.")
            messagebox.showerror("Dicionário não carregado", "Não há palavras no dicionário para o sistema escolher. Verifique o arquivo 'palavras.txt'.")
            return None

        min_len_global = 3

        if self.modo_jogo_selecionado.get() == "solo":
            if dificuldade == "Fácil":
                palavras_filtradas = [p for p in self.dicionario_palavras if min_len_global <= len(p) <= 7]
            elif dificuldade == "Médio":
                palavras_filtradas = [p for p in self.dicionario_palavras if min_len_global <= len(p) <= 10]
            elif dificuldade == "Difícil":
                palavras_filtradas = [p for p in self.dicionario_palavras if len(p) >= 8]
        else:
            if dificuldade == "Fácil":
                palavras_filtradas = [p for p in self.dicionario_palavras if min_len_global <= len(p) <= 10]
            elif dificuldade == "Médio":
                palavras_filtradas = [p for p in self.dicionario_palavras if len(p) >= min_len_global]
            elif dificuldade == "Difícil":
                palavras_filtradas = [p for p in self.dicionario_palavras if len(p) >= min_len_global]

        if not palavras_filtradas:
            logging.warning(f"Não foram encontradas palavras para a dificuldade '{dificuldade}'. Tentando fallback.")
            messagebox.showwarning("Palavras Insuficientes",
                                   f"Não foi possível encontrar palavras para a dificuldade '{dificuldade}'. Escolhendo uma palavra aleatória com no mínimo {min_len_global} letras.")
            valid_fallback_words = [p for p in self.dicionario_palavras if len(p) >= min_len_global]
            if valid_fallback_words:
                palavra_escolhida = random.choice(valid_fallback_words).upper()
                logging.info(f"Fallback: palavra '{palavra_escolhida}' escolhida.")
                return palavra_escolhida
            else:
                logging.critical("Nenhuma palavra válida encontrada no dicionário, nem mesmo com fallback.")
                messagebox.showerror("Erro Crítico", "Nenhuma palavra válida encontrada no dicionário, nem mesmo com fallback.")
                return None

        palavra_escolhida = random.choice(palavras_filtradas).upper()
        logging.info(f"Palavra do sistema escolhida: {palavra_escolhida} (Dificuldade: {dificuldade})")
        return palavra_escolhida

    def iniciar_fase_definicao_palavra(self):
        logging.info(f"Iniciando fase de definição de palavra. Modo: {self.modo_jogo_selecionado.get()}")

        self.partida_desistida = False

        if self.modo_jogo_selecionado.get() == 'solo':
            logging.info("Modo SOLO selecionado. Gerando palavra do sistema.")
            palavra_secreta_gerada = self.gerar_palavra_sistema()
            if palavra_secreta_gerada:
                self.jogadores[0]['palavra_a_adivinhar'] = palavra_secreta_gerada
                self.jogadores[0]['dificuldade_rodada'] = self.dificuldade_selecionada.get()
                self.jogador_atual_idx = 0
                logging.info(f"Palavra solo '{palavra_secreta_gerada}' atribuída ao jogador {self.jogadores[0]['nome']}.")
                self.iniciar_rodada_adivinhacao()
            else:
                logging.error("Falha ao gerar palavra para o jogo solo. Voltando ao menu.")
                messagebox.showerror("Erro na Geração da Palavra", "Não foi possível gerar uma palavra para o jogo solo. Voltando ao menu.")
                self.iniciar_configuracao()
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
        ttk.Button(self.frame_jogador1, text="VOLTAR AO INÍCIO", command=self.iniciar_selecao_modo, style="TButton").pack(pady=5)
        self.frame_jogador1.pack(expand=True, fill='both', pady=20)

        self.root.after(100, self.entry_palavra_secreta.focus_set)
        logging.info("Exibindo tela de definição de palavra para o definidor.")

    def on_entry_uppercase(self, var, event=None):
        current_value = var.get()
        new_value = current_value.upper()
        if current_value != new_value:
            var.set(new_value)
        
        if self.som_teclado and event and event.char and event.keysym not in (
            'BackSpace', 'Return', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 
            'Alt_L', 'Alt_R', 'Caps_Lock', 'Tab'):
            self.som_teclado.play()
            logging.debug(f"Som de teclado acionado por {event.keysym} em on_entry_uppercase.")

    def processar_palavra_secreta(self):
        palavra_digitada = self.palavra_secreta_var.get().strip()
        dificuldade_atual = self.dificuldade_selecionada.get()
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
        
        min_len = 3
        if self.modo_jogo_selecionado.get() == "solo":
            max_len_facil = 7
            max_len_medio = 10
        else:
            max_len_facil = 10

        if len(palavra_digitada) < min_len:
            messagebox.showwarning("ENTRADA INVÁLIDA", f"A PALAVRA DEVE TER NO MÍNIMO {min_len} LETRAS.")
            self.palavra_secreta_var.set("")
            self.entry_palavra_secreta.focus_set()
            logging.warning(f"Palavra digitada muito curta: '{palavra_digitada}'")
            return

        if dificuldade_atual == "Fácil" and len(palavra_digitada) > max_len_facil:
            messagebox.showwarning("PALAVRA MUITO LONGA", f"NA DIFICULDADE 'FÁCIL', A PALAVRA DEVE TER NO MÁXIMO {max_len_facil} LETRAS.")
            self.palavra_secreta_var.set("")
            self.entry_palavra_secreta.focus_set()
            logging.warning(f"Palavra '{palavra_digitada}' muito longa para dificuldade Fácil.")
            return
        
        if self.modo_jogo_selecionado.get() == "solo":
            if dificuldade_atual == "Médio" and len(palavra_digitada) > max_len_medio:
                messagebox.showwarning("PALAVRA MUITO LONGA", f"NA DIFICULDADE 'MÉDIO' (MODO SOLO), A PALAVRA DEVE TER NO MÁXIMO {max_len_medio} LETRAS.")
                self.palavra_secreta_var.set("")
                self.entry_palavra_secreta.focus_set()
                logging.warning(f"Palavra '{palavra_digitada}' muito longa para dificuldade Médio (Solo).")
                return
            elif dificuldade_atual == "Difícil" and len(palavra_digitada) < 8:
                messagebox.showwarning("PALAVRA MUITO CURTA", "NA DIFICULDADE 'DIFÍCIL' (MODO SOLO), A PALAVRA DEVE TER NO MÍNIMO 8 LETRAS.")
                self.palavra_secreta_var.set("")
                self.entry_palavra_secreta.focus_set()
                logging.warning(f"Palavra '{palavra_digitada}' muito curta para dificuldade Difícil (Solo).")
                return

        if self.dicionario_palavras and palavra_digitada.lower() not in self.dicionario_palavras:
            logging.info(f"Palavra '{palavra_digitada}' não encontrada no dicionário. Gerando sugestões.")
            sugestoes = self.sugerir_palavras(palavra_digitada.lower())
            self.mostrar_sugestoes(palavra_digitada.lower(), sugestoes)
            return

        if self.modo_jogo_selecionado.get() == 'multiplayer':
            # Armazena a palavra definida pelo jogador atual (definidor)
            self.jogadores[self.jogador_definidor_idx]['palavra_definida_por_mim'] = palavra_digitada.upper()

            jogador_que_vai_adivinhar_essa_palavra = (self.jogador_definidor_idx + 1) % len(self.jogadores)
            self.jogadores[jogador_que_vai_adivinhar_essa_palavra]['palavra_a_adivinhar'] = palavra_digitada.upper()
            self.jogadores[jogador_que_vai_adivinhar_essa_palavra]['dificuldade_rodada'] = dificuldade_atual
            self.jogador_atual_idx = (self.jogador_definidor_idx + 1) % len(self.jogadores)
            self.frame_jogador1.pack_forget()
            logging.info(f"Palavra '{palavra_digitada.upper()}' definida por {self.jogadores[self.jogador_definidor_idx]['nome']} para {self.jogadores[self.jogador_atual_idx]['nome']} (Multiplayer).")
        else:
            self.frame_jogador1.pack_forget()

        self.palavra_secreta = self.jogadores[self.jogador_atual_idx]['palavra_a_adivinhar']
        
        try:
            self.letras_embaralhadas = self.embaralhar_palavra(self.palavra_secreta)
        except Exception as e:
            logging.error(f"Erro ao embaralhar a palavra '{self.palavra_secreta}': {e}", exc_info=True)
            messagebox.showerror("ERRO FATAL", f"Não foi possível embaralhar a palavra. O jogo será reiniciado.\nErro: {e}")
            self.iniciar_selecao_modo()
            return

        logging.info(f"Palavra secreta definida para a rodada: '{self.palavra_secreta}'. Chamando iniciar_rodada_adivinhacao().")
        self.iniciar_rodada_adivinhacao()

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

    def iniciar_rodada_adivinhacao(self):
        logging.info(f"Iniciando rodada de adivinhação para o jogador: {self.jogadores[self.jogador_atual_idx]['nome']}")

        if self.timer_id:
            self.root.after_cancel(self.timer_id)

        self.partida_desistida = False

        self.palavra_secreta = self.jogadores[self.jogador_atual_idx]['palavra_a_adivinhar']
        if not self.palavra_secreta:
            logging.error(f"Jogador {self.jogadores[self.jogador_atual_idx]['nome']} não tem palavra para adivinhar. Retornando à configuração.")
            messagebox.showerror("ERRO DE SEQUÊNCIA", f"O JOGADOR {self.jogadores[self.jogador_atual_idx]['nome'].upper()} AINDA NÃO TEM UMA PALAVRA PARA ADIVINHAR. O JOGO TENTARÁ REDEFINIR.")
            self.iniciar_configuracao()
            return

        self.letras_embaralhadas = self.embaralhar_palavra(self.palavra_secreta)

        self.erros_rodada_atual = 0
        self.letras_ja_tentadas_exibicao.clear()
        self.letras_erradas_exibicao.clear()
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

        self.revelar_palavra_adivinhada_apenas()
        self.esconder_letras_embaralhadas_apenas()

        self.botao_iniciar_jogador2.pack_forget()
        self.botao_iniciar_jogador2.pack(pady=20)
        self.botao_iniciar_jogador2.config(state='normal')

        self.btn_desistir.pack(side=tk.BOTTOM, pady=10)
        self.btn_desistir.config(state='normal')

        self.label_instrucao_jogador2.config(text=f"VEZ DE: {self.jogadores[self.jogador_atual_idx]['nome'].upper()}. CLIQUE EM 'INICIAR RODADA' PARA COMEÇAR!", fg=COR_TEXTO_CLARO)
        self.label_letras_embaralhadas.config(text="LETRAS DISPONÍVEIS:", fg=COR_TEXTO_CLARO_DESTACADO)
        self.label_erros.config(text="")
        self.label_letras_tentadas.config(text="")
        self.label_letras_erradas.config(text="")
        self.label_tempo.config(text="TEMPO: 0.00S")

        logging.info("Interface da rodada de adivinhação preparada.")

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

        if self.som_teclado:
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
            self.iniciar_configuracao()
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
        
        # Exibe apenas as letras erradas da tentativa atual
        letras_exibicao_erradas = sorted(list(self.letras_erradas_exibicao))
        if letras_exibicao_erradas:
            self.label_letras_erradas.config(
                text="LETRAS ERRADAS NA POSIÇÃO ATUAL: " + ", ".join(letras_exibicao_erradas).upper(),
                fg=COR_VERMELHO_ERRO
            )
        else:
            self.label_letras_erradas.config(text="")

        if self.indice_atual < len(self.palavra_secreta):
            self.label_instrucao_jogador2.config(
                text=f"VEZ DE: {self.jogadores[self.jogador_atual_idx]['nome'].upper()} - ADIVINHE A LETRA DA POSIÇÃO {self.indice_atual + 1}:")
        else:
            self.label_instrucao_jogador2.config(
                text=f"VEZ DE: {self.jogadores[self.jogador_atual_idx]['nome'].upper()} - PALAVRA COMPLETA!"
            )

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
        self.letras_ja_tentadas_exibicao.add(letra_digitada)

        if letra_digitada == self.palavra_secreta[self.indice_atual]:
            current_entry.config(state='disabled', bg=COR_VERDE_ACERTO_CLARO, fg="white")
            logging.info(f"Acertou a letra '{letra_digitada}' na posição {self.indice_atual}.")
            is_last_letter_of_word = (self.indice_atual + 1) == len(self.palavra_secreta)
            
            # Limpar as letras erradas quando acertar uma letra
            self.letras_erradas_exibicao.clear()
            logging.info("Lista de letras erradas limpa após acerto.")
            
            if self.som_acerto and (not is_last_letter_of_word or self.modo_jogo_selecionado.get() == 'multiplayer'):
                self.som_acerto.play()
                logging.info(f"Som de acerto acionado para a letra '{letra_digitada}'.")
            elif is_last_letter_of_word and self.modo_jogo_selecionado.get() == 'solo':
                logging.info(f"Última letra '{letra_digitada}' acertada no modo solo. Som de acerto suprimido para priorizar som final.")
            self.indice_atual += 1
            self._atualizar_foco_entry()
        else:
            self.erros_rodada_atual += 1
            self.letras_erradas_exibicao.add(letra_digitada)
            self.tempo_penalidade_acumulada += PENALIDADE_ERRO
            logging.info(f"Errou a letra '{letra_digitada}' na posição {self.indice_atual}. Erros: {self.erros_rodada_atual}, Penalidade: {self.tempo_penalidade_acumulada}s.")
            if self.som_erro:
                self.som_erro.play()
                logging.info(f"Som de erro acionado para a letra '{letra_digitada}'.")
            original_bg = current_entry.cget("bg")
            current_entry.config(bg=COR_VERMELHO_ERRO, fg="white")
            self.root.after(200, lambda: current_entry.config(bg=original_bg, fg=COR_TEXTO_CLARO))
            self.entry_vars_adivinhacao[self.indice_atual].set("")
            current_entry.focus_set()
            logging.debug(f"Foco mantido na posição {self.indice_atual} após erro.")

        self.atualizar_interface_jogador2()

    def _atualizar_foco_entry(self):
        """Auxiliar para atualizar o foco após acerto de letra."""
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

    def carregar_ranking(self):
        if os.path.exists(self.ARQUIVO_RANKING):
            try:
                with open(self.ARQUIVO_RANKING, "r", encoding="utf-8") as f:
                    ranking_data = json.load(f)
                    for diff in ["Fácil", "Médio", "Difícil"]:
                        self.ranking_solo[diff] = ranking_data.get(diff, [])
                        self.ranking_solo[diff].sort(key=lambda x: (x.get('tempo', float('inf')), x.get('erros', 9999)))
                        self.ranking_solo[diff] = self.ranking_solo[diff][:10]
                logging.info("Ranking carregado com sucesso.")
            except json.JSONDecodeError:
                logging.error("Arquivo de ranking corrompido (JSONDecodeError). Criando um novo.", exc_info=True)
                messagebox.showwarning("ERRO DE RANKING", "ARQUIVO DE RANKING CORROMPIDO. CRIANDO UM NOVO.")
                self.ranking_solo = {"Fácil": [], "Médio": [], "Difícil": []}
            except Exception as e:
                logging.error(f"Ocorreu um erro ao carregar o ranking: {e}. Criando um novo.", exc_info=True)
                messagebox.showerror("ERRO AO CARREGAR RANKING", f"Ocorreu um erro ao carregar o ranking: {e}. Criando um novo.")
                self.ranking_solo = {"Fácil": [], "Médio": [], "Difícil": []}
        else:
            logging.info("Arquivo de ranking não encontrado. Inicializando ranking vazio.")
            self.ranking_solo = {"Fácil": [], "Médio": [], "Difícil": []}

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
        logging.info(f"Adicionando ao ranking: {nome}, Tempo: {tempo}, Erros: {erros}, Dificuldade: {dificuldade}, Palavra: {palavra}")
        if dificuldade not in self.ranking_solo:
            self.ranking_solo[dificuldade] = []
        
        self.ranking_solo[dificuldade].append({
            "nome": nome,
            "tempo": tempo,
            "erros": erros,
            "palavra": palavra
        })
        self.ranking_solo[dificuldade].sort(key=lambda x: (x['tempo'], x['erros']))
        self.ranking_solo[dificuldade] = self.ranking_solo[dificuldade][:10]
        logging.info(f"Ranking atualizado para {dificuldade}: {self.ranking_solo[dificuldade]}")

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

        if self.musica_menu and not pygame.mixer.get_busy():
            self.musica_menu.play(-1)
            logging.info("Música do menu iniciada.")

        self.label_selecao_modo.config(text="SELECIONE O MODO DE JOGO:")
        self.label_selecao_modo.pack(pady=20)

        self.radio_solo.pack(pady=10)
        self.radio_multiplayer.pack(pady=10)

        ttk.Button(self.frame_selecao_modo, text="COMO JOGAR?", command=self.mostrar_instrucoes, style="TButton").pack(pady=20)
        ttk.Button(self.frame_selecao_modo, text="SAIR DO JOGO", command=self.confirmar_saida, style="TButton").pack(pady=10)

        self.frame_selecao_modo.pack(expand=True, fill='both', pady=20)
        logging.info("frame_selecao_modo packed.")
        
        self._esconder_opcoes_nomes_multiplayer_e_botoes()
        logging.info("Tela de seleção de modo exibida.")

    def _esconder_opcoes_nomes_multiplayer_e_botoes(self):
        logging.info("Escondendo opções de nomes e botões de iniciar jogo.")
        if hasattr(self, 'label_num_jogadores_multiplayer') and self.label_num_jogadores_multiplayer.winfo_exists():
            self.label_num_jogadores_multiplayer.pack_forget()
        if hasattr(self, 'spinbox_num_jogadores') and self.spinbox_num_jogadores.winfo_exists():
            self.spinbox_num_jogadores.pack_forget()
        if hasattr(self, 'btn_definir_nomes_e_dificuldade') and self.btn_definir_nomes_e_dificuldade.winfo_exists():
            self.btn_definir_nomes_e_dificuldade.pack_forget()
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
            name_entry = tk.Entry(self.frame_entry_nomes, font=("Arial", 16), bd=2, relief="solid", bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO, textvariable=name_var)
            name_entry.pack(pady=5)
            self.entry_nomes_jogadores.append(name_entry)
            name_entry.bind("<KeyRelease>", lambda event: self.on_entry_uppercase(name_var, event))
            name_entry.bind("<Return>", lambda event: self.finalizar_cadastro_jogadores())

            self.frame_entry_nomes.pack(pady=10)
            self.btn_iniciar_jogo_principal.config(command=self.finalizar_cadastro_jogadores)
            self.btn_iniciar_jogo_principal.pack(pady=10)
            self.btn_iniciar_jogo_principal.config(state='normal')
            self.btn_voltar_nomes.pack(pady=5)
            name_entry.focus_set()

        else:
            logging.info("Preparando seleção de quantidade e nomes para o modo MULTIPLAYER.")
            self.frame_entry_nomes.pack_forget()
            self.btn_iniciar_jogo_principal.pack_forget()
            
            self.label_num_jogadores_multiplayer.pack(pady=5)
            self.spinbox_num_jogadores.pack(pady=5)
            self.btn_definir_nomes_e_dificuldade.pack(pady=10)
            self.btn_definir_nomes_e_dificuldade.config(state='normal')
            self.btn_voltar_nomes.pack(pady=5)

        self.frame_nomes_jogadores.pack(expand=True, fill='both', pady=20)
        self.root.after(100, lambda: self.spinbox_num_jogadores.focus_set() if self.modo_jogo_selecionado.get() == 'multiplayer' else self.entry_nomes_jogadores[0].focus_set())

    def _criar_entradas_nomes_dinamico(self):
        self.num_jogadores_total = self.num_jogadores_multiplayer.get()
        logging.info(f"Criando {self.num_jogadores_total} entradas de nome dinamicamente para multiplayer.")

        for widget in self.frame_entry_nomes.winfo_children():
            widget.destroy()
        self.entry_nomes_jogadores.clear()

        self.btn_definir_nomes_e_dificuldade.pack_forget()

        self.label_nomes_multiplayer.config(text="INSIRA OS NOMES DOS JOGADORES:")
        
        for i in range(self.num_jogadores_total):
            tk.Label(self.frame_entry_nomes, text=f"JOGADOR {i+1}:", font=("Arial", 14), bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO).pack(pady=5)
            name_var = tk.StringVar(self.root)
            name_entry = tk.Entry(self.frame_entry_nomes, font=("Arial", 16), bd=2, relief="solid", bg=COR_FUNDO_ESCURO_INPUT, fg=COR_TEXTO_CLARO, textvariable=name_var)
            name_entry.pack(pady=5)
            self.entry_nomes_jogadores.append(name_entry)
            
            name_entry.bind("<KeyRelease>", lambda event, var=name_var: self.on_entry_uppercase(var, event))
            name_entry.bind("<Return>", lambda event, idx=i: self.focar_proxima_entrada_nome(idx))

        self.frame_entry_nomes.pack(pady=10)

        self.btn_iniciar_jogo_principal.config(command=self.finalizar_cadastro_jogadores)
        self.btn_iniciar_jogo_principal.pack(pady=10)
        self.btn_voltar_nomes.pack(pady=5)
        
        if self.entry_nomes_jogadores:
            self.root.after(200, self.entry_nomes_jogadores[0].focus_set)
        self.verificar_nomes_preenchidos()

    def focar_proxima_entrada_nome(self, current_idx):
        logging.debug(f"Foco na entrada de nome: {current_idx}.")
        if not self.entry_nomes_jogadores[current_idx].get().strip():
            messagebox.showwarning("NOME INVÁLIDO", "POR FAVOR, INSIRA UM NOME ANTES DE CONTINUAR.")
            self.entry_nomes_jogadores[current_idx].focus_set()
            return

        self.root.update_idletasks()
        self.verificar_nomes_preenchidos()

        if current_idx + 1 < len(self.entry_nomes_jogadores):
            self.entry_nomes_jogadores[current_idx + 1].focus_set()
            logging.debug(f"Foco movido para a entrada {current_idx+2}.")
        else:
            logging.info("Última entrada de nome preenchida.")
            pass

    def verificar_nomes_preenchidos(self):
        todos_preenchidos = True
        for entry in self.entry_nomes_jogadores:
            if not entry.get().strip():
                todos_preenchidos = False
                break
        
        if todos_preenchidos:
            self.btn_iniciar_jogo_principal.config(state='normal')
        else:
            self.btn_iniciar_jogo_principal.config(state='disabled')

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
        logging.info(f"Jogadores cadastrados: {[j['nome'] for j in self.jogadores]}. Prosseguindo para configuração de dificuldade.")
        self.iniciar_configuracao()

    def on_dificuldade_selecionada(self):
        dificuldade_atual = self.dificuldade_selecionada.get()
        modo = self.modo_jogo_selecionado.get()
        logging.info(f"Dificuldade selecionada: {dificuldade_atual}, Modo: {modo}")

        for widget in self.frame_dificuldade.winfo_children():
            if isinstance(widget, ttk.Radiobutton):
                widget.config(style="TRadiobutton")
        
        if dificuldade_atual == "Fácil":
            self.radio_facil.config(style="TButton")
            if modo == "solo":
                self.label_dificuldade_explicacao.config(text="Palavras mais curtas (3-7 letras). Ideal para iniciantes.", fg=COR_VERDE_ACERTO_CLARO)
            else:
                self.label_dificuldade_explicacao.config(text="Palavras de 3 a 10 letras. Fácil no multiplayer.", fg=COR_VERDE_ACERTO_CLARO)
        elif dificuldade_atual == "Médio":
            self.radio_medio.config(style="TButton")
            if modo == "solo":
                self.label_dificuldade_explicacao.config(text="Palavras de tamanho moderado (3-10 letras). Equilíbrio entre desafio e diversão.", fg=COR_AMARELO_AVISO)
            else:
                self.label_dificuldade_explicacao.config(text="Palavras de 3 ou mais letras. Equilíbrio entre desafio e diversão no multiplayer.", fg=COR_AMARELO_AVISO)
        elif dificuldade_atual == "Difícil":
            self.radio_dificil.config(style="TButton")
            if modo == "solo":
                self.label_dificuldade_explicacao.config(text="Palavras com 8+ letras e letras extras para embaralhar. Para os mestres das palavras!", fg=COR_VERMELHO_ERRO)
            else:
                self.label_dificuldade_explicacao.config(text="Palavras de 3 ou mais letras e letras extras para embaralhar. Para os mestres das palavras no multiplayer!", fg=COR_VERMELHO_ERRO)
        
        self.label_dificuldade_explicacao.pack(pady=10)

    def iniciar_configuracao(self):
        self.rodadas_completas = 0
        self.jogador_definidor_idx = 0
        self.jogador_atual_idx = 0
        self.parar_timer()

        logging.info("Iniciando tela de configuração (dificuldade).")
        self.limpar_tela()
        self._criar_frames_iniciais()

        if self.musica_menu and not pygame.mixer.get_busy():
            self.musica_menu.play(-1)

        self.label_configuracao.config(text="SELECIONE A DIFICULDADE:")
        self.label_configuracao.pack(pady=20)

        self.frame_dificuldade.pack(pady=10, padx=20, ipadx=10, ipady=10)
        self.radio_facil.pack(pady=5, anchor='w')
        self.radio_medio.pack(pady=5, anchor='w')
        self.radio_dificil.pack(pady=5, anchor='w')

        self.label_dificuldade_explicacao.pack(pady=10)

        ttk.Button(self.frame_configuracao, text="INICIAR FASE DE PALAVRA", command=self.iniciar_fase_definicao_palavra, style="TButton").pack(pady=20)
        ttk.Button(self.frame_configuracao, text="VOLTAR", command=lambda: self.iniciar_selecao_modo(), style="TButton").pack(pady=5)

        self.frame_configuracao.pack(expand=True, fill='both', pady=20)
        
        self.label_dificuldade_explicacao.config(text="")
        
        if not self.dificuldade_selecionada.get():
            self.dificuldade_selecionada.set("Médio")
            logging.info("Dificuldade padrão 'Médio' definida.")
        self.on_dificuldade_selecionada()
        logging.info("Tela de configuração exibida.")

    def mostrar_placar_final_solo(self):
        logging.info("Exibindo placar final (Solo).")
        self.limpar_tela()
        self._criar_frames_iniciais()
        
        for widget in self.frame_placar_solo.winfo_children():
            widget.destroy()

        self.frame_placar_solo.pack(expand=True, fill='both', pady=20)

        tk.Label(self.frame_placar_solo, text="RESULTADO DA PARTIDA SOLO", font=("Arial", 24, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=20)
        
        jogador = self.jogadores[0]
        tempo_str = f"{jogador['tempo_rodada']:.2f} segundos" if isinstance(jogador['tempo_rodada'], float) else str(jogador['tempo_rodada'])
        erros_str = str(jogador['erros_rodada']) if isinstance(jogador['erros_rodada'], int) else str(jogador['erros_rodada'])

        tk.Label(self.frame_placar_solo, text=f"JOGADOR: {jogador['nome'].upper()}", font=("Arial", 18), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)
        tk.Label(self.frame_placar_solo, text=f"PALAVRA: {jogador['palavra_a_adivinhar'].upper()}", font=("Arial", 18), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)
        tk.Label(self.frame_placar_solo, text=f"DIFICULDADE: {jogador['dificuldade_rodada'].upper()}", font=("Arial", 18), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)
        tk.Label(self.frame_placar_solo, text=f"TEMPO FINAL: {tempo_str}", font=("Arial", 18), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)
        tk.Label(self.frame_placar_solo, text=f"ERROS: {erros_str}", font=("Arial", 18), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)

        tk.Label(self.frame_placar_solo, text="\nRANKING TOP 5 (SOLO)", font=("Arial", 20, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=20)

        for dificuldade_nome in ["Fácil", "Médio", "Difícil"]:
            tk.Label(self.frame_placar_solo, text=f"--- {dificuldade_nome.upper()} ---", font=("Arial", 16, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)
            
            top_5 = self.ranking_solo.get(dificuldade_nome, [])[:5] 
            
            if top_5:
                ranking_texto = ""
                for i, entrada in enumerate(top_5):
                    tempo_rank = f"{entrada['tempo']:.2f}s" if isinstance(entrada['tempo'], float) else str(entrada['tempo'])
                    erros_rank = str(entrada['erros']) if isinstance(entrada['erros'], int) else str(entrada['erros'])
                    palavra_rank = entrada.get('palavra', 'N/A').upper()
                    ranking_texto += f"{i+1}. {entrada['nome']} - Palavra: {palavra_rank} - Tempo: {tempo_rank} - Erros: {erros_rank}\n"
                
                tk.Label(self.frame_placar_solo, text=ranking_texto, font=("Arial", 14), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)
            else:
                tk.Label(self.frame_placar_solo, text="NENHUM REGISTRO AINDA.", font=("Arial", 12), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=5)

        ttk.Button(self.frame_placar_solo, text="JOGAR NOVAMENTE", command=self.iniciar_selecao_modo, style="TButton").pack(side=tk.LEFT, padx=10, pady=20)
        ttk.Button(self.frame_placar_solo, text="SAIR DO JOGO", command=self.confirmar_saida, style="TButton").pack(side=tk.RIGHT, padx=10, pady=20)
        
        if jogador['status_rodada'] == "INCOMPLETA" and self.som_fim_jogo:
            self.som_fim_jogo.play()
            logging.info("Som de fim de jogo acionado (derrota solo).")

        logging.info("Placar final solo exibido com Top 5 rankings.")

    def mostrar_placar_final_multiplayer(self):
        logging.info("Exibindo placar final (Multiplayer).")
        self.limpar_tela()
        self._criar_frames_iniciais()
        self.frame_placar_multiplayer.pack(expand=True, fill='both', pady=20)

        if self.som_fim_jogo:
            self.som_fim_jogo.play()
            logging.info("Som de fim de jogo acionado para o placar final multiplayer.")

        tk.Label(self.frame_placar_multiplayer, text="RESULTADO FINAL DA PARTIDA MULTIPLAYER", font=("Arial", 24, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO).pack(pady=20)
        
        colunas = ('Jogador', 'Palavra Definida', 'Dificuldade', 'Tempo Adivinhando', 'Erros Adivinhando', 'Status')
        tree = ttk.Treeview(self.frame_placar_multiplayer, columns=colunas, show='headings', style="Treeview")
        
        for col in colunas:
            tree.heading(col, text=col, anchor='center')
            if col == 'Jogador':
                tree.column(col, anchor='center', width=120)
            elif col == 'Palavra Definida':
                tree.column(col, anchor='center', width=150)
            elif col == 'Dificuldade':
                tree.column(col, anchor='center', width=100)
            elif col == 'Tempo Adivinhando':
                tree.column(col, anchor='center', width=150)
            elif col == 'Erros Adivinhando':
                tree.column(col, anchor='center', width=120)
            elif col == 'Status':
                tree.column(col, anchor='center', width=100)
            else:
                tree.column(col, anchor='center', width=100)
        
        self.style.configure("Treeview", background=COR_FUNDO_SECUNDARIO, foreground=COR_TEXTO_CLARO, fieldbackground=COR_FUNDO_SECUNDARIO)
        self.style.map("Treeview", background=[('selected', COR_AZUL_SUAVE_BOTOES)])
        self.style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background=COR_AZUL_SUAVE_BOTOES, foreground="white")

        for jogador in self.jogadores:
            jogador['tempo_total_partida'] = 0.0
            jogador['erros_total_partida'] = 0
            if jogador['status_rodada'] == "ADIVINHOU" and jogador['tempo_rodada'] != float('inf'):
                jogador['tempo_total_partida'] += jogador['tempo_rodada']
                jogador['erros_total_partida'] += jogador['erros_rodada']
            elif jogador['status_rodada'] == "INCOMPLETA":
                jogador['tempo_total_partida'] = float('inf')
                jogador['erros_total_partida'] = 9999

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
            
            # Garante que 'palavra_definida_por_mim' é exibida corretamente
            palavra_definida_exibicao = jogador.get('palavra_definida_por_mim', 'N/A')

            tree.insert('', tk.END, values=(
                jogador['nome'].upper(),
                palavra_definida_exibicao.upper() if palavra_definida_exibicao != 'N/A' else 'N/A',
                jogador['dificuldade_rodada'].upper() if jogador['dificuldade_rodada'] else "N/A",
                tempo_str,
                erros_str,
                jogador['status_rodada'].upper()
            ))
        
        tree.pack(pady=20, padx=20, fill='both', expand=True)

        campeao = None
        if jogadores_ordenados:
            campeao = jogadores_ordenados[0]
            tempo_campeao_str = f"{campeao['tempo_total_partida']:.2f}s" if isinstance(campeao['tempo_total_partida'], float) else str(campeao['tempo_total_partida'])
            erros_campeao_str = str(campeao['erros_total_partida']) if isinstance(campeao['erros_total_partida'], int) else str(campeao['erros_total_partida'])
            
            tk.Label(self.frame_placar_multiplayer, text=f"\nCAMPEÃO: {campeao['nome'].upper()}!", font=("Arial", 22, "bold"), fg=COR_VERDE_ACERTO, bg=COR_FUNDO_PRINCIPAL).pack(pady=10)
            tk.Label(self.frame_placar_multiplayer, text=f"TEMPO TOTAL: {tempo_campeao_str} - ERROS: {erros_campeao_str}", font=("Arial", 18), fg=COR_VERDE_ACERTO_CLARO, bg=COR_FUNDO_PRINCIPAL).pack(pady=5)
        else:
            tk.Label(self.frame_placar_multiplayer, text="\nNÃO FOUI POSSÍVEL DETERMINAR UM CAMPEÃO.", font=("Arial", 18, "bold"), fg=COR_AMARELO_AVISO, bg=COR_FUNDO_PRINCIPAL).pack(pady=10)
            tk.Label(self.frame_placar_multiplayer, text="Nenhum jogador conseguiu adivinhar a palavra.", font=("Arial", 14), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL).pack(pady=5)

        # Novo frame para os botões na parte inferior
        button_frame = tk.Frame(self.frame_placar_multiplayer, bg=COR_FUNDO_PRINCIPAL)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        ttk.Button(button_frame, text="JOGAR NOVAMENTE", command=self.iniciar_selecao_modo, style="TButton").pack(side=tk.LEFT, padx=10, expand=True)
        ttk.Button(button_frame, text="SAIR DO JOGO", command=self.confirmar_saida, style="TButton").pack(side=tk.RIGHT, padx=10, expand=True)
        logging.info("Placar final multiplayer exibido.")

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
        - FÁCIL (Solo): Palavras de 3 a 7 letras.
        - FÁCIL (Multiplayer): Palavras de 3 a 10 letras.
        - MÉDIO (Solo): Palavras de 3 a 10 letras (padrão).
        - MÉDIO (Multiplayer): Palavras de 3 ou mais letras.
        - DIFÍCIL (Solo): Palavras com 8+ letras e letras extras para embaralhar. Para os mestres das palavras!
        - DIFÍCIL (Multiplayer): Palavras de 3 ou mais letras e letras extras aleatórias são adicionadas para embaralhar!
        
        DICAS:
        - Use as letras embaralhadas para te ajudar!
        - Errar aumenta seu tempo, então pense bem antes de digitar.
        - Divirta-se e desafie seus rivais!
        """

        tk.Label(self.frame_instrucoes, text=instrucoes_texto, font=("Arial", 12), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_SECUNDARIO, justify=tk.LEFT, wraplength=self.root.winfo_width() - 100).pack(pady=10, padx=50, fill=tk.BOTH, expand=True)

        ttk.Button(self.frame_instrucoes, text="VOLTAR AO INÍCIO", command=self.iniciar_selecao_modo, style="TButton").pack(pady=20)

    def confirmar_saida(self):
        logging.info("Usuário tentou fechar a janela. Confirmando saída.")
        if messagebox.askyesno("SAIR DO JOGO", "TEM CERTEZA QUE DESEJA SAIR?"):
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

        self.radio_solo = ttk.Radiobutton(self.frame_selecao_modo, text="JOGADOR ÚNICO (SOLO)", variable=self.modo_jogo_selecionado, value="solo",
                                     command=self.mostrar_opcoes_multiplayer_e_nomes_e_dificuldade, style="TRadiobutton")
        self.radio_multiplayer = ttk.Radiobutton(self.frame_selecao_modo, text="MULTI JOGADOR (RIVAIS)", variable=self.modo_jogo_selecionado, value="multiplayer",
                                           command=self.mostrar_opcoes_multiplayer_e_nomes_e_dificuldade, style="TRadiobutton")

        # Frame de Nomes dos Jogadores (Dinâmico para Solo/Multi)
        self.frame_nomes_jogadores = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)
        self.label_nomes_multiplayer = tk.Label(self.frame_nomes_jogadores, text="SELECIONE A QUANTIDADE DE JOGADORES:", font=("Arial", 20, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)

        self.label_num_jogadores_multiplayer = tk.Label(self.frame_nomes_jogadores, text="QUANTOS JOGADORES?", font=("Arial", 14), bg=COR_FUNDO_SECUNDARIO, fg=COR_TEXTO_CLARO)
        self.spinbox_num_jogadores = ttk.Spinbox(self.frame_nomes_jogadores, from_=2, to=5, textvariable=self.num_jogadores_multiplayer, width=5, font=("Arial", 14), state='readonly')

        self.btn_definir_nomes_e_dificuldade = ttk.Button(self.frame_nomes_jogadores, text="DEFINIR NOMES", command=self._criar_entradas_nomes_dinamico, style="TButton")

        self.frame_entry_nomes = tk.Frame(self.frame_nomes_jogadores, bg=COR_FUNDO_PRINCIPAL)

        self.btn_iniciar_jogo_principal = ttk.Button(self.frame_nomes_jogadores, text="INICIAR JOGO", command=self.finalizar_cadastro_jogadores, style="TButton", state='disabled')
        self.btn_voltar_nomes = ttk.Button(self.frame_nomes_jogadores, text="VOLTAR", command=self.iniciar_selecao_modo, style="TButton")

        # Frame de Configuração de Dificuldade
        self.frame_configuracao = tk.Frame(self.root, bg=COR_FUNDO_PRINCIPAL)
        self.label_configuracao = tk.Label(self.frame_configuracao, text="SELECIONE A DIFICULDADE:", font=("Arial", 20, "bold"), fg=COR_TEXTO_CLARO, bg=COR_FUNDO_PRINCIPAL)

        self.frame_dificuldade = tk.Frame(self.frame_configuracao, bg=COR_FUNDO_SECUNDARIO, bd=2, relief="groove")

        self.radio_facil = ttk.Radiobutton(self.frame_dificuldade, text="FÁCIL", variable=self.dificuldade_selecionada, value="Fácil",
                                      command=self.on_dificuldade_selecionada, style="TRadiobutton")
        self.radio_medio = ttk.Radiobutton(self.frame_dificuldade, text="MÉDIO", variable=self.dificuldade_selecionada, value="Médio",
                                      command=self.on_dificuldade_selecionada, style="TRadiobutton")
        self.radio_dificil = ttk.Radiobutton(self.frame_dificuldade, text="DIFÍCIL", variable=self.dificuldade_selecionada, value="Difícil",
                                        command=self.on_dificuldade_selecionada, style="TRadiobutton")

        self.label_dificuldade_explicacao = tk.Label(self.frame_configuracao, text="", font=("Arial", 12, "italic"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_CLARO, wraplength=400)

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
