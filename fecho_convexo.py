import random
import math

def ponto_aleatorio():
    x = math.floor(100 * random.random())
    y = math.floor(100 * random.random())
    return (x, y)

def achar_centro(pontos):
    n = len(pontos)
    soma_x = 0
    soma_y = 0

    for x, y in pontos:
        soma_x += x
        soma_y += y

    return (soma_x / n, soma_y / n)

def distancia(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def ordenar_por_distancia(pontos):
    centro = achar_centro(pontos)
    print("Centro:", centro, "\n")

    # (indice_original, ponto, distancia)
    dados = [(i, p, distancia(centro, p)) for i, p in enumerate(pontos)]

    # ordenar pela distância
    dados_ordenados = sorted(dados, key=lambda x: x[2])

    for dado in dados_ordenados:
        print (dado)
    print()
    return dados_ordenados

def f(x):
    a = 1/4
    b = -1/2

    y = a*x+b
    return y

def main():
    n = 20
    pontos = [ponto_aleatorio() for _ in range(n)]
    print("Pontos:", pontos, "\n")

    pontos_ordenados = ordenar_por_distancia(pontos)
    i_min,p_min,d_min = pontos_ordenados[0]
    i_max,p_max,d_max = pontos_ordenados[-1]
    
    

if __name__ == "__main__":
    main()