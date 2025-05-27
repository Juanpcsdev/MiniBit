import socket
import threading
import random
from utils import gerar_log

PEERS = []
LOCK = threading.Lock()

def handle_client(conn, addr):
    with LOCK:
        if addr not in PEERS:
            PEERS.append(addr)
            gerar_log(f"[TRACKER] Novo peer conectado: {addr}")
    try:
        data = conn.recv(1024).decode()
        if data == 'GET_PEERS':
            with LOCK:
                available_peers = [p for p in PEERS if p != addr]
                if len(available_peers) <= 5:
                    response = str(available_peers)
                else:
                    response = str(random.sample(available_peers, 5))
            conn.send(response.encode())
            gerar_log(f"[TRACKER] Resposta para {addr}: {response}")
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