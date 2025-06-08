from sys import argv
import io
import os

def constroi_indice(arq: io.BufferedRandom) -> list[tuple[int, int]]:
    '''
    forma uma tupla com todos os ids e seus offsets do arquivo em ordem crescente dos ids
    '''
    arq.seek(0)
    led = int.from_bytes(arq.read(4), signed=True)
    offset = arq.tell()
    arq.seek(0, os.SEEK_END)
    offset_final = arq.tell()
    arq.seek(offset)
    chaves: list[tuple[int, int]] = []
    while offset < offset_final:
        dados, tamanho = leia_reg(arq)
        print(dados)
        id = dados.split('|')[0]
        if id.isdigit():
            chaves.append((int(id), offset))
        #print(arq.tell())
        leia_nulo(arq, arq.tell()) #11929
        #print(arq.tell())
        offset = arq.tell()
    chaves.sort()
    return chaves

def insere_indice(id: int, offset: str, indice: list[tuple[int, int]]) -> None:
    '''
    Insere um elemento (id, offset) na lista de indices e ordena
    '''
    indice.append((id, offset))
    indice.sort()

def leia_nulo(arq: io.BufferedRandom, offset: int) -> None:
    '''
    lê os bytes nulos da posição do *offset* e move o ponteiro para a posição do ultimo caractere nao nulo sequencialmente no arquivo 
    '''
    arq.seek(offset)
    offset_atual = arq.tell()
    campo = arq.read(2)
    if campo == b'\0\0':
        while campo != b'|' and campo != b'':
            campo = arq.read(1)
            if campo != b'':
                offset_atual = arq.tell()
    arq.seek(offset_atual)
    

    #if arq.read(2) == :
    #volta uma casa e le dois 
    # \0 \0 \0 \0 12 \0 04 |
    # 12 45 \0 187 


