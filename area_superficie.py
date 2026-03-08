import pygame
import numpy as np
import math
import time

# BIBLIOTECA DE FUNÇÕES
def get_function(key):
    """Retorna a função correspondente à tecla pressionada"""
    functions = {
        pygame.K_1: (lambda x, y: np.sin(x) * np.cos(y), "sin(x) * cos(y)"),
        pygame.K_2: (lambda x, y: 0.5 * (x**2 - y**2), "0.5*(x² - y²) [Sela]"),
        pygame.K_3: (lambda x, y: np.sin(2*x) * np.cos(2*y), "sin(2x) * cos(2y) [Ondulada]"),
        pygame.K_4: (lambda x, y: np.exp(-(x**2 + y**2)), "exp(-(x²+y²)) [Gaussiana]"),
        pygame.K_5: (lambda x, y: np.sin(x**2 + y**2) / (1 + 0.5*(x**2 + y**2)), "sin(r²)/(1+0.5r²) [Anel]"),
        pygame.K_6: (lambda x, y: 0.3 * np.sin(3*x) * np.cos(3*y) + 0.2 * np.sin(5*x) * np.cos(5*y), "Soma de ondas"),
        pygame.K_7: (lambda x, y: np.abs(x) + np.abs(y) - 1, "|x|+|y|-1 [Pirâmide]"),
        pygame.K_8: (lambda x, y: np.sqrt(x**2 + y**2) - 1, "sqrt(x²+y²)-1 [Cone]"),
        pygame.K_9: (lambda x, y: np.sin(x) * np.exp(-y) * np.exp(y), "sin(x*e^-y)*e^y [Original]"),
        pygame.K_0: (lambda x, y: 0.0, "0 [Plano]"),
    }
    return functions.get(key, (None, None))

