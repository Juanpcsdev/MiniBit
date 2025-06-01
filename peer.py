import socket
import threading
import random
import time
import os
import json
from utils import dividir_pasta_em_blocos, reconstruir_arquivo, gerar_log, salvar_contagem_blocos

TRACKER_HOST = 'localhost'
TRACKER_PORT = 5000
PEER_PORT_BASE = 6000

class Peer:
    def __init__(self, peer_id, arquivo_original='arquivos/'):
        """
        Inicializa um peer com informações básicas, como diretório de blocos e porta específica.
        """
        self.peer_id = peer_id
        self.bloco_dir = f'blocos_peer_{peer_id}'
        self.arquivo_original = arquivo_original
        self.blocks = set()
        self.known_peers = set()
        self.peer_blocks_map = {}
        self.unchoked_peers = set()
        self.choked_peers = set()
        self.lock = threading.RLock()  # Troquei para RLock
        self.port = PEER_PORT_BASE + peer_id

        self.block_count_file = 'blocos_peer_0/block_count.txt'
        self.BLOCKS_TOTAL = None
        self.BLOCKS = []

    def set_blocks_total_dynamic(self, max_retries=10, retry_delay=3):
        """
        Define dinamicamente o total de blocos lendo do arquivo block_count.txt.
        """
        attempts = 0
        while attempts < max_retries:
            try:
                if self.peer_id == 0:
                    blocos = [f for f in os.listdir(self.bloco_dir) if f.startswith('block_') and f != 'block_count.txt']
                    total = len(blocos)
                    salvar_contagem_blocos(self.bloco_dir)
                    self.BLOCKS_TOTAL = total
                    self.BLOCKS = [f'block_{i}' for i in range(total)]
                    gerar_log(f"[Peer {self.peer_id}] Salvou total de blocos: {total}")
                    return True
                else:
                    if os.path.exists(self.block_count_file):
                        with open(self.block_count_file, 'r') as f:
                            total = int(f.read().strip())
                        self.BLOCKS_TOTAL = total
                        self.BLOCKS = [f'block_{i}' for i in range(total)]
                        gerar_log(f"[Peer {self.peer_id}] Leu total de blocos: {total}")
                        return True
                    else:
                        gerar_log(f"[Peer {self.peer_id}] Arquivo {self.block_count_file} não encontrado. Tentando novamente ({attempts+1}/{max_retries})...")
                        attempts += 1
                        time.sleep(retry_delay)
            except Exception as e:
                gerar_log(f"[Peer {self.peer_id}] Erro ao ler/definir total de blocos: {e}")
                attempts += 1
                time.sleep(retry_delay)
        gerar_log(f"[Peer {self.peer_id}] Falhou ao definir total de blocos após {max_retries} tentativas.")
        return False

    def load_blocks(self, max_retries=10, retry_delay=3):
        """
        Carrega blocos existentes no diretório local do peer.
        """
        attempts = 0
        while attempts < max_retries:
            if not os.path.exists(self.bloco_dir):
                os.makedirs(self.bloco_dir)
            blocos = [f for f in os.listdir(self.bloco_dir) if f.startswith('block_') and f != 'block_count.txt']
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
        """
        Salva bloco recebido no diretório local.
        """
        caminho = os.path.join(self.bloco_dir, block_name)
        with open(caminho, 'wb') as f:
            f.write(data)
        with self.lock:
            self.blocks.add(block_name)
        gerar_log(f"[Peer {self.peer_id}] Salvou bloco {block_name}")

    def reconstruct_file(self):
        """
        Reconstrói arquivo original a partir dos blocos recebidos.
        """
        with self.lock:
            total_blocks = len(self.blocks)
            blocks_total = self.BLOCKS_TOTAL
        if total_blocks == blocks_total:
            reconstruir_arquivo(self.bloco_dir, f'reconstruido_peer_{self.peer_id}.txt')
            gerar_log(f"[Peer {self.peer_id}] Arquivo reconstruído com sucesso.")

    def register_to_tracker(self, max_retries=10, retry_delay=3):
        """
        Registra o peer e seus blocos no tracker.
        """
        retries = 0
        while retries < max_retries:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((TRACKER_HOST, TRACKER_PORT))
                    with self.lock:
                        blocks_str = ','.join(self.blocks)
                    message = f'REGISTER {self.port} {blocks_str}'
                    s.sendall(message.encode())
                    resp = s.recv(1024).decode()
                    if resp != 'OK':
                        gerar_log(f"[Peer {self.peer_id}] Tracker não confirmou registro.")
                        return False
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((TRACKER_HOST, TRACKER_PORT))
                    s.sendall(b'GET_PEERS')
                    data = s.recv(4096).decode()
                    info = json.loads(data)
                    peers = info['peers']
                    suggested_blocks = info['suggested_blocks']
                    with self.lock:
                        self.known_peers = set([tuple(p) for p in peers if tuple(p)[1] != self.port])
                        self.suggested_blocks = suggested_blocks
                gerar_log(f"[Peer {self.peer_id}] Peers conhecidos: {self.known_peers}")
                gerar_log(f"[Peer {self.peer_id}] Blocos sugeridos pelo tracker: {self.suggested_blocks}")
                return True
            except Exception as e:
                gerar_log(f"[Peer {self.peer_id}] Falha ao conectar tracker: {e}. Tentando novamente ({retries+1}/{max_retries})")
                retries += 1
                time.sleep(retry_delay)
        gerar_log(f"[Peer {self.peer_id}] Não conseguiu conectar ao tracker após {max_retries} tentativas.")
        return False

    def update_peer_blocks(self):
        """
        Atualiza o mapa de blocos possuídos pelos peers conhecidos.
        """
        for peer in list(self.known_peers):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect(peer)
                    s.sendall(b'GET_BLOCKS')
                    data = s.recv(4096).decode()
                    blocks = set(b for b in data.split(',') if b) if data else set()
                    with self.lock:
                        self.peer_blocks_map[peer] = blocks
                    gerar_log(f"[Peer {self.peer_id}] Atualizou blocos do peer {peer}: {blocks}")
            except Exception as e:
                gerar_log(f"[Peer {self.peer_id}] Erro ao atualizar blocos do peer {peer}: {e}")
                with self.lock:
                    if peer in self.peer_blocks_map:
                        del self.peer_blocks_map[peer]
                    if peer in self.known_peers:
                        self.known_peers.remove(peer)

    def calculate_rarest_blocks(self):
        """
        Calcula e retorna os blocos mais raros na rede.
        """
        frequency = {}
        with self.lock:
            for blocks in self.peer_blocks_map.values():
                for b in blocks:
                    frequency[b] = frequency.get(b, 0) + 1
        with self.lock:
            missing_blocks = set(self.BLOCKS) - self.blocks
        freq_missing = {b: frequency.get(b, 0) for b in missing_blocks}
        rarest = sorted(freq_missing.items(), key=lambda x: x[1])
        return [b for b, _ in rarest]

    def select_peers_for_unchoke(self):
        """
        Seleciona peers para desbloquear baseado nos blocos raros que eles têm.
        """
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

            gerar_log(f"[Peer {self.peer_id}] Peers fixos desbloqueados: {fixed_unchoked}")
            gerar_log(f"[Peer {self.peer_id}] Peer otimista desbloqueado: {optimistic}")
            gerar_log(f"[Peer {self.peer_id}] Peers choked (bloqueados): {self.choked_peers}")

    def unchoke_loop(self):
        """
        Loop contínuo para atualizar peers desbloqueados e bloqueados periodicamente.
        """
        gerar_log(f"[Peer {self.peer_id}] Iniciando unchoke loop")
        while True:
            try:
                self.update_peer_blocks()
                self.select_peers_for_unchoke()
                gerar_log(f"[Peer {self.peer_id}] Peers desbloqueados: {self.unchoked_peers}")
            except Exception as e:
                gerar_log(f"[Peer {self.peer_id}] Erro na unchoke_loop: {e}")
            time.sleep(10)

    def check_have(self, peer, block):
        """
        Verifica se um peer específico tem um bloco desejado.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect(peer)
                s.sendall(f'HAVE {block}'.encode())
                response = s.recv(1024).decode()
                return response == 'YES'
        except Exception as e:
            gerar_log(f"[Peer {self.peer_id}] Erro checando HAVE do bloco {block} no peer {peer}: {e}")
            return False

    def request_block(self, peer, block):
        """
        Solicita um bloco específico a um peer desbloqueado.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect(peer)
                s.sendall(f'REQUEST {block}'.encode())
                data = b""
                while True:
                    part = s.recv(4096)
                    if not part:
                        break
                    data += part
                if data:
                    self.save_block(block, data)
                    gerar_log(f"[Peer {self.peer_id}] Baixou {block} do peer {peer}")
                    self.reconstruct_file()
                    return True
                else:
                    gerar_log(f"[Peer {self.peer_id}] Dados recebidos vazios para bloco {block} do peer {peer}")
                    return False
        except Exception as e:
            gerar_log(f"[Peer {self.peer_id}] Erro ao baixar bloco {block} de {peer}: {e}")
            return False

    def try_download_block(self, peer, max_retries=3):
        """
        Tenta baixar blocos sugeridos ou raros de um peer específico.
        """
        with self.lock:
            suggested_blocks = list(self.suggested_blocks) if hasattr(self, 'suggested_blocks') else []
            current_blocks = set(self.blocks)

        if suggested_blocks:
            blocks_to_try = [b for b in suggested_blocks if b not in current_blocks]
            if not blocks_to_try:
                blocks_to_try = self.calculate_rarest_blocks()
        else:
            blocks_to_try = self.calculate_rarest_blocks()

        if not blocks_to_try:
            gerar_log(f"[Peer {self.peer_id}] Nenhum bloco para tentar baixar do peer {peer}")
            return

        gerar_log(f"[Peer {self.peer_id}] Tentando baixar blocos {blocks_to_try} do peer {peer}")

        for block in blocks_to_try:
            gerar_log(f"[Peer {self.peer_id}] Verificando se peer {peer} tem bloco {block}")
            have = self.check_have(peer, block)
            if have:
                with self.lock:
                    is_unchoked = peer in self.unchoked_peers
                if is_unchoked:
                    success = self.request_block(peer, block)
                    if success:
                        return
                else:
                    gerar_log(f"[Peer {self.peer_id}] Peer {peer} está choked, não pode pedir bloco")
                    return
            else:
                gerar_log(f"[Peer {self.peer_id}] Peer {peer} não tem bloco {block}")

        gerar_log(f"[Peer {self.peer_id}] Nenhum bloco baixado do peer {peer} nesta tentativa.")

    def server_thread(self):
        """
        Inicia o servidor local do peer para atender requisições.
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', self.port))
        server.listen()
        gerar_log(f"[Peer {self.peer_id}] Servidor ouvindo na porta {self.port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_peer_connection, args=(conn,), daemon=True).start()

    def handle_peer_connection(self, conn):
        """
        Trata requisições recebidas de outros peers.
        """
        try:
            msg = conn.recv(1024).decode()
            gerar_log(f"[Peer {self.peer_id}] Mensagem recebida no handle_peer_connection: {msg}")
            if msg.startswith('GET_BLOCKS'):
                with self.lock:
                    data = ','.join(self.blocks)
                conn.send(data.encode())
            elif msg.startswith('HAVE'):
                block = msg.split()[1]
                with self.lock:
                    if block in self.blocks:
                        gerar_log(f"[Peer {self.peer_id}] Respondendo YES para HAVE {block}")
                        conn.send(b'YES')
                    else:
                        gerar_log(f"[Peer {self.peer_id}] Respondendo NO para HAVE {block}")
                        conn.send(b'NO')
            elif msg.startswith('REQUEST'):
                block = msg.split()[1]
                with self.lock:
                    if block in self.blocks:
                        caminho = os.path.join(self.bloco_dir, block)
                        with open(caminho, 'rb') as f:
                            data = f.read()
                        gerar_log(f"[Peer {self.peer_id}] Enviando bloco {block}")
                        conn.sendall(data)
                        conn.shutdown(socket.SHUT_WR)  # Envia FIN para sinalizar fim
                    else:
                        gerar_log(f"[Peer {self.peer_id}] Bloco {block} solicitado não disponível")
                        conn.send(b'NOT_AVAILABLE')
            else:
                gerar_log(f"[Peer {self.peer_id}] Comando desconhecido: {msg}")
                conn.send(b'UNKNOWN_COMMAND')
        except Exception as e:
            gerar_log(f"[Peer {self.peer_id}] Erro na conexão: {e}")
        finally:
            conn.close()

    def run(self):
        """
        Método principal para inicializar o peer e começar o processo de download e compartilhamento.
        """
        gerar_log(f"[Peer {self.peer_id}] Iniciando execução principal")
        if self.peer_id == 0:
            dividir_pasta_em_blocos(self.arquivo_original, self.bloco_dir, tamanho_bloco=1024)
        if not self.set_blocks_total_dynamic():
            gerar_log(f"[Peer {self.peer_id}] Falha ao definir total de blocos, encerrando.")
            return
        if not self.load_blocks():
            gerar_log(f"[Peer {self.peer_id}] Erro ao carregar blocos locais, encerrando.")
            return

        threading.Thread(target=self.server_thread, daemon=True).start()
        threading.Thread(target=self.unchoke_loop, daemon=True).start()
        gerar_log(f"[Peer {self.peer_id}] Threads de servidor e unchoke iniciadas")

        time.sleep(10)  # <<<<< Aqui espera inicial

        max_attempts = 10
        attempts = 0

        while True:
            if self.BLOCKS_TOTAL is None:
                gerar_log(f"[Peer {self.peer_id}] BLOCKS_TOTAL indefinido, tentando novamente...")
                if not self.set_blocks_total_dynamic():
                    time.sleep(5)
                    continue

            with self.lock:
                blocks_count = len(self.blocks)
                blocks_total = self.BLOCKS_TOTAL

            if blocks_count == blocks_total:
                if self.peer_id != 0:
                    gerar_log(f"[Peer {self.peer_id}] Arquivo completo! Encerrando...")
                    break
                else:
                    gerar_log(f"[Peer {self.peer_id}] Arquivo completo, permanecendo online para servir os blocos.")

            if not self.register_to_tracker():
                gerar_log(f"[Peer {self.peer_id}] Não conseguiu conectar tracker, tentando novamente...")
                time.sleep(5)
                continue

            with self.lock:
                peers_list = list(self.known_peers)

            gerar_log(f"[Peer {self.peer_id}] Peers disponíveis: {peers_list}")
            if not peers_list:
                gerar_log(f"[Peer {self.peer_id}] Nenhum peer conhecido, aguardando...")
                time.sleep(5)
                continue

            peer = random.choice(peers_list)
            gerar_log(f"[Peer {self.peer_id}] Tentando baixar bloco de peer {peer}")
            self.try_download_block(peer)
            time.sleep(3)


if __name__ == '__main__':
    import sys
    peer_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    peer = Peer(peer_id)
    try:
        peer.run()
    except KeyboardInterrupt:
        gerar_log(f"[Peer {peer.peer_id}] Encerrado manualmente com CTRL+C. Até mais!")
        sys.exit(0)