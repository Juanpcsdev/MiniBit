# MiniBit – Sistema de Compartilhamento Distribuído (Trabalho de Sistemas Distribuídos)

Este projeto implementa um sistema semelhante ao BitTorrent utilizando Python e sockets TCP, com foco em estratégias como **rarest first** e **tit-for-tat** para otimização de downloads distribuídos.

## Estrutura do Projeto

```
MiniBit/
├── tracker.py              # Tracker central que registra e informa sobre peers e blocos
├── peer.py                 # Cliente peer que compartilha e baixa blocos
├── dist_block.py           # Script que distribui blocos iniciais entre peers
├── utils.py                # Funções utilitárias para divisão, reconstrução de arquivos e logs
├── run_full.py             # Script que executa todo o ambiente automaticamente
├── arquivos/               # Pasta com arquivos originais a serem compartilhados
├── blocos_peer_*/          # Pastas contendo blocos distribuídos
├── reconstruido_peer_X.txt # Arquivos reconstruídos por cada peer
└── README.md               # Este documento
```

## Arquitetura

O MiniBit consiste em:

- **Tracker Central**: Servidor responsável por manter o registro de todos os peers ativos e seus blocos.
- **Peers**: Clientes que trocam blocos diretamente entre si para completar o download.

## Descrição do Protocolo

### Mensagens Trocadas

- **REGISTER**: Peer registra no Tracker informando IP, porta e blocos.
- **GET_PEERS**: Peer solicita ao Tracker uma lista de peers e blocos sugeridos para download.
- **UPDATE_BLOCKS**: Peer informa ao Tracker os blocos atualizados que possui.
- **GET_BLOCKS**: Solicita a um peer os blocos disponíveis.
- **HAVE**: Pergunta a um peer específico se ele tem determinado bloco.
- **REQUEST**: Solicita efetivamente o envio de um bloco específico.

### Estados dos Peers

- **Unchoked**: Pode solicitar blocos aos peers.
- **Choked**: Não pode solicitar blocos até ser desbloqueado novamente.

## Estratégias Utilizadas

### Rarest First
- O Tracker mantém um registro da frequência de cada bloco entre os peers.
- Cada peer prioriza baixar os blocos mais raros na rede para aumentar a eficiência e disponibilidade.

### Tit-for-Tat
- Peers implementam um sistema de reciprocidade para decidir quais peers serão desbloqueados (unchoked).
- Priorizam peers que contribuem com blocos úteis (fixos) e escolhem aleatoriamente um peer otimista para descoberta contínua de novos peers produtivos.

## Como executar

### 1. Executar automaticamente todo o ambiente (Tracker e Peers)

Abra um terminal e execute:

```bash
python run_full.py
```

### 2. Executar manualmente

**Passo 1:** Iniciar Peer 0 (seed)

```bash
python peer.py 0
```

**Passo 2:** Distribuir blocos para outros peers

```bash
python dist_block.py
```

**Passo 3:** Iniciar Tracker

```bash
python tracker.py
```

**Passo 4:** Iniciar demais Peers (em terminais separados)

```bash
python peer.py 1
python peer.py 2
# e assim sucessivamente...
```

## ⚙️ Ajustando o Número de Peers

### ✅ Execução Automática (`run_full.py`)
Para alterar a quantidade de peers na execução automatizada:

1. **No arquivo `run_full.py`**
   - Vá até a linha:
     ```python
     NUM_PEERS = 5  # total de peers (incluindo peer 0)
     ```
   - Altere para o número desejado (máximo testado: 10).

2. **No arquivo `dist_block.py`**
   - Vá até a linha:
     ```python
     n_peers = 5
     ```
   - Atualize `n_peers=5` com o mesmo valor definido no `run_full.py`.

### 🛠 Execução Manual
Caso prefira executar manualmente:

- Altere **somente o valor `n_peers` no `dist_block.py`**, já que os peers são executados individualmente via terminal:

  ```bash
  python peer.py 0
  python dist_block.py
  python tracker.py
  python peer.py 1
  python peer.py 2
  ...

## Resultados de Testes

Foram realizados testes com diferentes quantidades de peers, sendo o **peer 0** responsável pela divisão e disseminação inicial dos blocos (seed). A distribuição dos blocos é **aleatória**, o que gera **variação natural no tempo total de execução**.

### ⏱️ Tempos de Execução (com finalização via CTRL+C)

#### 🔹 4 Peers (Peer 0 + 3)
```bash
02:12
02:11
02:15
03:00
```


#### 🔹 5 Peers (Peer 0 + 4)
```bash
01:54
02:48
02:49
03:38
05:17
```

#### 🔹 10 Peers (Peer 0 + 9)
```bash
04:15
04:35
06:46
```

### 📊 Médias Aproximadas
- **Média com 4 peers**: ~2 min 24 s
- **Média com 5 peers**: ~3 min 17 s
- **Média com 10 peers**: ~5 min 12 s

### 🧪 Conclusões
- A **estratégia rarest first** acelera a disseminação de blocos menos comuns.
- A **estratégia tit-for-tat com unchoke otimista** mantém o compartilhamento equilibrado e evita gargalos.
- O script `run_full.py` garante um ambiente de teste reproduzível e automatizado.
- A **aleatoriedade na distribuição de blocos** afeta diretamente o tempo de finalização dos peers.



## Dificuldades Enfrentadas

1. **Persistência e leitura do `block_count.txt`**
   - Inicialmente, o arquivo era incluído na contagem de blocos, o que causava inconsistência na divisão e reconstrução dos arquivos.
   - A lógica foi ajustada para ignorar esse arquivo durante o cálculo do total de blocos.

2. **Encerramento correto do peer 0**
   - Por padrão, o peer 0 encerrava ao completar seus blocos. No entanto, ele deveria permanecer ativo para servir os blocos a outros peers.
   - Foi implementada uma lógica de timeout com tentativas de verificação se os outros peers finalizaram.

3. **Peers rodando infinitamente quando algum finalizava**
   - Corrigido com controle central de estado e timeout, além de verificação dos peers completos.

4. **Mensagens de peers choked incoerentes**
   - O peer tentava baixar blocos antes da unchoke_loop atualizar os estados.
   - Resolvido adicionando `time.sleep` antes do loop principal, garantindo que os estados fossem inicializados corretamente.

5. **Dificuldade de teste manual com múltiplos peers**
   - Automatizado com `run_full.py`, que executa tudo em ordem correta: peer0 → distribuição → tracker → peers.

6. **Entendimento da estratégia tit-for-tat e rarest first**
   - Inicialmente confuso, foi necessária leitura adicional e revisão para implementar corretamente as prioridades e otimizações de troca.

7. **Manutenção e sincronização do estado da rede (peer_blocks_map)**
   - Várias exceções e inconsistências surgiram, resolvidas com uso de locks (RLock) e verificações de integridade.

## Script `run_full.py`

Automatiza toda a execução do sistema, iniciando sequencialmente:

- Peer inicial (seed) para divisão dos blocos
- Distribuição dos blocos entre demais peers
- Tracker central
- Demais peers para iniciar o compartilhamento

Permite iniciar e encerrar rapidamente todo o ambiente com uma única ação.

## Notas Importantes ⚠️

- **Segurança**: Este sistema não possui segurança avançada e é destinado exclusivamente para fins acadêmicos.
- **Extensibilidade**: Fácil adição de novos peers e adaptação de estratégias.
- **Tratamento de Erros**: Tratamento básico incluído para lidar com indisponibilidades temporárias.

## Licença

Este projeto foi desenvolvido como parte do trabalho acadêmico para a disciplina de **Sistemas Distribuídos**.