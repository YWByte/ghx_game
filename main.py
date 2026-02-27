"""
垃圾分类小游戏（单文件版）
- 4 类垃圾，50 个物体
- 10 秒倒计时拖拽分类
- 开始菜单 / 帮助说明 / 结果页面
"""

import sys
import math
import random
import os
import pygame

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ================================
# 常量与配置
# ================================
SCREEN_W, SCREEN_H = 1440, 900
FPS = 60
TIME_LIMIT = 10  # 每个垃圾 10 秒

STATE_MENU = "menu"
STATE_HELP = "help"
STATE_PLAY = "play"
STATE_RESULT = "result"

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK = (45, 45, 55)
LIGHT = (245, 248, 255)
MUTED = (120, 125, 140)

COLOR_BG_TOP = (230, 245, 255)
COLOR_BG_BOTTOM = (255, 250, 240)

CAT_RECY = "可回收"
CAT_KITCHEN = "厨余"
CAT_HAZ = "有害"
CAT_OTHER = "其他"

CATEGORY_STYLES = {
    CAT_RECY: (76, 175, 255),
    CAT_KITCHEN: (102, 204, 102),
    CAT_HAZ: (255, 120, 120),
    CAT_OTHER: (255, 200, 80),
}

CATEGORIES = [CAT_RECY, CAT_KITCHEN, CAT_HAZ, CAT_OTHER]

# 50 个垃圾数据：(名称, 分类, emoji)
TRASH_ITEMS = [
    ("纸盒", CAT_RECY, "📦"), ("塑料瓶", CAT_RECY, "🧴"), ("旧报纸", CAT_RECY, "📰"), ("玻璃杯", CAT_RECY, "🥛"),
    ("易拉罐", CAT_RECY, "🥫"), ("快递箱", CAT_RECY, "📫"), ("纸袋", CAT_RECY, "🛍️"), ("旧书本", CAT_RECY, "📚"),
    ("牛奶盒", CAT_RECY, "🥛"), ("纸筒", CAT_RECY, "🧻"), ("杂志", CAT_RECY, "📖"), ("塑料桶", CAT_RECY, "🪣"),
    ("菜叶", CAT_KITCHEN, "🥬"), ("果皮", CAT_KITCHEN, "🍌"), ("鱼骨", CAT_KITCHEN, "🐟"), ("蛋壳", CAT_KITCHEN, "🥚"),
    ("面包", CAT_KITCHEN, "🍞"), ("茶叶", CAT_KITCHEN, "🍵"), ("骨头", CAT_KITCHEN, "🦴"), ("剩饭", CAT_KITCHEN, "🍚"),
    ("花瓣", CAT_KITCHEN, "🌸"), ("果核", CAT_KITCHEN, "🍎"), ("蔬菜根", CAT_KITCHEN, "🥕"), ("瓜子壳", CAT_KITCHEN, "🌻"),
    ("电池", CAT_HAZ, "🔋"), ("水银温度计", CAT_HAZ, "🌡️"), ("过期药片", CAT_HAZ, "💊"), ("杀虫剂", CAT_HAZ, "🧪"),
    ("灯管", CAT_HAZ, "💡"), ("油漆桶", CAT_HAZ, "🎨"), ("荧光灯", CAT_HAZ, "🔦"), ("指甲油", CAT_HAZ, "💅"),
    ("消毒液", CAT_HAZ, "🧴"), ("口红", CAT_HAZ, "💄"), ("创可贴", CAT_HAZ, "🩹"), ("墨盒", CAT_HAZ, "🖨️"),
    ("纸巾", CAT_OTHER, "🧻"), ("陶瓷碗", CAT_OTHER, "🍜"), ("灰尘", CAT_OTHER, "💨"), ("烟蒂", CAT_OTHER, "🚬"),
    ("一次性餐盒", CAT_OTHER, "🍱"), ("脏塑料袋", CAT_OTHER, "🛍️"), ("口罩", CAT_OTHER, "😷"), ("海绵", CAT_OTHER, "🧽"),
    ("镜子", CAT_OTHER, "🪞"), ("贝壳", CAT_OTHER, "🐚"), ("尿不湿", CAT_OTHER, "👶"), ("棉签", CAT_OTHER, "🦻"),
    ("牙刷", CAT_OTHER, "🪥"), ("拖把头", CAT_OTHER, "🧹"),
]

