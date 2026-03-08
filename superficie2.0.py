import pygame
import numpy as np
from numba import njit, prange

# -----------------------------
# CONFIGURAÇÕES
# -----------------------------
DTYPE = np.float32
GRID_SIZE = 400

# -----------------------------
# Kernels Numba
# -----------------------------
@njit(parallel=True, cache=True, fastmath=True)
def wave_step_numba(u, u_old, c2_dt2, alpha, damping, max_val=10.0):
    N = u.shape[0]
    u_new = np.empty_like(u)
    
    for i in prange(1, N-1):
        for j in range(1, N-1):
            lap = u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1] - (u[i, j] * 4.0)
            val = (2.0 * u[i, j] - u_old[i, j] + (c2_dt2 + alpha) * lap) * damping
            
            if val > max_val:
                val = max_val
            elif val < -max_val:
                val = -max_val
            u_new[i, j] = val
    
    return u_new

@njit(parallel=True, cache=True, fastmath=True)
def wave_first_step_numba(u, c2_dt2, alpha, damping, max_val=10.0):
    N = u.shape[0]
    u_new = np.empty_like(u)
    
    for i in prange(1, N-1):
        for j in range(1, N-1):
            lap = u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1] - (u[i, j] * 4.0)
            val = (u[i, j] + (c2_dt2 + alpha) * lap) * damping
            
            if val > max_val:
                val = max_val
            elif val < -max_val:
                val = -max_val
            u_new[i, j] = val
    
    return u_new

# -----------------------------
# WaveField
# -----------------------------
class WaveField:
    __slots__ = ('N', 'u', 'u_old', 'first_step', 'c', 'dt', 'c2_dt2', 
                 'alpha', 'damping', 'max_val')
    
    def __init__(self, N, c=5.0, dt=0.1, alpha=0.0, damping=0.96, max_val=10000.0):
        self.N = N
        self.c = DTYPE(c)
        self.dt = DTYPE(dt)
        self.u = np.zeros((N, N), dtype=DTYPE)
        self.u_old = np.zeros((N, N), dtype=DTYPE)
        self.first_step = True
        self.c2_dt2 = DTYPE((c * dt) ** 2)
        self.alpha = DTYPE(alpha)
        self.damping = DTYPE(damping)
        self.max_val = DTYPE(max_val)

    def step(self):
        if self.first_step:
            self.u = wave_first_step_numba(self.u, self.c2_dt2, self.alpha, 
                                           self.damping, self.max_val)
            self.first_step = False
        else:
            u_new = wave_step_numba(self.u, self.u_old, self.c2_dt2, self.alpha, 
                                    self.damping, self.max_val)
            self.u_old = self.u
            self.u = u_new
    
    def clear(self):
        self.u.fill(0)
        self.u_old.fill(0)
        self.first_step = True

# -----------------------------
# Player
# -----------------------------
class Player:
    __slots__ = ('N', 'x', 'y', 'hidden')
    
    def __init__(self, N):
        self.N = N
        self.x = N // 4
        self.y = N // 4
        self.hidden = False

    def update(self, wavefield, keys):
        self.hidden = False
        dx = dy = 0
        
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        if keys[pygame.K_SPACE]: self.hidden = True

        self.x = max(0, min(self.N-1, self.x + dx))
        self.y = max(0, min(self.N-1, self.y + dy))
        
        if not self.hidden:
            wavefield.u[self.y, self.x] = DTYPE(2.0)

