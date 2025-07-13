# 🎮 Jogo de Adivinhação de Palavras - Desafio de Rivais

Bem-vindo(a) ao **Jogo de Adivinhação de Palavras - Desafio de Rivais**!  
Este é um jogo divertido e desafiador onde você testa seu vocabulário e raciocínio. Jogue sozinho para melhorar suas habilidades ou desafie amigos no modo multiplayer!

---

## 🖥️ Requisitos do Sistema

Para executar o jogo, é necessário ter:

### ✔️ Python 3.x
- Baixe em: https://www.python.org/

### 📦 Bibliotecas Utilizadas
A maioria já vem com o Python:

- `tkinter` (GUI)
- `tkinter.messagebox` (Diálogos)
- `tkinter.ttk` (Widgets temáticos)
- `random` (Sorteio de palavras e letras)
- `os` (Acesso ao sistema de arquivos)
- `time` (Cronometragem)
- `platform` (Detectar SO e ajustar a tela)
- `string` (Manipulação de texto)
- `json` (Salvar/carregar ranking)
- `sys` (Tratamento de exceções)

#### Extra:
- `requests` (para baixar dicionário online)

Se `requests` não estiver instalado, use:
```bash
pip install requests
```
### 🌐 Conexão com a Internet (Opcional)
- O jogo tentará baixar o arquivo palavras.txt se não estiver presente localmente.

- Sem o arquivo, o jogo funciona, mas sem validação das palavras.

### 🚀 Como Executar

1. Baixe o arquivo jogo.py.
2. Abra o terminal e vá até a pasta onde o salvou.
3. Execute o comando:

```bash
python jogo.py
```
A janela do jogo será aberta!

### 🎲 Como Jogar
Objetivo
Adivinhar a palavra secreta, letra por letra, com as letras embaralhadas fornecidas.

### Modos de Jogo
1. Jogador Único (Solo)
O sistema escolhe a palavra com base na dificuldade.

Seu desempenho (tempo e erros) é registrado em um ranking local.

2. Multi Jogador (Rivais)
Jogadores se revezam: um define a palavra e o outro tenta adivinhar.

Ganha quem acumular o menor tempo total (com menos erros em caso de empate).

### ⚙️ Níveis de Dificuldade
- Fácil

>Palavras curtas (3 a 7 letras no Solo, até 10 no Multiplayer).

- Médio

>Palavras médias (3 a 10 letras ou mais).

- Difícil

>Palavras com 8+ letras + letras extras embaralhadas para aumentar a dificuldade.

### 📌 Regras e Dicas
Você deve adivinhar a palavra letra por letra.

Pode usar o teclado físico ou clicar nas letras na tela.

Cada erro adiciona 3 segundos ao tempo total.

O tempo é essencial para o ranking e para vencer partidas multiplayer.

Se desistir no modo Solo, seu desempenho não será salvo no ranking.

### 🏁 Boa Sorte!
Divirta-se desafiando seus limites ou seus amigos neste incrível jogo de adivinhação! 🧠✨