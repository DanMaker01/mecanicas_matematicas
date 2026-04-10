import pygame
import math
import sys
import numpy as np
from scipy.interpolate import CubicSpline

# ============================================================================
# 1. Geometria Diferencial - Representação por Curvatura
# ============================================================================

def compute_curvature_and_tangent(points):
    """
    Computa a curvatura κ(s) e ângulo tangente θ(s) para uma curva
    parametrizada por comprimento de arco.
    
    Retorna:
        s: comprimentos de arco
        theta: ângulo tangente em radianos
        kappa: curvatura
        points: pontos originais
    """
    if len(points) < 3:
        return [], [], [], points
    
    # Calcula comprimentos de arco
    s = [0.0]
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        s.append(s[-1] + math.hypot(dx, dy))
    
    total_length = s[-1]
    
    # Calcula ângulos tangentes
    theta = [0.0]
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        angle = math.atan2(dy, dx)
        theta.append(angle)
    
    # Suaviza ângulos para evitar descontinuidades
    for i in range(1, len(theta)):
        diff = theta[i] - theta[i-1]
        if diff > math.pi:
            theta[i] -= 2*math.pi
        elif diff < -math.pi:
            theta[i] += 2*math.pi
    
    # Calcula curvatura κ = dθ/ds
    kappa = [0.0]
    for i in range(1, len(theta)):
        if s[i] - s[i-1] > 0:
            kappa.append((theta[i] - theta[i-1]) / (s[i] - s[i-1]))
        else:
            kappa.append(0.0)
    
    return s, theta, kappa, points

def reconstruct_curve_from_curvature(kappa_func, total_length, num_points=500, 
                                      initial_pos=(0,0), initial_angle=0):
    """
    Reconstrói uma curva a partir da função curvatura κ(s).
    Usa integração numérica: 
        θ(s) = ∫ κ(s) ds + θ0
        x(s) = ∫ cos(θ(s)) ds + x0
        y(s) = ∫ sin(θ(s)) ds + y0
    """
    s = np.linspace(0, total_length, num_points)
    
    # Calcula ângulo integrando curvatura usando método do trapézio
    theta = np.zeros(num_points)
    for i in range(1, num_points):
        # Método do trapézio para integração
        ds = s[i] - s[i-1]
        theta[i] = theta[i-1] + (kappa_func(s[i-1]) + kappa_func(s[i])) * ds / 2
    theta += initial_angle
    
    # Calcula posição integrando ângulo
    x = np.zeros(num_points)
    y = np.zeros(num_points)
    
    for i in range(1, num_points):
        ds = s[i] - s[i-1]
        # Método do trapézio para integração de cos e sin
        cos_avg = (math.cos(theta[i-1]) + math.cos(theta[i])) / 2
        sin_avg = (math.sin(theta[i-1]) + math.sin(theta[i])) / 2
        x[i] = x[i-1] + cos_avg * ds
        y[i] = y[i-1] + sin_avg * ds
    
    # Transladar para posição inicial desejada
    x += initial_pos[0] - x[0]
    y += initial_pos[1] - y[0]
    
    return [(x[i], y[i]) for i in range(num_points)]

