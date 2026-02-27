"""
items.py —— 游戏世界物体模块  (Google Doodle 美术风格)
包含：场景中的交互物体、装饰物、粒子特效
"""

import pygame
import random
import math
import os

from gfx import (
    draw_soft_circle, draw_soft_ellipse, draw_circle_shadow,
    draw_shadow, draw_rounded_card, draw_pill_badge,
    BIN_BLUE, BIN_GREEN, BIN_RED, BIN_GRAY,
    WHITE, NEAR_WHITE, CHARCOAL, DARK_GRAY, LIGHT_GRAY,
    GRASS, GRASS_DARK, EARTH, EARTH_DARK, EARTH_LIGHT,
    WOOD, WOOD_DARK, WATER, WATER_LIGHT, WATER_DARK,
    GREEN, RED, BLUE, YELLOW, SOFT_GREEN, SOFT_BLUE,
)


# ============================================================
#  共享字体（缓存，避免每帧重建）
# ============================================================
_cached_fonts = {}

def _get_font(size):
    if size in _cached_fonts:
        return _cached_fonts[size]
    paths = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                f = pygame.font.Font(p, size)
                _cached_fonts[size] = f
                return f
            except Exception:
                continue
    f = pygame.font.Font(None, size)
    _cached_fonts[size] = f
    return f


# ============================================================
#  粒子特效  — 柔和渐变 + alpha
# ============================================================
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(18, 35)
        self.max_life = self.life
        self.size = random.uniform(2.5, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.08
        self.vx *= 0.98
        self.life -= 1
        self.size = max(0.5, self.size - 0.12)

    def draw(self, screen):
        if self.life <= 0:
            return
        t = self.life / self.max_life
        alpha = int(220 * t)
        r = min(255, self.color[0] + int(60 * (1 - t)))
        g = min(255, self.color[1] + int(60 * (1 - t)))
        b = min(255, self.color[2] + int(60 * (1 - t)))
        s = max(1, int(self.size))
        surf = pygame.Surface((s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (r, g, b, alpha), (s + 1, s + 1), s)
        screen.blit(surf, (int(self.x) - s - 1, int(self.y) - s - 1))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=12):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)


# ============================================================
#  世界物体基类
# ============================================================
class WorldObject:
    def __init__(self, x, y, width, height, name=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name
        self.active = True
        self.interactable = True

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2,
                           self.y - self.height // 2,
                           self.width, self.height)

    def distance_to(self, px, py):
        return math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2)

    def update(self):
        pass

    def draw(self, screen):
        pass


# ============================================================
#  第一关物体 —— 垃圾分类
# ============================================================

TRASH_DATA = {
    "recyclable": {
        "bin_color": BIN_BLUE,
        "bin_label": "可回收",
        "items": ["塑料瓶", "易拉罐", "废纸", "玻璃瓶"],
    },
    "kitchen": {
        "bin_color": BIN_GREEN,
        "bin_label": "厨余",
        "items": ["果皮", "剩饭", "菜叶", "骨头"],
    },
    "hazardous": {
        "bin_color": BIN_RED,
        "bin_label": "有害",
        "items": ["废电池", "灯泡", "过期药", "油漆桶"],
    },
    "other": {
        "bin_color": BIN_GRAY,
        "bin_label": "其他",
        "items": ["旧毛巾", "烟蒂", "尘土", "陶瓷片"],
    },
}


