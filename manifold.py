import pygame
import math
import numpy as np
from pygame.locals import *

# Inicialização do Pygame
pygame.init()

# Constantes
LARGURA = 800
ALTURA = 600
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 0, 0)
VERDE = (0, 255, 0)
AZUL = (0, 0, 255)
AMARELO = (255, 255, 0)

class Ponto3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def to_array(self):
        return np.array([self.x, self.y, self.z, 1.0])

class Face:
    def __init__(self, v1, v2, v3):
        self.vertices = [v1, v2, v3]
        # Cores vibrantes e variadas
        self.cor = (np.random.randint(100, 256), 
                    np.random.randint(100, 256), 
                    np.random.randint(100, 256))

class MatrizTransformacao:
    @staticmethod
    def translacao(dx, dy, dz):
        return np.array([
            [1, 0, 0, dx],
            [0, 1, 0, dy],
            [0, 0, 1, dz],
            [0, 0, 0, 1]
        ], dtype=float)
    
    @staticmethod
    def rotacao_x(angulo):
        cos = math.cos(angulo)
        sin = math.sin(angulo)
        return np.array([
            [1, 0, 0, 0],
            [0, cos, -sin, 0],
            [0, sin, cos, 0],
            [0, 0, 0, 1]
        ], dtype=float)
    
    @staticmethod
    def rotacao_y(angulo):
        cos = math.cos(angulo)
        sin = math.sin(angulo)
        return np.array([
            [cos, 0, sin, 0],
            [0, 1, 0, 0],
            [-sin, 0, cos, 0],
            [0, 0, 0, 1]
        ], dtype=float)
    
    @staticmethod
    def rotacao_z(angulo):
        cos = math.cos(angulo)
        sin = math.sin(angulo)
        return np.array([
            [cos, -sin, 0, 0],
            [sin, cos, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=float)
    
    @staticmethod
    def escala(sx, sy, sz):
        return np.array([
            [sx, 0, 0, 0],
            [0, sy, 0, 0],
            [0, 0, sz, 0],
            [0, 0, 0, 1]
        ], dtype=float)

class Toro:
    def __init__(self, raio_maior=2.0, raio_menor=1.0, seg_u=20, seg_v=10):
        self.vertices = []
        self.faces = []
        self.matriz_modelo = np.eye(4)
        
        # Dicionário para mapear índices
        indices = {}
        
        # Criar vértices
        for i in range(seg_u):
            u = 2 * math.pi * i / seg_u
            for j in range(seg_v):
                v = 2 * math.pi * j / seg_v
                
                x = (raio_maior + raio_menor * math.cos(v)) * math.cos(u)
                y = (raio_maior + raio_menor * math.cos(v)) * math.sin(u)
                z = raio_menor * math.sin(v)
                
                indices[(i, j)] = len(self.vertices)
                self.vertices.append(Ponto3D(x, y, z))
        
        # Criar faces
        for i in range(seg_u):
            i_prox = (i + 1) % seg_u
            for j in range(seg_v):
                j_prox = (j + 1) % seg_v
                
                # Primeiro triângulo
                self.faces.append(Face(
                    indices[(i, j)],
                    indices[(i_prox, j)],
                    indices[(i, j_prox)]
                ))
                
                # Segundo triângulo
                self.faces.append(Face(
                    indices[(i_prox, j)],
                    indices[(i_prox, j_prox)],
                    indices[(i, j_prox)]
                ))

class Cubo:
    def __init__(self, tamanho=2.0):
        self.vertices = []
        self.faces = []
        self.matriz_modelo = np.eye(4)
        
        t = tamanho / 2
        vertices = [
            [-t, -t, -t], [t, -t, -t], [t, t, -t], [-t, t, -t],
            [-t, -t, t], [t, -t, t], [t, t, t], [-t, t, t]
        ]
        
        for v in vertices:
            self.vertices.append(Ponto3D(v[0], v[1], v[2]))
        
        # Faces (triângulos)
        faces = [
            (0, 1, 2), (0, 2, 3),  # Frente
            (4, 6, 5), (4, 7, 6),  # Trás
            (0, 3, 7), (0, 7, 4),  # Esquerda
            (1, 5, 6), (1, 6, 2),  # Direita
            (3, 2, 6), (3, 6, 7),  # Topo
            (0, 4, 5), (0, 5, 1)   # Base
        ]
        
        for f in faces:
            self.faces.append(Face(f[0], f[1], f[2]))

class RenderizadorSimples:
    def __init__(self, tela):
        self.tela = tela
        self.distancia_camera = 10
        self.rotacao_x = 0
        self.rotacao_y = 0
        self.escala = 200  # Fator de escala para projeção
    
    def projetar_ponto(self, ponto):
        # Aplica rotações
        # Rotação X
        y = ponto.y * math.cos(self.rotacao_x) - ponto.z * math.sin(self.rotacao_x)
        z = ponto.y * math.sin(self.rotacao_x) + ponto.z * math.cos(self.rotacao_x)
        
        # Rotação Y
        x = ponto.x * math.cos(self.rotacao_y) + z * math.sin(self.rotacao_y)
        z = -ponto.x * math.sin(self.rotacao_y) + z * math.cos(self.rotacao_y)
        
        # Projeção perspectiva simples
        if z + self.distancia_camera <= 0:
            return None
        
        fator = self.escala / (z + self.distancia_camera)
        x_proj = x * fator + LARGURA // 2
        y_proj = -y * fator + ALTURA // 2
        
        return (int(x_proj), int(y_proj))
    
    def renderizar(self, objeto):
        # Projetar todos os vértices
        pontos_proj = []
        for vertice in objeto.vertices:
            ponto_proj = self.projetar_ponto(vertice)
            pontos_proj.append(ponto_proj)
        
        # Desenhar faces
        for face in objeto.faces:
            pontos_face = []
            for idx in face.vertices:
                if pontos_proj[idx] is not None:
                    pontos_face.append(pontos_proj[idx])
            
            if len(pontos_face) == 3:
                # Desenhar face preenchida
                pygame.draw.polygon(self.tela, face.cor, pontos_face, 0)
                # Desenhar borda
                pygame.draw.polygon(self.tela, BRANCO, pontos_face, 1)

def main():
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Manifold 3D - Versão Simples")
    clock = pygame.time.Clock()
    
    # Criar objetos
    print("Criando toro...")
    toro = Toro(raio_maior=2.0, raio_menor=1.0, seg_u=24, seg_v=12)
    print(f"Toro: {len(toro.vertices)} vértices, {len(toro.faces)} faces")
    
    print("Criando cubo...")
    cubo = Cubo(tamanho=2.5)
    print(f"Cubo: {len(cubo.vertices)} vértices, {len(cubo.faces)} faces")
    
    objeto_atual = toro
    renderizador = RenderizadorSimples(tela)
    
    # Controles
    auto_rotacao = True
    mostrar_vertices = False
    fonte = pygame.font.Font(None, 24)
    
    print("\nInstruções:")
    print("- SETAS: Rotacionar")
    print("- ESPAÇO: Auto-rotação")
    print("- 1: Toro | 2: Cubo")
    print("- V: Mostrar vértices")
    print("- ESC: Sair")
    print("\nIniciando renderização...")
    
    rodando = True
    while rodando:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                rodando = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    rodando = False
                elif event.key == K_SPACE:
                    auto_rotacao = not auto_rotacao
                elif event.key == K_v:
                    mostrar_vertices = not mostrar_vertices
                elif event.key == K_1:
                    objeto_atual = toro
                elif event.key == K_2:
                    objeto_atual = cubo
        
        # Controles contínuos
        teclas = pygame.key.get_pressed()
        if teclas[K_LEFT]:
            renderizador.rotacao_y -= 0.03
        if teclas[K_RIGHT]:
            renderizador.rotacao_y += 0.03
        if teclas[K_UP]:
            renderizador.rotacao_x -= 0.03
        if teclas[K_DOWN]:
            renderizador.rotacao_x += 0.03
        
        # Auto-rotação
        if auto_rotacao:
            renderizador.rotacao_y += 0.01
        
        # Limpar tela
        tela.fill(PRETO)
        
        # Renderizar
        renderizador.renderizar(objeto_atual)
        
        # Mostrar vértices se ativado
        if mostrar_vertices:
            pontos_proj = []
            for vertice in objeto_atual.vertices:
                ponto = renderizador.projetar_ponto(vertice)
                if ponto:
                    pygame.draw.circle(tela, VERMELHO, ponto, 3)
        
        # Informações
        info = [
            f"Objeto: {'TORO' if objeto_atual == toro else 'CUBO'}",
            f"Faces: {len(objeto_atual.faces)}",
            f"Vértices: {len(objeto_atual.vertices)}",
            f"Auto-rotação: {'ON' if auto_rotacao else 'OFF'}",
            f"Mostrar vértices: {'ON' if mostrar_vertices else 'OFF'}",
            "",
            "SETAS: Rotacionar",
            "ESPAÇO: Auto-rotação",
            "V: Vértices",
            "1: Toro | 2: Cubo"
        ]
        
        y = 10
        for linha in info:
            cor = VERDE if 'ON' in linha else (VERMELHO if 'OFF' in linha else BRANCO)
            texto = fonte.render(linha, True, cor)
            tela.blit(texto, (10, y))
            y += 22
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()