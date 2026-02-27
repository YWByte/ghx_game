"""
main.py —— 环保小鸭闯关游戏 主程序  (Google Doodle 美术风格)
===========================================
一个环保主题的2D俯视角开放世界闯关游戏
- 主角：可爱的小鸭
- 3个关卡：垃圾分类 → 节约用水 → 植树造林
- 操作：方向键移动，空格键交互
- 目标：完成各关的环保任务
===========================================
"""

import pygame
import sys
import math
import random
import os

from player import Duck
from level import LevelManager, LEVEL_CONFIGS
from items import (
    ParticleSystem, Trash, TrashBin, Faucet, Puddle,
    SeedlingPile, PlantSpot, Lumberjack,
)
from gfx import (
    draw_rounded_card, draw_pill_badge, draw_shadow,
    draw_soft_circle, draw_progress_bar, draw_gradient_v,
    BLUE, RED, YELLOW, GREEN,
    SOFT_BLUE, SOFT_GREEN, SOFT_YELLOW, SOFT_RED,
    WHITE, NEAR_WHITE, LIGHT_GRAY, MID_GRAY, DARK_GRAY, CHARCOAL, NEAR_BLACK,
)

# ============================================================
#  初始化 Pygame
# ============================================================
pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("环保小鸭大冒险")
clock = pygame.time.Clock()


# ============================================================
#  音效
# ============================================================
def create_sound(frequency, duration_ms=100, volume =0.3):
    sample_rate = 44100
    num_samples = int(sample_rate * duration_ms / 1000)
    buf = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = i / sample_rate
        decay = max(0, 1 - i / num_samples)
        value = int(32767 * volume * decay * math.sin(2 * math.pi * frequency * t))
        buf[i * 2] = value & 0xFF
        buf[i * 2 + 1] = (value >> 8) & 0xFF
    return pygame.mixer.Sound(buffer=bytes(buf))


try:
    sound_collect = create_sound(880, 80, 0.2)
    sound_hurt = create_sound(200, 200, 0.3)
    sound_level_up = create_sound(660, 300, 0.25)
    sound_game_over = create_sound(150, 500, 0.3)
    sound_click = create_sound(440, 50, 0.15)
    sound_wrong = create_sound(250, 150, 0.25)
    sounds_enabled = True
except Exception:
    sounds_enabled = False


def play_sound(sound):
    if sounds_enabled:
        try:
            sound.play()
        except Exception:
            pass


# ============================================================
#  中文字体
# ============================================================
def get_font(size):
    font_paths = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                test = font.render("测试", True, (0, 0, 0))
                if test.get_width() > 10:
                    return font
            except Exception:
                continue
    return pygame.font.Font(None, size)


font_small = get_font(30)
font_medium = get_font(38)
font_large = get_font(66)
font_title = get_font(84)

# ============================================================
#  状态常量
# ============================================================
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_LEVEL_UP = "level_up"
STATE_WIN = "win"
STATE_GAME_OVER = "game_over"
STATE_HELP = "help"


