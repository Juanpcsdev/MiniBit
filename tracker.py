import socket
import threading
import random
import json
from utils import gerar_log

# Conjunto de peers ativos: (ip, porta)
PEERS = set()

# Mapeia cada peer para os blocos que ele possui
PEER_BLOCKS = {}

# Lock para sincronizar o acesso concorrente
LOCK = threading.Lock()

def handle_client(conn, addr):
    """
    Gerencia as requisições recebidas dos peers.

    Tipos de requisição:
    - REGISTER: registra um novo peer e seus blocos iniciais
    - GET_PEERS: retorna peers conhecidos e blocos sugeridos para download
    - UPDATE_BLOCKS: atualiza blocos que um peer possui
    """
    global PEERS, PEER_BLOCKS
    try:
        data = conn.recv(4096).decode()
        if data.startswith('REGISTER'):
            parts = data.split()
            if len(parts) < 3:
                conn.send(b'ERROR Invalid REGISTER format')
                return
            peer_port = int(parts[1])
            blocks_str = parts[2]
            blocks = set(blocks_str.split(',')) if blocks_str else set()
            peer_addr = (addr[0], peer_port)  # IP fixo do peer + porta que ele escuta
            with LOCK:
                if peer_addr not in PEERS:
                    PEERS.add(peer_addr)
                    gerar_log(f"[TRACKER] Novo peer registrado: {peer_addr}")
                PEER_BLOCKS[peer_addr] = blocks
            gerar_log(f"[TRACKER] Atualizou blocos do peer {peer_addr}: {blocks}")
            conn.send(b'OK')

        elif data == 'GET_PEERS':
            with LOCK:
                available_peers = [p for p in PEERS if p != addr]

                # Limita o número de peers retornados (máximo 5)
                peers_response = available_peers if len(available_peers) <= 5 else random.sample(available_peers, 5)

                # Determina os blocos mais raros entre os peers
                all_blocks = []
                for blocks in PEER_BLOCKS.values():
                    all_blocks.extend(blocks)
                freq = {}
                for b in all_blocks:
                    freq[b] = freq.get(b, 0) + 1
                rarest_blocks = sorted(freq.items(), key=lambda x: x[1])
                suggested_blocks = [b for b, _ in rarest_blocks[:5] if b and b.startswith('block_')]

                response = json.dumps({
                    'peers': peers_response,
                    'suggested_blocks': suggested_blocks
                })
            conn.send(response.encode())
            gerar_log(f"[TRACKER] Enviou peers e blocos sugeridos para {addr}")

        elif data.startswith('UPDATE_BLOCKS'):
            blocks_str = data[len('UPDATE_BLOCKS '):]
            blocks = set(blocks_str.split(',')) if blocks_str else set()
            with LOCK:
                # Atualiza blocos de todos os peers com mesmo IP
                peers_to_update = [p for p in PEERS if p[0] == addr[0]]
                for p in peers_to_update:
                    PEER_BLOCKS[p] = blocks
                    gerar_log(f"[TRACKER] Atualizou blocos do peer {p}: {blocks}")
            conn.send(b'OK')

        else:
            conn.send(b'UNKNOWN_COMMAND')

    except Exception as e:
        gerar_log(f"[TRACKER] Erro ao tratar peer {addr}: {e}")
    finally:
        conn.close()

def start_tracker(host='localhost', port=5000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()
    gerar_log(f"[TRACKER] Running on {host}:{port}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == '__main__':
    start_tracker()