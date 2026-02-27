"""
player.py —— 小鸭角色模块  (Google Doodle 美术风格)
包含：小鸭的绘制、移动、动画、碰撞检测、物品携带与交互
"""

import pygame
import math
import os

from gfx import (
    draw_soft_circle, draw_soft_ellipse, draw_pill_badge,
    YELLOW, WHITE, CHARCOAL, NEAR_BLACK,
)

# 小鸭配色
DUCK_BODY = (255, 213, 79)        # Material Amber 300
DUCK_BODY_LIGHT = (255, 236, 179) # Amber 100
DUCK_BODY_DARK = (255, 183, 77)   # Amber 400
DUCK_WING = (255, 193, 7)         # Amber 600
DUCK_BEAK = (255, 138, 51)        # Deep Orange 300
DUCK_FOOT = (255, 138, 51)
DUCK_HEAD = (255, 224, 100)
DUCK_HEAD_LIGHT = (255, 245, 180)
DUCK_BLUSH = (255, 171, 145)      # Deep Orange 200
DUCK_EYE = (55, 55, 55)


def _load_chinese_font(size):
    paths = [
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
    return pygame.font.Font(None, size)


class Duck:
    def __init__(self, screen_width=1440, screen_height=900):
        self.x = screen_width // 2
        self.y = screen_height // 2
        self.width = 80
        self.height = 80
        self.speed = 7
        self.base_speed = 7
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.lives = 3
        self.score = 0
        self.invincible = False
        self.invincible_timer = 0

        self.carrying = None
        self.carrying_category = None
        self.carrying_type = None

        self.interact_hint = ""
        self.hint_timer = 0

        self.slowed = False
        self.slow_timer = 0

        self.facing_right = True
        self.bob_timer = 0
        self.blink_timer = 0
        self.is_blinking = False
        self.walk_frame = 0

        self._label_font = _load_chinese_font(24)
        self._hint_font = _load_chinese_font(22)

    def handle_input(self, keys):
        moving = False
        current_speed = self.base_speed
        if self.slowed:
            current_speed = self.base_speed * 0.4
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.slowed = False

        if keys[pygame.K_LEFT]:
            self.x -= current_speed
            self.facing_right = False
            moving = True
        if keys[pygame.K_RIGHT]:
            self.x += current_speed
            self.facing_right = True
            moving = True
        if keys[pygame.K_UP]:
            self.y -= current_speed
            moving = True
        if keys[pygame.K_DOWN]:
            self.y += current_speed
            moving = True

        self.x = max(self.width // 2,
                     min(self.screen_width - self.width // 2, self.x))
        self.y = max(self.height // 2 + 75,
                     min(self.screen_height - self.height // 2, self.y))

        if moving:
            self.walk_frame += 1
        else:
            self.walk_frame = 0

    def update(self):
        self.bob_timer += 0.08
        self.blink_timer += 1
        if self.blink_timer > 120:
            self.is_blinking = True
            if self.blink_timer > 128:
                self.is_blinking = False
                self.blink_timer = 0
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        if self.hint_timer > 0:
            self.hint_timer -= 1

    def take_damage(self):
        if not self.invincible:
            self.lives -= 1
            self.invincible = True
            self.invincible_timer = 90
            return True
        return False

    def apply_slow(self, duration=60):
        self.slowed = True
        self.slow_timer = duration

    def pick_up(self, item_name, category, item_type):
        self.carrying = item_name
        self.carrying_category = category
        self.carrying_type = item_type

    def drop_item(self):
        self.carrying = None
        self.carrying_category = None
        self.carrying_type = None

    def show_hint(self, text, duration=90):
        self.interact_hint = text
        self.hint_timer = duration

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2,
                           self.y - self.height // 2,
                           self.width, self.height)

    def draw(self, screen):
        if self.invincible and self.invincible_timer % 6 < 3:
            return

        bob = math.sin(self.bob_timer) * 4
        cx = int(self.x)
        cy = int(self.y + bob)
        d = 1 if self.facing_right else -1

        # ---- 地面阴影 ----
        shadow = pygame.Surface((60, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 28), (0, 0, 60, 16))
        screen.blit(shadow, (cx - 30, cy + 33))

        # ---- 脚 ----
        foot_y = cy + 28
        foot_off = math.sin(self.walk_frame * 0.3) * 5 if self.walk_frame > 0 else 0
        pygame.draw.ellipse(screen, DUCK_FOOT,
                            (cx - 22, foot_y + int(foot_off), 23, 12))
        pygame.draw.ellipse(screen, DUCK_FOOT,
                            (cx + 1, foot_y - int(foot_off), 23, 12))
        # 脚趾纹
        pygame.draw.line(screen, (230, 115, 40),
                         (cx - 15, foot_y + int(foot_off) + 5),
                         (cx - 7, foot_y + int(foot_off)), 2)
        pygame.draw.line(screen, (230, 115, 40),
                         (cx + 8, foot_y - int(foot_off) + 5),
                         (cx + 16, foot_y - int(foot_off)), 2)

        # ---- 身体 ----
        body_rect = pygame.Rect(cx - 33, cy - 15, 66, 50)
        pygame.draw.ellipse(screen, DUCK_BODY, body_rect)
        # 腹部高光
        belly = pygame.Surface((40, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(belly, (*DUCK_BODY_LIGHT, 120), (0, 0, 40, 30))
        screen.blit(belly, (cx - 20, cy - 5))

        # ---- 翅膀 ----
        wing_bob = math.sin(self.bob_timer * 2) * 5
        wing_x = cx + d * 25
        pts = [
            (wing_x, cy - 7),
            (wing_x + d * 16, cy + 12 + int(wing_bob)),
            (wing_x + d * 3, cy + 23),
            (wing_x - d * 3, cy + 17),
        ]
        # 翅膀阴影
        shadow_pts = [(p[0] + 2, p[1] + 2) for p in pts]
        s = pygame.Surface((100, 66), pygame.SRCALPHA)
        offset_pts = [(p[0] - cx + 50, p[1] - cy + 16) for p in shadow_pts]
        pygame.draw.polygon(s, (0, 0, 0, 20), offset_pts)
        screen.blit(s, (cx - 50, cy - 16))
        pygame.draw.polygon(screen, DUCK_WING, pts)
        # 翅膀高光
        hl_pts = [pts[0], (wing_x + d * 8, cy + 3 + int(wing_bob // 2)), pts[3]]
        pygame.draw.polygon(screen, (255, 210, 60), hl_pts)

        # ---- 头 ----
        head_x = cx + d * 5
        head_y = cy - 30
        # 头部阴影
        head_shadow = pygame.Surface((56, 56), pygame.SRCALPHA)
        pygame.draw.circle(head_shadow, (0, 0, 0, 18), (28, 30), 25)
        screen.blit(head_shadow, (head_x - 28, head_y - 27))
        # 头
        pygame.draw.circle(screen, DUCK_HEAD, (head_x, head_y), 25)
        # 头部高光
        hl = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(hl, (*DUCK_HEAD_LIGHT, 80), (12, 12), 12)
        screen.blit(hl, (head_x - 15, head_y - 20))

        # ---- 眼睛 ----
        eye_x = head_x + d * 10
        eye_y = head_y - 3
        if self.is_blinking:
            pygame.draw.line(screen, DUCK_EYE,
                             (eye_x - 5, eye_y), (eye_x + 5, eye_y), 3)
        else:
            # 白底
            pygame.draw.circle(screen, WHITE, (eye_x, eye_y), 8)
            # 瞳孔
            pygame.draw.circle(screen, DUCK_EYE, (eye_x + d * 2, eye_y), 5)
            # 高光
            pygame.draw.circle(screen, WHITE, (eye_x + d * 2 + 1, eye_y - 2), 2)

        # ---- 嘴巴 ----
        beak_x = head_x + d * 23
        beak_y = head_y + 5
        beak_pts = [
            (head_x + d * 16, beak_y - 7),
            (beak_x, beak_y),
            (head_x + d * 16, beak_y + 7),
        ]
        pygame.draw.polygon(screen, DUCK_BEAK, beak_pts)
        # 嘴巴中线
        pygame.draw.line(screen, (230, 115, 40),
                         (head_x + d * 16, beak_y), (beak_x, beak_y), 2)

        # ---- 腮红 ----
        blush_x = head_x - d * 2
        blush_y = head_y + 10
        blush = pygame.Surface((16, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(blush, (*DUCK_BLUSH, 80), (0, 0, 16, 10))
        screen.blit(blush, (blush_x - 8, blush_y - 5))

        # ---- 头顶：携带物品 ----
        if self.carrying:
            draw_pill_badge(screen, cx, cy - 76,
                            f" {self.carrying} ",
                            self._label_font,
                            (66, 133, 244),  # Google Blue
                            WHITE, shadow=True)

        # ---- 交互提示 ----
        if self.hint_timer > 0 and self.interact_hint:
            alpha = min(255, self.hint_timer * 6)
            hint_surf = self._hint_font.render(
                self.interact_hint, True, WHITE)
            hw, hh = hint_surf.get_size()
            pad = 16
            bg = pygame.Surface((hw + pad * 2, hh + 12), pygame.SRCALPHA)
            pygame.draw.rect(bg, (60, 64, 67, min(200, alpha)),
                             (0, 0, hw + pad * 2, hh + 12),
                             border_radius=18)
            hx = cx - hw // 2 - pad
            hy = cy + 50
            screen.blit(bg, (hx, hy))
            screen.blit(hint_surf, (hx + pad, hy + 6))

        # ---- 减速指示 ----
        if self.slowed:
            draw_pill_badge(screen, cx, cy - 100, "减速中",
                            self._hint_font, (100, 181, 246), WHITE)

    def reset(self):
        self.x = self.screen_width // 2
        self.y = self.screen_height // 2
        self.invincible = False
        self.invincible_timer = 0
        self.carrying = None
        self.carrying_category = None
        self.carrying_type = None
        self.slowed = False
        self.slow_timer = 0
        self.interact_hint = ""
        self.hint_timer = 0

    def full_reset(self):
        self.reset()
        self.lives = 3
        self.score = 0
