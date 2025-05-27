with open('arquivo.txt', 'w') as f:
    base_text = """MiniBit - Sistema de Compartilhamento Cooperativo de Arquivos

Este arquivo serve como exemplo para a implementação do MiniBit,
um sistema distribuído inspirado no BitTorrent, para dividir,
compartilhar e reconstruir arquivos usando estratégias como
rarest first e tit-for-tat simplificado.

O conteúdo deste arquivo é fictício e serve apenas para teste
do sistema, dividindo em blocos de 1024 bytes.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed
do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco
laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit
esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
occaecat cupidatat non proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.

Fim do arquivo de teste MiniBit.

"""

    for _ in range(1000):  # Repete o texto 1000 vezes para aumentar o tamanho
        f.write(base_text)