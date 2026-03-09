import pygame
import numpy as np
from numba import njit, prange

# -----------------------------
# CONFIGURAÇÕES
# -----------------------------
DTYPE = np.float32
# Malha maior: 1000x800 (horizontalmente maior)
WORLD_WIDTH = 1200  # Largura do mundo
WORLD_HEIGHT = 800   # Altura do mundo
SCREEN_WIDTH = 1024  # Resolução da tela
SCREEN_HEIGHT = 768

# -----------------------------
# Kernels Numba
# -----------------------------
@njit(parallel=True, cache=True, fastmath=True)
def wave_step_numba(u, u_old, c2_dt2, alpha, damping, max_val=10.0):
    N, M = u.shape  # N = linhas, M = colunas
    u_new = np.empty_like(u)
    
    for i in prange(1, N-1):
        for j in range(1, M-1):
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
    N, M = u.shape
    u_new = np.empty_like(u)
    
    for i in prange(1, N-1):
        for j in range(1, M-1):
            lap = u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1] - (u[i, j] * 4.0)
            val = (u[i, j] + (c2_dt2 + alpha) * lap) * damping
            
            if val > max_val:
                val = max_val
            elif val < -max_val:
                val = -max_val
            u_new[i, j] = val
    
    return u_new

# -----------------------------
# Camera
# -----------------------------
class Camera:
    __slots__ = ('world_width', 'world_height', 'view_width', 'view_height',
                 'x', 'y', 'speed')
    
    def __init__(self, world_width, world_height, view_width, view_height):
        self.world_width = world_width
        self.world_height = world_height
        self.view_width = view_width
        self.view_height = view_height
        self.x = 0
        self.y = 0
        self.speed = 5
    
    def follow(self, target_x, target_y):
        """Segue o jogador, mantendo-o centralizado"""
        # Centralizar o jogador na tela
        target_cam_x = target_x - self.view_width // 2
        target_cam_y = target_y - self.view_height // 2
        
        # Mover câmera suavemente
        self.x += (target_cam_x - self.x) * 0.1
        self.y += (target_cam_y - self.y) * 0.1
        
        # Limitar ao mundo
        self.x = max(0, min(self.world_width - self.view_width, self.x))
        self.y = max(0, min(self.world_height - self.view_height, self.y))
    
    def get_view_rect(self):
        """Retorna o retângulo visível no mundo (x, y, largura, altura)"""
        return (int(self.x), int(self.y), self.view_width, self.view_height)
    
    def world_to_screen(self, world_x, world_y):
        """Converte coordenadas do mundo para coordenadas da tela"""
        screen_x = world_x - self.x
        screen_y = world_y - self.y
        return screen_x, screen_y
    
    def screen_to_world(self, screen_x, screen_y):
        """Converte coordenadas da tela para coordenadas do mundo"""
        world_x = screen_x + self.x
        world_y = screen_y + self.y
        return world_x, world_y

# -----------------------------
# WaveField - AGORA RETANGULAR
# -----------------------------
class WaveField:
    __slots__ = ('height', 'width', 'u', 'u_old', 'first_step', 'c', 'dt', 
                 'c2_dt2', 'alpha', 'damping', 'max_val')
    
    def __init__(self, height, width, c=5.0, dt=0.1, alpha=0.0, damping=0.96, max_val=99999999.0):
        self.height = height  # linhas (Y)
        self.width = width    # colunas (X)
        self.c = DTYPE(c)
        self.dt = DTYPE(dt)
        self.u = np.zeros((height, width), dtype=DTYPE)
        self.u_old = np.zeros((height, width), dtype=DTYPE)
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
    __slots__ = ('world_width', 'world_height', 'x', 'y', 'hidden', 'intensity')
    
    def __init__(self, world_width, world_height):
        self.world_width = world_width
        self.world_height = world_height
        self.x = world_width // 4
        self.y = world_height // 4
        self.hidden = False
        self.intensity = 10.0

    def update(self, wavefield, keys):
        self.hidden = False
        dx = dy = 0
        
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        if keys[pygame.K_SPACE]: self.hidden = True
        
        if self.hidden:
            dx *= 2
            dy *= 2
        
        self.x = max(0, min(self.world_width - 1, self.x + dx))
        self.y = max(0, min(self.world_height - 1, self.y + dy))
        
        if self.hidden:
            wavefield.u[self.y, self.x] = DTYPE(-self.intensity)
        else:
            wavefield.u[self.y, self.x] = DTYPE(self.intensity)