# -----------------------------
# Visualizador com eixos corrigidos
# -----------------------------
class FastVisualizer:
    __slots__ = ('screen', 'N', 'W', 'H', 'offset_x', 'offset_y',
                 'grid_surface', 'clock', 'fps', 'frame_count', 'last_time',
                 'font', 'colors_pos', 'colors_neg', 'show_info', 'pipeline')
    
    def __init__(self, screen, N, pipeline, show_info=True):
        self.screen = screen
        self.N = N
        self.W, self.H = screen.get_size()
        self.show_info = show_info
        self.pipeline = pipeline
        
        self.offset_x = (self.W - N) // 2
        self.offset_y = (self.H - N) // 2
        
        self.grid_surface = pygame.Surface((N, N), pygame.HWSURFACE)
        
        # Paleta de cores
        self.colors_pos = np.zeros((256, 3), dtype=np.uint8)
        self.colors_neg = np.zeros((256, 3), dtype=np.uint8)
        for i in range(256):
            self.colors_pos[i] = [0, i, 255]
            self.colors_neg[i] = [255, 255-i, 255-i]
        
        # FPS
        self.clock = pygame.time.Clock()
        self.fps = 0
        self.frame_count = 0
        self.last_time = pygame.time.get_ticks()
        self.font = pygame.font.Font(None, 20)

    def screen_to_grid(self, screen_x, screen_y):
        """Converte coordenadas da tela para coordenadas do grid numpy"""
        grid_col = screen_x - self.offset_x  # coluna (x)
        grid_row = screen_y - self.offset_y  # linha (y)
        
        if 0 <= grid_col < self.N and 0 <= grid_row < self.N:
            return grid_col, grid_row
        return None, None

    def render(self, u, player, wavefield):
        # FPS counter
        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time >= 1000:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        
        # CORREÇÃO: Transpor a matriz para que os eixos fiquem corretos na tela
        # u[linha, coluna] -> u_transposta[coluna, linha]
        u_for_display = u.T
        
        # Renderizar grid com a matriz transposta
        u_norm = np.clip(u_for_display * 0.5, -1.0, 1.0)
        u_abs = np.abs(u_norm)
        u_quant = (u_abs * 255).astype(np.uint8)
        
        rgb = np.zeros((self.N, self.N, 3), dtype=np.uint8)
        
        pos_mask = u_norm > 0.02
        neg_mask = u_norm < -0.02
        
        if np.any(pos_mask):
            rgb[pos_mask] = self.colors_pos[u_quant[pos_mask]]
        if np.any(neg_mask):
            rgb[neg_mask] = self.colors_neg[u_quant[neg_mask]]
        
        pygame.surfarray.blit_array(self.grid_surface, rgb)
        
        # Desenhar
        self.screen.fill(0)
        self.screen.blit(self.grid_surface, (self.offset_x, self.offset_y))
        
        # Jogador - converter coordenadas do jogador (que estão em u[linha, coluna])
        # para coordenadas da tela (que espera x, y)
        if not player.hidden:
            # player.x = coluna, player.y = linha
            screen_x = self.offset_x + player.x
            screen_y = self.offset_y + player.y
            pygame.draw.circle(self.screen, (255, 0, 0), (screen_x, screen_y), 3)
            pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), 1)
        
        # Informações
        if self.show_info:
            c_value = (wavefield.c2_dt2 ** 0.5) / wavefield.dt
            info = [
                f"FPS: {self.fps}",
                f"c={c_value:.1f} steps={self.pipeline.steps_per_frame}",
            ]
            
            # Mostrar posição do mouse
            mouse_screen_x, mouse_screen_y = pygame.mouse.get_pos()
            grid_col, grid_row = self.screen_to_grid(mouse_screen_x, mouse_screen_y)
            if grid_col is not None:
                info.append(f"Mouse: tela({mouse_screen_x},{mouse_screen_y}) -> grid[{grid_row},{grid_col}]")
            
            for i, text in enumerate(info):
                surf = self.font.render(text, True, (255, 255, 255))
                self.screen.blit(surf, (5, 5 + i * 20))
        
        pygame.display.flip()

