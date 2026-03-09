import pygame
import numpy as np

# -----------------------------
# WaveField
# -----------------------------
class WaveField:
    def __init__(self, N, c=6.9, dt=0.1, alpha=0.0, damping=0.99):
        self.N = N
        self.c = c
        self.dt = dt
        self.alpha = alpha
        self.damping = damping
        self.u = np.zeros((N,N), dtype=np.float32)
        self.u_old = np.zeros((N,N), dtype=np.float32)
        self.first_step = True

    def step(self):
        lap = (
            np.roll(self.u, 1, axis=0) + np.roll(self.u, -1, axis=0) +
            np.roll(self.u, 1, axis=1) + np.roll(self.u, -1, axis=1) -
            4*self.u
        )
        if self.first_step:
            u_new = self.u + (self.c*self.dt)**2 * lap + self.alpha*lap
            self.first_step = False
        else:
            u_new = (2*self.u - self.u_old + (self.c*self.dt)**2 * lap) + self.alpha*lap

        # Bordas
        u_new[0,:] = u_new[-1,:] = u_new[:,0] = u_new[:,-1] = 0.0
        u_new *= self.damping

        self.u_old[:] = self.u
        self.u[:] = u_new

# -----------------------------
# Player com controles melhorados
# -----------------------------
class Player:
    def __init__(self, N, intensity=1.0, speed=1.0):
        self.N = N
        self.x = N / 4
        self.y = N / 4
        self.original_intensity = intensity
        self.intensity = intensity
        self.base_speed = speed
        self.speed = speed
        self.hidden = False
        self.mode = "normal"  # normal, turbo, stealth
        
        # Estados dos botões
        self.keys_pressed = {}
        self.mouse_buttons = [False, False, False]
        self.mouse_pos = (0, 0)

    def update(self, wavefield, keys, mouse_buttons, mouse_pos):
        # Reset estados
        dx, dy = 0.0, 0.0
        self.speed = self.base_speed
        self.intensity = self.original_intensity
        self.mode = "normal"
        
        # Movimento básico com setas
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += self.speed
        
        # Modificadores de movimento
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.speed *= 2  # Turbo
            self.mode = "turbo"
        
        # Modificadores de interação
        if keys[pygame.K_SPACE]:
            self.mode = "stealth"
            self.intensity = -self.original_intensity * 2  # Onda negativa
        
        if keys[pygame.K_z]:
            self.mode = "erase"
            self.intensity = 0  # Não cria onda
            
        if keys[pygame.K_x]:
            self.mode = "super"
            self.intensity = self.original_intensity * 5  # Onda super forte
        
        if keys[pygame.K_c]:
            self.mode = "pulse"
            self.intensity = self.original_intensity * 10  # Pulso forte momentâneo
        
        # Aplicar movimento
        self.x += dx
        self.y += dy
        
        # Reduzir intensidade se estiver em movimento (menos impacto)
        if dx != 0 or dy != 0 and self.mode not in ["turbo", "super"]:
            self.intensity *= 0.5
        
        # Manter dentro dos limites
        self.x = np.clip(self.x, 0, self.N-1)
        self.y = np.clip(self.y, 0, self.N-1)
        
        # Posição no grid
        col = int(round(self.x))
        row = int(round(self.y))
        
        # Aplicar efeito do jogador no wavefield baseado no modo
        if self.mode == "stealth":
            wavefield.u[row, col] += -self.intensity
        elif self.mode == "erase":
            wavefield.u[row, col] = 0  # Apaga completamente
        elif self.mode == "pulse":
            # Pulso em área 3x3
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    r, c = row + dr, col + dc
                    if 0 <= r < self.N and 0 <= c < self.N:
                        wavefield.u[r, c] += self.intensity * 0.3
        else:  # normal, turbo, super
            wavefield.u[row, col] += self.intensity
        
        # Interação com mouse (botões)
        if mouse_buttons[0]:  # Botão esquerdo
            self.handle_mouse_click(mouse_pos, wavefield, button=0)
        if mouse_buttons[2]:  # Botão direito
            self.handle_mouse_click(mouse_pos, wavefield, button=2)
        if mouse_buttons[1]:  # Botão do meio
            self.handle_mouse_click(mouse_pos, wavefield, button=1)
    
    def handle_mouse_click(self, mouse_pos, wavefield, button=0):
        """Processa clique do mouse em diferentes botões"""
        x_mouse, y_mouse = mouse_pos
        # Converter para coordenadas do grid (simplificado)
        # Nota: Em uma implementação real, você usaria a câmera para converter
        grid_x = int(x_mouse * self.N / 1200)  # 1200 é largura da tela
        grid_y = int(y_mouse * self.N / 800)   # 800 é altura da tela
        
        grid_x = np.clip(grid_x, 0, self.N-1)
        grid_y = np.clip(grid_y, 0, self.N-1)
        
        if button == 0:  # Esquerdo - onda positiva
            wavefield.u[grid_y, grid_x] += 5.0
        elif button == 2:  # Direito - onda negativa
            wavefield.u[grid_y, grid_x] += -5.0
        elif button == 1:  # Meio - pulso circular
            for dr in [-2, -1, 0, 1, 2]:
                for dc in [-2, -1, 0, 1, 2]:
                    r, c = grid_y + dr, grid_x + dc
                    if 0 <= r < self.N and 0 <= c < self.N:
                        dist = (dr*dr + dc*dc) ** 0.5
                        if dist < 2.5:
                            wavefield.u[r, c] += 3.0 * (1 - dist/3)