# ============================================================
#  Google 风格按钮
# ============================================================
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, icon=None):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.scale = 1.0
        self.elevation = 3  # Material elevation
        self.icon = icon

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        target = 1.04 if self.is_hovered else 1.0
        self.scale += (target - self.scale) * 0.15

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        w = int(self.rect.width * self.scale)
        h = int(self.rect.height * self.scale)
        x = self.rect.centerx - w // 2
        y = self.rect.centery - h // 2
        scaled = pygame.Rect(x, y, w, h)
        radius = h // 2  # 药丸形

        # 阴影
        elev = 5 if self.is_hovered else 3
        shadow = pygame.Surface((w + 12, h + 12), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 35),
                         (6, elev + 3, w, h), border_radius=radius)
        surface.blit(shadow, (x - 6, y - 3))

        # 主体
        pygame.draw.rect(surface, color, scaled, border_radius=radius)

        # 高光条
        hl = pygame.Surface((w - 12, h // 3), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 35 if not self.is_hovered else 50))
        surface.blit(hl, (x + 6, y + 3))

        # 文字
        text_surf = font_medium.render(self.text, True, WHITE)
        tr = text_surf.get_rect(center=scaled.center)
        surface.blit(text_surf, tr)

    def is_clicked(self, mouse_pos, mouse_click):
        return mouse_click and self.rect.collidepoint(mouse_pos)


# ============================================================
#  菜单背景 — 柔和渐变 + 浮动圆形
# ============================================================
class MenuBackground:
    def __init__(self):
        self.time = 0
        # 预渲染渐变底图
        self.base = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        draw_gradient_v(self.base, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                        (230, 240, 255), (200, 225, 250))
        # 浮动装饰圆
        self.circles = []
        for _ in range(24):
            self.circles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "r": random.randint(30, 110),
                "color": random.choice([SOFT_BLUE, SOFT_GREEN, SOFT_YELLOW, SOFT_RED]),
                "speed": random.uniform(0.3, 0.8),
                "phase": random.uniform(0, 6.28),
            })

    def update(self):
        self.time += 0.015

    def draw(self, surface):
        surface.blit(self.base, (0, 0))
        for c in self.circles:
            cx = c["x"] + math.sin(self.time + c["phase"]) * 30
            cy = c["y"] + math.cos(self.time * 0.7 + c["phase"]) * 22
            alpha = 30 + int(math.sin(self.time * 1.5 + c["phase"]) * 15)
            s = pygame.Surface((c["r"] * 2, c["r"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*c["color"], alpha),
                               (c["r"], c["r"]), c["r"])
            surface.blit(s, (int(cx) - c["r"], int(cy) - c["r"]))


# ============================================================
#  纸屑粒子（过关/胜利时）
# ============================================================
class Confetti:
    def __init__(self):
        self.particles = []

    def burst(self, count=80):
        for _ in range(count):
            self.particles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(-80, -10),
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(1.5, 5),
                "size": random.randint(6, 12),
                "color": random.choice([BLUE, RED, YELLOW, GREEN,
                                        SOFT_BLUE, SOFT_GREEN, SOFT_YELLOW]),
                "rot": random.uniform(0, 6.28),
                "rot_speed": random.uniform(-0.1, 0.1),
                "life": random.randint(160, 320),
            })

    def update(self):
        for p in self.particles[:]:
            p["x"] += p["vx"] + math.sin(p["rot"]) * 0.5
            p["y"] += p["vy"]
            p["rot"] += p["rot_speed"]
            p["life"] -= 1
            if p["life"] <= 0 or p["y"] > SCREEN_HEIGHT + 30:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            alpha = min(255, p["life"] * 3)
            s = p["size"]
            w = max(3, int(s * abs(math.cos(p["rot"]))))
            surf = pygame.Surface((w, s), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*p["color"], alpha), (0, 0, w, s),
                             border_radius=2)
            surface.blit(surf, (int(p["x"]), int(p["y"])))


