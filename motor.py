import pygame
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

# Inicialização
pygame.init()

# Constantes
LARGURA, ALTURA = 1200, 700
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (255, 80, 80)
VERDE = (80, 255, 80)
AZUL = (80, 150, 255)
AMARELO = (255, 255, 80)
CINZA = (40, 40, 40)
CINZA_CLARO = (100, 100, 100)
CINZA_ESCURO = (25, 25, 25)
ROXO = (180, 80, 255)

@dataclass
class Ponto:
    x: float
    y: float
    id: int
    selected: bool = False
    
class RegiaoPoligonal:  # inclusive com furos
    def __init__(self):
        self.pontos_externos: List[Ponto] = []
        self.furos: List[List[Ponto]] = []
        self.contador_id = 0
        
    def adicionar_ponto_externo(self, x, y):
        ponto = Ponto(x, y, self.contador_id)
        self.pontos_externos.append(ponto)
        self.contador_id += 1
        
    def adicionar_furo(self):
        self.furos.append([])
        
    def adicionar_ponto_furo(self, indice_furo, x, y):
        if 0 <= indice_furo < len(self.furos):
            ponto = Ponto(x, y, self.contador_id)
            self.furos[indice_furo].append(ponto)
            self.contador_id += 1
    
    def desenhar(self, screen):
        # Desenhar polígono externo
        if len(self.pontos_externos) >= 3:
            pontos_ext = [(p.x, p.y) for p in self.pontos_externos]
            pygame.draw.polygon(screen, (0, 80, 40), pontos_ext)
            pygame.draw.polygon(screen, VERDE, pontos_ext, 2)
            
        # Desenhar furos
        for furo in self.furos:
            if len(furo) >= 3:
                pontos_furo = [(p.x, p.y) for p in furo]
                pygame.draw.polygon(screen, CINZA_ESCURO, pontos_furo)
                pygame.draw.polygon(screen, VERMELHO, pontos_furo, 2)

class ListaPontosIndependente:
    def __init__(self, x, y, largura, altura):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.pontos: List[Ponto] = []
        self.contador_id = 0
        self.selecionado = None
        self.rolagem = 0
        self.fonte = pygame.font.Font(None, 20)
        self.fonte_titulo = pygame.font.Font(None, 24)
        
    def adicionar_ponto(self, x, y):
        ponto = Ponto(x, y, self.contador_id)
        self.pontos.append(ponto)
        self.contador_id += 1
        return ponto
    
    def remover_ponto(self, id_ponto):
        for i, ponto in enumerate(self.pontos):
            if ponto.id == id_ponto:
                del self.pontos[i]
                if self.selecionado and self.selecionado.id == id_ponto:
                    self.selecionado = None
                return True
        return False
    
    def selecionar_ponto(self, x, y, raio=15):
        # Primeiro desmarcar todos
        self.desmarcar_todos()
        
        # Procurar ponto próximo
        for ponto in self.pontos:
            if math.hypot(ponto.x - x, ponto.y - y) < raio:
                ponto.selected = True
                self.selecionado = ponto
                return ponto
        return None
    
    def selecionar_por_id_lista(self, index):
        """Seleciona ponto pelo índice na lista"""
        self.desmarcar_todos()
        if 0 <= index < len(self.pontos):
            self.pontos[index].selected = True
            self.selecionado = self.pontos[index]
            return True
        return False
    
    def desmarcar_todos(self):
        for ponto in self.pontos:
            ponto.selected = False
        self.selecionado = None
    
    def desenhar_pontos(self, screen):
        """Desenha os pontos no mapa"""
        for ponto in self.pontos:
            cor = VERMELHO if ponto.selected else AZUL
            pygame.draw.circle(screen, cor, (int(ponto.x), int(ponto.y)), 6)
            pygame.draw.circle(screen, BRANCO, (int(ponto.x), int(ponto.y)), 6, 1)
    
    def desenhar_lista(self, screen):
        # Fundo da lista
        pygame.draw.rect(screen, CINZA, (self.x, self.y, self.largura, self.altura))
        pygame.draw.rect(screen, CINZA_CLARO, (self.x, self.y, self.largura, self.altura), 2)
        
        # Título
        titulo = self.fonte_titulo.render("PONTOS INDEPENDENTES", True, BRANCO)
        screen.blit(titulo, (self.x + 10, self.y + 10))
        
        # Instruções
        instrucoes = [
            "Clique no mapa: adiciona ponto",
            "Clique na lista: seleciona",
            "Delete: remove selecionado",
            "ESC: desmarcar todos"
        ]
        for i, inst in enumerate(instrucoes):
            texto = self.fonte.render(inst, True, CINZA_CLARO)
            screen.blit(texto, (self.x + 10, self.y + 40 + i * 18))
        
        y_offset = self.y + 120 - self.rolagem
        
        # Cabeçalho da lista
        cab = self.fonte.render(f"--- {len(self.pontos)} pontos ---", True, AMARELO)
        screen.blit(cab, (self.x + 10, y_offset))
        y_offset += 25
        
        # Listar pontos
        for i, ponto in enumerate(self.pontos):
            if y_offset + 20 > self.y and y_offset < self.y + self.altura:
                cor = VERMELHO if ponto.selected else BRANCO
                
                if ponto.selected:
                    pygame.draw.rect(screen, CINZA_ESCURO, (self.x + 5, y_offset - 2, self.largura - 10, 22))
                
                texto = f"{i}: Ponto {ponto.id} ({int(ponto.x)}, {int(ponto.y)})"
                render = self.fonte.render(texto, True, cor)
                screen.blit(render, (self.x + 20, y_offset))
            y_offset += 22
        
        # Barra de rolagem
        total_height = len(self.pontos) * 22 + 45
        if total_height > self.altura:
            altura_barra = self.altura * (self.altura / total_height)
            pos_barra = self.y + 120 + (self.rolagem / total_height) * (self.altura - altura_barra)
            pygame.draw.rect(screen, CINZA_CLARO, 
                           (self.x + self.largura - 10, pos_barra, 5, altura_barra))
    
    def handle_click_lista(self, x, y):
        """Processa clique na lista para selecionar ponto"""
        if x < self.x or x > self.x + self.largura or y < self.y or y > self.y + self.altura:
            return False
        
        y_local = y - self.y - 120 + self.rolagem
        y_offset = 25  # Pular cabeçalho
        
        for i, ponto in enumerate(self.pontos):
            if y_offset <= y_local <= y_offset + 20:
                self.selecionar_por_id_lista(i)
                return True
            y_offset += 22
        
        return False

