#2bytes tamanho - 2 bytes ID

from sys import argv
import io
import os

def constroi_indice(arq: io.BufferedReader) -> list[tuple[int, int]]:
    '''
    forma uma tupla com os ids e os offsets
    '''
    num_registros = int.from_bytes(arq.read(4))
    chaves: list[tuple[int, int]] = []
    for _ in range(num_registros):
        offset = arq.tell()
        dados, tamanho = leia_reg(arq)
        id = (dados.split('|'))[0]
        chaves.append((id, offset))
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

if __name__ == '__main__':
    filmes = open('filmes.dat', 'rb')
    print(constroi_indice(filmes))
    print("oi")


