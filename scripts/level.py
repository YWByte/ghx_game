"""
level.py —— 关卡与游戏世界模块  (Google Doodle 美术风格)
包含：关卡配置、GameWorld场景管理、俯视角场景绘制、精致HUD
"""

import pygame
import math
import random
import os

from items import (
    Trash, TrashBin, TRASH_DATA,
    Faucet, Puddle,
    SeedlingPile, PlantSpot, Lumberjack,
    Decoration,
)
from gfx import (
    draw_soft_circle, draw_soft_ellipse, draw_rounded_card,
    draw_pill_badge, draw_progress_bar, draw_shadow,
    BLUE, RED, YELLOW, GREEN,
    SOFT_BLUE, SOFT_GREEN, SOFT_YELLOW,
    WHITE, NEAR_WHITE, LIGHT_GRAY, MID_GRAY, DARK_GRAY, CHARCOAL, NEAR_BLACK,
    GRASS, GRASS_LIGHT, GRASS_DARK,
    EARTH, EARTH_LIGHT, EARTH_DARK,
    WATER, WATER_LIGHT,
)

# 共享字体缓存
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
#  关卡配置信息
# ============================================================
LEVEL_CONFIGS = {
    1: {
        "name": "第一关：垃圾分类",
        "description": "在操场上捡垃圾，送到正确的垃圾桶！",
        "target_score": 15,
        "tip": "空格键拾取/投放垃圾，送到对应颜色的垃圾桶！",
        "color": BLUE,
    },
    2: {
        "name": "第二关：节约用水",
        "description": "在教室饭堂里关掉漏水的水龙头！",
        "target_score": 20,
        "time_limit": 60,
        "tip": "空格键关水龙头，小心水坑会让你滑倒减速！",
        "color": WATER,
    },
    3: {
        "name": "第三关：植树造林",
        "description": "拾取树苗种到土坑里，躲避伐木工人！",
        "target_score": 12,
        "tip": "先去树苗堆拿树苗，再到土坑按空格种下！",
        "color": GREEN,
    },
}


