import os

def dividir_arquivo_em_blocos(caminho_arquivo, pasta_saida, tamanho_bloco=1024):
    """
    Divide um arquivo em blocos de tamanho fixo e salva na pasta de saída.
    Cada bloco é salvo como block_0, block_1, ...
    """
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    with open(caminho_arquivo, 'rb') as f:
        bloco_num = 0
        while True:
            dados = f.read(tamanho_bloco)
            if not dados:
                break
            caminho_bloco = os.path.join(pasta_saida, f'block_{bloco_num}')
            with open(caminho_bloco, 'wb') as bf:
                bf.write(dados)
            bloco_num += 1
    print(f"[UTILS] Arquivo dividido em {bloco_num} blocos na pasta {pasta_saida}")

def salvar_contagem_blocos(pasta_blocos, arquivo_contagem='block_count.txt'):
    blocos = [b for b in os.listdir(pasta_blocos) if b.startswith('block_')]
    total = len(blocos)
    caminho = os.path.join(pasta_blocos, arquivo_contagem)
    with open(caminho, 'w') as f:
        f.write(str(total))
    print(f"[UTILS] Salvou contagem de blocos ({total}) em {caminho}")

def reconstruir_arquivo(pasta_blocos, nome_arquivo_saida):
    """
    Junta os blocos na pasta e reconstrói o arquivo original.
    Os blocos devem estar nomeados block_0, block_1, ...
    """
    blocos = sorted([b for b in os.listdir(pasta_blocos) if b.startswith('block_')],
                    key=lambda x: int(x.split('_')[1]))
    with open(nome_arquivo_saida, 'wb') as f_out:
        for bloco in blocos:
            caminho_bloco = os.path.join(pasta_blocos, bloco)
            with open(caminho_bloco, 'rb') as bf:
                f_out.write(bf.read())
    print(f"[UTILS] Arquivo reconstruído em {nome_arquivo_saida}")

def gerar_log(mensagem, arquivo_log=None):
    """
    Função simples para gerar logs no console e opcionalmente salvar em arquivo.
    """
    print(f"[LOG] {mensagem}")
    if arquivo_log:
        with open(arquivo_log, 'a') as f:
            f.write(mensagem + '\n')