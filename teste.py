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
        dados, tamanho = leia_reg(arq)
        id = dados.split('|')[0]
        #if id.isdigit():
        chaves.append((int(id), offset))
        print(arq.tell())
        leia_nulo(arq, arq.tell()) #11929
        print(arq.tell())
        offset = arq.tell()
    print('Final:', offset_final)
    chaves.sort()
    return chaves

def insere_indice() -> None:
    pass

def leia_nulo(arq: io.BufferedRandom, offset: int):
    #Enquanto campo == b'0' e campo != b'|' e campo != b''
    #Então, offset_atual = arq.tell() - 5
    arq.seek(offset)
    offset_atual = arq.tell()
    campo = arq.read(1)
    if campo != b'':
        while campo == b'\0' and campo != b'|' and campo != b'':
            campo = arq.read(1)
        offset_atual = arq.tell() - 2
        arq.seek(offset_atual)
    else: 
        return offset_atual


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


def remove_registro(arq: io.BufferedRandom, id: int, indice: list[tuple[int, int]]) -> None:
    '''
    Remove o id do arq, fazendo a busca pelo id na lista de indices
    '''
    if busca_binaria(id, indice) != -1:
        offset = busca_binaria(id, indice)
        arq.seek(offset)
        tam = int.from_bytes(arq.read(2))
        indice.remove((id, busca_binaria(id, indice)))
        arq.write(b'*')
        insere_led(arq, tam, offset)
    else:
        print("ID não existe. Tente novamente")

def insere_registro(arq: io.BufferedRandom, registro: str, indices: list[tuple[int, int]]):
    '''
    
    
    Insere o registro
    '''
    tam_reg = len(registro)
    led = leia_led(arq)
    if led[0][0] == -1:
        #insere no final do arq
        offset = arq.seek(0, os.SEEK_END).tell()
        escreve_arq(arq, offset, registro, 0)
        id = int(registro.split('|')[0])
        indices.append((id, offset))
    else:
        i = 0
        while led[i][1] < tam_reg and i < len(led) -1:
            i += 1
        diferenca = led[i][1] - tam_reg - 2
        offset_insere = led[i][0]
        if i == 0:
            print('ENTROU INSERIR NO CABEÇALHO')
            #insere no offset que estava no cabeçalho
            escreve_arq(arq, offset_insere, registro, diferenca)
            #altera o cabeçalho
            altera_led(arq, led, 0, led[i+1][0])
        elif i == len(led) - 1:
            #Insere no final e não é necessário alterar a led
            print("ENTROU INSERIR FIMMMMM")
            arq.seek(0, os.SEEK_END)
            #tamanho_bytes = len(registro).to_bytes(2)
            #registro_bytes = registro.encode()
            #arq.write(tamanho_bytes)
            #arq.write(registro_bytes)
            offset_final = arq.tell()
            escreve_arq(arq, offset_final, registro, 0)
        else:
            print("ENTROU INSERIR MEIOOOOO!!!")
            #insere no meio
            escreve_arq(arq, offset_insere, registro, diferenca)
            #Altera a ordem da LED
            altera_led(arq, led, led[i-1][0], led[i+1][0])
    indices.sort()
            
def escreve_registro(arq: io.BufferedRandom, offset_insere: int, registro: str, diferenca_tamanho: int) -> None:
    '''
    A função recebe o offset para a inserção e o conteúdo do registro, escrevendo-o no arquivo.
    '''
    tamanho_bytes = len(registro).to_bytes(2)
    arq.seek(offset_insere)
    registro_bytes = registro.encode()
    arq.write(tamanho_bytes + registro_bytes)
    if diferenca_tamanho > 0:
        arq.write(b'\0' * diferenca_tamanho)

def altera_led(arq: io.BufferedRandom, led: list[tuple[int, int]], offset_anterior: int, offset_prox: int) -> None:
    '''
        Ordena a LED
        Faz o offset_anterior apontar para o offset_prox, no caso estamos removendo um offset da led
        se o offset removido estiver no cabecalho, reescreve o offset_prox no cabecalho mesmo
    '''
    arq.seek(offset_anterior)
    if offset_anterior != 0:
        arq.read(3)
    arq.write(offset_prox.to_bytes(4, signed = True))
    led = leia_led(arq)


def insere_led(arq: io.BufferedRandom, tam_novo: int, offset_novo: int) -> None:
    '''A função insere o novo elemento que foi removido na LED mantendo-a ordenada'''
    led = leia_led(arq)
    i = 0
    tamanho_led = len(led) - 1 #9
    while led[i][1] < tam_novo and i < tamanho_led:
        i += 1

    led.append((offset_novo, tam_novo))
    if i == 0:
        escreve_fragmentacao(arq, 0, offset_novo)
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
    if offset_frag != 0:
        arq.read(3)
    arq.write(offset_prox_frag.to_bytes(4, signed=True))

def leia_led(arq: io.BufferedRandom) -> list[tuple[int, int]]:
    '''
    A função lê o cabeça da led no arquivo e retorna uma lista contendo todas as fragmentações na ordem
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
    #led = leia_led(filmes)
    indices = constroi_indice(filmes)
    print(indices)
    remove_registro(filmes, 29, indices)
    #print(busca_binaria(29, indices))
    #remove_registro(filmes, 20, indices)
    #remove_registro(filmes, 123, indices)
    #remove_registro(filmes, 85, indices)
    #remove_registro(filmes, 114, indices)
    #remove_registro(filmes, 160, indices)
    filme = '137|CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC|Ang Lee|2000|Ação|120|Chow Yun|'
    #led = leia_led(filmes)
    print(len(filme))
    #insere_arq(filmes, filme)
    imprime_led(filmes)


