import pygame
import numpy as np
import random
from enum import Enum
from collections import deque
import math

# Inicialização
pygame.init()

# Configurações da tela
LARGURA, ALTURA = 1600, 1000
TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Cadeia de Suprimentos - Gráficos em Tempo Real")
FPS = 30

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA_ESCURO = (20, 20, 20)
CINZA_MEDIO = (40, 40, 40)
CINZA_CLARO = (80, 80, 80)

# Cores por camada (mais vibrantes)
CORES_CAMADA = {
    0: (255, 80, 80),    # Matéria-prima - Vermelho vibrante
    1: (255, 160, 80),   # Processamento - Laranja
    2: (255, 255, 80),   # Manufatura - Amarelo
    3: (80, 255, 80),    # Distribuição - Verde
    4: (80, 200, 255),   # Varejo - Azul
    5: (200, 80, 255),   # Consumidor - Roxo
}

# Cores para fluxos
COR_FLUXO = {
    'produto': (0, 200, 255),   # Ciano
    'dinheiro': (50, 255, 50),  # Verde
    'informacao': (255, 200, 0), # Amarelo
}

class TipoNo(Enum):
    EXTRACAO = 0
    PROCESSAMENTO = 1
    MANUFATURA = 2
    DISTRIBUICAO = 3
    VAREJO = 4
    CONSUMIDOR = 5

class No:
    def __init__(self, x, y, tipo, id):
        self.x = x
        self.y = y
        self.tipo = tipo
        self.id = id
        self.nome = f"{tipo.name}_{id}"
        
        # Capacidades e estoques
        self.capacidade = random.randint(80, 150)
        self.estoque = random.randint(20, 50)
        self.producao = random.randint(8, 20)
        self.demanda = random.randint(10, 25)
        
        # Financeiro
        self.dinheiro = random.randint(500, 1000)
        self.preco_venda = random.uniform(8, 15)
        self.custo_producao = random.uniform(3, 8)
        
        # Conectores
        self.fornecedores = []
        self.clientes = []
        
        # Status
        self.eficiencia = random.uniform(0.7, 1.0)
        
    def atualizar(self):
        # Produzir se for nó de produção
        if self.tipo != TipoNo.CONSUMIDOR:
            producao_efetiva = self.producao * self.eficiencia
            self.estoque += producao_efetiva
            self.dinheiro -= self.custo_producao * producao_efetiva
        
        # Consumir se for consumidor
        if self.tipo == TipoNo.CONSUMIDOR:
            consumo = min(self.estoque, self.demanda)
            self.estoque -= consumo
            self.dinheiro += consumo * self.preco_venda * 0.5  # Gastam dinheiro
        
        # Limitar estoque
        self.estoque = max(0, min(self.estoque, self.capacidade))
        
        # Ajustar produção baseada no estoque
        if self.estoque < self.capacidade * 0.2:
            self.producao *= 1.05
            self.preco_venda *= 1.02
        elif self.estoque > self.capacidade * 0.8:
            self.producao *= 0.95
            self.preco_venda *= 0.98
            
    def desenhar(self, tela, camada_ativa, fonte):
        if camada_ativa == -1 or camada_ativa == self.tipo.value:
            cor = CORES_CAMADA[self.tipo.value]
            
            # Tamanho baseado no estoque
            raio = 12 + int(self.estoque / 15)
            
            # Desenhar nó
            pygame.draw.circle(tela, cor, (int(self.x), int(self.y)), raio)
            pygame.draw.circle(tela, BRANCO, (int(self.x), int(self.y)), raio, 2)
            
            # Desenhar ID e estoque
            texto_id = fonte.render(f"{self.id}", True, BRANCO)
            tela.blit(texto_id, (self.x - 8, self.y - 35))
            
            texto_estoque = fonte.render(f"{self.estoque:.0f}", True, BRANCO)
            tela.blit(texto_estoque, (self.x - 10, self.y - 55))
            
            # Desenhar dinheiro
            texto_dinheiro = fonte.render(f"${self.dinheiro:.0f}", True, (100, 255, 100))
            tela.blit(texto_dinheiro, (self.x - 20, self.y + 25))