# -----------------------------
# Visualizador 3D
# -----------------------------
class Visualizer3D:
    def __init__(self, screen, N, scale_3d=5.0):
        self.screen = screen
        self.N = N
        self.W, self.H = screen.get_size()
        self.scale_3d = scale_3d
        
        # Projeção isométrica
        self.angle_x = np.pi / 6
        self.angle_y = np.pi / 6
        
        self.cos_x = np.cos(self.angle_x)
        self.sin_x = np.sin(self.angle_x)
        self.cos_y = np.cos(self.angle_y)
        self.sin_y = np.sin(self.angle_y)
        
        self.center_x = self.W // 2
        self.center_y = self.H // 2
        self.grid_scale = min(self.W, self.H) / (N * 1.2)
        self.offset_x = 0
        self.offset_y = -50
        
        # Fonte para texto
        self.font = pygame.font.Font(None, 24)
        
        print(f"Visualizador 3D: N={N}, scale={self.grid_scale:.2f}")

    def project(self, x, y, z):
        world_x = x - self.N/2
        world_y = y - self.N/2
        
        screen_x = self.center_x + self.offset_x + (world_x - world_y) * self.cos_x * self.grid_scale
        screen_y = self.center_y + self.offset_y + (world_x + world_y) * self.sin_x * self.grid_scale - z * self.scale_3d
        
        return int(screen_x), int(screen_y)

    def screen_to_grid(self, screen_x, screen_y):
        """Converte coordenadas da tela para coordenadas do grid"""
        adj_x = screen_x - self.center_x - self.offset_x
        adj_y = screen_y - self.center_y - self.offset_y
        
        denom = 2 * self.cos_x * self.sin_x * self.grid_scale**2
        if abs(denom) < 1e-6:
            return self.N//2, self.N//2
        
        world_x = (adj_x / (self.cos_x * self.grid_scale) + adj_y / (self.sin_x * self.grid_scale)) / 2
        world_y = (adj_y / (self.sin_x * self.grid_scale) - adj_x / (self.cos_x * self.grid_scale)) / 2
        
        grid_x = world_x + self.N/2
        grid_y = world_y + self.N/2
        
        return int(np.clip(grid_x, 0, self.N-1)), int(np.clip(grid_y, 0, self.N-1))

    def render(self, u2D, player):
        self.screen.fill((0, 0, 0))
        
        # Desenhar linhas do grid (otimizado - pula algumas linhas)
        step = max(1, self.N // 50)  # Adaptativo
        
        # Linhas horizontais (i constante)
        for i in range(0, self.N, step):
            points = []
            for j in range(self.N):
                screen_x, screen_y = self.project(j, i, u2D[i, j])
                points.append((screen_x, screen_y))
            
            if len(points) > 1:
                z_avg = np.mean(u2D[i, :])
                brightness = int(128 + z_avg * 30)
                brightness = np.clip(brightness, 50, 255)
                color = (brightness//2, brightness, brightness//2)
                pygame.draw.lines(self.screen, color, False, points, 1)
        
        # Linhas verticais (j constante)
        for j in range(0, self.N, step):
            points = []
            for i in range(self.N):
                screen_x, screen_y = self.project(j, i, u2D[i, j])
                points.append((screen_x, screen_y))
            
            if len(points) > 1:
                z_avg = np.mean(u2D[:, j])
                brightness = int(128 + z_avg * 30)
                brightness = np.clip(brightness, 50, 255)
                color = (brightness//2, brightness, brightness//2)
                pygame.draw.lines(self.screen, color, False, points, 1)
        
        # Desenhar jogador
        self.draw_player(u2D, player)
        
        # Desenhar informações de controle
        self.draw_controls(player)
        
        pygame.display.flip()
    
    def draw_player(self, u2D, player):
        """Desenha o jogador com cor baseada no modo"""
        px, py = int(round(player.x)), int(round(player.y))
        if 0 <= px < self.N and 0 <= py < self.N:
            z = u2D[py, px]
            screen_x, screen_y = self.project(px, py, z)
            
            # Escolher cor baseada no modo
            if player.mode == "stealth":
                color = (100, 100, 255)  # Azul
                size = 6
            elif player.mode == "turbo":
                color = (255, 255, 0)    # Amarelo
                size = 8
            elif player.mode == "erase":
                color = (255, 0, 255)    # Magenta
                size = 6
            elif player.mode == "super":
                color = (255, 128, 0)    # Laranja
                size = 10
            elif player.mode == "pulse":
                color = (0, 255, 255)    # Ciano
                size = 12
            else:  # normal
                color = (255, 0, 0)      # Vermelho
                size = 6
            
            # Desenhar círculo principal
            pygame.draw.circle(self.screen, color, (screen_x, screen_y), size, 2)
            pygame.draw.circle(self.screen, color, (screen_x, screen_y), size//2)
            
            # Rastro
            if player.mode == "turbo":
                for i in range(1, 4):
                    trail_x = screen_x - i * player.speed * 2
                    trail_y = screen_y - i * player.speed * 2
                    if 0 <= trail_x < self.W and 0 <= trail_y < self.H:
                        alpha = 255 - i * 60
                        pygame.draw.circle(self.screen, (alpha, alpha, 0), (trail_x, trail_y), size-i)
    
    def draw_controls(self, player):
        """Desenha informações de controle na tela"""
        controls = [
            f"Modo: {player.mode.upper()}",
            f"Intensidade: {player.intensity:.1f}",
            f"Velocidade: {player.speed:.1f}",
            f"Posição: ({player.x:.1f}, {player.y:.1f})",
            "",
            "CONTROLES:",
            "Setas/WASD: Mover",
            "Shift: Turbo",
            "Espaço: Stealth (onda -)",
            "Z: Apagar",
            "X: Super onda",
            "C: Pulso",
            "Mouse Esq: Onda +",
            "Mouse Dir: Onda -",
            "Mouse Meio: Pulso"
        ]
        
        y_offset = 10
        for text in controls:
            color = (255, 255, 255)
            if "Modo:" in text and player.mode != "normal":
                color = (255, 255, 0)
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (10, y_offset))
            y_offset += 22

# -----------------------------
# Pipeline
# -----------------------------
class WavePipeline:
    def __init__(self, screen, N=100):
        self.wavefield = WaveField(N)
        self.player = Player(N, intensity=2.0, speed=1.5)
        self.visualizer = Visualizer3D(screen, N, scale_3d=8.0)
        self.running = True
        self.show_axes = True
        self.clock = pygame.time.Clock()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time em segundos
            
            # Obter estados dos inputs
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            mouse_pos = pygame.mouse.get_pos()

            # Processar eventos
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.running = False
                    elif e.key == pygame.K_r:  # Reset
                        self.wavefield.u.fill(0)
                        self.wavefield.u_old.fill(0)
                        self.wavefield.first_step = True
                        print("Reset!")
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    # Já processamos via mouse_buttons no player
                    pass

            # Atualizar jogador com todos os inputs
            self.player.update(self.wavefield, keys, mouse_buttons, mouse_pos)
            
            # Step da física
            self.wavefield.step()
            
            # Renderizar
            self.visualizer.render(self.wavefield.u, self.player)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Simulação de Onda 3D - Controles Melhorados")
    
    print("=" * 50)
    print("SIMULAÇÃO DE ONDA 3D - CONTROLES COMPLETOS")
    print("=" * 50)
    print("\nMOVIMENTO:")
    print("  Setas ou WASD: Mover")
    print("  Shift: Turbo (velocidade 2x)")
    print("\nMODOS DE ONDA:")
    print("  Espaço: Stealth (onda negativa)")
    print("  Z: Apagar (não cria onda)")
    print("  X: Super onda (5x intensidade)")
    print("  C: Pulso (área 3x3)")
    print("\nMOUSE:")
    print("  Botão Esquerdo: Onda positiva")
    print("  Botão Direito: Onda negativa")
    print("  Botão Meio: Pulso circular")
    print("\nOUTROS:")
    print("  R: Reset")
    print("  ESC: Sair")
    print("=" * 50)
    
    try:
        pipeline = WavePipeline(screen, N=100)
        pipeline.run()
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()