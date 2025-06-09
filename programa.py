from sys import argv
import io
import os

def constroi_indice(arq: io.BufferedRandom) -> list[tuple[int, int]]:
    '''
    A partir da leitura do arquivo, a função constroi um índice (lista) ordenado a
    partir do ID.
    O índice contém tuplas[ID, byte-offset] correspondentes a todos
    os registros do arquivo.
    '''
    arq.seek(4)
    offset = arq.tell()
    arq.seek(0, os.SEEK_END)
    offset_final = arq.tell()
    arq.seek(offset)
    chaves: list[tuple[int, int]] = []
    while offset < offset_final:
        dados, tamanho = leia_reg(arq)
        id = dados.split('|')[0]
        if id.isdigit():
            chaves.append((int(id), offset))
        leia_nulo(arq, arq.tell())
        offset = arq.tell()
    chaves.sort()
    return chaves

def insere_no_indice(id: int, offset: int, indice: list[tuple[int, int]]) -> None:            #Sepa mudar o nome????????????
    '''
    A função insere uma tupla[ID, byte-offset] ao índice e o ordena. É chamada
    quando um novo registro é inserido no arquivo.

    Parâmetros:
        id:
        offset:
        indice: 
    '''
    indice.append((id, offset))
    indice.sort()

def leia_nulo(arq: io.BufferedRandom, offset_inicio_busca: int) -> None:
    '''
    Tem como função posicionar o ponteiro de L/E no início do próximo registro
    quando fragmentação externa é encontrada.
    A função inicia a leitura no arquivo a partir do offset_inicio_busca, buscando
    o início (bytes de tamanho) do próximo registro.
    É chamada durante a construção do índice.
    
    Parâmetros:
        arq: O objeto de arquivo binário aberto.
        offset_inicio_busca: O offset a partir do qual a busca pelo próximo
                            registro válido deve começar.

    Retorna:
        ...
    '''
    arq.seek(offset_inicio_busca)
    encontrou_inicio_valido = False
    final = False

    while not encontrou_inicio_valido and not final:
        pos_antes_tentativa = arq.tell()
        bytes_tamanho = arq.read(2)

        if not bytes_tamanho:
            final = True
        else:
            tamanho_candidato = int.from_bytes(bytes_tamanho)
            if tamanho_candidato > 0:
                arq.seek(pos_antes_tentativa)
                encontrou_inicio_valido = True
            else:
                arq.seek(pos_antes_tentativa + 1)

def leia_reg(arq: io.BufferedRandom) -> tuple[str, int]:
    ''' 
    A função lê um registro do arquivo e retorna uma tupla[registro, tamanho]
    correspondente a str do registro e o seu tamanho.
    É chamada na construção do índice.

    Retorna:
    '''
    tamanho = int.from_bytes(arq.read(2))
    excluido = arq.read(1)
    if tamanho > 0 and excluido != b'*':
        registro_byte = arq.read(tamanho-1)
        registro = excluido.decode() + registro_byte.decode()
        return (registro, tamanho)
    arq.seek(tamanho - 1, os.SEEK_CUR)
    return ('', 0)

def busca_binaria(id: int, indice: list[tuple[int, int]]) -> int:
    '''
    A função faz a busca binária em um índice a partir do ID (chave) do registro,
    retornando o byte-offset correspondente.
    É chamado na remoção e inserção de registros, para checar se existe ou não um
    registro com determinado índice.

    Parâmetros:
        id:
        indice:
    
    Retorna:
        Se o id existir, a função retorna seu byte-offset, se não, retorna -1.
    '''
    i = 0
    f = len(indice) - 1
    while i <= f:
        m = (i + f)//2
        if indice[m][0] == id:
            return indice[m][1]
        if indice[m][0] < id:
            i = m + 1
        else: 
            f = m - 1
    return -1

def remove_registro(arq: io.BufferedRandom, id: int, indice: list[tuple[int, int]]) -> None:
    '''
    A função remove o registro do arquivo pelo seu id. Escreve após o tamanho, "*"
    e a chama a função "insere_fragmentação()" que insere na LED a nova fragmentação e
    escreve a posição do byte-offset da próxima fragmentação da LED pela função
    "escreve_fragmentação()".

    Parâmetros:
        arq:
        id:
        indice:
    '''
    if busca_binaria(id, indice) != -1:
        offset = busca_binaria(id, indice)
        arq.seek(offset)
        tam = int.from_bytes(arq.read(2))
        indice.remove((id, busca_binaria(id, indice)))
        arq.write(b'*')
        insere_fragmentacao(arq, tam, offset)
        imprime_remocao(id, tam, offset)
    else:
        imprime_remocao(id, 0, -1)