class Fluxo:
    def __init__(self, origem, destino, tipo, quantidade, valor=0):
        self.origem = origem
        self.destino = destino
        self.tipo = tipo
        self.quantidade = quantidade
        self.valor = valor
        self.progresso = 0
        self.velocidade = random.uniform(0.03, 0.06)
        
    def atualizar(self):
        self.progresso += self.velocidade
        return self.progresso >= 1
    
    def desenhar(self, tela, camada_ativa):
        if camada_ativa == -1 or camada_ativa == self.origem.tipo.value or camada_ativa == self.destino.tipo.value:
            x1, y1 = self.origem.x, self.origem.y
            x2, y2 = self.destino.x, self.destino.y
            
            x = x1 + (x2 - x1) * self.progresso
            y = y1 + (y2 - y1) * self.progresso
            
            cor = COR_FLUXO[self.tipo]
            
            # Tamanho diferente para dinheiro e produtos
            tamanho = 6 if self.tipo == 'dinheiro' else 4
            pygame.draw.circle(tela, cor, (int(x), int(y)), tamanho)
            
            # Mostrar valor nos fluxos de dinheiro
            if self.tipo == 'dinheiro' and self.valor > 0:
                fonte = pygame.font.Font(None, 14)
                texto = fonte.render(f"${self.valor:.0f}", True, (200, 255, 200))
                tela.blit(texto, (int(x) - 15, int(y) - 20))

class GraficoCamada:
    def __init__(self, x, y, largura, altura, titulo, cor, camada):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.titulo = titulo
        self.cor = cor
        self.camada = camada
        
        # Histórico de dados
        self.historico_estoque = deque(maxlen=100)
        self.historico_dinheiro = deque(maxlen=100)
        self.historico_producao = deque(maxlen=100)
        self.tempo = deque(maxlen=100)
        
        for i in range(100):
            self.tempo.append(i)
    
    def atualizar(self, nos_camada):
        # Calcular totais da camada
        estoque_total = sum(n.estoque for n in nos_camada)
        dinheiro_total = sum(n.dinheiro for n in nos_camada)
        producao_total = sum(n.producao for n in nos_camada if n.tipo != TipoNo.CONSUMIDOR)
        
        self.historico_estoque.append(estoque_total)
        self.historico_dinheiro.append(dinheiro_total)
        self.historico_producao.append(producao_total)
    
    def desenhar(self, tela, fonte_pequena):
        # Fundo do gráfico
        pygame.draw.rect(tela, CINZA_ESCURO, (self.x, self.y, self.largura, self.altura))
        pygame.draw.rect(tela, CINZA_CLARO, (self.x, self.y, self.largura, self.altura), 2)
        
        # Título da camada
        titulo_render = fonte_pequena.render(f"{self.titulo}", True, self.cor)
        tela.blit(titulo_render, (self.x + 10, self.y + 5))
        
        # Grid
        for i in range(0, self.largura, 30):
            pygame.draw.line(tela, CINZA_MEDIO, 
                           (self.x + i, self.y), 
                           (self.x + i, self.y + self.altura), 1)
        
        # Desenhar curvas
        self._desenhar_curva(tela, self.historico_estoque, self.cor, 'estoque', self.y + 30)
        self._desenhar_curva(tela, self.historico_dinheiro, (100, 255, 100), 'dinheiro', self.y + 30)
        self._desenhar_curva(tela, self.historico_producao, self.cor, 'producao', self.y + 30, dashed=True)
        
        # Legenda
        self._desenhar_legenda(tela, fonte_pequena)
        
        # Valores atuais
        if self.historico_estoque:
            estoque_atual = self.historico_estoque[-1]
            dinheiro_atual = self.historico_dinheiro[-1] if self.historico_dinheiro else 0
            
            texto_estoque = fonte_pequena.render(f"Estoque: {estoque_atual:.0f}", True, self.cor)
            texto_dinheiro = fonte_pequena.render(f"Dinheiro: ${dinheiro_atual:.0f}", True, (100, 255, 100))
            
            tela.blit(texto_estoque, (self.x + self.largura - 150, self.y + 5))
            tela.blit(texto_dinheiro, (self.x + self.largura - 150, self.y + 25))
    
    def _desenhar_curva(self, tela, historico, cor, tipo, y_base, dashed=False):
        if len(historico) < 2:
            return
        
        # Normalizar valores
        max_val = max(historico) if max(historico) > 0 else 1
        pontos = []
        
        for i, valor in enumerate(historico):
            x = self.x + (self.largura - 20) * i / 99 + 10
            y = y_base + (self.altura - 50) * (1 - valor / max_val)
            pontos.append((int(x), int(y)))
        
        # Desenhar linha
        if dashed:
            # Linha tracejada para produção
            for i in range(0, len(pontos)-1, 2):
                if i+1 < len(pontos):
                    pygame.draw.line(tela, cor, pontos[i], pontos[i+1], 2)
        else:
            pygame.draw.lines(tela, cor, False, pontos, 2)
    
    def _desenhar_legenda(self, tela, fonte):
        # Legenda das linhas
        y_leg = self.y + self.altura - 25
        
        # Estoque (sólida)
        pygame.draw.line(tela, self.cor, (self.x + 10, y_leg), (self.x + 30, y_leg), 2)
        texto = fonte.render("Estoque", True, self.cor)
        tela.blit(texto, (self.x + 35, y_leg - 8))
        
        # Dinheiro (verde)
        pygame.draw.line(tela, (100, 255, 100), (self.x + 100, y_leg), (self.x + 120, y_leg), 2)
        texto = fonte.render("Dinheiro", True, (100, 255, 100))
        tela.blit(texto, (self.x + 125, y_leg - 8))
        
        # Produção (tracejada)
        for i in range(0, 20, 4):
            pygame.draw.line(tela, self.cor, (self.x + 200 + i, y_leg), (self.x + 200 + i + 2, y_leg), 2)
        texto = fonte.render("Produção", True, self.cor)
        tela.blit(texto, (self.x + 225, y_leg - 8))

