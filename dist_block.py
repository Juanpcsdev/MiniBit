import os
import shutil
import random

def dist_block(seed_dir='blocos_peer_0', num_peers=4, min_blocos=1, max_blocos=10):
    """
    Distribui blocos aleatórios da seed (peer 0) para os demais peers.
    
    Args:
        seed_dir: pasta com blocos do peer 0 (seed).
        num_peers: total de peers (incluindo seed).
        min_blocos: número mínimo de blocos que cada peer recebe.
        max_blocos: número máximo de blocos que cada peer recebe.
    """
    blocos = [f for f in os.listdir(seed_dir) if f.startswith('block_')]
    print(f"Seed tem {len(blocos)} blocos.")

    for peer_id in range(1, num_peers):
        destino = f'blocos_peer_{peer_id}'
        if not os.path.exists(destino):
            os.makedirs(destino)
        num_blocos_peer = random.randint(min_blocos, max_blocos)
        blocos_para_copiar = random.sample(blocos, num_blocos_peer)
        for bloco in blocos_para_copiar:
            src = os.path.join(seed_dir, bloco)
            dst = os.path.join(destino, bloco)
            shutil.copy(src, dst)
        print(f"Peer {peer_id} recebeu {num_blocos_peer} blocos: {blocos_para_copiar}")

if __name__ == '__main__':
    dist_block()