def leia_reg(arq: io.BufferedRandom) -> tuple[str, int]:
    ''' 
    Lê o registro do seek atual e retorna uma tupla ['registro', tamanho]
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
        insere_fragmentacao(arq, tam, offset)
    else:
        print("ID não existe. Tente novamente")

def insere_registro(arq: io.BufferedRandom, registro: str, indice: list[tuple[int, int]]) -> None:
    '''
    Insere o registro
    '''
    id = int(registro.split('|')[0])
    if (busca_binaria(id, indice)) == -1:
        tam_reg = len(registro) + 2
        led = leia_led(arq)

        if led[0][0] == -1: #insere no final do arq
            arq.seek(0, os.SEEK_END)
            offset = arq.tell()
            escreve_registro(arq, offset, registro, 0)
            insere_indice(id, offset, indice)
        else:
            i = 0
            while led[i][1] < tam_reg and i < len(led) -1:
                i += 1
            diferenca = led[i][1] - tam_reg - 2
            offset_insere = led[i][0]

            if i == 0: #insere no cabeçalho
                print('ENTROU INSERIR NO CABEÇALHO')
                escreve_registro(arq, offset_insere, registro, diferenca)
                insere_indice(id, offset_insere, indice)
                ordena_led(arq, led, 0, led[i+1][0])

            elif i == len(led) - 1: #insere no fim
                print("ENTROU INSERIR FIMMMMM")
                arq.seek(0, os.SEEK_END)
                offset_final = arq.tell()
                escreve_registro(arq, offset_final, registro, 0)
                insere_indice(id, offset_final, indice)

            else: #Insere no meio
                print("ENTROU INSERIR MEIOOOOO!!!")
                escreve_registro(arq, offset_insere, registro, diferenca)
                insere_indice(id, offset_insere, indice)
                ordena_led(arq, led, led[i-1][0], led[i+1][0])
    else:
        print("ID já existe no arquivo. Tente inserir com outro ID")
            
def escreve_registro(arq: io.BufferedRandom, offset_insere: int, registro: str, diferenca_tamanho: int) -> None:
    '''
    A função recebe o offset para a inserção e o conteúdo do registro, escrevendo-o no arquivo.
    '''
    tamanho_bytes = (len(registro) + 2).to_bytes(2)
    arq.seek(offset_insere)
    registro_bytes = registro.encode()
    arq.write(tamanho_bytes + registro_bytes)
    if diferenca_tamanho > 0:
        vazios = b'\0' * diferenca_tamanho
        arq.write(vazios)


def ordena_led(arq: io.BufferedRandom, led: list[tuple[int, int]], offset_anterior: int, offset_prox: int) -> None:
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

def insere_fragmentacao(arq: io.BufferedRandom, tam_novo: int, offset_novo: int) -> None:
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
    '''A função escreve a posição da próxima fragmentação'''
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
    '''
    A função imprime a led da seguinte forma:
    LED -> [offset: 1850, tam: 90] -> [offset: 477, tam: 92] -> [offset: 1942, tam: 109] -> fim
    Total: 3 espacos disponiveis
    '''
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
    indice = constroi_indice(filmes)
    #led = leia_led(filmes)
    #remove_registro(filmes, 29, indice)
    #remove_registro(filmes, 20, indice)
    #remove_registro(filmes, 123, indice)
    #remove_registro(filmes, 85, indice)
    #remove_registro(filmes, 114, indice)
    #remove_registro(filmes, 160, indice)
    #filme = '137|CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC|Ang Lee|2000|Ação|120|Chow Yun|'
    #led = leia_led(filmes)
    #print(len(filme))
    #insere_registro(filmes, filme, indice)
    #imprime_led(filmes)
    #print(busca_binaria(32, indice))
    #print(indice)

    busca_binaria(113, indice)
    busca_binaria(34, indice)
    busca_binaria(221, indice)
    insere_registro(filmes, '12|O Silêncio dos Inocentes|Jonathan Demme|1991|Crime, Drama, Suspense|118|Jodie Foster, Anthony Hopkins, Lawrence A. Bonney|', indice)
    remove_registro(filmes, 85, indice) #Em algum lugar do passado
    remove_registro(filmes, 20, indice) #Forrest Gump
    remove_registro(filmes, 311, indice)
    remove_registro(filmes, 123, indice) #As aventuras de pi
    #remove_registro(filmes, 7, indice) #A origem
    remove_registro(filmes, 114, indice)
    insere_registro(filmes, '72|O Senhor dos Anéis: O Retorno do Rei|Peter Jackson|2003|Aventura, Fantasia|201|Elijah Wood, Ian McKellen, Viggo Mortensen|', indice)
    #insere_registro(filmes, '150|O Tigre e o Dragão|Ang Lee|2000|Ação, Aventura, Fantasia|120|Chow Yun|', indice)
    insere_registro(filmes, "47|Jurassic World|Colin Trevorrow|2015|Ação, Aventura, Ficção Científica|124|Chris Pratt, Bryce Dallas Howard, Vincent D'Onofrio|", indice)
    remove_registro(filmes, 160, indice) #Capitão Fantástico
    #busca_binaria(150, indice)
    remove_registro(filmes, 12, indice) 
    #busca_binaria(29, indice)
    #busca_binaria(7, indice)
    #insere_registro(filmes, '44|Como Treinar o Seu Dragão|Dean DeBlois, Chris Sanders|2010|Animação, Aventura, Família|98|Jay Baruchel, Gerard Butler, Craig Ferguson|', indice)
    #insere_registro(filmes,'126|Corações de Ferro|David Ayer|2014|Ação, Drama, Guerra|134|Brad Pitt, Shia LaBeouf, Logan Lerman|', indice)
   
    print(constroi_indice(filmes))
    print('-----------------------------------------------------------------')
    imprime_led(filmes)
    print('-----------------------------------------------------------------')

    '''
    b 113
    b 34
    b 221
    i 12|O Silêncio dos Inocentes|Jonathan Demme|1991|Crime, Drama, Suspense|118|Jodie Foster, Anthony Hopkins, Lawrence A. Bonney|
    r 85
    r 20
    r 311
    r 123
    r 7
    r 114
    i 72|O Senhor dos Anéis: O Retorno do Rei|Peter Jackson|2003|Aventura, Fantasia|201|Elijah Wood, Ian McKellen, Viggo Mortensen|
    i 150|O Tigre e o Dragão|Ang Lee|2000|Ação, Aventura, Fantasia|120|Chow Yun|
    i 47|Jurassic World|Colin Trevorrow|2015|Ação, Aventura, Ficção Científica|124|Chris Pratt, Bryce Dallas Howard, Vincent D'Onofrio|
    r 160
    b 150
    r 12
    b 29
    b 7
    i 44|Como Treinar o Seu Dragão|Dean DeBlois, Chris Sanders|2010|Animação, Aventura, Família|98|Jay Baruchel, Gerard Butler, Craig Ferguson|
    i 126|Corações de Ferro|David Ayer|2014|Ação, Drama, Guerra|134|Brad Pitt, Shia LaBeouf, Logan Lerman|
    '''


    '''
    Busca pelo registro de chave "20"
    20|Forrest Gump|Robert Zemeckis|1994|Drama, Romance|142|Tom Hanks, Robin Wright, Gary Sinise (93 bytes)
    Inserção do registro de chave "66" (77 bytes)
    Local: fim do arquivo
    Remoção do registro de chave "153"
    Registro removido! (92 bytes)
    Local: offset = 477 bytes (0x1dd)
    Remoção do registro de chave "230"
    Erro: registro não encontrado!
    Inserção do registro de chave "11" (97 bytes)
    Local: fim do arquivo
    Inserção do registro de chave "150" (77 bytes)
    Tamanho do espaço reutilizado: 92 bytes
    Local: offset = 477 bytes (0x1dd)'''