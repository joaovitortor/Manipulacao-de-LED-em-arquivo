#2bytes tamanho - 2 bytes ID

from sys import argv
import io
import os

def constroi_indice(arq: io.BufferedRandom) -> list[tuple[int, int]]:
    '''
    forma uma tupla com todos os ids e seus offsets do arquivo em ordem crescente dos ids
    '''
    led = int.from_bytes(arq.read(4), signed=True)
    offset = arq.tell()
    arq.seek(0, os.SEEK_END)
    offset_final = arq.tell()
    arq.seek(offset)
    chaves: list[tuple[int, int]] = []
    while offset < offset_final:
        offset = arq.tell()
        dados, tamanho = leia_reg(arq)
        id = dados.split('|')[0]
        if id.isdigit():
            id_int = int(id)
            chaves.append((id_int, offset))
    chaves.sort()
    return chaves

def leia_reg(arq: io.BufferedRandom) -> tuple[str, int]:
    '''
    Lê o registro do seek atual e retorna uma tupla 
    ['registro', tamanho]
    '''
    
    tamanho = int.from_bytes(arq.read(2))
    if tamanho > 0:
        registro = arq.read(1).decode()
        if registro != '*':
            registro += arq.read(tamanho-1).decode()
            return (registro, tamanho)
        arq.read(tamanho-1)
        return ('', 0)
    return ('', 0)

def busca_binaria(chave: int, indice: list[tuple[int, int]]) -> int:
    '''A função recebe uma chave(ID) e um índice que contém tuplas(dados, tam) e retorna o byte-offset.'''
    i = 0
    f = len(indice) - 1
    while i <= f:
        m = (i + f)//2
        if indice[m][0] == chave:
            return indice[m][1]
        if indice[m][0] < chave:
            i = m + 1
        else: 
            f = m - 1
    return -1

def le_e_imprime(arq: io.BufferedRandom, offset: int) -> None:
    '''
    Imprime um registro 
    '''
    arq.seek(offset)
    dados, tamanho = leia_reg(arq)
    registros = dados.split('|')
    for registro in registros:
        print(registro)

def remove_id(arq: io.BufferedRandom, id: int, indice: list[tuple[int, int]]) -> None:
    if busca_binaria(id, indice) != -1:
        offset = busca_binaria(id, indice)
        arq.seek(offset)
        tam = int.from_bytes(arq.read(2))
        indice.remove((id, busca_binaria(id, indice)))
        arq.write(b'*')
        insere_led(arq, tam, offset)
    else:
        print("ID não existe. Tente novamente")


def insere_led(arq: io.BufferedRandom, tam_novo: int, offset_novo: int) -> None:
    '''A função insere o novo elemento que foi removido na LED mantendo-a ordenada'''
    led = leia_led(arq)
    i = 0
    tamanho_led = len(led) - 1 #9
    while led[i][1] < tam_novo and i < tamanho_led:
        i += 1

    led.append((offset_novo, tam_novo))
    if i == 0:
        arq.seek(0)
        arq.write(offset_novo.to_bytes(4, signed=True))
        escreve_fragmentacao(arq, offset_novo, led[i][0])
        #escreve o novo no cabeçalho
        #escreve na nova frag do offset do i = 0 
        i == 0
    elif i == tamanho_led:
        #arq.seek(led[i-1][0])
        #arq.read(3)
        #offset_ultimo = int.from_bytes(arq.read(4))
        #arq.seek(offset_ultimo)
        #arq.read(3)
        #arq.write(offset_novo.to_bytes(4, signed=True))
        ##led[i][0] = -1
        escreve_fragmentacao(arq, led[i-1][0], offset_novo)
        escreve_fragmentacao(arq, offset_novo, -1)
        #escreve na posição i o offset da nova frag
        #na nova frag coloca offset_prox = -1
        #significa que percorreu toda a lista, o frag_novo aponta para -1
    else:
        escreve_fragmentacao(arq, led[i-1][0], offset_novo)
        escreve_fragmentacao(arq, offset_novo, led[i][0])
        #precisa colocar no registro: o (i -1) aponta para a frag_nova e a frag_nova aponta para frag i
        #escreve na frag i - 1 a posicao da nova frag (led[i-1][0] #offset da posicao i - 1)
        #escreve na nova_frag a posicao da frag i
    led = leia_led(arq)


def escreve_fragmentacao(arq: io.BufferedRandom, offset_frag: int, offset_prox_frag: int) -> None:
    arq.seek(offset_frag)
    arq.read(3)
    arq.write(offset_prox_frag.to_bytes(4, signed=True))

def leia_led(arq: io.BufferedRandom) -> list[tuple[int, int]]:
    '''
    A função lê o cabeça da led e retorna uma lista contendo todas as fragmentações na ordem
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
    #LED -> [offset: 1850, tam: 90] -> [offset: 477, tam: 92] -> [offset: 1942, tam: 109] -> fim
    #Total: 3 espacos disponiveis
    led = leia_led(arq)
    texto = ''
    for offset, tam in led:
        if offset == -1:
            texto += 'fim'
        else:
            texto += f'[offset: {offset}, tam: {tam}] -> '
    texto += f'\nTotal de espaços: {len(led)-1}'
    print(texto)

    
if __name__ == '__main__':
    filmes = open('filmes.dat', 'r+b')
    indices = constroi_indice(filmes)
    remove_id(filmes, 29, indices)
    print(busca_binaria(29, indices))
    remove_id(filmes, 20, indices)
    remove_id(filmes, 123, indices)
    remove_id(filmes, 85, indices)
    remove_id(filmes, 114, indices)
    remove_id(filmes, 160, indices)
    imprime_led(filmes)