class DifferentialGeometryInterpolation:
    """
    Interpolação de curvas usando geometria diferencial.
    Preserva comprimento de arco interpolando curvatura.
    """
    
    def __init__(self, curve1_points, curve2_points, target_length, num_samples=500):
        self.target_length = target_length
        self.num_samples = num_samples
        
        # Garantir que ambas as curvas estejam parametrizadas por comprimento de arco
        self.curve1 = reparametrize_by_arc_length(curve1_points, target_length, num_samples)
        self.curve2 = reparametrize_by_arc_length(curve2_points, target_length, num_samples)
        
        # Computar curvatura e ângulo para cada curva
        self.s1, self.theta1, self.kappa1, _ = compute_curvature_and_tangent(self.curve1)
        self.s2, self.theta2, self.kappa2, _ = compute_curvature_and_tangent(self.curve2)
        
        # Criar funções interpoladoras para curvatura
        # Garantir que temos pontos suficientes
        if len(self.s1) < 4:
            self.s1 = np.linspace(0, target_length, num_samples)
            self.kappa1 = np.zeros(num_samples)
        
        if len(self.s2) < 4:
            self.s2 = np.linspace(0, target_length, num_samples)
            self.kappa2 = np.zeros(num_samples)
        
        try:
            self.kappa1_func = CubicSpline(self.s1, self.kappa1, bc_type='natural')
            self.kappa2_func = CubicSpline(self.s2, self.kappa2, bc_type='natural')
        except:
            # Fallback para interpolação linear se CubicSpline falhar
            print("Usando interpolação linear para curvatura")
            self.kappa1_func = lambda s: np.interp(s, self.s1, self.kappa1)
            self.kappa2_func = lambda s: np.interp(s, self.s2, self.kappa2)
        
        # Ângulos iniciais (em s=0)
        self.theta1_0 = self.theta1[0] if len(self.theta1) > 0 else 0
        self.theta2_0 = self.theta2[0] if len(self.theta2) > 0 else 0
        
        # Posições iniciais
        self.pos1_0 = self.curve1[0]
        self.pos2_0 = self.curve2[0]
        
        print("=" * 60)
        print("GEOMETRIA DIFERENCIAL - ANÁLISE DAS CURVAS")
        print("=" * 60)
        print(f"Curva 1 - Comprimento: {self.s1[-1]:.3f}, κ médio: {np.mean(self.kappa1):.6f}")
        print(f"Curva 2 - Comprimento: {self.s2[-1]:.3f}, κ médio: {np.mean(self.kappa2):.6f}")
        print(f"Curva 1 - Ângulo inicial: {math.degrees(self.theta1_0):.2f}°")
        print(f"Curva 2 - Ângulo inicial: {math.degrees(self.theta2_0):.2f}°")
        print()
    
    def interpolate_curvature(self, c, s):
        """
        Interpola a curvatura em um dado s.
        Método: Interpolação linear das curvaturas
        """
        kappa1 = self.kappa1_func(s)
        kappa2 = self.kappa2_func(s)
        return (1 - c) * kappa1 + c * kappa2
    
    def interpolate_angle_initial(self, c):
        """Interpola o ângulo inicial"""
        return (1 - c) * self.theta1_0 + c * self.theta2_0
    
    def interpolate_position_initial(self, c):
        """Interpola a posição inicial"""
        x = (1 - c) * self.pos1_0[0] + c * self.pos2_0[0]
        y = (1 - c) * self.pos1_0[1] + c * self.pos2_0[1]
        return (x, y)
    
    def get_curve(self, c):
        """
        Gera a curva interpolada usando curvatura interpolada.
        Preserva comprimento de arco naturalmente.
        """
        # Cria função de curvatura interpolada
        def kappa_interp(s):
            return self.interpolate_curvature(c, s)
        
        # Ângulo e posição inicial interpolados
        theta0 = self.interpolate_angle_initial(c)
        pos0 = self.interpolate_position_initial(c)
        
        # Reconstrói curva
        return reconstruct_curve_from_curvature(
            kappa_interp, 
            self.target_length, 
            self.num_samples,
            pos0,
            theta0
        )
    
    def compute_curvature_statistics(self):
        """Computa estatísticas das curvaturas para análise"""
        s_plot = np.linspace(0, self.target_length, 200)
        kappa1_plot = [self.kappa1_func(s) for s in s_plot]
        kappa2_plot = [self.kappa2_func(s) for s in s_plot]
        
        print("Estatísticas de Curvatura:")
        print(f"  κ1 - média: {np.mean(kappa1_plot):.6f}, max: {np.max(kappa1_plot):.6f}")
        print(f"  κ2 - média: {np.mean(kappa2_plot):.6f}, max: {np.max(kappa2_plot):.6f}")
        print()

# ============================================================================
# 2. Método Alternativo: Interpolação de Ângulo Direto
# ============================================================================

