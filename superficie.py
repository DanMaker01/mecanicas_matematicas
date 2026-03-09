import pygame
import numpy as np

# -----------------------------
# WaveField
# -----------------------------
class WaveField:
    def __init__(self, N, c=5, dt=0.1, alpha=0.0, damping=0.99):
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
# Player
# -----------------------------
class Player:
    def __init__(self, N, intensity=10.0, speed=1.0):
        self.N = N
        self.x = N / 4
        self.y = N / 4
        self.original_intensity = intensity
        self.intensity = intensity
        self.speed = speed
        self.hidden = False
        self.bomb_cooldown = 0

    def update(self, wavefield, keys):
        if self.hidden:
            self.hidden = False

        dx, dy = 0.0, 0.0
        self.intensity = self.original_intensity

        if keys[pygame.K_LEFT]: dx -= self.speed
        if keys[pygame.K_RIGHT]: dx += self.speed
        if keys[pygame.K_UP]: dy -= self.speed
        if keys[pygame.K_DOWN]: dy += self.speed
        self.x += dx
        self.y += dy

        if dx != 0 or dy != 0:
            self.intensity = self.original_intensity / 2

        self.x = np.clip(self.x, 0, self.N-1)
        self.y = np.clip(self.y, 0, self.N-1)

        col = int(round(self.x))
        row = int(round(self.y))
        
        if keys[pygame.K_SPACE]: 
            self.hidden = True
            # wavefield.u[row, col] += -self.intensity
        else:
            wavefield.u[row, col] = self.intensity
        
        if self.bomb_cooldown <= 0:
            if keys[pygame.K_RETURN]:
                wavefield.u[row,col] += 50*self.intensity
                self.bomb_cooldown = 20
        else:
            self.bomb_cooldown -= 1
            # print("cooldown:",self.bomb_cooldown)