class Trash(WorldObject):
    def __init__(self, x, y, category):
        self.category = category
        data = TRASH_DATA[category]
        self.item_name = random.choice(data["items"])
        super().__init__(x, y, 26, 26, self.item_name)
        self.bob_timer = random.uniform(0, 6.28)
        self.glow_timer = random.uniform(0, 6.28)

    def update(self):
        self.bob_timer += 0.06
        self.glow_timer += 0.04

    def draw(self, screen):
        if not self.active:
            return
        cx, cy = int(self.x), int(self.y)
        bob = int(math.sin(self.bob_timer) * 2.5)
        glow = int(math.sin(self.glow_timer) * 15) + 15

        # 地面小阴影
        shadow_s = pygame.Surface((20, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 25), (0, 0, 20, 8))
        screen.blit(shadow_s, (cx - 10, cy + 10))

        # 发光光圈提示可交互
        glow_s = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 255, 200, glow), (18, 18), 16)
        screen.blit(glow_s, (cx - 18, cy - 18 + bob))

        if self.category == "recyclable":
            # 蓝色瓶子
            pygame.draw.rect(screen, (56, 126, 230),
                             (cx - 6, cy - 11 + bob, 12, 20), border_radius=4)
            pygame.draw.rect(screen, (46, 106, 200),
                             (cx - 4, cy - 14 + bob, 8, 5), border_radius=2)
            # 高光
            hl = pygame.Surface((4, 10), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 70))
            screen.blit(hl, (cx - 3, cy - 8 + bob))
            # 回收标
            pygame.draw.polygon(screen, (220, 240, 255), [
                (cx, cy - 3 + bob), (cx - 4, cy + 4 + bob), (cx + 4, cy + 4 + bob)
            ], 1)

        elif self.category == "kitchen":
            # 果皮/食物
            draw_soft_ellipse(screen, (cx - 9, cy - 7 + bob, 18, 14),
                              (200, 160, 50))
            pygame.draw.arc(screen, (100, 170, 60),
                            (cx - 7, cy - 9 + bob, 14, 10), 0.2, 3.0, 2)
            # 小叶子
            pygame.draw.ellipse(screen, (80, 180, 60),
                                (cx + 3, cy - 11 + bob, 6, 4))

        elif self.category == "hazardous":
            # 电池
            pygame.draw.rect(screen, (220, 60, 55),
                             (cx - 7, cy - 9 + bob, 14, 18), border_radius=3)
            pygame.draw.rect(screen, (80, 80, 80),
                             (cx - 4, cy - 12 + bob, 8, 4), border_radius=2)
            # 闪电标记
            pts = [(cx - 2, cy - 4 + bob), (cx + 2, cy - 1 + bob),
                   (cx - 1, cy - 1 + bob), (cx + 3, cy + 5 + bob),
                   (cx - 1, cy + 1 + bob), (cx - 3, cy + 1 + bob)]
            pygame.draw.polygon(screen, YELLOW, pts)

        else:
            # 灰色杂物
            pygame.draw.rect(screen, (168, 168, 162),
                             (cx - 8, cy - 8 + bob, 16, 16), border_radius=3)
            pygame.draw.line(screen, (130, 130, 125),
                             (cx - 4, cy - 4 + bob), (cx + 4, cy + 4 + bob), 2)
            pygame.draw.line(screen, (130, 130, 125),
                             (cx + 4, cy - 4 + bob), (cx - 4, cy + 4 + bob), 2)
            # 高光
            hl = pygame.Surface((8, 4), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 50))
            screen.blit(hl, (cx - 6, cy - 7 + bob))