# -----------------------------
# Pipeline principal
# -----------------------------
class WavePipeline:
    __slots__ = ('wavefield', 'player', 'visualizer', 'running', 'clock',
                 'steps_per_frame', 'mouse_was_pressed', 'last_mouse_pos',
                 'frame_times')
    
    def __init__(self, screen, N=400):
        self.wavefield = WaveField(N)
        self.player = Player(N)
        self.visualizer = FastVisualizer(screen, N, self, show_info=True)
        self.running = True
        self.clock = pygame.time.Clock()
        self.steps_per_frame = 5
        self.mouse_was_pressed = False
        self.last_mouse_pos = (-1, -1)
        self.frame_times = []

    def run(self):
        while self.running:
            frame_start = pygame.time.get_ticks()
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        self.running = False
                    elif e.key == pygame.K_c:
                        self.wavefield.clear()
                        print("Limpo!")
                    elif e.key == pygame.K_2:
                        self.steps_per_frame = min(100, self.steps_per_frame + 1)
                        print(f"Steps: {self.steps_per_frame}")
                    elif e.key == pygame.K_1:
                        self.steps_per_frame = max(1, self.steps_per_frame - 1)
                        print(f"Steps: {self.steps_per_frame}")
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    x, y = e.pos
                    grid_col, grid_row = self.visualizer.screen_to_grid(x, y)
                    if grid_col is not None and grid_row is not None:
                        print(f"\nCLIQUE:")
                        print(f"  Tela: ({x}, {y})")
                        print(f"  Grid: coluna={grid_col}, linha={grid_row}")
                        print(f"  Array original: u[{grid_row}, {grid_col}]")
                        
                        # # Área 3x3 - u[linha, coluna]
                        # for d_row in (-1, 0, 1):
                        #     for d_col in (-1, 0, 1):
                        #         row = grid_row + d_row
                        #         col = grid_col + d_col
                        #         if 0 <= row < self.wavefield.N and 0 <= col < self.wavefield.N:
                        #             self.wavefield.u[row, col] = 8.0
            
            # Mouse arrastando
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:
                x, y = pygame.mouse.get_pos()
                if (x, y) != self.last_mouse_pos:
                    grid_col, grid_row = self.visualizer.screen_to_grid(x, y)
                    if grid_col is not None and grid_row is not None:
                        intensity = 8.0 if not self.mouse_was_pressed else 4.0
                        # u[linha, coluna] = u[grid_row, grid_col]
                        self.wavefield.u[grid_row, grid_col] = intensity
                        self.mouse_was_pressed = True
                        self.last_mouse_pos = (x, y)
            else:
                self.mouse_was_pressed = False
            
            # Jogador
            keys = pygame.key.get_pressed()
            self.player.update(self.wavefield, keys)
            
            # Steps de física
            for _ in range(self.steps_per_frame):
                self.wavefield.step()
            
            # Renderizar
            self.visualizer.render(self.wavefield.u, self.player, self.wavefield)
            
            # Controle de FPS
            self.clock.tick(60)
            
            # Ajuste automático
            # frame_time = pygame.time.get_ticks() - frame_start
            # self.frame_times.append(frame_time)
            # if len(self.frame_times) > 30:
            #     avg_time = sum(self.frame_times) / len(self.frame_times)
            #     if avg_time > 16.5 and self.steps_per_frame > 1:
            #         self.steps_per_frame -= 1
            #         self.frame_times.clear()
            #     elif avg_time < 14.0 and self.steps_per_frame < 4:
            #         self.steps_per_frame += 1
            #         self.frame_times.clear()

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Ondas 60 FPS - Eixos Corrigidos")
    
    W, H = 1024, 768
    screen = pygame.display.set_mode((W, H), pygame.HWSURFACE | pygame.DOUBLEBUF)
    N = GRID_SIZE
    
    print("=" * 70)
    print("SIMULAÇÃO DE ONDAS 60 FPS")
    print("=" * 70)
    print(f"Grid: {N}x{N}")
    print("\nCORREÇÃO DOS EIXOS:")
    print("  A matriz numpy u[linha, coluna] é TRANSPOSTA na renderização")
    print("  para que os eixos fiquem corretos na tela.")
    print("  Agora X é horizontal, Y é vertical!")
    print("\nCONTROLES:")
    print("  Setas: mover jogador")
    print("  Clique: criar onda")
    print("  C: limpar")
    print("  ↑/↓: ajustar steps")
    print("  ESC: sair")
    print("=" * 70)
    
    try:
        pipeline = WavePipeline(screen, N)
        pipeline.run()
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()