class Simulacao:
    def __init__(self):
        self.poligono_mapa = RegiaoPoligonal()
        self.lista_pontos = ListaPontosIndependente(LARGURA - 350, 50, 320, ALTURA - 100)
        self.arrastando = False
        
    def setup(self):
        self.screen = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Pontos Independentes + Polígono Fixo")
        self.clock = pygame.time.Clock()
        
        # POLÍGONO FIXO - não vai ser alterado pelos cliques
        self.poligono_mapa.adicionar_ponto_externo(200, 200)
        self.poligono_mapa.adicionar_ponto_externo(500, 150)
        self.poligono_mapa.adicionar_ponto_externo(550, 350)
        self.poligono_mapa.adicionar_ponto_externo(300, 400)
        self.poligono_mapa.adicionar_ponto_externo(150, 300)
        
        # Adicionar um furo
        self.poligono_mapa.adicionar_furo()
        self.poligono_mapa.adicionar_ponto_furo(0, 300, 250)
        self.poligono_mapa.adicionar_ponto_furo(0, 400, 250)
        self.poligono_mapa.adicionar_ponto_furo(0, 350, 300)
        
        # Adicionar alguns pontos independentes de exemplo
        self.lista_pontos.adicionar_ponto(100, 100)
        self.lista_pontos.adicionar_ponto(600, 200)
        self.lista_pontos.adicionar_ponto(400, 500)
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clique esquerdo
                    x, y = event.pos
                    
                    # Verificar se clicou na lista
                    if self.lista_pontos.handle_click_lista(x, y):
                        pass
                    # Verificar se clicou em algum ponto existente
                    elif x < LARGURA - 360:  # Área do mapa
                        ponto_sel = self.lista_pontos.selecionar_ponto(x, y)
                        if ponto_sel:
                            self.arrastando = True
                        else:
                            # ADICIONAR PONTO NOVO (independente do polígono)
                            self.lista_pontos.adicionar_ponto(x, y)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.arrastando = False
            
            elif event.type == pygame.MOUSEMOTION:
                if self.arrastando and self.lista_pontos.selecionado:
                    x, y = event.pos
                    if x < LARGURA - 360:  # Só arrastar no mapa
                        self.lista_pontos.selecionado.x = x
                        self.lista_pontos.selecionado.y = y
            
            elif event.type == pygame.MOUSEWHEEL:
                self.lista_pontos.rolagem -= event.y * 20
                self.lista_pontos.rolagem = max(0, self.lista_pontos.rolagem)
                self.lista_pontos.rolagem = min(self.lista_pontos.rolagem, 
                                               max(0, len(self.lista_pontos.pontos) * 22 + 45 - self.lista_pontos.altura))
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DELETE:
                    if self.lista_pontos.selecionado:
                        self.lista_pontos.remover_ponto(self.lista_pontos.selecionado.id)

                elif event.key == pygame.K_ESCAPE:
                    self.lista_pontos.desmarcar_todos()
        
        return True
    
    def update(self, dt):
        pass
    
    def render(self):
        # Limpar tela
        self.screen.fill(CINZA_ESCURO)
        
        # Área do mapa
        mapa_rect = pygame.Rect(0, 0, LARGURA - 360, ALTURA)
        pygame.draw.rect(self.screen, (20, 20, 30), mapa_rect)
        
        # Desenhar grade
        for x in range(0, LARGURA - 360, 50):
            pygame.draw.line(self.screen, CINZA, (x, 0), (x, ALTURA), 1)
        for y in range(0, ALTURA, 50):
            pygame.draw.line(self.screen, CINZA, (0, y), (LARGURA - 360, y), 1)
        
        # Desenhar POLÍGONO FIXO (não é alterado pelos cliques)
        self.poligono_mapa.desenhar(self.screen)
        
        # Desenhar PONTOS INDEPENDENTES (adicionados pelos cliques)
        self.lista_pontos.desenhar_pontos(self.screen)
        
        # Instruções
        fonte = pygame.font.Font(None, 20)
        texto1 = fonte.render("Clique no mapa: ADICIONA PONTO (independente do polígono)", True, BRANCO)
        texto2 = fonte.render(f"Total de pontos: {len(self.lista_pontos.pontos)}", True, AMARELO)
        self.screen.blit(texto1, (20, 20))
        self.screen.blit(texto2, (20, 50))
        
        # Desenhar lista de pontos
        self.lista_pontos.desenhar_lista(self.screen)
        
        pygame.display.flip()
    
    def executar(self):
        self.setup()
        rodando = True
        
        while rodando:
            dt = self.clock.tick(60) / 1000.0
            rodando = self.handle_events()
            self.update(dt)
            self.render()
        
        pygame.quit()

# Executar
if __name__ == "__main__":
    sim = Simulacao()
    sim.executar()