# ============================================================
#  游戏世界
# ============================================================
class GameWorld:
    def __init__(self, level_id, screen_width=1440, screen_height=900):
        self.level_id = level_id
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.objects = []
        self.decorations = []
        self.score = 0
        self.time_left = -1
        self.timer_frames = 0

        # 第二关专用
        self.faucet_reopen_timer = 0
        self.faucet_reopen_interval = 300

        # 预渲染的地面贴图（避免每帧重绘）
        self._ground_cache = None

        self._build_level()

    def _build_level(self):
        if self.level_id == 1:
            self._build_level_1()
        elif self.level_id == 2:
            self._build_level_2()
        elif self.level_id == 3:
            self._build_level_3()

    # --------------------------------------------------
    #  第一关：操场
    # --------------------------------------------------
    def _build_level_1(self):
        bin_y = 128
        categories = ["recyclable", "kitchen", "hazardous", "other"]
        bin_positions = [252, 576, 900, 1224]
        for cat, bx in zip(categories, bin_positions):
            self.objects.append(TrashBin(bx, bin_y, cat))

        self._spawn_trash(20)

        # 丰富装饰
        self.decorations.append(Decoration(100, 315, "slide"))
        self.decorations.append(Decoration(1340, 315, "swing"))
        self.decorations.append(Decoration(180, 780, "track_cone"))
        self.decorations.append(Decoration(1260, 780, "track_cone"))
        self.decorations.append(Decoration(100, 600, "bench"))
        self.decorations.append(Decoration(1340, 600, "bench"))
        # 花草
        for x_pos in [260, 520, 900, 1160]:
            self.decorations.append(Decoration(x_pos, 845, "grass"))
        for x_pos in [130, 420, 1000, 1310]:
            self.decorations.append(Decoration(x_pos, 830, "flower"))

    def _spawn_trash(self, count):
        categories = list(TRASH_DATA.keys())
        for _ in range(count):
            x = random.randint(120, self.screen_width - 120)
            y = random.randint(235, self.screen_height - 100)
            cat = random.choice(categories)
            self.objects.append(Trash(x, y, cat))

    # --------------------------------------------------
    #  第二关：教室饭堂
    # --------------------------------------------------
    def _build_level_2(self):
        config = LEVEL_CONFIGS[2]
        self.time_left = config["time_limit"] * 60

        faucet_positions = [
            (200, 128), (480, 128), (760, 128), (1040, 128), (1320, 128),
            (200, 428), (680, 428), (1160, 428),
        ]
        for fx, fy in faucet_positions:
            self.objects.append(Faucet(fx, fy))

        puddle_positions = [
            (340, 300), (860, 540), (510, 690), (1120, 300), (250, 620),
        ]
        for px, py in puddle_positions:
            self.objects.append(Puddle(px, py))

        desk_positions = [
            (300, 620), (580, 620), (860, 620), (1140, 620),
            (300, 770), (580, 770), (860, 770), (1140, 770),
        ]
        for dx, dy in desk_positions:
            self.decorations.append(Decoration(dx, dy, "desk"))
            self.decorations.append(Decoration(dx, dy + 48, "chair"))

        self.decorations.append(Decoration(130, 280, "sink"))
        self.decorations.append(Decoration(1310, 280, "sink"))

    # --------------------------------------------------
    #  第三关：荒地公园
    # --------------------------------------------------
    def _build_level_3(self):
        self.objects.append(SeedlingPile(100, 450))
        self.objects.append(SeedlingPile(1340, 450))

        plant_positions = [
            (250, 180), (510, 150), (860, 180), (1120, 150),
            (340, 375), (680, 345), (1040, 375),
            (250, 600), (600, 570), (950, 600),
            (420, 750), (770, 780),
        ]
        for px, py in plant_positions:
            self.objects.append(PlantSpot(px, py))

        self.objects.append(Lumberjack(510, 255, 170, 1270))
        self.objects.append(Lumberjack(860, 495, 170, 1270))
        self.objects.append(Lumberjack(340, 690, 170, 1270))

        self.decorations.append(Decoration(80, 120, "bush"))
        self.decorations.append(Decoration(1360, 120, "bush"))
        self.decorations.append(Decoration(80, 840, "tree"))
        self.decorations.append(Decoration(1360, 840, "tree"))
        for x_pos in [340, 680, 1040]:
            self.decorations.append(Decoration(x_pos, 855, "fence"))
        self.decorations.append(Decoration(250, 840, "grass"))
        self.decorations.append(Decoration(1170, 840, "grass"))

    # --------------------------------------------------
    #  更新
    # --------------------------------------------------
    def update(self):
        for obj in self.objects:
            obj.update()

        if self.level_id == 2:
            if self.time_left > 0:
                self.time_left -= 1
            self.faucet_reopen_timer += 1
            if self.faucet_reopen_timer >= self.faucet_reopen_interval:
                self.faucet_reopen_timer = 0
                self._reopen_random_faucet()

    def _reopen_random_faucet(self):
        closed = [o for o in self.objects
                  if isinstance(o, Faucet) and not o.is_open]
        if closed:
            faucet = random.choice(closed)
            faucet.reopen()

    # --------------------------------------------------
    #  交互
    # --------------------------------------------------
    def get_nearest_interactable(self, px, py, max_dist=80):
        nearest = None
        min_dist = max_dist
        for obj in self.objects:
            if not obj.active or not obj.interactable:
                continue
            dist = obj.distance_to(px, py)
            if dist < min_dist:
                min_dist = dist
                nearest = obj
        return nearest

    def get_colliding_puddles(self, px, py):
        for obj in self.objects:
            if isinstance(obj, Puddle) and obj.active:
                if obj.distance_to(px, py) < 50:
                    return True
        return False

    def get_colliding_lumberjacks(self, px, py):
        for obj in self.objects:
            if isinstance(obj, Lumberjack) and obj.active:
                if obj.distance_to(px, py) < 50:
                    return obj
        return None

    def is_level_complete(self):
        config = LEVEL_CONFIGS[self.level_id]
        return self.score >= config["target_score"]

    def is_time_up(self):
        if self.level_id == 2 and self.time_left == 0:
            return True
        return False

    def count_remaining(self):
        if self.level_id == 1:
            return len([o for o in self.objects
                        if isinstance(o, Trash) and o.active])
        elif self.level_id == 3:
            return len([o for o in self.objects
                        if isinstance(o, PlantSpot) and not o.planted])
        return 0

    # --------------------------------------------------
    #  绘制场景  — 预渲染缓存
    # --------------------------------------------------
    def draw_ground(self, screen):
        if self._ground_cache is None:
            self._ground_cache = pygame.Surface(
                (self.screen_width, self.screen_height))
            if self.level_id == 1:
                self._render_playground(self._ground_cache)
            elif self.level_id == 2:
                self._render_classroom(self._ground_cache)
            elif self.level_id == 3:
                self._render_wasteland(self._ground_cache)
        screen.blit(self._ground_cache, (0, 0))

    def _render_playground(self, surf):
        """第一关：操场 — 柔和草地 + 跑道"""
        # 渐变草地
        for y in range(self.screen_height):
            t = y / self.screen_height
            r = int(148 + 25 * t)
            g = int(215 - 20 * t)
            b = int(110 + 15 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.screen_width, y))

        # 跑道
        track_rect = pygame.Rect(130, 240, 1180, 590)
        pygame.draw.ellipse(surf, (212, 175, 140), track_rect)
        inner = track_rect.inflate(-120, -110)
        pygame.draw.ellipse(surf, (138, 205, 108), inner)
        # 跑道线 — 柔和白色
        pygame.draw.ellipse(surf, (255, 255, 255, 180), track_rect, 4)
        mid = track_rect.inflate(-60, -55)
        pygame.draw.ellipse(surf, (255, 255, 255, 100), mid, 2)
        pygame.draw.ellipse(surf, (255, 255, 255, 180), inner, 4)

        # 中间草地纹理 — 浅色圆点
        rng = random.Random(42)
        for _ in range(70):
            fx = rng.randint(inner.left + 35, inner.right - 35)
            fy = rng.randint(inner.top + 35, inner.bottom - 35)
            c = rng.choice([(120, 200, 95), (130, 210, 100), (110, 190, 85)])
            pygame.draw.circle(surf, c, (fx, fy), rng.randint(3, 8))

        # 小雏菊
        rng2 = random.Random(123)
        for _ in range(14):
            fx = rng2.randint(inner.left + 50, inner.right - 50)
            fy = rng2.randint(inner.top + 50, inner.bottom - 50)
            for a in range(0, 360, 60):
                dx = int(6 * math.cos(math.radians(a)))
                dy = int(6 * math.sin(math.radians(a)))
                pygame.draw.circle(surf, WHITE, (fx + dx, fy + dy), 3)
            pygame.draw.circle(surf, YELLOW, (fx, fy), 3)

        # 垃圾桶区域 — 圆角卡片
        card_surf = pygame.Surface((1360, 108), pygame.SRCALPHA)
        pygame.draw.rect(card_surf, (240, 238, 230, 200), (0, 0, 1360, 108),
                         border_radius=16)
        pygame.draw.rect(card_surf, (210, 208, 200, 150), (0, 0, 1360, 108),
                         width=2, border_radius=16)
        surf.blit(card_surf, (40, 72))

    def _render_classroom(self, surf):
        """第二关：教室/饭堂 — 瓷砖地板"""
        # 温暖底色
        surf.fill((235, 220, 198))

        # 瓷砖 — 棋盘格
        tile = 80
        colors = [(230, 218, 195), (222, 210, 185)]
        for tx in range(0, self.screen_width, tile):
            for ty in range(0, self.screen_height, tile):
                ci = ((tx // tile) + (ty // tile)) % 2
                pygame.draw.rect(surf, colors[ci], (tx, ty, tile, tile))
                # 砖缝
                pygame.draw.rect(surf, (210, 198, 175), (tx, ty, tile, tile), 1)

        # 墙壁带
        for wy in [75, 385]:
            # 墙壁
            pygame.draw.rect(surf, (200, 205, 212), (0, wy, self.screen_width, 90))
            # 顶部线
            pygame.draw.line(surf, (180, 185, 192),
                             (0, wy), (self.screen_width, wy), 3)
            # 底部线
            pygame.draw.line(surf, (180, 185, 192),
                             (0, wy + 90), (self.screen_width, wy + 90), 3)
            # 腰线
            pygame.draw.line(surf, (170, 175, 185),
                             (0, wy + 45), (self.screen_width, wy + 45), 2)
            # 高光
            hl = pygame.Surface((self.screen_width, 8), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 30))
            surf.blit(hl, (0, wy + 3))

    def _render_wasteland(self, surf):
        """第三关：荒地/公园 — 泥土质感"""
        # 渐变泥土
        for y in range(self.screen_height):
            t = y / self.screen_height
            r = int(175 + 20 * t)
            g = int(155 + 15 * t)
            b = int(115 + 10 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.screen_width, y))

        # 草皮块 — 柔和椭圆
        rng = random.Random(77)
        grass_spots = [
            (80, 75, 180, 100), (380, 225, 150, 85),
            (880, 120, 210, 85), (1140, 465, 165, 100),
            (150, 690, 200, 85), (720, 735, 180, 85),
            (600, 90, 130, 70), (1040, 720, 115, 62),
        ]
        for gx, gy, gw, gh in grass_spots:
            # 柔和边缘
            s = pygame.Surface((gw + 14, gh + 14), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (130, 185, 95, 60), (0, 0, gw + 14, gh + 14))
            pygame.draw.ellipse(s, (140, 195, 100, 120), (7, 7, gw, gh))
            surf.blit(s, (gx - 7, gy - 7))
            # 草纹
            for _ in range(8):
                fx = gx + rng.randint(15, gw - 15)
                fy = gy + rng.randint(8, gh - 8)
                pygame.draw.circle(surf, (120, 180, 85), (fx, fy), 3)

        # 小路 — 圆角
        path_s = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        pygame.draw.rect(path_s, (155, 140, 105, 160),
                         (660, 0, 80, self.screen_height), border_radius=12)
        pygame.draw.rect(path_s, (155, 140, 105, 160),
                         (0, 420, self.screen_width, 65), border_radius=12)
        surf.blit(path_s, (0, 0))

        # 石子
        rng2 = random.Random(55)
        for _ in range(25):
            sx = rng2.randint(666, 735)
            sy = rng2.randint(15, self.screen_height - 15)
            pygame.draw.circle(surf, (140, 128, 95), (sx, sy), rng2.randint(3, 6))
        for _ in range(25):
            sx = rng2.randint(15, self.screen_width - 15)
            sy = rng2.randint(428, 478)
            pygame.draw.circle(surf, (140, 128, 95), (sx, sy), rng2.randint(3, 6))

        # 树苗堆区域
        for rx in [25, 1270]:
            area = pygame.Surface((150, 120), pygame.SRCALPHA)
            pygame.draw.rect(area, (120, 140, 85, 100), (0, 0, 150, 120),
                             border_radius=18)
            pygame.draw.rect(area, (100, 120, 70, 80), (0, 0, 150, 120),
                             width=3, border_radius=18)
            surf.blit(area, (rx, 390))

    # --------------------------------------------------
    #  绘制物体
    # --------------------------------------------------
    def draw_objects(self, screen):
        for deco in self.decorations:
            deco.draw(screen)
        for obj in self.objects:
            if obj.active:
                obj.draw(screen)

    # --------------------------------------------------
    #  HUD  — Material / Google 风格
    # --------------------------------------------------
    def draw_hud(self, screen, font, lives):
        config = LEVEL_CONFIGS[self.level_id]
        sw = self.screen_width

        # ---- 顶部栏 ----
        hud = pygame.Surface((sw, 72), pygame.SRCALPHA)
        pygame.draw.rect(hud, (255, 255, 255, 210), (0, 0, sw, 72))
        # 底边线
        pygame.draw.line(hud, (0, 0, 0, 20), (0, 71), (sw, 71), 1)
        screen.blit(hud, (0, 0))

        font_name = _get_font(26)
        font_score = _get_font(24)
        accent = config.get("color", BLUE)

        # 关卡名称 — 药丸标签
        draw_pill_badge(screen, 140, 24, config["name"], font_name,
                        accent, WHITE, shadow=True)

        # 分数
        if self.level_id == 1:
            score_str = f"已分类 {self.score}/{config['target_score']}"
        elif self.level_id == 2:
            seconds_left = max(0, self.time_left // 60)
            score_str = f"已关 {self.score}/{config['target_score']}"
        else:
            score_str = f"已种 {self.score}/{config['target_score']}"

        score_surf = font_score.render(score_str, True, CHARCOAL)
        screen.blit(score_surf, (350, 9))

        # 进度条
        progress = min(1.0, self.score / max(1, config["target_score"]))
        bar_color = GREEN if progress < 1.0 else YELLOW
        draw_progress_bar(screen, 350, 42, 300, 16, progress,
                          LIGHT_GRAY, bar_color)

        # 计时器（第二关）
        if self.level_id == 2:
            seconds_left = max(0, self.time_left // 60)
            t_color = RED if seconds_left < 15 else CHARCOAL
            timer_str = f"{seconds_left}s"
            draw_pill_badge(screen, 740, 24, timer_str, font_name,
                            (RED if seconds_left < 15 else MID_GRAY),
                            WHITE, shadow=True)

        # 生命值 — 精致爱心
        for i in range(lives):
            hx = sw - 55 - i * 48
            hy = 28
            # 阴影
            s = pygame.Surface((36, 36), pygame.SRCALPHA)
            self._draw_heart(s, 18, 16, 13, (0, 0, 0, 30))
            screen.blit(s, (hx - 18 + 2, hy - 16 + 3))
            # 红心
            self._draw_heart(screen, hx, hy, 13, (234, 67, 83))
            # 高光
            hl = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(hl, (255, 255, 255, 80), (5, 5), 5)
            screen.blit(hl, (hx - 6, hy - 10))

    def _draw_heart(self, surface, cx, cy, size, color):
        """画一个可爱的爱心"""
        r = size * 0.55
        pygame.draw.circle(surface, color,
                           (int(cx - r * 0.7), int(cy - r * 0.3)), int(r))
        pygame.draw.circle(surface, color,
                           (int(cx + r * 0.7), int(cy - r * 0.3)), int(r))
        pygame.draw.polygon(surface, color, [
            (int(cx - size * 0.9), int(cy)),
            (cx, int(cy + size * 1.1)),
            (int(cx + size * 0.9), int(cy)),
        ])


# ============================================================
#  关卡管理器
# ============================================================
class LevelManager:
    def __init__(self, screen_width=1440, screen_height=900):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_level = 1
        self.total_levels = 3
        self.world = None

    def get_config(self):
        return LEVEL_CONFIGS[self.current_level]

    def build_world(self):
        self.world = GameWorld(self.current_level,
                               self.screen_width, self.screen_height)
        return self.world

    def next_level(self):
        if self.current_level < self.total_levels:
            self.current_level += 1
            return True
        return False

    def reset(self):
        self.current_level = 1
        self.world = None