# -----------------------------
# Visualizador 3D otimizado com projeção isométrica corrigida
# -----------------------------
class Visualizer3D:
    def __init__(self, screen, N, scale_3d=5.0):
        self.screen = screen
        self.N = N
        self.W, self.H = screen.get_size()
        self.scale_3d = scale_3d
        
        # Projeção isométrica (ângulos fixos)
        self.angle_x = np.pi / 6  # 30 graus rotação horizontal
        self.angle_y = np.pi / 6  # 30 graus elevação
        
        self.cos_x = np.cos(self.angle_x)
        self.sin_x = np.sin(self.angle_x)
        self.cos_y = np.cos(self.angle_y)
        self.sin_y = np.sin(self.angle_y)
        
        # Centro da tela
        self.center_x = self.W // 2
        self.center_y = self.H // 2
        
        # Escala do grid (ajustada para N=100 caber na tela)
        self.grid_scale = min(self.W, self.H) / (N * 1.2)
        
        # Offsets para centralizar a grade
        self.offset_x = 0
        self.offset_y = -50  # Deslocar para cima
        
        print(f"Visualizador 3D inicializado: N={N}, scale={self.grid_scale:.2f}")

    def project(self, x, y, z):
        """
        Projeção isométrica corrigida:
        x, y são coordenadas do grid (x = coluna, y = linha)
        z é a altura
        """
        # Converter coordenadas do grid para coordenadas de mundo
        # O grid vai de (0,0) a (N-1,N-1)
        # Queremos centralizar em (0,0)
        world_x = x - self.N/2
        world_y = y - self.N/2
        
        # Rotação isométrica: primeiro rotacionar em torno de Y, depois projetar
        # Esta é uma projeção isométrica padrão
        screen_x = self.center_x + self.offset_x + (world_x - world_y) * self.cos_x * self.grid_scale
        screen_y = self.center_y + self.offset_y + (world_x + world_y) * self.sin_x * self.grid_scale - z * self.scale_3d
        
        return int(screen_x), int(screen_y)

    def screen_to_grid(self, screen_x, screen_y):
        """
        Converte coordenadas da tela para coordenadas aproximadas do grid.
        Útil para interação com mouse.
        """
        # Ajustar para centro e offset
        adj_x = screen_x - self.center_x - self.offset_x
        adj_y = screen_y - self.center_y - self.offset_y
        
        # Resolver sistema linear da projeção (ignorando altura z para aproximação)
        # screen_x = (world_x - world_y) * cos_x * scale
        # screen_y = (world_x + world_y) * sin_x * scale
        
        # Resolver para world_x e world_y
        denom = 2 * self.cos_x * self.sin_x * self.grid_scale**2
        if abs(denom) < 1e-6:
            return self.N//2, self.N//2
        
        world_x = (adj_x / (self.cos_x * self.grid_scale) + adj_y / (self.sin_x * self.grid_scale)) / 2
        world_y = (adj_y / (self.sin_x * self.grid_scale) - adj_x / (self.cos_x * self.grid_scale)) / 2
        
        # Converter de volta para coordenadas do grid
        grid_x = world_x + self.N/2
        grid_y = world_y + self.N/2
        
        return int(np.clip(grid_x, 0, self.N-1)), int(np.clip(grid_y, 0, self.N-1))

    def render(self, u2D, player):
        self.screen.fill((0, 0, 0))
        
        # Desenhar linhas do grid na direção X (i constante)
        for i in range(0, self.N, 2):
            points = []
            for j in range(self.N):
                screen_x, screen_y = self.project(j, i, u2D[i, j])
                points.append((screen_x, screen_y))
            
            if len(points) > 1:
                # Cor baseada na altura
                z_avg = np.mean(u2D[i, :])
                brightness = int(128 + z_avg * 30)
                brightness = np.clip(brightness, 50, 255)
                color = (brightness//2, brightness, brightness//2)
                pygame.draw.lines(self.screen, color, False, points, 1)
        
        # Desenhar linhas do grid na direção Y (j constante)
        for j in range(0, self.N, 2):
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
        
        # Desenhar eixos para referência (opcional)
        self._draw_axes()
        
        # Desenhar o player
        px, py = int(round(player.x)), int(round(player.y))
        if 0 <= px < self.N and 0 <= py < self.N:
            z = u2D[py, px] if not player.hidden else 0
            screen_x, screen_y = self.project(px, py, z)
            
            if not player.hidden:
                # Círculo vermelho com brilho
                # pygame.draw.circle(self.screen, (255, 0, 0), (screen_x, screen_y), 6)
                # pygame.draw.circle(self.screen, (255, 100, 100), (screen_x-1, screen_y-1), 3)
                # Pequeno rastro
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nx, ny = screen_x + dx, screen_y + dy
                    if 0 <= nx < self.W and 0 <= ny < self.H:
                        self.screen.set_at((nx, ny), (100, 0, 0))
            else:
                pygame.draw.circle(self.screen, (100, 255, 100), (screen_x, screen_y), 4)


        # self._draw_hud(player)
        
    


    def _draw_axes(self):
        """Desenha eixos de referência"""
        # Eixo X (vermelho)
        start = self.project(0, self.N//2, 0)
        end = self.project(self.N-1, self.N//2, 0)
        pygame.draw.line(self.screen, (255, 0, 0), start, end, 1)
        
        # Eixo Y (verde)
        start = self.project(self.N//2, 0, 0)
        end = self.project(self.N//2, self.N-1, 0)
        pygame.draw.line(self.screen, (0, 255, 0), start, end, 1)
        
        # Eixo Z (azul) - vertical
        center = self.project(self.N//2, self.N//2, 0)
        top = self.project(self.N//2, self.N//2, 1)
        pygame.draw.line(self.screen, (0, 0, 255), center, top, 1)

# -----------------------------
# Pipeline
# -----------------------------
class WavePipeline:
    def __init__(self, screen, N=100):
        # self.wavefield = WaveField(N, c= 12.0, damping=0.11)
        self.wavefield = WaveField(N)
        self.player = Player(N)
        self.visualizer = Visualizer3D(screen, N, scale_3d=8.0)
        self.running = True
        self.show_axes = True

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            clock.tick(60)
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            mouse_pos = pygame.mouse.get_pos()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_a:  # Tecla 'A' para alternar eixos
                        self.show_axes = not self.show_axes
                    elif e.key == pygame.K_ESCAPE:
                        self.running = False

            # Adicionar onda com clique do mouse
            if mouse_buttons[0]:  # Botão esquerdo
                self.add_wave_at_mouse(mouse_pos)

            self.player.update(self.wavefield, keys)
            self.wavefield.step()
            self.visualizer.render(self.wavefield.u, self.player)

            self._draw_hud(screen)
            
            pygame.display.flip()

    def _draw_hud(self,screen):
        """Draws HUD with game information"""
        font = pygame.font.Font(None, 24)
        
        row = int(round(self.player.y))
        col = int(round(self.player.x))

        player_pos_text = f"Player: ({self.player.x}, {self.player.y})"
        intensity_text = f"Intensity: {self.wavefield.u[row,col]}"
        cooldown_text = f"Bomb CD: {self.player.bomb_cooldown}"
        
        texts = [player_pos_text, intensity_text, cooldown_text]
        
        for i, text in enumerate(texts):
            surface = font.render(text, True, (255, 255, 255))
            screen.blit(surface, (10, 10 + i * 30))
            

            

    
    def add_wave_at_mouse(self, mouse_pos):
        x_mouse, y_mouse = mouse_pos
        
        # Usar a função de conversão melhorada
        grid_x, grid_y = self.visualizer.screen_to_grid(x_mouse, y_mouse)
        
        # Adicionar onda com intensidade
        self.wavefield.u[grid_y, grid_x] += 4.0
        
        # Feedback visual (opcional)
        print(f"Mouse em ({x_mouse}, {y_mouse}) -> Grid ({grid_x}, {grid_y})")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Simulação de Onda 3D - Clique para criar ondas")
    
    print("Controles:")
    print("  - Setas: mover jogador")
    print("  - Espaço: esconder jogador")
    print("  - Clique esquerdo: criar onda")
    print("  - A: alternar eixos de referência")
    print("  - ESC: sair")
    
    pipeline = WavePipeline(screen, N=100)
    pipeline.run()
    pygame.quit()