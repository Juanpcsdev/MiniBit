import os
import shutil
import random

def dist_block(seed_dir='blocos_peer_0', num_peers=5, min_blocos=1, max_blocos=10):
    # Lê contagem real de blocos
    contagem_path = os.path.join(seed_dir, 'block_count.txt')
    if not os.path.exists(contagem_path):
        raise FileNotFoundError(f"Arquivo de contagem de blocos não encontrado: {contagem_path}")
    with open(contagem_path, 'r') as f:
        total_blocos = int(f.read().strip())
    blocos = [f'block_{i}' for i in range(total_blocos)]  # Aqui gera a lista limpa dos blocos reais
    print(f"Seed tem {total_blocos} blocos.")

    for peer_id in range(1, num_peers):
        destino = f'blocos_peer_{peer_id}'
        if not os.path.exists(destino):
            os.makedirs(destino)
        num_blocos_peer = random.randint(min_blocos, min(max_blocos, total_blocos - 1))
        blocos_para_copiar = random.sample(blocos, num_blocos_peer)
        for bloco in blocos_para_copiar:
            src = os.path.join(seed_dir, bloco)
            dst = os.path.join(destino, bloco)
            shutil.copy(src, dst)
        print(f"Peer {peer_id} recebeu {num_blocos_peer} blocos: {blocos_para_copiar}")

if __name__ == '__main__':
    dist_block()
