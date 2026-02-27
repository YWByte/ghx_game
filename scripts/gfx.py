"""
gfx.py —— 共享渲染工具库
Google Doodle 风格：柔和阴影、圆润形状、明亮配色、Material 质感
"""

import pygame
import math

# ============================================================
#  Google 风格调色板
# ============================================================
# 主色
BLUE = (66, 133, 244)
RED = (234, 67, 53)
YELLOW = (251, 188, 4)
GREEN = (52, 168, 83)

# 柔和辅助色
SOFT_BLUE = (162, 199, 254)
SOFT_RED = (246, 166, 159)
SOFT_YELLOW = (253, 226, 147)
SOFT_GREEN = (161, 222, 175)

# 中性色
WHITE = (255, 255, 255)
NEAR_WHITE = (248, 249, 250)
LIGHT_GRAY = (232, 234, 237)
MID_GRAY = (189, 193, 198)
DARK_GRAY = (95, 99, 104)
CHARCOAL = (60, 64, 67)
NEAR_BLACK = (32, 33, 36)

# 场景色
GRASS_LIGHT = (168, 218, 131)
GRASS = (124, 195, 93)
GRASS_DARK = (98, 168, 72)
EARTH_LIGHT = (210, 180, 140)
EARTH = (180, 150, 110)
EARTH_DARK = (150, 125, 90)
WOOD = (160, 110, 60)
WOOD_DARK = (120, 82, 42)
WATER = (100, 181, 246)
WATER_LIGHT = (144, 202, 249)
WATER_DARK = (66, 165, 245)

# 垃圾桶色（更鲜艳的 Google 风）
BIN_BLUE = (66, 133, 244)
BIN_GREEN = (52, 168, 83)
BIN_RED = (234, 67, 53)
BIN_GRAY = (154, 160, 166)


# ============================================================
#  绘图工具函数
# ============================================================

def draw_shadow(surface, rect, radius=8, offset=(3, 4), alpha=40):
    """绘制柔和投影"""
    shadow = pygame.Surface((rect.width + 6, rect.height + 6), pygame.SRCALPHA)
    shadow_rect = pygame.Rect(3, 3, rect.width, rect.height)
    pygame.draw.rect(shadow, (0, 0, 0, alpha), shadow_rect, border_radius=radius)
    surface.blit(shadow, (rect.x + offset[0] - 3, rect.y + offset[1] - 3))


def draw_circle_shadow(surface, cx, cy, radius, offset=(2, 3), alpha=35):
    """绘制圆形投影"""
    s = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
    pygame.draw.circle(s, (0, 0, 0, alpha),
                       (radius + 5, radius + 5), radius)
    surface.blit(s, (cx - radius - 5 + offset[0], cy - radius - 5 + offset[1]))


def draw_rounded_card(surface, rect, color, radius=12, shadow=True, border=None):
    """绘制 Material 风格圆角卡片"""
    if shadow:
        draw_shadow(surface, rect, radius, (2, 3), 45)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    # 顶部高光条
    highlight = pygame.Surface((rect.width - 4, 3), pygame.SRCALPHA)
    highlight.fill((*[min(255, c + 35) for c in color[:3]], 80))
    surface.blit(highlight, (rect.x + 2, rect.y + 2))
    if border:
        pygame.draw.rect(surface, border, rect, width=2, border_radius=radius)


def draw_pill_badge(surface, x, y, text, font, bg_color, text_color=WHITE, shadow=True):
    """绘制药丸形标签"""
    text_surf = font.render(text, True, text_color)
    tw, th = text_surf.get_size()
    pad_x, pad_y = 14, 6
    w = tw + pad_x * 2
    h = th + pad_y * 2
    rect = pygame.Rect(x - w // 2, y - h // 2, w, h)

    if shadow:
        draw_shadow(surface, rect, h // 2, (1, 2), 35)
    pygame.draw.rect(surface, bg_color, rect, border_radius=h // 2)
    # 高光
    hl = pygame.Surface((w - 4, h // 3), pygame.SRCALPHA)
    hl.fill((255, 255, 255, 40))
    surface.blit(hl, (rect.x + 2, rect.y + 1))
    surface.blit(text_surf, (x - tw // 2, y - th // 2))
    return rect


def draw_gradient_v(surface, rect, color_top, color_bottom):
    """绘制垂直渐变矩形（优化：只绘制 rect 内）"""
    x, y, w, h = rect
    for row in range(h):
        ratio = row / max(1, h - 1)
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (x, y + row), (x + w - 1, y + row))


def draw_soft_circle(surface, cx, cy, radius, color, highlight=True):
    """绘制带高光的柔和圆"""
    pygame.draw.circle(surface, color, (cx, cy), radius)
    if highlight and radius > 4:
        hl_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        hl_r = max(2, radius // 3)
        pygame.draw.circle(hl_surf, (255, 255, 255, 55),
                           (radius - radius // 4, radius - radius // 4), hl_r)
        surface.blit(hl_surf, (cx - radius, cy - radius))


def draw_soft_ellipse(surface, rect, color, highlight=True):
    """绘制带高光的柔和椭圆"""
    pygame.draw.ellipse(surface, color, rect)
    if highlight:
        r = pygame.Rect(rect[0] + rect[2] // 6, rect[1] + rect[3] // 6,
                        rect[2] // 2, rect[3] // 3)
        s = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (255, 255, 255, 45), (0, 0, r.width, r.height))
        surface.blit(s, r.topleft)


def lerp_color(c1, c2, t):
    """线性插值两个颜色"""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def ease_out_quad(t):
    """缓出二次动画曲线"""
    return 1 - (1 - t) ** 2


def draw_progress_bar(surface, x, y, width, height, progress, bg_color=LIGHT_GRAY,
                      fill_color=GREEN, radius=None):
    """绘制圆角进度条"""
    if radius is None:
        radius = height // 2
    # 背景
    pygame.draw.rect(surface, bg_color, (x, y, width, height), border_radius=radius)
    # 填充
    fw = max(0, int(width * min(1.0, progress)))
    if fw > 0:
        pygame.draw.rect(surface, fill_color, (x, y, fw, height), border_radius=radius)
        # 高光
        hl = pygame.Surface((fw, height // 2), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 40))
        surface.blit(hl, (x, y))