# -----------------------------
# Visualizador com Câmera
# -----------------------------
class FastVisualizer:
    __slots__ = ('screen', 'view_width', 'view_height', 'camera',
                 'grid_surface', 'clock', 'fps', 'frame_count', 'last_time',
                 'font', 'colors_pos', 'colors_neg', 'show_info', 'pipeline')
    
    def __init__(self, screen, camera, pipeline, show_info=True):
        self.screen = screen
        self.camera = camera
        self.view_width = camera.view_width
        self.view_height = camera.view_height
        self.show_info = show_info
        self.pipeline = pipeline
        
        self.grid_surface = pygame.Surface((self.view_width, self.view_height), pygame.HWSURFACE)
        
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

    def world_to_screen(self, world_x, world_y):
        """Converte coordenadas do mundo para tela (considerando câmera)"""
        return self.camera.world_to_screen(world_x, world_y)

    def screen_to_world(self, screen_x, screen_y):
        """Converte coordenadas da tela para mundo"""
        return self.camera.screen_to_world(screen_x, screen_y)

    def render(self, u, player, wavefield):
        # FPS counter
        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        if current_time - self.last_time >= 1000:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        
        # Obter view rect da câmera
        view_x, view_y, view_w, view_h = self.camera.get_view_rect()
        
        # Extrair apenas a porção visível do mundo
        u_visible = u[view_y:view_y + view_h, view_x:view_x + view_w]
        
        # CORREÇÃO: Transpor para eixos corretos na tela
        u_for_display = u_visible.T
        
        # Renderizar
        u_norm = np.clip(u_for_display * 0.5, -1.0, 1.0)
        u_abs = np.abs(u_norm)
        u_quant = (u_abs * 255).astype(np.uint8)
        
        rgb = np.zeros((view_w, view_h, 3), dtype=np.uint8)
        
        pos_mask = u_norm > 0.02
        neg_mask = u_norm < -0.02
        
        if np.any(pos_mask):
            rgb[pos_mask] = self.colors_pos[u_quant[pos_mask]]
        if np.any(neg_mask):
            rgb[neg_mask] = self.colors_neg[u_quant[neg_mask]]
        
        pygame.surfarray.blit_array(self.grid_surface, rgb)
        
        # Desenhar
        self.screen.fill(0)
        self.screen.blit(self.grid_surface, (0, 0))
        
        # Jogador (converter para coordenadas da tela)
        screen_x, screen_y = self.world_to_screen(player.x, player.y)
        if 0 <= screen_x < self.view_width and 0 <= screen_y < self.view_height:
            if not player.hidden:
                pygame.draw.circle(self.screen, (255, 0, 0), (int(screen_x), int(screen_y)), 3)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(screen_x), int(screen_y)), 1)
        
        # Informações
        if self.show_info:
            c_value = (wavefield.c2_dt2 ** 0.5) / wavefield.dt
            info = [
                f"FPS: {self.fps}",
                f"c={c_value:.1f} steps={self.pipeline.steps_per_frame}",
                f"Camera: ({int(self.camera.x)}, {int(self.camera.y)})",
                f"Jogador: ({player.x}, {player.y})",
                f"Mundo: {wavefield.width}x{wavefield.height}"
            ]
            
            # Mostrar posição do mouse no mundo
            mouse_screen_x, mouse_screen_y = pygame.mouse.get_pos()
            if mouse_screen_x < self.view_width and mouse_screen_y < self.view_height:
                world_x, world_y = self.screen_to_world(mouse_screen_x, mouse_screen_y)
                info.append(f"Mouse mundo: ({int(world_x)}, {int(world_y)})")
            
            for i, text in enumerate(info):
                surf = self.font.render(text, True, (255, 255, 255))
                self.screen.blit(surf, (5, 5 + i * 20))
        
        pygame.display.flip()

# -----------------------------
# Pipeline principal com Câmera
# -----------------------------
class WavePipeline:
    __slots__ = ('wavefield', 'player', 'camera', 'visualizer', 'running', 'clock',
                 'steps_per_frame', 'mouse_was_pressed', 'last_mouse_pos',
                 'frame_times')
    
    def __init__(self, screen, world_width, world_height, view_width, view_height):
        self.wavefield = WaveField(world_height, world_width)  # height, width
        self.player = Player(world_width, world_height)
        self.camera = Camera(world_width, world_height, view_width, view_height)
        self.visualizer = FastVisualizer(screen, self.camera, self, show_info=True)
        self.running = True
        self.clock = pygame.time.Clock()
        self.steps_per_frame = 2
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
                    # Converter tela para mundo
                    world_x, world_y = self.visualizer.screen_to_world(x, y)
                    if 0 <= world_x < self.wavefield.width and 0 <= world_y < self.wavefield.height:
                        self.wavefield.u[int(world_y), int(world_x)] = 8.0
            
            # Mouse arrastando
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:
                x, y = pygame.mouse.get_pos()
                if (x, y) != self.last_mouse_pos:
                    world_x, world_y = self.visualizer.screen_to_world(x, y)
                    if 0 <= world_x < self.wavefield.width and 0 <= world_y < self.wavefield.height:
                        intensity = 8.0 if not self.mouse_was_pressed else 4.0
                        self.wavefield.u[int(world_y), int(world_x)] = intensity
                        self.mouse_was_pressed = True
                        self.last_mouse_pos = (x, y)
            else:
                self.mouse_was_pressed = False
            
            # Jogador
            keys = pygame.key.get_pressed()
            self.player.update(self.wavefield, keys)
            
            # Atualizar câmera para seguir jogador
            self.camera.follow(self.player.x, self.player.y)
            
            # Steps de física
            for _ in range(self.steps_per_frame):
                self.wavefield.step()
            
            # Renderizar
            self.visualizer.render(self.wavefield.u, self.player, self.wavefield)
            
            # Controle de FPS
            self.clock.tick(60)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Ondas com Câmera - Mundo 1200x800")
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    
    print("=" * 70)
    print("SIMULAÇÃO DE ONDAS COM CÂMERA")
    print("=" * 70)
    print(f"Mundo: {WORLD_WIDTH}x{WORLD_HEIGHT}")
    print(f"Tela: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print("\nA câmera segue o jogador automaticamente!")
    print("\nCONTROLES:")
    print("  Setas: mover jogador")
    print("  Espaço: modo oculto (anda mais rápido e deixa rastro negativo)")
    print("  Clique: criar onda")
    print("  C: limpar")
    print("  1/2: diminuir/aumentar steps por frame")
    print("  ESC: sair")
    print("=" * 70)
    
    try:
        pipeline = WavePipeline(screen, WORLD_WIDTH, WORLD_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT)
        pipeline.run()
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()