class AngleBasedInterpolation:
    """
    Interpolação baseada em ângulo tangente (mais simples).
    """
    
    def __init__(self, curve1_points, curve2_points, target_length, num_samples=500):
        self.target_length = target_length
        self.num_samples = num_samples
        
        self.curve1 = reparametrize_by_arc_length(curve1_points, target_length, num_samples)
        self.curve2 = reparametrize_by_arc_length(curve2_points, target_length, num_samples)
        
        _, self.theta1, _, _ = compute_curvature_and_tangent(self.curve1)
        _, self.theta2, _, _ = compute_curvature_and_tangent(self.curve2)
        
        self.s = np.linspace(0, target_length, num_samples)
        
        # Garantir que temos arrays do mesmo tamanho
        if len(self.theta1) < num_samples:
            self.theta1 = np.interp(self.s, np.linspace(0, target_length, len(self.theta1)), self.theta1)
        if len(self.theta2) < num_samples:
            self.theta2 = np.interp(self.s, np.linspace(0, target_length, len(self.theta2)), self.theta2)
        
        # Criar splines para ângulos
        try:
            self.theta1_func = CubicSpline(self.s, self.theta1[:len(self.s)], bc_type='natural')
            self.theta2_func = CubicSpline(self.s, self.theta2[:len(self.s)], bc_type='natural')
        except:
            print("Usando interpolação linear para ângulos")
            self.theta1_func = lambda s: np.interp(s, self.s, self.theta1)
            self.theta2_func = lambda s: np.interp(s, self.s, self.theta2)
        
        self.pos1_0 = self.curve1[0]
        self.pos2_0 = self.curve2[0]
    
    def get_curve(self, c):
        """Interpola ângulo tangente diretamente"""
        s = self.s
        
        # Interpola ângulo
        theta = (1 - c) * self.theta1_func(s) + c * self.theta2_func(s)
        
        # Interpola posição inicial
        x0 = (1 - c) * self.pos1_0[0] + c * self.pos2_0[0]
        y0 = (1 - c) * self.pos1_0[1] + c * self.pos2_0[1]
        
        # Reconstrói curva
        x = np.zeros(len(s))
        y = np.zeros(len(s))
        x[0] = x0
        y[0] = y0
        
        for i in range(1, len(s)):
            ds = s[i] - s[i-1]
            cos_avg = (math.cos(theta[i-1]) + math.cos(theta[i])) / 2
            sin_avg = (math.sin(theta[i-1]) + math.sin(theta[i])) / 2
            x[i] = x[i-1] + cos_avg * ds
            y[i] = y[i-1] + sin_avg * ds
        
        return [(x[i], y[i]) for i in range(len(s))]

# ============================================================================
# 3. Utilitários
# ============================================================================

def compute_arc_length(points):
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        total += math.hypot(dx, dy)
    return total

def reparametrize_by_arc_length(points, target_length, num_samples):
    if len(points) < 2:
        return points
    
    arc_lengths = [0.0]
    for i in range(1, len(points)):
        dx = points[i][0] - points[i-1][0]
        dy = points[i][1] - points[i-1][1]
        arc_lengths.append(arc_lengths[-1] + math.hypot(dx, dy))
    
    current_length = arc_lengths[-1]
    if current_length == 0:
        return points
    
    scale = target_length / current_length
    scaled_s = [s * scale for s in arc_lengths]
    uniform_s = [target_length * i / (num_samples - 1) for i in range(num_samples)]
    
    resampled = []
    idx = 0
    for s in uniform_s:
        while idx < len(scaled_s) - 1 and scaled_s[idx + 1] < s:
            idx += 1
        
        if idx >= len(points) - 1:
            resampled.append(points[-1])
        else:
            s0, s1 = scaled_s[idx], scaled_s[idx + 1]
            p0, p1 = points[idx], points[idx + 1]
            alpha = (s - s0) / (s1 - s0) if s1 - s0 > 0 else 0
            x = p0[0] + alpha * (p1[0] - p0[0])
            y = p0[1] + alpha * (p1[1] - p0[1])
            resampled.append((x, y))
    
    return resampled

# ============================================================================
# 4. Definição das Curvas
# ============================================================================

L = 300.0

# Curva 1: Linha reta
g1_points = [(t, 0.0) for t in np.linspace(0, L, 500)]

# Curva 2: Círculo
circle_center = (L/2, 200)
r = L / (2 * math.pi)

def g2_original(t):
    return (circle_center[0] + 2*r * math.cos(t)*math.sin(2*t), 
            circle_center[1] + (1/2)*r * math.sin(t))

t_values = np.linspace(0, 2*math.pi, 1000)
g2_raw = [g2_original(t) for t in t_values]
g2_points = reparametrize_by_arc_length(g2_raw, L, 500)

# ============================================================================
# 5. Pygame Visualização
# ============================================================================

pygame.init()
screen = pygame.display.set_mode((1000, 700))
pygame.display.set_caption("Geometria Diferencial - Interpolação com Preservação de Comprimento")
clock = pygame.time.Clock()

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
GRAY = (200, 200, 200)

font = pygame.font.SysFont("Arial", 14)
title_font = pygame.font.SysFont("Arial", 16, bold=True)
small_font = pygame.font.SysFont("Arial", 12)