class DiskVisualizer:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1280, 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Visualizador 3D - XY no plano, Z para cima")
        
        # Parâmetros da câmera isométrica
        self.camera_distance = 15
        self.camera_angle_x = 35  # ângulo vertical (elevação)
        self.camera_angle_y = 45  # ângulo horizontal (azimute)
        
        # Parâmetros do disco
        self.center_x = 0.0
        self.center_y = 0.0
        self.radius = 1.0
        self.show_mesh = False
        self.show_debug = True
        
        # Função atual
        self.current_func = lambda x, y: np.sin(x) * np.cos(y)
        self.func_name = "sin(x) * cos(y)"
        
        # Velocidades
        self.move_speed = 0.05
        self.radius_speed = 0.1
        
        # Estatísticas
        self.fps = 0
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.Font(None, 28)
        self.font_normal = pygame.font.Font(None, 22)
        self.font_small = pygame.font.Font(None, 18)
        
        # Resolução da malha
        self.mesh_resolution = 400
        self.curve_resolution = 1000
        self.curve_range = 50.0
        
        # Pré-calcular valores para a malha do disco
        self.precompute_disk()
        
        self.running = True
    
    def precompute_disk(self):
        """Pré-calcula os pontos da malha do disco"""
        res = self.mesh_resolution
        self.theta = np.linspace(0, 2*np.pi, res)
        self.r_vals = np.linspace(0, 1, res)
    
    def set_function(self, func, name):
        """Muda a função atual"""
        self.current_func = func
        self.func_name = name
    
    def project_3d_to_2d(self, x, y, z):
        """
        Projeta um ponto 3D para 2D usando projeção isométrica
        CORREÇÃO: XY no plano, Z para cima
        """
        # Rotação em torno de Y (azimute)
        x1 = x * math.cos(math.radians(self.camera_angle_y)) - z * math.sin(math.radians(self.camera_angle_y))
        y1 = y
        z1 = x * math.sin(math.radians(self.camera_angle_y)) + z * math.cos(math.radians(self.camera_angle_y))
        
        # Rotação em torno de X (elevação)
        x2 = x1
        y2 = y1 * math.cos(math.radians(self.camera_angle_x)) - z1 * math.sin(math.radians(self.camera_angle_x))
        z2 = y1 * math.sin(math.radians(self.camera_angle_x)) + z1 * math.cos(math.radians(self.camera_angle_x))
        
        # Aplicar distância da câmera
        scale = 40 / (1 + z2/self.camera_distance)  # Perspectiva simples
        screen_x = self.width // 2 + x2 * scale
        screen_y = self.height // 2 - y2 * scale  # Inverter Y para tela
        
        return int(screen_x), int(screen_y)
    
    def draw_line_3d(self, p1, p2, color, width=1):
        """Desenha uma linha 3D"""
        x1, y1 = self.project_3d_to_2d(*p1)
        x2, y2 = self.project_3d_to_2d(*p2)
        pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), width)
    
    def draw_point_3d(self, p, color, size=3):
        """Desenha um ponto 3D"""
        x, y = self.project_3d_to_2d(*p)
        pygame.draw.circle(self.screen, color, (x, y), size)
    
    def render_grid(self):
        """Renderiza a grade no plano XY"""
        size = 5.0
        step = 1.0
        color = (80, 80, 80)
        
        # Linhas paralelas a X (y varia)
        for y in np.arange(-size, size + step, step):
            p1 = (-size, y, 0)
            p2 = (size, y, 0)
            self.draw_line_3d(p1, p2, color, 1)
        
        # Linhas paralelas a Y (x varia)
        for x in np.arange(-size, size + step, step):
            p1 = (x, -size, 0)
            p2 = (x, size, 0)
            self.draw_line_3d(p1, p2, color, 1)
        
        # Eixos coordenados
        # Eixo X (vermelho) - horizontal no plano
        self.draw_line_3d((-size, 0, 0), (size, 0, 0), (255, 0, 0), 3)
        
        # Eixo Y (verde) - vertical no plano
        self.draw_line_3d((0, -size, 0), (0, size, 0), (0, 255, 0), 3)
        
        # Eixo Z (azul) - para cima
        self.draw_line_3d((0, 0, 0), (0, 0, 3), (0, 0, 255), 3)
    
    def render_plane_lines(self):
        """Renderiza as retas no plano XY (x=x0 e y=y0)"""
        range_val = 5.0
        
        # Reta x = center_x (ao longo de Y) - VERMELHA
        p1 = (self.center_x, -range_val, 0)
        p2 = (self.center_x, range_val, 0)
        self.draw_line_3d(p1, p2, (255, 100, 100), 2)
        
        # Reta y = center_y (ao longo de X) - VERDE
        p1 = (-range_val, self.center_y, 0)
        p2 = (range_val, self.center_y, 0)
        self.draw_line_3d(p1, p2, (100, 255, 100), 2)
    
    def render_surface_curves(self):
        """Renderiza as curvas na superfície"""
        # Curva em X: u(x, center_y) - VERMELHA
        points = []
        for x in np.linspace(-self.curve_range, self.curve_range, self.curve_resolution):
            z = self.current_func(x, self.center_y)
            points.append((x, self.center_y, z))
        
        for i in range(len(points) - 1):
            self.draw_line_3d(points[i], points[i+1], (255, 50, 50), 2)
        
        # Curva em Y: u(center_x, y) - VERDE
        points = []
        for y in np.linspace(-self.curve_range, self.curve_range, self.curve_resolution):
            z = self.current_func(self.center_x, y)
            points.append((self.center_x, y, z))
        
        for i in range(len(points) - 1):
            self.draw_line_3d(points[i], points[i+1], (50, 255, 50), 2)
    
    def render_disk_plane(self):
        """Renderiza o disco no plano XY"""
        # Pontos da borda
        border_points = []
        for theta in self.theta:
            x = self.center_x + self.radius * np.cos(theta)
            y = self.center_y + self.radius * np.sin(theta)
            border_points.append((x, y, 0))
        
        # Desenhar borda
        for i in range(len(border_points)):
            p1 = border_points[i]
            p2 = border_points[(i+1) % len(border_points)]
            self.draw_line_3d(p1, p2, (255, 255, 0), 2)
        
        # Desenhar centro
        self.draw_point_3d((self.center_x, self.center_y, 0), (255, 0, 0), 5)
    
    def render_disk_surface(self):
        """Renderiza o disco na superfície z = u(x,y)"""
        # Pontos da borda na superfície
        border_points = []
        for theta in self.theta:
            x = self.center_x + self.radius * np.cos(theta)
            y = self.center_y + self.radius * np.sin(theta)
            z = self.current_func(x, y)
            border_points.append((x, y, z))
        
        # Desenhar borda
        for i in range(len(border_points)):
            p1 = border_points[i]
            p2 = border_points[(i+1) % len(border_points)]
            self.draw_line_3d(p1, p2, (255, 255, 0), 2)
        
        # Linhas verticais da borda (plano -> superfície)
        for i, theta in enumerate(self.theta):
            x = self.center_x + self.radius * np.cos(theta)
            y = self.center_y + self.radius * np.sin(theta)
            z = self.current_func(x, y)
            self.draw_line_3d((x, y, 0), (x, y, z), (150, 150, 150), 1)
        
        # Desenhar centro na superfície
        z_center = self.current_func(self.center_x, self.center_y)
        self.draw_point_3d((self.center_x, self.center_y, z_center), (255, 255, 255), 6)
        
        # Linha vertical do centro
        self.draw_line_3d((self.center_x, self.center_y, 0), 
                          (self.center_x, self.center_y, z_center), 
                          (255, 255, 0), 2)
    
    def render_debug_info(self):
        """Renderiza informações de debug"""
        # Fundos semi-transparentes
        s = pygame.Surface((400, 300), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (10, 10))
        
        s = pygame.Surface((350, 150), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (self.width - 360, 10))
        
        s = pygame.Surface((300, 130), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (10, self.height - 210))
        
        s = pygame.Surface((250, 100), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (self.width - 260, self.height - 160))
        
        s = pygame.Surface((900, 120), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        self.screen.blit(s, (self.width // 2 - 450, self.height - 130))
        
        # Função atual
        y = 20
        text = self.font_title.render(f"FUNÇÃO: {self.func_name}", True, (255, 255, 0))
        self.screen.blit(text, (20, y))
        y += 35
        
        # Informações do centro
        x_right = self.width - 350
        h = 0.01
        du_dx = (self.current_func(self.center_x + h, self.center_y) - 
                 self.current_func(self.center_x - h, self.center_y)) / (2*h)
        du_dy = (self.current_func(self.center_x, self.center_y + h) - 
                 self.current_func(self.center_x, self.center_y - h)) / (2*h)
        
        center_info = [
            ("CENTRO DO DISCO", (255, 200, 100)),
            (f"Posição: ({self.center_x:.2f}, {self.center_y:.2f})", (200, 200, 255)),
            (f"u(x,y) = {self.current_func(self.center_x, self.center_y):.4f}", (100, 255, 100)),
            (f"∂u/∂x = {du_dx:.4f}", (255, 150, 150)),
            (f"∂u/∂y = {du_dy:.4f}", (150, 255, 150)),
        ]
        
        y_right = 20
        for text, color in center_info:
            surf = self.font_normal.render(text, True, color)
            self.screen.blit(surf, (x_right, y_right))
            y_right += 25
        
        # Parâmetros do disco
        y_bottom = self.height - 200
        disk_info = [
            ("DISCO", (100, 200, 255)),
            (f"Centro: ({self.center_x:.2f}, {self.center_y:.2f})", (200, 200, 200)),
            (f"Raio: {self.radius:.2f}", (200, 200, 200)),
            (f"Modo: {'SUPERFÍCIE' if self.show_mesh else 'PLANO'}", (255, 200, 0)),
        ]
        
        for text, color in disk_info:
            surf = self.font_normal.render(text, True, color)
            self.screen.blit(surf, (20, y_bottom))
            y_bottom += 25
        
        # Performance
        x_right_perf = self.width - 250
        y_perf = self.height - 150
        perf_info = [
            ("PERFORMANCE", (0, 255, 255)),
            (f"FPS: {self.fps}", (0, 255, 0) if self.fps > 50 else (255, 255, 0)),
        ]
        
        for text, color in perf_info:
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (x_right_perf, y_perf))
            y_perf += 20
        
        # Controles
        y_controls = self.height - 120
        controls = [
            ("CONTROLES:", (255, 255, 255)),
            ("SETAS: Mover centro | Z/X: Raio | TAB: Plano/Superfície | D: Debug", (180, 180, 180)),
            ("1-0: Trocar função | R: Reset", (180, 180, 180)),
            ("EIXOS: X (vermelho) | Y (verde) | Z (azul para cima)", (255, 255, 255)),
            ("Retas: Vermelha (x=x0) | Verde (y=y0)", (255, 200, 100)),
            ("Curvas: Vermelha (u(x,y0)) | Verde (u(x0,y))", (255, 200, 100)),
        ]
        
        x_center = self.width // 2 - 450
        for text, color in controls:
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (x_center, y_controls))
            y_controls += 20
    
    def run(self):
        last_pos = (self.center_x, self.center_y)
        last_radius = self.radius
        fps_counter = 0
        fps_timer = time.time()
        
        while self.running:
            # FPS
            fps_counter += 1
            if time.time() - fps_timer >= 1.0:
                self.fps = fps_counter
                fps_counter = 0
                fps_timer = time.time()
            
            # Eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_TAB:
                        self.show_mesh = not self.show_mesh
                    elif event.key == pygame.K_d:
                        self.show_debug = not self.show_debug
                    elif event.key == pygame.K_r:
                        self.center_x = 0
                        self.center_y = 0
                        self.radius = 1.0
                    else:
                        func, name = get_function(event.key)
                        if func is not None:
                            self.set_function(func, name)
            
            # Controle contínuo
            keys = pygame.key.get_pressed()
            
            # CORREÇÃO: Setas movem no plano XY
            if keys[pygame.K_LEFT]:
                self.center_x -= self.move_speed
            if keys[pygame.K_RIGHT]:
                self.center_x += self.move_speed
            if keys[pygame.K_UP]:
                self.center_y += self.move_speed
            if keys[pygame.K_DOWN]:
                self.center_y -= self.move_speed
            
            if keys[pygame.K_z]:
                self.radius = max(0.01, self.radius - self.radius_speed)
            if keys[pygame.K_x]:
                self.radius = min(50.0, self.radius + self.radius_speed)
            
            # Limpar tela
            self.screen.fill((20, 20, 20))
            
            # Renderizar tudo
            # self.render_grid()
            self.render_plane_lines()
            
            if self.show_mesh:
                self.render_disk_surface()
                self.render_surface_curves()
            else:
                self.render_disk_plane()
            
            if self.show_debug:
                self.render_debug_info()
            
            # Atualizar tela
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    app = DiskVisualizer()
    app.run()