# ================================
# 工具函数
# ================================

def get_font(size):
    paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return pygame.font.Font(p, size)
            except Exception:
                pass
    return pygame.font.Font(None, size)


def draw_text(surface, text, font, color, center):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)
    return rect


def draw_gradient(surface, top, bottom):
    for y in range(SCREEN_H):
        ratio = y / SCREEN_H
        color = (
            int(top[0] * (1 - ratio) + bottom[0] * ratio),
            int(top[1] * (1 - ratio) + bottom[1] * ratio),
            int(top[2] * (1 - ratio) + bottom[2] * ratio),
        )
        pygame.draw.line(surface, color, (0, y), (SCREEN_W, y))


def rounded_rect(surface, rect, color, radius=20, alpha=255):
    temp = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(temp, (*color, alpha), temp.get_rect(), border_radius=radius)
    surface.blit(temp, rect.topleft)


def draw_button(surface, rect, label, font, base_color, hover=False):
    color = tuple(min(255, c + 20) for c in base_color) if hover else base_color
    rounded_rect(surface, rect, color, 28)
    pygame.draw.rect(surface, (255, 255, 255, 80), rect, 3, border_radius=28)
    draw_text(surface, label, font, WHITE, rect.center)


def draw_star(surface, center, size, color):
    cx, cy = center
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = size if i % 2 == 0 else size * 0.45
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(surface, color, points)


# ================================
# Emoji 渲染（Pillow → pygame Surface）
# ================================

_emoji_cache = {}

# Apple Color Emoji 只支持特定尺寸，用不支持的尺寸会渲染成灰色方块
_APPLE_EMOJI_SIZES = [160, 96, 64, 52, 48, 40, 32, 26, 20]