# Configuração
offset_x = 80
offset_y = 80
c_value = 0.0
dragging_slider = False
slider_x = 150
slider_y = 650
slider_width = 500
slider_height = 10

# Inicializa métodos
print("Inicializando interpolação por curvatura...")
differential_method = DifferentialGeometryInterpolation(g1_points, g2_points, L, num_samples=500)
print("\nInicializando interpolação por ângulo...")
angle_method = AngleBasedInterpolation(g1_points, g2_points, L, num_samples=500)

# Escolha do método (True = curvatura, False = ângulo)
use_curvature_method = True

def world_to_screen(point):
    return (offset_x + point[0], offset_y + point[1])

def draw_curve(points, color, width=2):
    if len(points) < 2:
        return
    screen_points = [world_to_screen(p) for p in points]
    pygame.draw.lines(screen, color, False, screen_points, width)

def draw_axes():
    origin = world_to_screen((0, 0))
    x_end = world_to_screen((L, 0))
    y_end = world_to_screen((0, 300))
    pygame.draw.line(screen, GRAY, origin, x_end, 1)
    pygame.draw.line(screen, GRAY, origin, y_end, 1)
    
    for x in range(0, int(L)+1, 50):
        tick_start = world_to_screen((x, -5))
        tick_end = world_to_screen((x, 5))
        pygame.draw.line(screen, GRAY, tick_start, tick_end, 1)
        label = small_font.render(str(x), True, GRAY)
        screen.blit(label, (tick_start[0] - 10, tick_start[1] + 5))

