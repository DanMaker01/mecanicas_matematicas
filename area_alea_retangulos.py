import random
import statistics

def gerar_retangulos(q, largura_max=100, altura_max=100):
    retangulos = []
    areas = []

    for _ in range(q):
        largura = random.uniform(0, largura_max)
        altura = random.uniform(0, altura_max)
        area = largura * altura

        retangulos.append((largura, altura))
        areas.append(area)

    return retangulos, areas


def analisar_areas(areas):
    print(f"Quantidade: {len(areas)}")
    print(f"Área média: {statistics.mean(areas):.3f}")
    print(f"Área mínima: {min(areas):.3f}")
    print(f"Área máxima: {max(areas):.3f}")
    print(f"Desvio padrão: {statistics.stdev(areas):.3f}")


if __name__ == "__main__":
    q = 100000  # quantidade de retângulos

    retangulos, areas = gerar_retangulos(q)
    analisar_areas(areas)

    # Mostrar alguns exemplos
    print("\nPrimeiros 10 retângulos (largura, altura, área):")
    for i in range(10):
        l, a = retangulos[i]
        print(f"{i+1}: ({l:.2f}, {a:.2f}) -> área = {l*a:.2f}")