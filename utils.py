import os

# Divide uma pasta contendo arquivos em blocos numerados sequencialmente
def dividir_pasta_em_blocos(pasta_origem, pasta_saida, tamanho_bloco=1024):
    # Cria pasta de saída se não existir
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    bloco_num = 0  # Contador para numerar os blocos
    for root, dirs, files in os.walk(pasta_origem):
        # Percorre arquivos da pasta de origem
        for arquivo in files:
            caminho_completo = os.path.join(root, arquivo)
            with open(caminho_completo, 'rb') as f:
                while True:
                    dados = f.read(tamanho_bloco)
                    if not dados:
                        break
                    nome_bloco = f'block_{bloco_num}'
                    caminho_bloco = os.path.join(pasta_saida, nome_bloco)
                    with open(caminho_bloco, 'wb') as bf:
                        bf.write(dados)
                    bloco_num += 1
    print(f"[UTILS] Pasta dividida em {bloco_num} blocos na pasta {pasta_saida}")

# Salva a contagem total dos blocos em um arquivo de texto
def salvar_contagem_blocos(pasta_blocos, arquivo_contagem='block_count.txt'):
    blocos = [b for b in os.listdir(pasta_blocos) if b.startswith('block_') and b != arquivo_contagem]
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