class TrashBin(WorldObject):
    def __init__(self, x, y, category):
        self.category = category
        data = TRASH_DATA[category]
        self.color = data["bin_color"]
        self.label = data["bin_label"]
        super().__init__(x, y, 52, 60, self.label + "垃圾桶")
        self.interactable = True

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)

        # 阴影
        shadow_s = pygame.Surface((44, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 30), (0, 0, 44, 12))
        screen.blit(shadow_s, (cx - 22, cy + 20))

        # 桶身 — 梯形
        c = self.color
        cd = tuple(max(0, v - 30) for v in c)
        cl = tuple(min(255, v + 50) for v in c)

        body = [
            (cx - 21, cy - 18), (cx + 21, cy - 18),
            (cx + 17, cy + 20), (cx - 17, cy + 20),
        ]
        pygame.draw.polygon(screen, c, body)
        pygame.draw.polygon(screen, cd, body, 2)

        # 桶身高光条
        hl = pygame.Surface((6, 32), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 55))
        screen.blit(hl, (cx - 16, cy - 15))

        # 桶盖
        pygame.draw.rect(screen, cl, (cx - 24, cy - 25, 48, 10), border_radius=4)
        # 盖子把手
        pygame.draw.rect(screen, cd, (cx - 5, cy - 30, 10, 7), border_radius=3)

        # 分类标签
        font = _get_font(15)
        label_surf = font.render(self.label, True, WHITE)
        lw = label_surf.get_width()
        # 标签背景
        tag_bg = pygame.Surface((lw + 12, 20), pygame.SRCALPHA)
        pygame.draw.rect(tag_bg, (0, 0, 0, 60), (0, 0, lw + 12, 20), border_radius=10)
        screen.blit(tag_bg, (cx - lw // 2 - 6, cy - 4))
        screen.blit(label_surf, (cx - lw // 2, cy - 2))

        # 底部装饰线
        pygame.draw.line(screen, cl, (cx - 14, cy + 16), (cx + 14, cy + 16), 1)


# ============================================================
#  第二关物体 —— 节约用水
# ============================================================
class Faucet(WorldObject):
    def __init__(self, x, y):
        super().__init__(x, y, 36, 36, "水龙头")
        self.is_open = True
        self.drip_timer = 0
        self.drip_particles = []

    def update(self):
        if self.is_open:
            self.drip_timer += 1
            if self.drip_timer % 7 == 0:
                self.drip_particles.append({
                    "x": self.x + random.uniform(-2, 2),
                    "y": self.y + 20,
                    "vy": 0.8,
                    "size": random.uniform(2.5, 4),
                    "life": 35,
                    "max_life": 35,
                })
        for d in self.drip_particles[:]:
            d["y"] += d["vy"]
            d["vy"] += 0.12
            d["life"] -= 1
            d["size"] = max(0.5, d["size"] - 0.05)
            if d["life"] <= 0:
                self.drip_particles.remove(d)

    def close(self):
        self.is_open = False
        self.drip_particles.clear()
        self.interactable = False

    def reopen(self):
        self.is_open = True
        self.interactable = True
        self.drip_timer = 0

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)

        # 墙砖底座
        pygame.draw.rect(screen, (195, 195, 200), (cx - 16, cy - 16, 32, 24),
                         border_radius=4)
        pygame.draw.rect(screen, (175, 175, 180), (cx - 16, cy - 16, 32, 24),
                         width=2, border_radius=4)
        # 高光
        hl = pygame.Surface((28, 4), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 45))
        screen.blit(hl, (cx - 14, cy - 14))

        # 水管
        pygame.draw.rect(screen, (190, 195, 200), (cx - 5, cy + 6, 10, 16),
                         border_radius=3)
        # 龙头嘴 — 圆润
        draw_soft_circle(screen, cx, cy + 22, 7, (185, 190, 195))

        if self.is_open:
            # 红色指示灯
            draw_soft_circle(screen, cx, cy - 6, 6, (234, 67, 53))
            # 水柱
            water_h = 20
            water_s = pygame.Surface((6, water_h), pygame.SRCALPHA)
            for row in range(water_h):
                a = int(120 * (1 - row / water_h))
                pygame.draw.line(water_s, (100, 181, 246, a), (0, row), (5, row))
            screen.blit(water_s, (cx - 3, cy + 24))

            # 水滴
            for d in self.drip_particles:
                t = d["life"] / d["max_life"]
                alpha = int(180 * t)
                s = max(1, int(d["size"]))
                ds = pygame.Surface((s * 2 + 2, s * 2 + 4), pygame.SRCALPHA)
                # 水滴形
                pygame.draw.circle(ds, (100, 181, 246, alpha), (s + 1, s + 2), s)
                pygame.draw.polygon(ds, (100, 181, 246, alpha), [
                    (s + 1, 0), (s - 1, s), (s + 3, s)
                ])
                screen.blit(ds, (int(d["x"]) - s - 1, int(d["y"]) - s - 2))
        else:
            # 绿色指示灯
            draw_soft_circle(screen, cx, cy - 6, 6, GREEN)


class Puddle(WorldObject):
    def __init__(self, x, y):
        super().__init__(x, y, 44, 22, "水坑")
        self.interactable = False
        self.wobble = random.uniform(0, 6.28)

    def update(self):
        self.wobble += 0.04

    def draw(self, screen):
        if not self.active:
            return
        cx, cy = int(self.x), int(self.y)
        w = 22 + int(math.sin(self.wobble) * 2)

        # 外圈
        puddle_s = pygame.Surface((w * 2 + 4, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(puddle_s, (100, 181, 246, 100), (0, 2, w * 2 + 4, 18))
        pygame.draw.ellipse(puddle_s, (130, 200, 250, 140), (3, 4, w * 2 - 2, 14))
        # 高光
        pygame.draw.ellipse(puddle_s, (200, 230, 255, 80),
                            (w - 6, 4, 14, 7))
        screen.blit(puddle_s, (cx - w - 2, cy - 10))


# ============================================================
#  第三关物体 —— 植树造林
# ============================================================
class SeedlingPile(WorldObject):
    def __init__(self, x, y):
        super().__init__(x, y, 52, 52, "树苗堆")

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)

        # 泥土堆
        draw_soft_ellipse(screen, (cx - 24, cy + 8, 48, 16), EARTH)

        # 三棵树苗
        for ox, oy in [(-12, 4), (0, -6), (12, 4)]:
            tx, ty = cx + ox, cy + oy
            # 干
            pygame.draw.rect(screen, WOOD, (tx - 2, ty + 2, 4, 12),
                             border_radius=1)
            # 冠
            pts = [(tx, ty - 12), (tx - 9, ty + 3), (tx + 9, ty + 3)]
            pygame.draw.polygon(screen, (72, 194, 106), pts)
            # 冠高光
            pts2 = [(tx, ty - 10), (tx - 5, ty - 2), (tx + 5, ty - 2)]
            pygame.draw.polygon(screen, (110, 218, 140), pts2)

        # 标签
        font = _get_font(12)
        tag = font.render("树苗", True, WHITE)
        tw = tag.get_width()
        bg = pygame.Surface((tw + 8, 16), pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 50), (0, 0, tw + 8, 16), border_radius=8)
        screen.blit(bg, (cx - tw // 2 - 4, cy + 22))
        screen.blit(tag, (cx - tw // 2, cy + 22))


class PlantSpot(WorldObject):
    def __init__(self, x, y):
        super().__init__(x, y, 34, 34, "种植点")
        self.planted = False
        self.grow_timer = 0

    def plant(self):
        self.planted = True
        self.interactable = False
        self.grow_timer = 0

    def update(self):
        if self.planted:
            self.grow_timer = min(60, self.grow_timer + 1)

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)
        if self.planted:
            # 生长动画
            t = min(1.0, self.grow_timer / 40)
            scale = 0.3 + 0.7 * t

            # 树干
            th = int(16 * scale)
            pygame.draw.rect(screen, WOOD,
                             (cx - 3, cy - th + 8, 6, th), border_radius=2)
            # 树冠
            r = int(14 * scale)
            draw_soft_circle(screen, cx, cy - th - r + 10, r, (72, 194, 106))
            if r > 4:
                draw_soft_circle(screen, cx - 3, cy - th - r + 5, r // 2 + 1,
                                 (110, 218, 140))
        else:
            # 土坑
            # 坑影
            draw_soft_ellipse(screen, (cx - 16, cy - 9, 32, 18), EARTH_DARK)
            draw_soft_ellipse(screen, (cx - 12, cy - 6, 24, 12), EARTH)

            # 小旗帜
            pygame.draw.line(screen, (200, 50, 40),
                             (cx + 12, cy - 18), (cx + 12, cy + 2), 2)
            pygame.draw.polygon(screen, RED, [
                (cx + 12, cy - 18), (cx + 22, cy - 14), (cx + 12, cy - 10)
            ])
            # 旗高光
            pts_hl = [(cx + 13, cy - 17), (cx + 19, cy - 14), (cx + 13, cy - 11)]
            pygame.draw.polygon(screen, (255, 110, 100), pts_hl)


class Lumberjack(WorldObject):
    def __init__(self, x, y, x_min, x_max):
        super().__init__(x, y, 30, 44, "伐木工人")
        self.interactable = False
        self.speed = random.uniform(1.0, 2.0)
        self.direction = random.choice([-1, 1])
        self.x_min = x_min
        self.x_max = x_max
        self.walk_frame = 0

    def update(self):
        self.x += self.speed * self.direction
        self.walk_frame += 1
        if self.x < self.x_min or self.x > self.x_max:
            self.direction *= -1

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)
        d = self.direction
        bob = int(math.sin(self.walk_frame * 0.15) * 2)

        # 地面阴影
        shadow_s = pygame.Surface((28, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 25), (0, 0, 28, 8))
        screen.blit(shadow_s, (cx - 14, cy + 24))

        # 腿
        leg_off = int(math.sin(self.walk_frame * 0.15) * 4)
        pygame.draw.rect(screen, (72, 74, 130),
                         (cx - 8, cy + 12 + bob, 8, 12 + leg_off), border_radius=3)
        pygame.draw.rect(screen, (72, 74, 130),
                         (cx + 1, cy + 12 + bob, 8, 12 - leg_off), border_radius=3)
        # 鞋
        pygame.draw.rect(screen, (90, 70, 50),
                         (cx - 10, cy + 22 + bob + leg_off, 10, 5), border_radius=2)
        pygame.draw.rect(screen, (90, 70, 50),
                         (cx + 1, cy + 22 + bob - leg_off, 10, 5), border_radius=2)

        # 身体 — 格子衬衫
        pygame.draw.rect(screen, (210, 65, 45),
                         (cx - 11, cy - 8 + bob, 22, 24), border_radius=5)
        # 格子纹
        for lx in range(cx - 9, cx + 10, 5):
            pygame.draw.line(screen, (180, 45, 30),
                             (lx, cy - 6 + bob), (lx, cy + 14 + bob), 1)
        for ly in range(cy - 6 + bob, cy + 14 + bob, 5):
            pygame.draw.line(screen, (180, 45, 30),
                             (cx - 9, ly), (cx + 9, ly), 1)

        # 头
        draw_soft_circle(screen, cx, cy - 16 + bob, 11, (238, 200, 164))
        # 胡子
        pygame.draw.rect(screen, (120, 80, 50),
                         (cx - 6, cy - 10 + bob, 12, 5), border_radius=2)
        # 帽子
        pygame.draw.rect(screen, (100, 65, 30),
                         (cx - 12, cy - 27 + bob, 24, 10), border_radius=4)
        pygame.draw.rect(screen, (100, 65, 30),
                         (cx - 15, cy - 19 + bob, 30, 5), border_radius=2)
        # 帽高光
        hl = pygame.Surface((20, 3), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 40))
        screen.blit(hl, (cx - 10, cy - 25 + bob))
        # 眼睛
        pygame.draw.circle(screen, CHARCOAL, (cx + d * 4, cy - 18 + bob), 2)

        # 斧头
        ax = cx + d * 16
        ay = cy - 4 + bob
        pygame.draw.line(screen, WOOD_DARK, (cx + d * 10, cy + bob), (ax, ay - 14), 3)
        pygame.draw.polygon(screen, (190, 195, 200), [
            (ax, ay - 16), (ax + d * 10, ay - 11), (ax + d * 3, ay - 3)
        ])
        # 斧刃高光
        pygame.draw.line(screen, (230, 235, 240),
                         (ax + d * 2, ay - 14), (ax + d * 8, ay - 10), 1)


# ============================================================
#  装饰物  — 精致化
# ============================================================
class Decoration(WorldObject):
    def __init__(self, x, y, deco_type):
        super().__init__(x, y, 44, 44, deco_type)
        self.deco_type = deco_type
        self.interactable = False

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)

        if self.deco_type == "desk":
            # 阴影
            s = pygame.Surface((44, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 20), (0, 0, 44, 6))
            screen.blit(s, (cx - 22, cy + 16))
            # 桌面
            pygame.draw.rect(screen, (185, 145, 90), (cx - 22, cy - 8, 44, 18),
                             border_radius=3)
            # 桌面高光
            hl = pygame.Surface((40, 4), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 40))
            screen.blit(hl, (cx - 20, cy - 7))
            # 桌腿
            pygame.draw.rect(screen, (155, 115, 65), (cx - 19, cy + 10, 5, 10),
                             border_radius=2)
            pygame.draw.rect(screen, (155, 115, 65), (cx + 14, cy + 10, 5, 10),
                             border_radius=2)

        elif self.deco_type == "chair":
            pygame.draw.rect(screen, (165, 125, 70), (cx - 8, cy - 4, 16, 14),
                             border_radius=3)
            pygame.draw.rect(screen, (155, 115, 60), (cx - 8, cy - 16, 16, 14),
                             border_radius=3)
            hl = pygame.Surface((12, 3), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 35))
            screen.blit(hl, (cx - 6, cy - 15))

        elif self.deco_type == "slide":
            # 滑道 — 红色
            pygame.draw.polygon(screen, (234, 88, 76), [
                (cx - 14, cy - 22), (cx + 22, cy + 18),
                (cx + 22, cy + 22), (cx - 14, cy - 16)
            ])
            # 高光
            pygame.draw.line(screen, (255, 140, 130),
                             (cx - 12, cy - 18), (cx + 18, cy + 16), 2)
            # 梯子
            for i in range(2):
                lx = cx - 16 + i * 10
                pygame.draw.line(screen, (150, 150, 155),
                                 (lx, cy - 22), (lx, cy + 22), 3)
            for ry in range(cy - 18, cy + 18, 8):
                pygame.draw.line(screen, (150, 150, 155),
                                 (cx - 16, ry), (cx - 6, ry), 2)

        elif self.deco_type == "swing":
            # 横杆
            pygame.draw.line(screen, (150, 150, 155),
                             (cx - 14, cy - 26), (cx + 14, cy - 26), 4)
            # 绳子
            for sx in [-6, 6]:
                pygame.draw.line(screen, (165, 130, 80),
                                 (cx + sx, cy - 26), (cx + sx, cy + 2), 2)
            # 座板
            pygame.draw.rect(screen, WOOD, (cx - 9, cy + 2, 18, 5),
                             border_radius=2)

        elif self.deco_type == "track_cone":
            # 阴影
            s = pygame.Surface((20, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 20), (0, 0, 20, 6))
            screen.blit(s, (cx - 10, cy + 6))
            # 锥体
            pygame.draw.polygon(screen, (251, 153, 51), [
                (cx, cy - 14), (cx - 9, cy + 6), (cx + 9, cy + 6)
            ])
            # 白条
            pygame.draw.line(screen, WHITE,
                             (cx - 4, cy - 2), (cx + 4, cy - 2), 2)
            # 底座
            pygame.draw.rect(screen, (251, 188, 4),
                             (cx - 11, cy + 6, 22, 5), border_radius=2)

        elif self.deco_type == "sink":
            pygame.draw.rect(screen, (210, 215, 220), (cx - 18, cy - 12, 36, 24),
                             border_radius=5)
            pygame.draw.rect(screen, (190, 195, 200), (cx - 18, cy - 12, 36, 24),
                             width=2, border_radius=5)
            pygame.draw.ellipse(screen, WATER_LIGHT, (cx - 10, cy - 6, 20, 12))
            # 龙头
            pygame.draw.rect(screen, (180, 185, 190), (cx - 2, cy - 16, 4, 8),
                             border_radius=2)

        elif self.deco_type == "tree":
            # 阴影
            s = pygame.Surface((36, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 20), (0, 0, 36, 10))
            screen.blit(s, (cx - 18, cy + 14))
            # 树干
            pygame.draw.rect(screen, WOOD, (cx - 5, cy, 10, 22), border_radius=3)
            # 树冠
            draw_soft_circle(screen, cx, cy - 10, 20, (60, 165, 70))
            draw_soft_circle(screen, cx - 6, cy - 16, 12, (85, 190, 95))
            draw_soft_circle(screen, cx + 6, cy - 14, 10, (100, 200, 110))

        elif self.deco_type == "bush":
            s = pygame.Surface((30, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 18), (0, 0, 30, 8))
            screen.blit(s, (cx - 15, cy + 8))
            draw_soft_ellipse(screen, (cx - 16, cy - 8, 32, 20), (65, 160, 65))
            draw_soft_ellipse(screen, (cx - 10, cy - 14, 22, 16), (85, 185, 85))

        elif self.deco_type == "fence":
            for fx in range(-16, 20, 8):
                pygame.draw.rect(screen, (195, 175, 140),
                                 (cx + fx, cy - 16, 5, 26), border_radius=2)
            pygame.draw.rect(screen, (175, 155, 120),
                             (cx - 18, cy - 12, 42, 4), border_radius=2)
            pygame.draw.rect(screen, (175, 155, 120),
                             (cx - 18, cy - 2, 42, 4), border_radius=2)

        elif self.deco_type == "grass":
            for gx in range(-10, 12, 3):
                h = random.randint(8, 15)
                c = random.choice([(90, 185, 65), (75, 170, 55), (100, 195, 75)])
                pygame.draw.line(screen, c,
                                 (cx + gx, cy + 4), (cx + gx + 1, cy - h), 2)

        elif self.deco_type == "flower":
            # 茎
            pygame.draw.line(screen, (80, 170, 55),
                             (cx, cy + 10), (cx, cy - 4), 2)
            # 花瓣
            for angle in range(0, 360, 72):
                px = cx + int(5 * math.cos(math.radians(angle)))
                py = cy - 4 + int(5 * math.sin(math.radians(angle)))
                color = random.choice([RED, YELLOW, (255, 150, 200)])
                pygame.draw.circle(screen, color, (px, py), 3)
            pygame.draw.circle(screen, YELLOW, (cx, cy - 4), 3)

        elif self.deco_type == "bench":
            # 长凳
            pygame.draw.rect(screen, WOOD, (cx - 20, cy - 4, 40, 8),
                             border_radius=3)
            pygame.draw.rect(screen, WOOD_DARK, (cx - 18, cy + 4, 4, 10),
                             border_radius=2)
            pygame.draw.rect(screen, WOOD_DARK, (cx + 14, cy + 4, 4, 10),
                             border_radius=2)
            # 高光
            hl = pygame.Surface((36, 3), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 40))
            screen.blit(hl, (cx - 18, cy - 3))
