import subprocess
import time
import sys
import os
import signal

NUM_PEERS = 4  # número total de peers (incluindo o peer 0)

def run_command(cmd, wait=True):
    print(f"[RUN] Executando: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd)
    if wait:
        proc.wait()
    return proc

def main():
    # Passo 1: Peer 0 divide o arquivo (gera blocos)
    print("[RUN] Passo 1: Peer 0 dividindo arquivo original...")
    run_command([sys.executable, 'peer.py', '0'])

    # Passo 2: Distribui blocos para peers (exceto peer 0)
    print("[RUN] Passo 2: Distribuindo blocos para peers...")
    run_command([sys.executable, 'dist_block.py'])

    # Passo 3: Inicia tracker
    print("[RUN] Passo 3: Iniciando tracker...")
    tracker_proc = run_command([sys.executable, 'tracker.py'], wait=False)
    time.sleep(1)  # espera tracker iniciar

    # Passo 4: Inicia todos os peers (0,1,2,...)
    print("[RUN] Passo 4: Iniciando peers...")
    peer_procs = []
    for peer_id in range(NUM_PEERS):
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