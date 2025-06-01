import subprocess
import time
import sys
import signal
from datetime import datetime

NUM_PEERS = 5  # total de peers (incluindo peer 0)

def run_command(cmd, wait=True):
    print(f"[RUN] Executando: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd)
    if wait:
        proc.wait()
    return proc

def main():
    # INÍCIO DA MEDIÇÃO DE TEMPO
    inicio = datetime.now()

    print("[RUN] Passo 1: Peer 0 iniciando e dividindo arquivo...")
    peer0_proc = run_command([sys.executable, 'peer.py', '0'], wait=False)
    time.sleep(5)

    print("[RUN] Passo 2: Distribuindo blocos para peers...")
    run_command([sys.executable, 'dist_block.py'])

    print("[RUN] Passo 3: Iniciando tracker...")
    tracker_proc = run_command([sys.executable, 'tracker.py'], wait=False)
    time.sleep(2)

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
        fim = datetime.now()
        duracao = fim - inicio
        print(f"\n[RUN] CTRL+C detectado. Encerrando processos...")
        print(f"[RUN] Tempo total de execução: {duracao}")
        for p in peer_procs:
            p.terminate()
        tracker_proc.terminate()
        print("[RUN] Todos os processos encerrados. Até mais!")


if __name__ == '__main__':
    main()