# ============================================================
#  主游戏类
# ============================================================
class Game:
    def __init__(self):
        self.state = STATE_MENU
        self.duck = Duck(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.level_manager = LevelManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particles = ParticleSystem()
        self.confetti = Confetti()
        self.world = None

        self.menu_bg = MenuBackground()

        cx = SCREEN_WIDTH // 2
        self.btn_start = Button(cx, 520, 360, 78, "开始游戏",
                                GREEN, (62, 188, 93))
        self.btn_help = Button(cx, 618, 360, 78, "游戏帮助",
                               BLUE, (86, 153, 254))
        self.btn_quit = Button(cx, 716, 360, 78, "退出游戏",
                               MID_GRAY, (169, 173, 178))
        self.btn_back = Button(cx, 800, 300, 72, "返回菜单",
                               BLUE, (86, 153, 254))
        self.btn_retry = Button(cx, 600, 360, 78, "重新开始",
                                GREEN, (62, 188, 93))
        self.btn_menu = Button(cx, 698, 360, 78, "返回菜单",
                               BLUE, (86, 153, 254))
        self.btn_next = Button(cx, 630, 360, 78, "下一关",
                               GREEN, (62, 188, 93))

        self.result_timer = 0
        self.tip_timer = 180
        self.tip_text = ""
        self.shake_timer = 0
        self.shake_intensity = 0
        self.total_score = 0
        self.space_cooldown = 0

    # --------------------------------------------------
    #  主循环
    # --------------------------------------------------
    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            space_pressed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_click = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state in (STATE_PLAYING, STATE_HELP):
                            self.state = STATE_MENU
                    if event.key == pygame.K_SPACE:
                        space_pressed = True

            if self.space_cooldown > 0:
                self.space_cooldown -= 1
                space_pressed = False

            if self.state == STATE_MENU:
                self._update_menu(mouse_pos, mouse_click)
                self._draw_menu(mouse_pos)
            elif self.state == STATE_PLAYING:
                self._update_playing(space_pressed)
                self._draw_playing()
            elif self.state == STATE_LEVEL_UP:
                self._update_level_up(mouse_pos, mouse_click)
                self._draw_level_up(mouse_pos)
            elif self.state == STATE_WIN:
                self._update_result(mouse_pos, mouse_click, True)
                self._draw_result(mouse_pos, True)
            elif self.state == STATE_GAME_OVER:
                self._update_result(mouse_pos, mouse_click, False)
                self._draw_result(mouse_pos, False)
            elif self.state == STATE_HELP:
                self._update_help(mouse_pos, mouse_click)
                self._draw_help(mouse_pos)

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

    # --------------------------------------------------
    #  菜单
    # --------------------------------------------------
    def _update_menu(self, mouse_pos, mouse_click):
        self.menu_bg.update()
        for btn in [self.btn_start, self.btn_help, self.btn_quit]:
            btn.update(mouse_pos)

        if self.btn_start.is_clicked(mouse_pos, mouse_click):
            play_sound(sound_click)
            self._start_game()
        if self.btn_help.is_clicked(mouse_pos, mouse_click):
            play_sound(sound_click)
            self.state = STATE_HELP
        if self.btn_quit.is_clicked(mouse_pos, mouse_click):
            pygame.quit()
            sys.exit()

    def _draw_menu(self, mouse_pos):
        self.menu_bg.draw(screen)

        t = pygame.time.get_ticks() / 1000
        title_y = 100 + math.sin(t * 1.5) * 8

        # 标题 — Google 四色
        title_str = "环保小鸭大冒险"
        google_colors = [BLUE, RED, YELLOW, BLUE, GREEN, RED, YELLOW]
        total_w = 0
        char_surfs = []
        for i, ch in enumerate(title_str):
            c = google_colors[i % len(google_colors)]
            s = font_title.render(ch, True, c)
            char_surfs.append(s)
            total_w += s.get_width()

        x_cursor = SCREEN_WIDTH // 2 - total_w // 2
        for i, s in enumerate(char_surfs):
            yo = math.sin(t * 2 + i * 0.5) * 4
            # 阴影
            shadow = font_title.render(title_str[i], True, (0, 0, 0, 40))
            screen.blit(shadow, (x_cursor + 3, int(title_y + yo) + 3))
            screen.blit(s, (x_cursor, int(title_y + yo)))
            x_cursor += s.get_width()

        # 副标题
        sub = font_small.render("保护地球，从我做起！", True, DARK_GRAY)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2,
                           int(title_y) + 95))

        # 菜单小鸭
        duck_y = int(title_y) + 225 + math.sin(t * 2) * 8
        self._draw_menu_duck(SCREEN_WIDTH // 2, duck_y)

        # 按钮
        self.btn_start.draw(screen)
        self.btn_help.draw(screen)
        self.btn_quit.draw(screen)

        # 版本
        ver = font_small.render("v3.0  小学五年级编程作品", True, MID_GRAY)
        screen.blit(ver, (SCREEN_WIDTH // 2 - ver.get_width() // 2,
                           SCREEN_HEIGHT - 48))

    def _draw_menu_duck(self, cx, cy):
        """菜单中的大号可爱小鸭"""
        # 阴影
        s = pygame.Surface((80, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 25), (0, 0, 80, 22))
        screen.blit(s, (cx - 40, cy + 35))
        # 脚
        pygame.draw.ellipse(screen, (255, 138, 51), (cx - 22, cy + 28, 26, 13))
        pygame.draw.ellipse(screen, (255, 138, 51), (cx + 3, cy + 28, 26, 13))
        # 身体
        pygame.draw.ellipse(screen, (255, 213, 79), (cx - 36, cy - 16, 72, 55))
        belly = pygame.Surface((46, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(belly, (255, 236, 179, 120), (0, 0, 46, 32))
        screen.blit(belly, (cx - 23, cy - 6))
        # 翅膀
        pygame.draw.polygon(screen, (255, 193, 7), [
            (cx + 26, cy - 6), (cx + 46, cy + 13), (cx + 26, cy + 22)
        ])
        # 头
        pygame.draw.circle(screen, (255, 224, 100), (cx + 6, cy - 32), 28)
        hl = pygame.Surface((26, 26), pygame.SRCALPHA)
        pygame.draw.circle(hl, (255, 245, 180, 80), (13, 13), 13)
        screen.blit(hl, (cx - 13, cy - 52))
        # 眼睛
        pygame.draw.circle(screen, WHITE, (cx + 16, cy - 36), 10)
        pygame.draw.circle(screen, (55, 55, 55), (cx + 18, cy - 36), 6)
        pygame.draw.circle(screen, WHITE, (cx + 19, cy - 37), 3)
        # 嘴
        pygame.draw.polygon(screen, (255, 138, 51), [
            (cx + 30, cy - 38), (cx + 50, cy - 30), (cx + 30, cy - 22)
        ])
        pygame.draw.line(screen, (230, 115, 40),
                         (cx + 30, cy - 30), (cx + 46, cy - 30), 2)
        # 腮红
        blush = pygame.Surface((18, 11), pygame.SRCALPHA)
        pygame.draw.ellipse(blush, (255, 171, 145, 80), (0, 0, 18, 11))
        screen.blit(blush, (cx - 4, cy - 22))

    # --------------------------------------------------
    #  帮助页
    # --------------------------------------------------
    def _update_help(self, mouse_pos, mouse_click):
        self.menu_bg.update()
        self.btn_back.update(mouse_pos)
        if self.btn_back.is_clicked(mouse_pos, mouse_click):
            play_sound(sound_click)
            self.state = STATE_MENU

    def _draw_help(self, mouse_pos):
        self.menu_bg.draw(screen)

        # 卡片
        card = pygame.Rect(100, 45, 1240, 720)
        draw_rounded_card(screen, card, NEAR_WHITE, 20, shadow=True)

        title = font_large.render("游戏帮助", True, CHARCOAL)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 72))

        sections = [
            ("操作说明", BLUE, [
                "← → ↑ ↓  方向键控制小鸭走动",
                "空格键      与物体交互（拾取/投放/关闭）",
                "ESC        返回菜单",
            ]),
            ("关卡介绍", GREEN, [
                "第一关 操场：捡垃圾送到正确垃圾桶",
                "第二关 教室：关掉漏水的水龙头",
                "第三关 荒地：拾取树苗种到土坑里",
            ]),
            ("小贴士", YELLOW, [
                "靠近物体时按空格键可以交互",
                "一次只能携带一个物品",
                "分错垃圾桶会扣分哦！",
            ]),
        ]

        y = 170
        for title_text, accent, lines in sections:
            draw_pill_badge(screen, 240, y, title_text, font_small,
                            accent, WHITE, shadow=False)
            y += 42
            for line in lines:
                surf = font_small.render(line, True, DARK_GRAY)
                screen.blit(surf, (200, y))
                y += 38
            y += 16

        self.btn_back.draw(screen)

    # --------------------------------------------------
    #  开始
    # --------------------------------------------------
    def _start_game(self):
        self.state = STATE_PLAYING
        self.duck.full_reset()
        self.level_manager.reset()
        self.world = self.level_manager.build_world()
        self.particles = ParticleSystem()
        self.total_score = 0
        self.tip_timer = 180
        self.tip_text = self.level_manager.get_config()["tip"]

    # --------------------------------------------------
    #  游戏中
    # --------------------------------------------------
    def _update_playing(self, space_pressed):
        keys = pygame.key.get_pressed()
        self.duck.handle_input(keys)
        self.duck.update()

        if self.world:
            self.world.update()
        self.particles.update()

        if self.shake_timer > 0:
            self.shake_timer -= 1
        if self.tip_timer > 0:
            self.tip_timer -= 1

        if not self.world:
            return

        level_id = self.level_manager.current_level
        px, py = self.duck.x, self.duck.y

        if level_id == 2:
            if self.world.get_colliding_puddles(px, py):
                self.duck.apply_slow(30)

        if level_id == 3:
            lj = self.world.get_colliding_lumberjacks(px, py)
            if lj:
                if self.duck.take_damage():
                    play_sound(sound_hurt)
                    self.particles.emit(px, py, (255, 80, 80), 20)
                    self.shake_timer = 10
                    self.shake_intensity = 7

        if space_pressed:
            self._handle_interact(level_id, px, py)

        if self.duck.lives <= 0:
            self.state = STATE_GAME_OVER
            self.result_timer = 0
            play_sound(sound_game_over)
            return

        if self.world.is_time_up():
            if self.world.score < LEVEL_CONFIGS[2]["target_score"]:
                self.state = STATE_GAME_OVER
                self.result_timer = 0
                play_sound(sound_game_over)
                return

        if self.world.is_level_complete():
            self.total_score += self.world.score
            self.confetti.burst(70)
            if self.level_manager.current_level >= self.level_manager.total_levels:
                self.state = STATE_WIN
                self.result_timer = 0
                self.confetti.burst(100)
                play_sound(sound_level_up)
            else:
                self.state = STATE_LEVEL_UP
                self.result_timer = 0
                play_sound(sound_level_up)

        if level_id == 1:
            trash_count = len([o for o in self.world.objects
                               if isinstance(o, Trash) and o.active])
            if trash_count < 5:
                self.world._spawn_trash(8)

    def _handle_interact(self, level_id, px, py):
        nearest = self.world.get_nearest_interactable(px, py, max_dist=80)
        if level_id == 1:
            self._interact_level_1(nearest, px, py)
        elif level_id == 2:
            self._interact_level_2(nearest)
        elif level_id == 3:
            self._interact_level_3(nearest, px, py)
        self.space_cooldown = 10

    def _interact_level_1(self, nearest, px, py):
        if nearest is None:
            self.duck.show_hint("附近没有可交互的物体", 60)
            return
        if isinstance(nearest, Trash) and self.duck.carrying is None:
            self.duck.pick_up(nearest.item_name, nearest.category, "trash")
            nearest.active = False
            play_sound(sound_collect)
            self.particles.emit(nearest.x, nearest.y, (100, 255, 100), 10)
            self.duck.show_hint(f"拾取了 {nearest.item_name}", 60)
        elif isinstance(nearest, TrashBin) and self.duck.carrying_type == "trash":
            if self.duck.carrying_category == nearest.category:
                self.world.score += 1
                play_sound(sound_collect)
                self.particles.emit(nearest.x, nearest.y, (100, 255, 100), 15)
                self.duck.show_hint("分类正确！+1", 60)
            else:
                self.world.score = max(0, self.world.score - 1)
                play_sound(sound_wrong)
                self.particles.emit(nearest.x, nearest.y, (255, 80, 80), 15)
                self.duck.show_hint("分错了！-1", 60)
            self.duck.drop_item()
        elif isinstance(nearest, TrashBin) and self.duck.carrying is None:
            self.duck.show_hint("先去捡一个垃圾再来投放", 60)
        elif isinstance(nearest, Trash) and self.duck.carrying is not None:
            self.duck.show_hint("手上已经有东西了", 60)

    def _interact_level_2(self, nearest):
        if nearest is None:
            self.duck.show_hint("附近没有可交互的物体", 60)
            return
        if isinstance(nearest, Faucet) and nearest.is_open:
            nearest.close()
            self.world.score += 1
            play_sound(sound_collect)
            self.particles.emit(nearest.x, nearest.y, (100, 200, 255), 12)
            self.duck.show_hint("关掉水龙头！+1", 60)

    def _interact_level_3(self, nearest, px, py):
        if nearest is None:
            self.duck.show_hint("附近没有可交互的物体", 60)
            return
        if isinstance(nearest, SeedlingPile) and self.duck.carrying is None:
            self.duck.pick_up("树苗", "seedling", "seedling")
            play_sound(sound_collect)
            self.particles.emit(nearest.x, nearest.y, (100, 255, 100), 10)
            self.duck.show_hint("拾取了树苗", 60)
        elif isinstance(nearest, PlantSpot) and not nearest.planted:
            if self.duck.carrying_type == "seedling":
                nearest.plant()
                self.world.score += 1
                self.duck.drop_item()
                play_sound(sound_collect)
                self.particles.emit(nearest.x, nearest.y, (50, 200, 50), 15)
                self.duck.show_hint("种下一棵树！+1", 60)
            else:
                self.duck.show_hint("先去树苗堆拿一棵树苗", 60)
        elif isinstance(nearest, SeedlingPile) and self.duck.carrying is not None:
            self.duck.show_hint("手上已经有东西了", 60)

    # --------------------------------------------------
    #  绘制游戏画面
    # --------------------------------------------------
    def _draw_playing(self):
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            shake_x = random.randint(-self.shake_intensity, self.shake_intensity)
            shake_y = random.randint(-self.shake_intensity, self.shake_intensity)

        game_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.world:
            self.world.draw_ground(game_surf)
            self.world.draw_objects(game_surf)

        self.particles.draw(game_surf)
        self.duck.draw(game_surf)

        if self.world:
            self.world.draw_hud(game_surf, font_medium, self.duck.lives)

        # 提示文字 — 药丸标签
        if self.tip_timer > 0 and self.tip_text:
            alpha = min(200, self.tip_timer * 3)
            tip_surf = font_small.render(self.tip_text, True, WHITE)
            tw = tip_surf.get_width()
            bg = pygame.Surface((tw + 42, 44), pygame.SRCALPHA)
            pygame.draw.rect(bg, (60, 64, 67, alpha),
                             (0, 0, tw + 42, 44), border_radius=22)
            game_surf.blit(bg, (SCREEN_WIDTH // 2 - tw // 2 - 21, 80))
            game_surf.blit(tip_surf, (SCREEN_WIDTH // 2 - tw // 2, 88))

        screen.fill((0, 0, 0))
        screen.blit(game_surf, (shake_x, shake_y))

    # --------------------------------------------------
    #  过关画面
    # --------------------------------------------------
    def _update_level_up(self, mouse_pos, mouse_click):
        self.result_timer += 1
        self.confetti.update()
        self.btn_next.update(mouse_pos)
        if self.btn_next.is_clicked(mouse_pos, mouse_click) and self.result_timer > 30:
            play_sound(sound_click)
            self.level_manager.next_level()
            self.world = self.level_manager.build_world()
            self.duck.reset()
            self.tip_text = self.level_manager.get_config()["tip"]
            self.tip_timer = 180
            self.state = STATE_PLAYING

    def _draw_level_up(self, mouse_pos):
        if self.world:
            self.world.draw_ground(screen)
            self.world.draw_objects(screen)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        self.confetti.draw(screen)

        # 卡片
        card = pygame.Rect(SCREEN_WIDTH // 2 - 320, 150, 640, 420)
        draw_rounded_card(screen, card, NEAR_WHITE, 24, shadow=True)

        bounce = abs(math.sin(self.result_timer * 0.06)) * 12
        title = font_large.render("过关啦！", True, GREEN)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,
                             185 - int(bounce)))

        score = font_medium.render(
            f"本关完成：{self.world.score if self.world else 0} 个任务",
            True, CHARCOAL)
        screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 320))

        nxt = self.level_manager.current_level + 1
        if nxt <= 3:
            cfg = LEVEL_CONFIGS[nxt]
            nt = font_medium.render(f"下一关：{cfg['name']}", True, BLUE)
            screen.blit(nt, (SCREEN_WIDTH // 2 - nt.get_width() // 2, 400))
            dt = font_small.render(cfg["description"], True, DARK_GRAY)
            screen.blit(dt, (SCREEN_WIDTH // 2 - dt.get_width() // 2, 452))

        self.btn_next.draw(screen)

    # --------------------------------------------------
    #  胜利/失败
    # --------------------------------------------------
    def _update_result(self, mouse_pos, mouse_click, won):
        self.result_timer += 1
        self.confetti.update()
        self.btn_retry.update(mouse_pos)
        self.btn_menu.update(mouse_pos)

        if self.result_timer > 30:
            if self.btn_retry.is_clicked(mouse_pos, mouse_click):
                play_sound(sound_click)
                self._start_game()
            if self.btn_menu.is_clicked(mouse_pos, mouse_click):
                play_sound(sound_click)
                self.state = STATE_MENU

    def _draw_result(self, mouse_pos, won):
        if won:
            draw_gradient_v(screen, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                            (235, 245, 230), (210, 235, 205))
        else:
            draw_gradient_v(screen, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
                            (240, 235, 245), (225, 220, 235))

        self.confetti.draw(screen)

        # 卡片
        card = pygame.Rect(SCREEN_WIDTH // 2 - 350, 100, 700, 420)
        draw_rounded_card(screen, card, NEAR_WHITE, 24, shadow=True)

        bounce = abs(math.sin(self.result_timer * 0.05)) * 10

        if won:
            title = font_large.render("恭喜通关！", True, GREEN)
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,
                                 140 - int(bounce)))

            total_t = font_medium.render(f"总完成：{self.total_score} 个任务",
                                         True, CHARCOAL)
            screen.blit(total_t, (SCREEN_WIDTH // 2 - total_t.get_width() // 2, 260))

            msg = font_medium.render("你是环保小卫士！地球因你更美好！",
                                     True, DARK_GRAY)
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 350))

            # 星星
            for i in range(3):
                sx = SCREEN_WIDTH // 2 - 80 + i * 80
                sy = 440
                self._draw_star(screen, sx, sy, 22, YELLOW)
        else:
            title = font_large.render("游戏结束", True, RED)
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,
                                 140 - int(bounce)))

            score_t = font_medium.render(
                f"已完成：{self.world.score if self.world else 0} 个",
                True, CHARCOAL)
            screen.blit(score_t, (SCREEN_WIDTH // 2 - score_t.get_width() // 2, 280))

            msg = font_medium.render("别灰心，再试一次吧！", True, DARK_GRAY)
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 370))

        self.btn_retry.draw(screen)
        self.btn_menu.draw(screen)

    def _draw_star(self, surface, cx, cy, size, color):
        """五角星"""
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = size if i % 2 == 0 else size * 0.45
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)
        # 高光
        inner = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = (size * 0.6 if i % 2 == 0 else size * 0.25)
            inner.append((cx + r * math.cos(angle), cy - 2 + r * math.sin(angle)))
        pygame.draw.polygon(surface, (255, 235, 120), inner)


# ============================================================
#  启动
# ============================================================
if __name__ == "__main__":
    print("=" * 40)
    print("  环保小鸭大冒险 v3.0")
    print("  保护地球，从我做起！")
    print("=" * 40)
    print()
    print("操作说明：")
    print("  方向键 ← → ↑ ↓  控制小鸭走动")
    print("  空格键            与物体交互")
    print("  ESC              返回菜单")
    print()

    game = Game()
    game.run()