class CadeiaSuprimentos:
    def __init__(self):
        self.nos = []
        self.fluxos = []
        self.ciclo = 0
        self.camada_atual = -1
        
        # Dados agregados por camada
        self.dados_camada = {}
        
        # Criar rede e gráficos
        self.criar_rede()
        self.criar_graficos()
        
    def criar_rede(self):
        """Cria uma cadeia de suprimentos completa"""
        pos_y_camada = {
            0: 150, 1: 250, 2: 400, 3: 550, 4: 650, 5: 750
        }
        
        # Criar nós
        for tipo in TipoNo:
            num_nos = {
                TipoNo.EXTRACAO: 3,
                TipoNo.PROCESSAMENTO: 3,
                TipoNo.MANUFATURA: 3,
                TipoNo.DISTRIBUICAO: 2,
                TipoNo.VAREJO: 4,
                TipoNo.CONSUMIDOR: 5
            }[tipo]
            
            for i in range(num_nos):
                x = 150 + (LARGURA - 800) * (i + 1) / (num_nos + 1)
                y = pos_y_camada[tipo.value]
                self.nos.append(No(x, y, tipo, len(self.nos)))
        
        # Conectar nós
        for no in self.nos:
            if no.tipo.value > 0:
                fornecedores = [n for n in self.nos if n.tipo.value == no.tipo.value - 1]
                if fornecedores:
                    num_conexoes = random.randint(1, min(2, len(fornecedores)))
                    no.fornecedores = random.sample(fornecedores, num_conexoes)
            
            if no.tipo.value < 5:
                clientes = [n for n in self.nos if n.tipo.value == no.tipo.value + 1]
                if clientes:
                    num_conexoes = random.randint(1, min(2, len(clientes)))
                    no.clientes = random.sample(clientes, num_conexoes)
    
    def criar_graficos(self):
        """Cria gráficos para cada camada"""
        self.graficos = []
        
        # Posicionar gráficos na lateral direita
        for camada in range(6):
            x = LARGURA - 550
            y = 50 + camada * 140
            largura = 500
            altura = 120
            
            titulo = TipoNo(camada).name
            cor = CORES_CAMADA[camada]
            
            self.graficos.append(GraficoCamada(x, y, largura, altura, titulo, cor, camada))
    
    def atualizar_fluxos(self):
        """Cria fluxos de produtos e dinheiro"""
        for no in self.nos:
            # Fluxo de produtos
            if no.clientes and no.estoque > 15:
                for cliente in no.clientes:
                    if random.random() < 0.25:
                        quantidade = min(no.estoque * 0.15, 8)
                        valor_venda = quantidade * no.preco_venda
                        
                        no.estoque -= quantidade
                        no.dinheiro += valor_venda
                        cliente.dinheiro -= valor_venda
                        cliente.estoque += quantidade
                        
                        # Criar fluxo visual de produto
                        self.fluxos.append(Fluxo(no, cliente, 'produto', quantidade))
                        
                        # Criar fluxo visual de dinheiro (pagamento)
                        self.fluxos.append(Fluxo(cliente, no, 'dinheiro', 0, valor_venda))
            
            # Fluxo de informação (demanda)
            if no.fornecedores and no.estoque < no.capacidade * 0.4:
                if random.random() < 0.2:
                    fornecedor = random.choice(no.fornecedores)
                    self.fluxos.append(Fluxo(no, fornecedor, 'informacao', 0))
        
        # Atualizar e remover fluxos concluídos
        self.fluxos = [f for f in self.fluxos if not f.atualizar()]
    
    def atualizar_dados_camada(self):
        """Atualiza dados históricos para os gráficos"""
        for camada in range(6):
            nos_camada = [n for n in self.nos if n.tipo.value == camada]
            self.graficos[camada].atualizar(nos_camada)
    
    def desenhar_resumo_global(self, tela, fonte):
        """Desenha um resumo global de toda a cadeia"""
        x_base = 50
        y_base = ALTURA - 150
        
        # Fundo
        s = pygame.Surface((400, 130))
        s.set_alpha(200)
        s.fill(CINZA_ESCURO)
        tela.blit(s, (x_base - 10, y_base - 10))
        
        # Título
        titulo = fonte.render("RESUMO GLOBAL DA CADEIA", True, BRANCO)
        tela.blit(titulo, (x_base, y_base - 5))
        
        # Totais
        dinheiro_total = sum(n.dinheiro for n in self.nos)
        estoque_total = sum(n.estoque for n in self.nos)
        producao_total = sum(n.producao for n in self.nos if n.tipo != TipoNo.CONSUMIDOR)
        
        textos = [
            f"Ciclo: {self.ciclo}",
            f"Dinheiro Total: ${dinheiro_total:,.0f}",
            f"Estoque Total: {estoque_total:.0f}",
            f"Produção Total: {producao_total:.0f}"
        ]
        
        for i, texto in enumerate(textos):
            cor = BRANCO
            if "Dinheiro" in texto:
                cor = (100, 255, 100)
            render = fonte.render(texto, True, cor)
            tela.blit(render, (x_base, y_base + 20 + i * 25))
    
    def desenhar_controles(self, tela, fonte):
        """Desenha painel de controle"""
        x_base = LARGURA - 200
        y_base = ALTURA - 150
        
        s = pygame.Surface((180, 130))
        s.set_alpha(200)
        s.fill(CINZA_ESCURO)
        tela.blit(s, (x_base, y_base))
        
        titulo = fonte.render("CONTROLES", True, BRANCO)
        tela.blit(titulo, (x_base + 10, y_base + 5))
        
        controles = [
            "0-5: Camada específica",
            "T: Todas camadas",
            "Espaço: Pausar",
            "R: Resetar"
        ]
        
        for i, controle in enumerate(controles):
            render = fonte.render(controle, True, CINZA_CLARO)
            tela.blit(render, (x_base + 10, y_base + 35 + i * 20))
    
    def executar(self):
        clock = pygame.time.Clock()
        rodando = True
        pausado = False
        
        fonte = pygame.font.Font(None, 18)
        fonte_grafico = pygame.font.Font(None, 14)
        
        while rodando:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False
                
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_SPACE:
                        pausado = not pausado
                    
                    elif evento.key == pygame.K_r:
                        self.nos = []
                        self.fluxos = []
                        self.criar_rede()
                        self.criar_graficos()
                        self.ciclo = 0
                    
                    elif evento.key == pygame.K_t:
                        self.camada_atual = -1
                    
                    elif pygame.K_0 <= evento.key <= pygame.K_5:
                        self.camada_atual = evento.key - pygame.K_0
            
            if not pausado:
                self.ciclo += 1
                
                # Atualizar nós
                for no in self.nos:
                    no.atualizar()
                
                # Atualizar fluxos
                self.atualizar_fluxos()
                
                # Atualizar dados dos gráficos
                self.atualizar_dados_camada()
            
            # Desenhar tudo
            TELA.fill(PRETO)
            
            # Desenhar área da cadeia (esquerda)
            area_cadeia = pygame.Surface((LARGURA - 600, ALTURA))
            area_cadeia.fill(CINZA_ESCURO)
            TELA.blit(area_cadeia, (0, 0))
            
            # Linhas das camadas
            for y in [150, 250, 400, 550, 650, 750]:
                cor = CINZA_MEDIO
                if self.camada_atual != -1 and y == [150, 250, 400, 550, 650, 750][self.camada_atual]:
                    cor = CORES_CAMADA[self.camada_atual]
                pygame.draw.line(TELA, cor, (0, y), (LARGURA - 600, y), 1)
            
            # Desenhar conexões
            for no in self.nos:
                if self.camada_atual == -1 or self.camada_atual == no.tipo.value:
                    for cliente in no.clientes:
                        if self.camada_atual == -1 or self.camada_atual == cliente.tipo.value:
                            pygame.draw.line(TELA, CINZA_CLARO, (no.x, no.y), (cliente.x, cliente.y), 1)
            
            # Desenhar nós
            for no in self.nos:
                no.desenhar(TELA, self.camada_atual, fonte)
            
            # Desenhar fluxos
            for fluxo in self.fluxos:
                fluxo.desenhar(TELA, self.camada_atual)
            
            # Desenhar gráficos (direita)
            for grafico in self.graficos:
                grafico.desenhar(TELA, fonte_grafico)
            
            # Desenhar resumos
            self.desenhar_resumo_global(TELA, fonte)
            self.desenhar_controles(TELA, fonte)
            
            pygame.display.flip()
            clock.tick(FPS)
        
        pygame.quit()

# Executar
if __name__ == "__main__":
    sim = CadeiaSuprimentos()
    sim.executar()