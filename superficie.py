import pygame
import numpy as np

# -----------------------------
# WaveField
# -----------------------------
class WaveField:
    def __init__(self, N, c=5, dt=0.1, alpha=0.0, damping=0.98):
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
# KeyboardHandler - Gerencia eventos do teclado (CORRIGIDO)
# -----------------------------
class KeyboardHandler:
    def __init__(self):
        self.keys = {}  # Teclas atualmente pressionadas
        self.just_pressed = set()  # Teclas pressionadas neste frame
        self.just_released = set()  # Teclas soltas neste frame
        self.hold_times = {}  # Tempo de pressionamento
        
    def handle_event(self, event):
        """Processa eventos de teclado"""
        if event.type == pygame.KEYDOWN:
            self.keys[event.key] = True
            self.just_pressed.add(event.key)
            if event.key not in self.hold_times:
                self.hold_times[event.key] = 0
                
        elif event.type == pygame.KEYUP:
            if event.key in self.keys:
                del self.keys[event.key]
            self.just_released.add(event.key)
            if event.key in self.hold_times:
                del self.hold_times[event.key]
    
    def update(self):
        """Atualiza hold times (chamar no início do frame)"""
        # Incrementar hold times para teclas pressionadas
        for key in self.keys:
            if key in self.hold_times:
                self.hold_times[key] += 1
            else:
                self.hold_times[key] = 1
    
    def clear_frame_flags(self):
        """Limpa flags de frame (chamar no final do frame)"""
        self.just_pressed.clear()
        self.just_released.clear()
    
    def is_pressed(self, key):
        """Tecla está pressionada (qualquer duração)"""
        return self.keys.get(key, False)
    
    def is_just_pressed(self, key):
        """Tecla foi pressionada neste frame"""
        return key in self.just_pressed
    
    def is_just_released(self, key):
        """Tecla foi solta neste frame"""
        return key in self.just_released
    
    def get_hold_time(self, key):
        """Tempo que a tecla está pressionada (em frames)"""
        return self.hold_times.get(key, 0)
    
    def get_pressed_keys(self):
        """Retorna lista de teclas pressionadas"""
        return list(self.keys.keys())