def _find_emoji_font():
    """查找系统 emoji 字体"""
    candidates = [
        "/System/Library/Fonts/Apple Color Emoji.ttc",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "C:/Windows/Fonts/seguiemj.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

_EMOJI_FONT_PATH = _find_emoji_font() if HAS_PIL else None

def _best_emoji_render_size(target):
    """选择 >= target 且最接近的可用渲染尺寸，保证缩放后清晰"""
    best = _APPLE_EMOJI_SIZES[0]  # 默认最大
    for s in _APPLE_EMOJI_SIZES:
        if s >= target:
            best = s
    return best

def emoji_to_surface(emoji_char, size=80):
    """将 emoji 渲染为 pygame Surface（带缓存）"""
    key = (emoji_char, size)
    if key in _emoji_cache:
        return _emoji_cache[key]

    if HAS_PIL and _EMOJI_FONT_PATH:
        try:
            render_size = _best_emoji_render_size(size)
            font = ImageFont.truetype(_EMOJI_FONT_PATH, render_size)
            canvas = render_size + 40
            img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.text((4, 4), emoji_char, font=font, embedded_color=True)
            bbox = img.getbbox()
            if bbox:
                img = img.crop(bbox)
            raw = img.tobytes()
            surf = pygame.image.fromstring(raw, img.size, "RGBA")
            surf = pygame.transform.smoothscale(surf, (size, size))
            _emoji_cache[key] = surf
            return surf
        except Exception:
            pass

    # 回退：用中文字体渲染 emoji 文字
    fallback_font = get_font(size)
    surf = fallback_font.render(emoji_char, True, (80, 80, 80))
    _emoji_cache[key] = surf
    return surf


def draw_item_icon(surface, center, size, category, seed, emoji_char=None):
    """绘制物品图标：优先用 emoji，回退用几何图形"""
    if emoji_char:
        emoji_surf = emoji_to_surface(emoji_char, size * 2)
        rect = emoji_surf.get_rect(center=center)
        surface.blit(emoji_surf, rect)
        return

    # 回退：原来的几何图标
    x, y = center
    base = CATEGORY_STYLES[category]
    shade = (min(255, base[0] + 40), min(255, base[1] + 40), min(255, base[2] + 40))
    r = size
    random.seed(seed)
    if category == CAT_RECY:
        pygame.draw.circle(surface, base, center, r)
        pygame.draw.circle(surface, shade, center, r - 8)
        pygame.draw.rect(surface, WHITE, (x - 6, y - 18, 12, 36), border_radius=6)
    elif category == CAT_KITCHEN:
        pygame.draw.ellipse(surface, base, (x - r, y - r + 4, r * 2, r * 2 - 8))
        pygame.draw.circle(surface, shade, (x - 8, y - 6), 6)
        pygame.draw.circle(surface, shade, (x + 10, y + 4), 5)
    elif category == CAT_HAZ:
        pygame.draw.circle(surface, base, center, r)
        pygame.draw.circle(surface, WHITE, center, r - 8)
        pygame.draw.circle(surface, base, center, r - 14)
    else:
        pygame.draw.rect(surface, base, (x - r, y - r, r * 2, r * 2), border_radius=12)
        draw_star(surface, (x, y), r // 2, shade)


def make_bins():
    bin_w, bin_h = 240, 170
    gap = 50
    total = bin_w * 4 + gap * 3
    start_x = (SCREEN_W - total) // 2
    y = SCREEN_H - 230
    bins = []
    for i, cat in enumerate(CATEGORIES):
        x = start_x + i * (bin_w + gap)
        rect = pygame.Rect(x, y, bin_w, bin_h)
        bins.append({"rect": rect, "cat": cat, "color": CATEGORY_STYLES[cat]})
    return bins


# ================================
# 轻量类
# ================================

class TrashItem:
    def __init__(self, name, category, index, emoji=""):
        self.name = name
        self.category = category
        self.index = index
        self.emoji = emoji
        self.radius = 46
        self.reset_position()

    def reset_position(self):
        self.pos = [SCREEN_W // 2, 260]
        self.dragging = False
        self.offset = (0, 0)

    def start_drag(self, mouse_pos):
        mx, my = mouse_pos
        dx = mx - self.pos[0]
        dy = my - self.pos[1]
        if dx * dx + dy * dy <= (self.radius + 8) ** 2:
            self.dragging = True
            self.offset = (dx, dy)
            return True
        return False

    def drag(self, mouse_pos):
        if self.dragging:
            mx, my = mouse_pos
            self.pos = [mx - self.offset[0], my - self.offset[1]]

    def stop_drag(self):
        self.dragging = False

    def draw(self, surface):
        draw_item_icon(surface, self.pos, self.radius, self.category, self.index, self.emoji)


# ================================
# 游戏主逻辑
# ================================

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("垃圾分类小能手")
        self.clock = pygame.time.Clock()

        self.font_title = get_font(72)
        self.font_big = get_font(40)
        self.font_mid = get_font(30)
        self.font_small = get_font(24)

        self.state = STATE_MENU
        self.bins = make_bins()
        self.reset_game()

        self.btn_start = pygame.Rect(SCREEN_W // 2 - 160, 520, 320, 70)
        self.btn_help = pygame.Rect(SCREEN_W // 2 - 160, 620, 320, 70)
        self.btn_back = pygame.Rect(60, 60, 160, 56)
        self.btn_retry = pygame.Rect(SCREEN_W // 2 - 180, 560, 360, 70)
        self.btn_menu = pygame.Rect(SCREEN_W // 2 - 180, 650, 360, 70)

    def reset_game(self):
        items = [TrashItem(n, c, i, e) for i, (n, c, e) in enumerate(TRASH_ITEMS)]
        random.shuffle(items)
        self.items = items
        self.current_idx = 0
        self.score = 0
        self.correct = 0
        self.message = ""
        self.msg_timer = 0
        self.start_item_time = pygame.time.get_ticks()

    def current_item(self):
        if self.current_idx >= len(self.items):
            return None
        return self.items[self.current_idx]

    def next_item(self):
        self.current_idx += 1
        if self.current_idx < len(self.items):
            self.items[self.current_idx].reset_position()
            self.start_item_time = pygame.time.get_ticks()

    def add_message(self, text, ok=True):
        self.message = text
        self.msg_timer = 60
        if ok:
            self.score += 300
            self.correct += 1
        else:
            self.score = max(0, self.score - 1)

    def time_left(self):
        elapsed = (pygame.time.get_ticks() - self.start_item_time) / 1000
        return max(0, TIME_LIMIT - elapsed)

    def draw_hud(self):
        rounded_rect(self.screen, pygame.Rect(40, 20, 360, 60), (255, 255, 255), 20, 200)
        draw_text(self.screen, f"得分：{self.score}", self.font_mid, DARK, (160, 50))
        t_left = self.time_left()
        rounded_rect(self.screen, pygame.Rect(SCREEN_W - 240, 20, 200, 60), (255, 255, 255), 20, 200)
        draw_text(self.screen, f"倒计时：{t_left:.1f}s", self.font_small, DARK, (SCREEN_W - 140, 50))

    def draw_bins(self):
        for b in self.bins:
            rect = b["rect"]
            rounded_rect(self.screen, rect, b["color"], 26, 230)
            pygame.draw.rect(self.screen, WHITE, rect, 3, border_radius=26)
            draw_text(self.screen, b["cat"], self.font_small, WHITE, rect.center)
            draw_star(self.screen, (rect.centerx, rect.top + 20), 10, WHITE)

    def draw_top_panel(self, item):
        panel = pygame.Rect(120, 90, SCREEN_W - 240, 180)
        rounded_rect(self.screen, panel, (255, 255, 255), 28, 220)
        draw_text(self.screen, "请拖拽到正确垃圾桶", self.font_small, MUTED, (SCREEN_W // 2, 120))
        draw_text(self.screen, item.name, self.font_big, DARK, (SCREEN_W // 2, 170))

    def handle_drop(self, item):
        dropped = False
        for b in self.bins:
            if b["rect"].collidepoint(item.pos):
                dropped = True
                if b["cat"] == item.category:
                    self.add_message("分类正确！+2", True)
                else:
                    self.add_message("分错啦！-1", False)
                self.next_item()
                return
        if not dropped:
            item.reset_position()

    def update_game(self, events):
        item = self.current_item()
        if item is None:
            self.state = STATE_RESULT
            return

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                item.start_drag(e.pos)
            if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if item.dragging:
                    item.stop_drag()
                    self.handle_drop(item)
            if e.type == pygame.MOUSEMOTION:
                item.drag(e.pos)

        if self.time_left() <= 0:
            self.add_message("超时啦！-1", False)
            self.next_item()

        if self.msg_timer > 0:
            self.msg_timer -= 1

    def draw_message(self):
        if self.msg_timer > 0:
            color = (100, 200, 120) if "+" in self.message else (255, 120, 120)
            rounded_rect(self.screen, pygame.Rect(SCREEN_W // 2 - 140, 300, 280, 48), color, 20, 200)
            draw_text(self.screen, self.message, self.font_small, WHITE, (SCREEN_W // 2, 324))

    def draw_menu(self, mouse_pos):
        draw_gradient(self.screen, COLOR_BG_TOP, COLOR_BG_BOTTOM)
        draw_text(self.screen, "垃圾分类小能手", self.font_title, (60, 140, 230), (SCREEN_W // 2, 220))
        draw_text(self.screen, "10 秒内把垃圾放进正确的桶！", self.font_mid, DARK, (SCREEN_W // 2, 300))

        draw_item_icon(self.screen, (SCREEN_W // 2 - 140, 380), 34, CAT_RECY, 1, "📦")
        draw_item_icon(self.screen, (SCREEN_W // 2, 380), 34, CAT_KITCHEN, 2, "🍌")
        draw_item_icon(self.screen, (SCREEN_W // 2 + 140, 380), 34, CAT_HAZ, 3, "🔋")

        draw_button(self.screen, self.btn_start, "开始游戏", self.font_mid, (90, 180, 255), self.btn_start.collidepoint(mouse_pos))
        draw_button(self.screen, self.btn_help, "游戏帮助", self.font_mid, (120, 210, 120), self.btn_help.collidepoint(mouse_pos))

    def draw_help(self, mouse_pos):
        draw_gradient(self.screen, COLOR_BG_TOP, COLOR_BG_BOTTOM)
        rounded_rect(self.screen, pygame.Rect(120, 120, SCREEN_W - 240, 600), WHITE, 28, 230)
        draw_text(self.screen, "游戏帮助", self.font_title, (70, 160, 240), (SCREEN_W // 2, 190))
        tips = [
            "1. 按住垃圾图标拖拽到正确垃圾桶",
            "2. 每个垃圾只有 10 秒倒计时",
            "3. 分类正确加分，错误或超时扣分",
            "4. 共 50 个垃圾，全部完成后结算成绩",
        ]
        y = 280
        for t in tips:
            draw_text(self.screen, t, self.font_mid, DARK, (SCREEN_W // 2, y))
            y += 60
        draw_button(self.screen, self.btn_back, "返回", self.font_mid, (90, 180, 255), self.btn_back.collidepoint(mouse_pos))

    def draw_result(self, mouse_pos):
        draw_gradient(self.screen, (240, 245, 255), (255, 250, 240))
        rounded_rect(self.screen, pygame.Rect(200, 160, SCREEN_W - 400, 520), WHITE, 28, 230)
        draw_text(self.screen, "成绩结算", self.font_title, (90, 160, 240), (SCREEN_W // 2, 240))
        acc = int(self.correct / len(TRASH_ITEMS) * 100)
        draw_text(self.screen, f"总得分：{self.score}", self.font_big, DARK, (SCREEN_W // 2, 340))
        draw_text(self.screen, f"正确率：{acc}%", self.font_big, DARK, (SCREEN_W // 2, 400))
        draw_button(self.screen, self.btn_retry, "再来一次", self.font_mid, (120, 210, 120), self.btn_retry.collidepoint(mouse_pos))
        draw_button(self.screen, self.btn_menu, "返回菜单", self.font_mid, (90, 180, 255), self.btn_menu.collidepoint(mouse_pos))

    def run(self):
        while True:
            mouse_pos = pygame.mouse.get_pos()
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAY:
                        self.state = STATE_MENU

            if self.state == STATE_MENU:
                if any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events):
                    if self.btn_start.collidepoint(mouse_pos):
                        self.reset_game()
                        self.state = STATE_PLAY
                    elif self.btn_help.collidepoint(mouse_pos):
                        self.state = STATE_HELP
                self.draw_menu(mouse_pos)

            elif self.state == STATE_HELP:
                if any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events):
                    if self.btn_back.collidepoint(mouse_pos):
                        self.state = STATE_MENU
                self.draw_help(mouse_pos)

            elif self.state == STATE_PLAY:
                draw_gradient(self.screen, COLOR_BG_TOP, COLOR_BG_BOTTOM)
                item = self.current_item()
                if item:
                    self.draw_top_panel(item)
                    item.draw(self.screen)
                self.draw_bins()
                self.draw_hud()
                self.draw_message()
                self.update_game(events)

            elif self.state == STATE_RESULT:
                if any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in events):
                    if self.btn_retry.collidepoint(mouse_pos):
                        self.reset_game()
                        self.state = STATE_PLAY
                    elif self.btn_menu.collidepoint(mouse_pos):
                        self.state = STATE_MENU
                self.draw_result(mouse_pos)

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