def insere_registro(arq: io.BufferedRandom, registro: str, indice: list[tuple[int, int]]) -> None:
    '''
    A função leva em consideração o tamanho do registro para encontrar o local
    adequado para a inserção.

    Parâmetros:
        arq:
        registro:
        indice:

    '''
    id = int(registro.split('|')[0])
    if (busca_binaria(id, indice)) == -1:
        tam_reg = len(registro.encode())
        led = leia_led(arq)
        i = 0
        while led[i][1] < tam_reg and i < len(led) -1:
            i += 1
        diferenca = led[i][1] - tam_reg
        offset_insere = led[i][0]
        if i == 0 and led[i][0] != -1: #insere no offset da cabeca da LED
            escreve_registro(arq, offset_insere, registro, diferenca)
            insere_no_indice(id, offset_insere, indice)
            ordena_led(arq, 0, led[i+1][0])
            imprime_insercao(offset_insere, id, tam_reg, led[i][1])
        elif i == len(led) - 1: #insere no fim do arquivo            
            arq.seek(0, os.SEEK_END)                                                        
            offset_final = arq.tell()                                                       
            escreve_registro(arq, offset_final, registro, 0)                                
            insere_no_indice(id, offset_final, indice)                                         
            imprime_insercao(-1, id, tam_reg, 0)                                            
        else: #Insere no meio da LED
            escreve_registro(arq, offset_insere, registro, diferenca)
            insere_no_indice(id, offset_insere, indice)
            ordena_led(arq, led[i-1][0], led[i+1][0])
            imprime_insercao(offset_insere, id, tam_reg, led[i][1])
        leia_led(arq)
    else:
        print('ID já existe no arquivo. Insira com outro ID\n')
            
def escreve_registro(arq: io.BufferedRandom, offset_insere: int, registro: str, diferenca_tamanho: int) -> None:
    '''
    A função escreve o registro na posição offset_insere. Se a diferença_tamanho
    for maior que 0, ou seja, se for inserido em um espaço de fragmentação maior
    que o registro, escreve nulos até o fim da fragmentação.

    Parâmetros:
        arq:
        offset_insere:
        registro:
        diferenca_tamanho:
    '''
    arq.seek(offset_insere)
    tamanho_bytes = (len(registro.encode())).to_bytes(2)
    registro_bytes = registro.encode()
    arq.write(tamanho_bytes)
    arq.write(registro_bytes)
    if diferenca_tamanho > 0:
        vazios = b'\0' * diferenca_tamanho
        arq.write(vazios)

def ordena_led(arq: io.BufferedRandom, offset_anterior: int, offset_prox: int) -> None:
    '''
    A função ordena a led.
    Recebe o byte-offset do elemento anterior e do proximo, fazendo o "anterior"
    apontar para o "próximo".
    Se a inserção for realizada na fragmentação da cabeça da led, escreve o offset_prox
    na cabeça da led(cabeçalho).
    É chamada quando inserida uma fragmentação na led feita uma inserção de registro que altera a ordem da led.

    Parâmetros:
        arq:
        offset_anterior:
        offset_prox:
    '''
    arq.seek(offset_anterior)
    if offset_anterior != 0:
        arq.read(3)
    arq.write(offset_prox.to_bytes(4, signed = True))

def insere_fragmentacao(arq: io.BufferedRandom, tam_novo: int, offset_novo: int) -> None:
    '''
    A função insere na led a fragmentação resultante da remoção de um registro.
    Para isso, recebe o tamanho da nova fragmentação para comparar com o tamanho
    das outras fragmentações para ordenar a led de forma apropriada.

    Parâmetros:
        arq:
        tam_novo:
        offset_novo:
    '''
    led = leia_led(arq)
    i = 0
    tamanho_led = len(led) - 1
    while led[i][1] < tam_novo and i < tamanho_led:
        i += 1
    led.append((offset_novo, tam_novo))
    if i == 0: #insere no cabecalho
        ordena_led(arq, 0, offset_novo)
        ordena_led(arq, offset_novo, led[i][0])
        i == 0
    elif i == tamanho_led:
        ordena_led(arq, led[i-1][0], offset_novo)
        ordena_led(arq, offset_novo, -1)
    else:
        ordena_led(arq, led[i-1][0], offset_novo)
        ordena_led(arq, offset_novo, led[i][0])
    leia_led(arq)


