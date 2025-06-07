#2bytes tamanho - 2 bytes ID

from sys import argv
import io
import os

def constroi_indice(arq: io.BufferedReader) -> list[tuple[int, int]]:
    '''
    forma uma tupla com os ids e os offsets
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

def leia_reg(arq: io.BufferedReader) -> tuple[str, int]:
    tamanho = int.from_bytes(arq.read(2))
    if tamanho > 0:
        registro = arq.read(tamanho).decode()
        return (registro, tamanho)
    return ('', 0)

def busca():
    pass

def busca_binaria(chave: int, indice: list[tuple[int, int]]) -> int:
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

def le_e_imprime(arq: io.BufferedReader, offset: int) -> None:
    arq.seek(offset)
    dados, tamanho = leia_reg(arq)
    registros = dados.split('|')
    for registro in registros:
        print(registro)






def le_e_imprime_led(arq: io.BufferedReader) -> None:
    # talvez separar a função em duas 
    arq.seek(0)
    cabeca = int.from_bytes(arq.read(4), signed=True)
    led: list[int] = []
    led.append(cabeca)
    while cabeca != -1:
        arq.seek(cabeca)
        arq.read(3)
        cabeca = int.from_bytes(arq.read(4), signed=True)
        led.append(cabeca)
    


if __name__ == '__main__':
    filmes = open('filmes.dat', 'rb')
    indices = constroi_indice(filmes)
    le_e_imprime(filmes, busca_binaria(29, indices))

    #print(int.from_bytes(filmes.read(4), signed=True))


