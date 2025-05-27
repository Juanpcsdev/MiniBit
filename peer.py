import socket
import threading
import random
import time
import ast
import os
from utils import dividir_arquivo_em_blocos, reconstruir_arquivo, gerar_log

TRACKER_HOST = 'localhost'
TRACKER_PORT = 5000
PEER_PORT_BASE = 6000
BLOCKS_TOTAL = 20
BLOCKS = [f'block_{i}' for i in range(BLOCKS_TOTAL)]

class Peer:
    def __init__(self, peer_id, arquivo_original='arquivo.txt'):
        self.peer_id = peer_id
        self.bloco_dir = f'blocos_peer_{peer_id}'
        self.arquivo_original = arquivo_original
        self.blocks = set()
        self.known_peers = set()
        self.peer_blocks_map = {}
        self.unchoked_peers = set()
        self.choked_peers = set()
        self.lock = threading.Lock()
        self.port = PEER_PORT_BASE + peer_id

    def load_blocks(self, max_retries=10, retry_delay=3):
        attempts = 0
        while attempts < max_retries:
            if not os.path.exists(self.bloco_dir):
                os.makedirs(self.bloco_dir)
            blocos = [f for f in os.listdir(self.bloco_dir) if f.startswith('block_')]
            if blocos:
                self.blocks = set(blocos)
                gerar_log(f"[Peer {self.peer_id}] Carregou {len(self.blocks)} blocos locais.")
                return True
            else:
                gerar_log(f"[Peer {self.peer_id}] Nenhum bloco local encontrado. Tentando novamente ({attempts+1}/{max_retries})...")
                attempts += 1
                time.sleep(retry_delay)
        gerar_log(f"[Peer {self.peer_id}] Não encontrou blocos locais após {max_retries} tentativas.")
        return False


    def save_block(self, block_name, data):
        caminho = os.path.join(self.bloco_dir, block_name)
        with open(caminho, 'wb') as f:
            f.write(data)
        self.blocks.add(block_name)
        gerar_log(f"[Peer {self.peer_id}] Salvou bloco {block_name}")

    def reconstruct_file(self):
        if len(self.blocks) == BLOCKS_TOTAL:
            reconstruir_arquivo(self.bloco_dir, f'reconstruido_peer_{self.peer_id}.txt')
            gerar_log(f"[Peer {self.peer_id}] Arquivo reconstruído com sucesso.")

    def register_to_tracker(self, max_retries=10, retry_delay=3):
        retries = 0
        while retries < max_retries:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((TRACKER_HOST, TRACKER_PORT))
                    s.sendall(b'GET_PEERS')
                    data = s.recv(4096).decode()
                    peers = ast.literal_eval(data)
                    self.known_peers = set([p for p in peers if p[1] != self.port])
                gerar_log(f"[Peer {self.peer_id}] Peers conhecidos: {self.known_peers}")
                return True
            except Exception as e:
                gerar_log(f"[Peer {self.peer_id}] Falha ao conectar tracker: {e}. Tentando novamente ({retries+1}/{max_retries})")
                retries += 1
                time.sleep(retry_delay)
        gerar_log(f"[Peer {self.peer_id}] Não conseguiu conectar ao tracker após {max_retries} tentativas.")
        return False

    def update_peer_blocks(self):
        for peer in list(self.known_peers):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect(peer)
                    s.sendall(b'GET_BLOCKS')
                    data = s.recv(4096).decode()
                    blocks = set(data.split(',')) if data else set()
                    with self.lock:
                        self.peer_blocks_map[peer] = blocks
            except Exception as e:
                gerar_log(f"[Peer {self.peer_id}] Erro ao atualizar blocos do peer {peer}: {e}")
                with self.lock:
                    if peer in self.peer_blocks_map:
                        del self.peer_blocks_map[peer]
                    if peer in self.known_peers:
                        self.known_peers.remove(peer)

    def calculate_rarest_blocks(self):
        frequency = {}
        with self.lock:
            for blocks in self.peer_blocks_map.values():
                for b in blocks:
                    frequency[b] = frequency.get(b, 0) + 1
        missing_blocks = set(BLOCKS) - self.blocks
        freq_missing = {b: frequency.get(b, 0) for b in missing_blocks}
        rarest = sorted(freq_missing.items(), key=lambda x: x[1])
        return [b for b, _ in rarest]

    def select_peers_for_unchoke(self):
        with self.lock:
            rarest_blocks = self.calculate_rarest_blocks()
            peer_scores = {}
            for peer, blocks in self.peer_blocks_map.items():
                score = sum((len(rarest_blocks) - rarest_blocks.index(b)) for b in blocks if b in rarest_blocks)
                peer_scores[peer] = score
            sorted_peers = sorted(peer_scores.items(), key=lambda x: x[1], reverse=True)
            fixed_unchoked = set([p for p, _ in sorted_peers[:4]])
            other_peers = list(self.known_peers - fixed_unchoked)
            optimistic = set()
            if other_peers:
                optimistic.add(random.choice(other_peers))
            self.unchoked_peers = fixed_unchoked | optimistic
            self.choked_peers = self.known_peers - self.unchoked_peers
            gerar_log(f"[Peer {self.peer_id}] Unchoked: {self.unchoked_peers}, Choked: {self.choked_peers}")

    def unchoke_loop(self):
        while True:
            self.update_peer_blocks()
            self.select_peers_for_unchoke()
            time.sleep(10)

    def try_download_block(self, peer, max_retries=3):
        with self.lock:
            rarest_blocks = self.calculate_rarest_blocks()
        if not rarest_blocks:
            return
        retries = 0
        while retries < max_retries:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3)
                    s.connect(peer)
                    for block in rarest_blocks:
                        s.sendall(f'HAVE {block}'.encode())
                        response = s.recv(1024).decode()
                        if response == 'YES':
                            with self.lock:
                                if peer in self.unchoked_peers:
                                    s.sendall(f'REQUEST {block}'.encode())
                                    data = s.recv(4096)
                                    self.save_block(block, data)
                                    gerar_log(f"[Peer {self.peer_id}] Baixou {block} do peer {peer}")
                                    self.reconstruct_file()
                                    return
                                else:
                                    gerar_log(f"[Peer {self.peer_id}] Peer {peer} está choked, não pode pedir bloco")
                                    return
                        else:
                            continue
            except Exception as e:
                gerar_log(f"[Peer {self.peer_id}] Erro ao baixar bloco de {peer}: {e}. Tentando novamente ({retries+1}/{max_retries})")
                retries += 1
                time.sleep(2)
        gerar_log(f"[Peer {self.peer_id}] Falhou em baixar bloco de {peer} após {max_retries} tentativas.")


    def server_thread(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', self.port))
        server.listen()
        gerar_log(f"[Peer {self.peer_id}] Servidor ouvindo na porta {self.port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_peer_connection, args=(conn,), daemon=True).start()

    def handle_peer_connection(self, conn):
        try:
            msg = conn.recv(1024).decode()
            if msg.startswith('GET_BLOCKS'):
                with self.lock:
                    data = ','.join(self.blocks)
                conn.send(data.encode())
            elif msg.startswith('HAVE'):
                block = msg.split()[1]
                with self.lock:
                    if block in self.blocks:
                        conn.send(b'YES')
                    else:
                        conn.send(b'NO')
            elif msg.startswith('REQUEST'):
                block = msg.split()[1]
                with self.lock:
                    if block in self.blocks:
                        caminho = os.path.join(self.bloco_dir, block)
                        with open(caminho, 'rb') as f:
                            data = f.read()
                        conn.sendall(data)
                    else:
                        conn.send(b'NOT_AVAILABLE')
            else:
                conn.send(b'UNKNOWN_COMMAND')
        except Exception as e:
            gerar_log(f"[Peer {self.peer_id}] Erro na conexão: {e}")
        finally:
            conn.close()

    def run(self):
        if self.peer_id == 0:
            dividir_arquivo_em_blocos(self.arquivo_original, self.bloco_dir, tamanho_bloco=1024)
        if not self.load_blocks():
            gerar_log(f"[Peer {self.peer_id}] Erro ao carregar blocos locais, encerrando.")
            return
        threading.Thread(target=self.server_thread, daemon=True).start()
        threading.Thread(target=self.unchoke_loop, daemon=True).start()

        while True:
            if len(self.blocks) == BLOCKS_TOTAL:
                gerar_log(f"[Peer {self.peer_id}] Arquivo completo! Encerrando...")
                break
            if not self.register_to_tracker():
                gerar_log(f"[Peer {self.peer_id}] Não conseguiu conectar tracker, tentando novamente...")
                time.sleep(5)
                continue
            peers_list = list(self.known_peers)
            if not peers_list:
                gerar_log(f"[Peer {self.peer_id}] Nenhum peer conhecido, aguardando...")
                time.sleep(5)
                continue
            peer = random.choice(peers_list)
            self.try_download_block(peer)
            time.sleep(3)


if __name__ == '__main__':
    import sys
    peer_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    peer = Peer(peer_id)
    peer.run()