def leia_led(arq: io.BufferedRandom) -> list[tuple[int, int]]:
    '''
    A função lê a cabeça da led no arquivo e retorna uma lista contendo todas as fragmentações na ordem
    '''
    arq.seek(0)
    offset_prox = int.from_bytes(arq.read(4), signed=True)
    led: list[tuple[int, int]] = []
    while offset_prox != -1:
        arq.seek(offset_prox)
        tam = int.from_bytes(arq.read(2))
        arq.read(1)
        led.append((offset_prox, tam))
        offset_prox = int.from_bytes(arq.read(4), signed=True)
    led.append((-1, 0))
    return led

def imprime_led(arq: io.BufferedRandom) -> None:
    '''
    A função imprime a led da seguinte forma:
    LED -> [offset: 1850, tam: 90] -> [offset: 477, tam: 92] -> [offset: 1942, tam: 109] -> fim
    Total: 3 espacos disponiveis
    '''
    led = leia_led(arq)
    texto = 'LED -> '
    for offset, tam in led:
        if offset == -1:
            texto += 'fim'
        else:
            texto += f'[offset: {offset}, tam: {tam}] -> '
    texto += f'\nTotal de espaços: {len(led)-1}'
    print(texto) 
    print()  

def imprime_busca(arq: io.BufferedRandom, id: int, indice: list[tuple[int, int]]) -> None:
    '''
    Busca pelo registro de chave "20"
    20|Forrest Gump|Robert Zemeckis|1994|Drama, Romance|142|Tom Hanks, Robin Wright, Gary Sinise (93 bytes)
    '''
    offset = busca_binaria(id, indice)
    print(f'Busca pelo registro de chave: "{id}"')
    if offset != -1:
        arq.seek(offset)
        dados, tamanho = leia_reg(arq)
        print(dados)
    else:
        print('Id não existe')
    print()

def imprime_insercao(offset: int, id: int, tamanho: int, frag: int) -> None:
    ''' Inserção do registro de chave "66" (77 bytes)
        Local: fim do arquivo

        Inserção do registro de chave "150" (77 bytes)
        Tamanho do espaço reutilizado: 92 bytes
        Local: offset = 477 bytes (0x1dd)
    '''
    print(f'Inserção do registro de chave: "{id}" ({tamanho} bytes)')
    if offset == -1:
        print('Local: fim do arquivo')
    else:
        print(f'Tamanho do espaço reutilizado: {frag} bytes')
        print(f'Local: offset = {offset} bytes ({hex(offset)})')
    print()

def imprime_remocao(id: int, tamanho: int, offset: int) -> None:
    '''
    Remoção do registro de chave "153"
    Registro removido! (92 bytes)
    Local: offset = 477 bytes (0x1dd)

    Remoção do registro de chave "230"
    Erro: registro não encontrado!
    '''
    print(f'Remoção do registro de chave "{id}"')
    if offset == -1:
        print('Erro: registro não encontrado!')
    else:
        print(f'Registro removido! ({tamanho} bytes)')
        print(f'Local: offset = {offset} bytes ({hex(offset)})')
    print()

def main() -> None:
    if (len(argv) > 1):
        operacao = argv[1]
        with open('filmes.dat', 'r+b') as filmes:
            indice = constroi_indice(filmes)
            if operacao == '-e' and len(argv) == 3:
                nomeArq = argv[2]
                with open(nomeArq, 'r') as arq:
                    comandos = arq.readlines()
                    for comando in comandos:
                        if comando[0] == 'b':
                            id = int(comando[2:])
                            imprime_busca(filmes, id, indice)
                        if comando[0] == 'r':
                            id = int(comando[2:])
                            remove_registro(filmes, id, indice)
                        if comando[0] == 'i':
                            registro = comando[2:]
                            insere_registro(filmes, registro, indice)
                    print('As operações do arquivo dados/operacoes.txt foram executadas com sucesso!')
            elif operacao == '-p':
                imprime_led(filmes)
                print('A LED foi impressa com sucesso!')
    else:
        print('Quantidade de comandos inválida')

if __name__ == '__main__':
    main()
