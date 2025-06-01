import os
import shutil
import random

n_peers= 5

def dist_block(seed_dir='blocos_peer_0', num_peers= n_peers, min_blocos=1, max_blocos=10):
    """
    Distribui aleatoriamente blocos do diretório seed para outros peers.

    Args:
        seed_dir (str): Diretório que contém os blocos originais e arquivo 'block_count.txt'.
        num_peers (int): Número total de peers na rede (incluindo o seed).
        min_blocos (int): Mínimo de blocos que um peer pode receber.
        max_blocos (int): Máximo de blocos que um peer pode receber.
    """

    # Ler arquivo que indica a quantidade total de blocos no peer seed
    contagem_path = os.path.join(seed_dir, 'block_count.txt')
    if not os.path.exists(contagem_path):
        raise FileNotFoundError(f"Arquivo de contagem de blocos não encontrado: {contagem_path}")
    
    # Obter o número total de blocos
    with open(contagem_path, 'r') as f:
        total_blocos = int(f.read().strip())
    
    # Criar lista com nomes dos blocos disponíveis
    blocos = [f'block_{i}' for i in range(total_blocos)]  # Aqui gera a lista limpa dos blocos reais
    print(f"Seed tem {total_blocos} blocos.")

    # Distribuir blocos aleatoriamente entre os peers restantes
    for peer_id in range(1, num_peers):
        destino = f'blocos_peer_{peer_id}'
        if not os.path.exists(destino):
            os.makedirs(destino)
        
        # Escolher aleatoriamente quantos blocos este peer vai receber
        num_blocos_peer = random.randint(min_blocos, min(max_blocos, total_blocos - 1))

        # Escolher blocos específicos para este peer
        blocos_para_copiar = random.sample(blocos, num_blocos_peer)

        # Copiar cada bloco selecionado para o diretório do peer
        for bloco in blocos_para_copiar:
            src = os.path.join(seed_dir, bloco)
            dst = os.path.join(destino, bloco)
            shutil.copy(src, dst)
        print(f"Peer {peer_id} recebeu {num_blocos_peer} blocos: {blocos_para_copiar}")

if __name__ == '__main__':
    dist_block()
