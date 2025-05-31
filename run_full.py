import subprocess
import time
import sys
import os
import signal

NUM_PEERS = 5  # total de peers (incluindo peer 0)

def run_command(cmd, wait=True):
    print(f"[RUN] Executando: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd)
    if wait:
        proc.wait()
    return proc

def main():
    # Passo 1: Peer 0 divide o arquivo, mas NÃO finaliza (rodando em background)
    print("[RUN] Passo 1: Peer 0 iniciando e dividindo arquivo...")
    peer0_proc = run_command([sys.executable, 'peer.py', '0'], wait=False)
    time.sleep(5)  # espera peer 0 criar blocos e começar a rodar

    # Passo 2: Distribui blocos para peers (exceto peer 0)
    print("[RUN] Passo 2: Distribuindo blocos para peers...")
    run_command([sys.executable, 'dist_block.py'])  # espera terminar

    # Passo 3: Inicia tracker
    print("[RUN] Passo 3: Iniciando tracker...")
    tracker_proc = run_command([sys.executable, 'tracker.py'], wait=False)
    time.sleep(2)  # espera tracker iniciar

    # Passo 4: Inicia peers 1,2,... (peer 0 já iniciado)
    print("[RUN] Passo 4: Iniciando peers restantes...")
    peer_procs = [peer0_proc]
    for peer_id in range(1, NUM_PEERS):
        proc = run_command([sys.executable, 'peer.py', str(peer_id)], wait=False)
        peer_procs.append(proc)
        time.sleep(1)

    print("[RUN] Sistema MiniBit iniciado com sucesso! CTRL+C para encerrar.")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[RUN] CTRL+C detectado. Encerrando processos...")
        for p in peer_procs:
            p.send_signal(signal.SIGINT)
        tracker_proc.send_signal(signal.SIGINT)
        print("[RUN] Todos os processos encerrados. Até mais!")

if __name__ == '__main__':
    main()