def draw_slider():
    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
    pygame.draw.rect(screen, GRAY, slider_rect)
    handle_x = slider_x + c_value * slider_width
    pygame.draw.circle(screen, BLUE, (int(handle_x), slider_y + slider_height//2), 10)
    return pygame.Rect(handle_x - 10, slider_y - 10, 20, 20)

def draw_curvature_plot():
    """Desenha gráfico da curvatura interpolada"""
    if not use_curvature_method:
        return
    
    plot_x = 700
    plot_y = 450
    plot_w = 250
    plot_h = 150
    
    # Fundo do gráfico
    pygame.draw.rect(screen, WHITE, (plot_x, plot_y, plot_w, plot_h))
    pygame.draw.rect(screen, BLACK, (plot_x, plot_y, plot_w, plot_h), 1)
    
    # Amostra curvaturas
    s_plot = np.linspace(0, L, 200)
    try:
        kappa1 = [differential_method.kappa1_func(s) for s in s_plot]
        kappa2 = [differential_method.kappa2_func(s) for s in s_plot]
        kappa_interp = [differential_method.interpolate_curvature(c_value, s) for s in s_plot]
    except:
        return
    
    # Escala
    max_kappa = max(max(kappa1), max(kappa2), max(kappa_interp))
    min_kappa = min(min(kappa1), min(kappa2), min(kappa_interp))
    if max_kappa == min_kappa:
        max_kappa = min_kappa + 1
    
    # Desenha curvas de curvatura
    def kappa_to_y(k):
        return plot_y + plot_h - (k - min_kappa) / (max_kappa - min_kappa) * plot_h
    
    # Curva 1
    points1 = [(plot_x + (s/L) * plot_w, kappa_to_y(k)) for s, k in zip(s_plot, kappa1)]
    pygame.draw.lines(screen, RED, False, points1, 2)
    
    # Curva 2
    points2 = [(plot_x + (s/L) * plot_w, kappa_to_y(k)) for s, k in zip(s_plot, kappa2)]
    pygame.draw.lines(screen, BLUE, False, points2, 2)
    
    # Curva interpolada
    points_interp = [(plot_x + (s/L) * plot_w, kappa_to_y(k)) for s, k in zip(s_plot, kappa_interp)]
    pygame.draw.lines(screen, GREEN, False, points_interp, 3)
    
    # Labels
    label = small_font.render("Curvatura κ(s)", True, BLACK)
    screen.blit(label, (plot_x + 10, plot_y - 15))
    label = small_font.render(f"κ ∈ [{min_kappa:.4f}, {max_kappa:.4f}]", True, BLACK)
    screen.blit(label, (plot_x + 10, plot_y + plot_h + 5))

def draw_info(curve_points):
    y = 20
    
    # Título
    title = title_font.render("Geometria Diferencial - Interpolação de Curvatura", True, BLACK)
    screen.blit(title, (20, y))
    y += 30
    
    # Método atual
    method_text = "Interpolação de Curvatura κ(s)" if use_curvature_method else "Interpolação de Ângulo θ(s)"
    text = font.render(method_text, True, GREEN if use_curvature_method else CYAN)
    screen.blit(text, (20, y))
    y += 25
    
    # Comprimento
    length = compute_arc_length(curve_points)
    diff = length - L
    
    color = GREEN if abs(diff) < 0.01 else ORANGE if abs(diff) < 0.1 else RED
    len_text = font.render(f"Comprimento: {length:.6f} (alvo: {L:.3f})", True, color)
    screen.blit(len_text, (20, y))
    y += 22
    
    diff_text = font.render(f"Diferença: {diff:+.6f}", True, color)
    screen.blit(diff_text, (20, y))
    y += 30
    
    # Informações geométricas
    if use_curvature_method:
        theta0 = differential_method.interpolate_angle_initial(c_value)
        pos0 = differential_method.interpolate_position_initial(c_value)
        
        info_text = font.render(f"Ângulo inicial: {math.degrees(theta0):.2f}°", True, BLACK)
        screen.blit(info_text, (20, y))
        y += 20
        
        info_text = font.render(f"Posição inicial: ({pos0[0]:.1f}, {pos0[1]:.1f})", True, BLACK)
        screen.blit(info_text, (20, y))
        y += 30
    
    # Legenda
    legend_y = y
    pygame.draw.line(screen, RED, (20, legend_y + 8), (60, legend_y + 8), 2)
    text = font.render("Curva 1 (linha reta)", True, RED)
    screen.blit(text, (65, legend_y))
    
    pygame.draw.line(screen, BLUE, (20, legend_y + 28), (60, legend_y + 28), 2)
    text = font.render("Curva 2 (círculo)", True, BLUE)
    screen.blit(text, (65, legend_y + 20))
    
    color = GREEN if use_curvature_method else CYAN
    pygame.draw.line(screen, color, (20, legend_y + 48), (60, legend_y + 48), 3)
    text = font.render("Curva interpolada", True, color)
    screen.blit(text, (65, legend_y + 40))
    
    # Instruções
    inst_y = 620
    inst_text = font.render("← →  ou arraste slider: muda c | ESPAÇO: alterna método", True, BLACK)
    screen.blit(inst_text, (20, inst_y))
    inst_text2 = small_font.render("Método 1: Interpola curvatura (preserva comprimento perfeitamente)", True, BLACK)
    screen.blit(inst_text2, (20, inst_y + 20))
    inst_text3 = small_font.render("Método 2: Interpola ângulo (simples, mas pode ter pequenas variações)", True, BLACK)
    screen.blit(inst_text3, (20, inst_y + 35))

# Loop principal
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                use_curvature_method = not use_curvature_method
                print(f"\nAlternando para: {'Curvatura' if use_curvature_method else 'Ângulo'}")
            elif event.key == pygame.K_LEFT:
                c_value = max(0, c_value - 0.02)
            elif event.key == pygame.K_RIGHT:
                c_value = min(1, c_value + 0.02)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_rect = draw_slider()
            if handle_rect.collidepoint(event.pos):
                dragging_slider = True
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging_slider = False
        elif event.type == pygame.MOUSEMOTION and dragging_slider:
            mouse_x, _ = event.pos
            c_value = (mouse_x - slider_x) / slider_width
            c_value = max(0.0, min(1.0, c_value))
    
    screen.fill(WHITE)
    draw_axes()
    
    # Desenha curvas originais
    draw_curve(g1_points, RED, 2)
    draw_curve(g2_points, BLUE, 2)
    
    # Gera curva interpolada
    if use_curvature_method:
        curve_points = differential_method.get_curve(c_value)
    else:
        curve_points = angle_method.get_curve(c_value)
    
    # Desenha curva interpolada
    color = GREEN if use_curvature_method else CYAN
    draw_curve(curve_points, color, 3)
    
    # Desenha gráfico de curvatura
    if use_curvature_method:
        draw_curvature_plot()
    
    draw_slider()
    draw_info(curve_points)
    
    # Debug no console para variações significativas
    length = compute_arc_length(curve_points)
    if abs(length - L) > 0.1 and use_curvature_method:
        print(f"⚠️ c={c_value:.3f}: comprimento={length:.6f} (diferença={length-L:+.6f})")
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()