# -----------------------------
# MouseHandler - Gerencia eventos do mouse
# -----------------------------
class MouseHandler:
    def __init__(self):
        self.buttons = {
            1: {'pressed': False, 'just_pressed': False, 'just_released': False, 'hold_time': 0, 'pos': (0,0)},
            2: {'pressed': False, 'just_pressed': False, 'just_released': False, 'hold_time': 0, 'pos': (0,0)},
            3: {'pressed': False, 'just_pressed': False, 'just_released': False, 'hold_time': 0, 'pos': (0,0)},
            4: {'pressed': False, 'just_pressed': False, 'just_released': False, 'hold_time': 0, 'pos': (0,0)},
            5: {'pressed': False, 'just_pressed': False, 'just_released': False, 'hold_time': 0, 'pos': (0,0)}
        }
        self.pos = (0, 0)
        self.rel = (0, 0)
        self.wheel = 0
        
    def handle_event(self, event):
        """Processa eventos do mouse"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in self.buttons:
                self.buttons[event.button]['pressed'] = True
                self.buttons[event.button]['just_pressed'] = True
                self.buttons[event.button]['pos'] = event.pos
                self.buttons[event.button]['hold_time'] = 0
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in self.buttons:
                self.buttons[event.button]['pressed'] = False
                self.buttons[event.button]['just_released'] = True
                self.buttons[event.button]['hold_time'] = 0
                
        elif event.type == pygame.MOUSEMOTION:
            self.pos = event.pos
            self.rel = event.rel
            
        elif event.type == pygame.MOUSEWHEEL:
            self.wheel = event.y
    
    def update(self):
        """Atualiza hold times"""
        for button in self.buttons.values():
            if button['pressed']:
                button['hold_time'] += 1
    
    def clear_frame_flags(self):
        """Limpa flags de frame"""
        for button in self.buttons.values():
            button['just_pressed'] = False
            button['just_released'] = False
    
    def is_pressed(self, button):
        return self.buttons[button]['pressed']
    
    def is_just_pressed(self, button):
        return self.buttons[button]['just_pressed']
    
    def is_just_released(self, button):
        return self.buttons[button]['just_released']
    
    def get_hold_time(self, button):
        return self.buttons[button]['hold_time']
    
    def get_press_position(self, button):
        return self.buttons[button]['pos']

# -----------------------------
# Player
# -----------------------------
class Player:
    def __init__(self, N, intensity=5.0, speed=1.0):
        self.N = N
        self.x = N / 4
        self.y = N / 4
        self.original_intensity = intensity
        self.intensity = intensity
        self.speed = speed
        self.hidden = False
        self.bomb_cooldown = 0
        self.space_hold_time = 0
        self.enter_hold_time = 0

    def update(self, wavefield, keyboard):
        # Reset estados
        dx, dy = 0.0, 0.0
        self.intensity = self.original_intensity
        self.hidden = False
        
        # Movimento com setas
        if keyboard.is_pressed(pygame.K_LEFT) or keyboard.is_pressed(pygame.K_a):
            dx -= self.speed
        if keyboard.is_pressed(pygame.K_RIGHT) or keyboard.is_pressed(pygame.K_d):
            dx += self.speed
        if keyboard.is_pressed(pygame.K_UP) or keyboard.is_pressed(pygame.K_w):
            dy -= self.speed
        if keyboard.is_pressed(pygame.K_DOWN) or keyboard.is_pressed(pygame.K_s):
            dy += self.speed
        
        # Turbo com SHIFT
        if keyboard.is_pressed(pygame.K_LSHIFT) or keyboard.is_pressed(pygame.K_RSHIFT):
            dx *= 2
            dy *= 2
        
        self.x += dx
        self.y += dy
        
        # Reduzir intensidade se estiver em movimento
        if dx != 0 or dy != 0:
            self.intensity = self.original_intensity / 2
        
        self.x = np.clip(self.x, 0, self.N-1)
        self.y = np.clip(self.y, 0, self.N-1)
        
        col = int(round(self.x))
        row = int(round(self.y))
        
        # ESPAÇO - diferentes comportamentos
        if keyboard.is_just_pressed(pygame.K_z):
            # Ao pressionar espaço
            self.hidden = True
            wavefield.u[row, col] += -2*self.intensity 
            print("Z: Mergulhar!")
            
        elif keyboard.is_pressed(pygame.K_z):
            # Segurando espaço
            self.hidden = True
            # Efeito a cada 10 frames
            # if keyboard.get_hold_time(pygame.K_SPACE) % 10 == 0:
                # wavefield.u[row, col] += -self.intensity * 0.3
                
        # elif keyboard.is_just_released(pygame.K_SPACE):
        #     # Ao soltar espaço
        #     hold_time = keyboard.get_hold_time(pygame.K_SPACE)
        #     intensidade = self.intensity *1
        #     # wavefield.u[row, col] += intensidade
        #     for dr in [-1,1]:
        #         for dc in [-1,0,1]:
        #             r,c = row+dr,col+dc
        #             if 0<=r<self.N and 0<=c<self.N:
        #                 wavefield.u[r,c]+=1*intensidade
        #     print(f"SPACE Solto. Intesidade: {intensidade}")
            
        else:
            # Modo normal
            wavefield.u[row, col] = self.intensity
        
        # # ENTER/RETURN - bomba
        # if keyboard.is_just_pressed(pygame.K_x):
        #     # Ao pressionar Enter
        #     if self.bomb_cooldown <= 0:
        #         wavefield.u[row, col] += 20 * self.intensity
        #         self.bomb_cooldown = 20
        #         print("X: Bomba!")
                
        # elif keyboard.is_pressed(pygame.K_RETURN):
        #     # Segurando Enter - bomba carregada
        #     if self.bomb_cooldown <= 0:
        #         hold_time = keyboard.get_hold_time(pygame.K_RETURN)
        #         wavefield.u[row, col] += 30 * self.intensity * (hold_time / 20)
        #         self.bomb_cooldown = 15
        #         print(f"ENTER: Carregada! ({hold_time} frames)")
                
        # elif keyboard.is_just_released(pygame.K_RETURN):
        #     # Ao soltar Enter
        #     hold_time = keyboard.get_hold_time(pygame.K_RETURN)
            # if hold_time > 5:
            #     wavefield.u[row, col] += 10 * self.intensity
            #     print(f"ENTER: Bomba residual ({hold_time} frames)")
        
        # Tecla C - pulso
        if keyboard.is_just_pressed(pygame.K_x):
            wavefield.u[row, col] -= 6 * self.intensity
            print("x: Pulso!")
        if keyboard.is_pressed(pygame.K_x):
            if keyboard.get_hold_time(pygame.K_x) % 10 == 0:
                print("x: onda!") 
                wavefield.u[row,col] -= 3*self.intensity

        
        # Tecla R - reset
        if keyboard.is_just_pressed(pygame.K_r):
            wavefield.u.fill(0)
            wavefield.u_old.fill(0)
            wavefield.first_step = True
            print("R: Reset completo!")
        
        # Atualizar cooldown da bomba
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1

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
        
        # Centro da tela
        self.center_x = self.W // 2
        self.center_y = self.H // 2
        
        # Escala do grid
        self.grid_scale = min(self.W, self.H) / (N * 1.2)
        
        # Offsets
        self.offset_x = 0
        self.offset_y = -50
        
        print(f"Visualizador 3D inicializado: N={N}, scale={self.grid_scale:.2f}")

    def project(self, x, y, z):
        world_x = x - self.N/2
        world_y = y - self.N/2
        
        screen_x = self.center_x + self.offset_x + (world_x - world_y) * self.cos_x * self.grid_scale
        screen_y = self.center_y + self.offset_y + (world_x + world_y) * self.sin_x * self.grid_scale - z * self.scale_3d
        
        return int(screen_x), int(screen_y)

    def screen_to_grid(self, screen_x, screen_y):
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

    def render(self, u2D, player, mouse_handler, keyboard_handler):
        self.screen.fill((0, 0, 0))
        
        # Desenhar linhas do grid
        for i in range(0, self.N, 2):
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
        
        # Desenhar eixos
        self._draw_axes()
        
        # Desenhar o player
        self.draw_player(u2D, player)
        
        # Desenhar feedback visual
        self.draw_feedback(u2D, mouse_handler, keyboard_handler)
    
    def draw_player(self, u2D, player):
        px, py = int(round(player.x)), int(round(player.y))
        if 0 <= px < self.N and 0 <= py < self.N:
            z = u2D[py, px] if not player.hidden else 0
            screen_x, screen_y = self.project(px, py, z)
            
            if not player.hidden:
                # pygame.draw.circle(self.screen, (255, 0, 0), (screen_x, screen_y), 6)
                # pygame.draw.circle(self.screen, (255, 100, 100), (screen_x, screen_y), 3)
                pass
            else:
                pygame.draw.circle(self.screen, (100, 255, 100), (screen_x, screen_y), 4)
                pass
    
    def draw_feedback(self, u2D, mouse_handler, keyboard_handler):
        """Desenha feedback visual para inputs"""
        # Cursor do mouse
        mouse_x, mouse_y = mouse_handler.pos
        grid_x, grid_y = self.screen_to_grid(mouse_x, mouse_y)
        
        if 0 <= grid_x < self.N and 0 <= grid_y < self.N:
            proj_x, proj_y = self.project(grid_x, grid_y, u2D[grid_y, grid_x])
            
            # Feedback do mouse
            if mouse_handler.is_pressed(1):
                color = (255, 100, 100) if mouse_handler.is_just_pressed(1) else (255, 0, 0)
                size = 12 if mouse_handler.is_just_pressed(1) else 8
                pygame.draw.circle(self.screen, color, (proj_x, proj_y), size, 2)
            
            # Feedback das teclas principais
            # if keyboard_handler.is_pressed(pygame.K_SPACE):
            #     self._draw_key_feedback("SPACE", (255, 255, 0), keyboard_handler.get_hold_time(pygame.K_SPACE))
            # if keyboard_handler.is_pressed(pygame.K_RETURN):
            #     self._draw_key_feedback("ENTER", (255, 0, 0), keyboard_handler.get_hold_time(pygame.K_RETURN))
            # if keyboard_handler.is_pressed(pygame.K_c):
            #     self._draw_key_feedback("C", (0, 255, 255), keyboard_handler.get_hold_time(pygame.K_c))
    
    def _draw_key_feedback(self, key_name, color, hold_time):
        font = pygame.font.Font(None, 36)
        text = f"{key_name}: {hold_time}"
        surf = font.render(text, True, color)
        self.screen.blit(surf, (self.W - 200, 10))
    
    def _draw_axes(self):
        start = self.project(0, self.N//2, 0)
        end = self.project(self.N-1, self.N//2, 0)
        pygame.draw.line(self.screen, (255, 0, 0), start, end, 1)
        
        start = self.project(self.N//2, 0, 0)
        end = self.project(self.N//2, self.N-1, 0)
        pygame.draw.line(self.screen, (0, 255, 0), start, end, 1)
        
        center = self.project(self.N//2, self.N//2, 0)
        top = self.project(self.N//2, self.N//2, 1)
        pygame.draw.line(self.screen, (0, 0, 255), center, top, 1)

# -----------------------------
# Pipeline
# -----------------------------
class WavePipeline:
    def __init__(self, screen, N=100):
        self.wavefield = WaveField(N)
        self.player = Player(N)
        self.visualizer = Visualizer3D(screen, N, scale_3d=8.0)
        self.mouse = MouseHandler()
        self.keyboard = KeyboardHandler()
        self.running = True
        self.show_axes = True

    def run(self):
        clock = pygame.time.Clock()
        last_mouse_grid = (-1, -1)
        
        while self.running:
            clock.tick(60)
            
            # Processar eventos
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_a:
                        self.show_axes = not self.show_axes
                    elif e.key == pygame.K_ESCAPE:
                        self.running = False
                    else:
                        self.keyboard.handle_event(e)
                elif e.type == pygame.KEYUP:
                    self.keyboard.handle_event(e)
                else:
                    self.mouse.handle_event(e)
            
            # Atualizar hold times (depois de processar eventos)
            self.keyboard.update()
            self.mouse.update()
            
            # Interações com mouse
            current_grid = self.visualizer.screen_to_grid(*self.mouse.pos)
            
            if self.mouse.is_just_pressed(1):
                grid_x, grid_y = current_grid
                self.wavefield.u[grid_y, grid_x] += 8.0
                
            elif self.mouse.is_pressed(1) and self.mouse.get_hold_time(1) > 5:
                if current_grid != last_mouse_grid:
                    grid_x, grid_y = current_grid
                    self.wavefield.u[grid_y, grid_x] += 2.0
                    
            elif self.mouse.is_just_released(1):
                hold_time = self.mouse.get_hold_time(1)
                grid_x, grid_y = current_grid
                self.wavefield.u[grid_y, grid_x] += hold_time * 0.5
            
            if self.mouse.is_just_pressed(3):
                grid_x, grid_y = current_grid
                self.wavefield.u[grid_y, grid_x] -= 8.0
                
            elif self.mouse.is_pressed(3) and self.mouse.get_hold_time(3) > 5:
                if current_grid != last_mouse_grid:
                    grid_x, grid_y = current_grid
                    self.wavefield.u[grid_y, grid_x] -= 2.0
            
            if self.mouse.is_just_pressed(2):
                grid_x, grid_y = current_grid
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        r, c = grid_y + dr, grid_x + dc
                        if 0 <= r < self.wavefield.N and 0 <= c < self.wavefield.N:
                            self.wavefield.u[r, c] += 5.0
            
            if self.mouse.wheel != 0:
                self.wavefield.damping += self.mouse.wheel * 0.01
                self.wavefield.damping = np.clip(self.wavefield.damping, 0.9, 1.0)
                self.mouse.wheel = 0
            
            last_mouse_grid = current_grid
            
            # Atualizar jogador
            self.player.update(self.wavefield, self.keyboard)
            
            # Step da física
            self.wavefield.step()
            
            # Renderizar
            self.visualizer.render(self.wavefield.u, self.player, self.mouse, self.keyboard)
            
            # HUD
            self._draw_hud(screen)
            
            pygame.display.flip()
            
            # Limpar flags de frame no final (DEPOIS de usar)
            self.keyboard.clear_frame_flags()
            self.mouse.clear_frame_flags()

    def _draw_hud(self, screen):
        font = pygame.font.Font(None, 24)
        
        row = int(round(self.player.y))
        col = int(round(self.player.x))

        texts = [
            f"Mouse: Criar ondas",
            f"Setas: Mover",
            f"Z: Mergulhar (segurar para ficar submerso)",
            f"X: Onda (segurar para ficar pulsando)",
            f"-----------------------------",
            f"Player: ({self.player.x:.1f}, {self.player.y:.1f})",
            f"Mouse Grid: {self.visualizer.screen_to_grid(*self.mouse.pos)}",
            f"Keys pressed: {len(self.keyboard.get_pressed_keys())}",
            f"Bomb CD: {self.player.bomb_cooldown}",
            f"Damping: {self.wavefield.damping:.3f}",
            f"Intensity: {self.wavefield.u[row,col]:.1f}",
            f"-----------------------------",
        ]
        
        for i, text in enumerate(texts):
            surface = font.render(text, True, (255, 255, 255))
            screen.blit(surface, (10, 10 + i * 30))

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Simulação de Onda 3D - Teclado com Estados")
    
    print("=" * 60)
    print("SIMULAÇÃO DE ONDA 3D - TECLADO COM ESTADOS")
    print("=" * 60)
    print("\nTECLADO:")
    print("  - X: Onda (segurar para ficar pulsando)")
    print("  - Z: Mergulhar")
    print("  - R: Reset")
    print("  - SHIFT: Turbo")
    print("\nMOUSE:")
    print("  Esquerdo: Onda (pressionar/soltar/arrastar)")
    print("  Direito: Onda negativa")
    print("  Meio: Pulso")
    print("  Roda: Ajusta damping")
    print("=" * 60)
    
    pipeline = WavePipeline(screen, N=100)
    pipeline.run()
    pygame.quit()