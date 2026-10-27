# -*- coding: utf-8 -*-
import pygame
import os
import random
import sys
import math
# ==================================================
# 1. 资源加载与管理 (Asset Manager)
# ==================================================
def get_asset_path(file_name):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", file_name)
def load_img(filename, w=None, h=None):
    try:
        img = pygame.image.load(get_asset_path(filename)).convert_alpha()
        return pygame.transform.scale(img, (w, h)) if w and h else img
    except Exception: return None
def load_img_scale_height(filename, target_h):
    try:
        img = pygame.image.load(get_asset_path(filename)).convert_alpha()
        ow, oh = img.get_size()
        return pygame.transform.scale(img, (int(ow * (target_h / oh)), target_h))
    except Exception: return None
def load_snd(filename):
    try:
        snd = pygame.mixer.Sound(get_asset_path(filename))
        snd.set_volume(1)
        return snd
    except Exception: return None
def get_chinese_font(size=36):
    try: return pygame.font.Font(get_asset_path("NotoSansSC.ttf"), size)
    except Exception:
        try: return pygame.font.SysFont("Microsoft YaHei", size)
        except Exception: return pygame.font.Font(None, size)

# -------------------------- 窗口缩放映射配置 --------------------------
DESIGN_W, DESIGN_H = 1920, 1017
# 映射缓存，仅初始化 / VIDEORESIZE 更新，主循环只读
scale = 1.0
off_x = 0.0
off_y = 0.0
draw_w = DESIGN_W
draw_h = DESIGN_H

def update_mapping(win_w, win_h):
    global scale, off_x, off_y, draw_w, draw_h
    scale = min(win_w / DESIGN_W, win_h / DESIGN_H)
    dst_w = DESIGN_W * scale
    dst_h = DESIGN_H * scale
    off_x = (win_w - dst_w) / 2
    off_y = (win_h - dst_h) / 2
    draw_w, draw_h = int(dst_w), int(dst_h)
# ----------------------------------------------------------------------

# 初始化
pygame.init()
# 真实窗口对象，初始大小，开启RESIZABLE
win = pygame.display.set_mode((1280, 678), pygame.RESIZABLE)
# 虚拟游戏画布，固定原始分辨率，所有游戏逻辑绘制到此
game_surf = pygame.Surface((DESIGN_W, DESIGN_H), pygame.SRCALPHA)
# 原来的screen别名指向虚拟画布，业务代码完全不动
screen = game_surf

pygame.display.set_caption("超级吴国鸡跑酷")
clock = pygame.time.Clock()
# 初始化坐标映射缓存
update_mapping(*win.get_size())

try:
    icon_img = pygame.image.load(get_asset_path("icon32.ico"))
    pygame.display.set_icon(icon_img)
except Exception: pass
font = get_chinese_font(32)
font_big = get_chinese_font(48)
font_small = get_chinese_font(24)
font_reset = get_chinese_font(28)
font_input = get_chinese_font(26)
bg_img = load_img("bg.jpg", DESIGN_W, DESIGN_H)
TARGET_HEIGHT = 425
GROUND_Y = DESIGN_H - TARGET_HEIGHT
# 玩家资源预加载
player_frames_right = [load_img_scale_height(f"run{i}.png", TARGET_HEIGHT) for i in range(3)]
player_frames_right = [f for f in player_frames_right if f]
player_frames_left = [pygame.transform.flip(f, True, False) for f in player_frames_right]
player_masks_right = [pygame.mask.from_surface(f) for f in player_frames_right]
player_masks_left = [pygame.mask.from_surface(f) for f in player_frames_left]
# 红温资源预生成
hurt_frames_right, hurt_masks_right = [], []
hurt_frames_left, hurt_masks_left = [], []
for i, f in enumerate(player_frames_right):
    mask = player_masks_right[i]
    red_overlay = pygame.Surface(f.get_size(), pygame.SRCALPHA)
    red_overlay.fill((255, 0, 0, 90))
    red_img = f.copy()
    red_img.blit(mask.to_surface(surface=red_overlay, setcolor=(255, 0, 0, 90), unsetcolor=(0, 0, 0, 0)), (0, 0))
    hurt_frames_right.append(red_img)
    hurt_masks_right.append(pygame.mask.from_surface(red_img))
    left_img = pygame.transform.flip(red_img, True, False)
    hurt_frames_left.append(left_img)
    hurt_masks_left.append(pygame.mask.from_surface(left_img))
coin_img = load_img("coin.png", 150, 150) or pygame.Surface((150, 150), pygame.SRCALPHA)
if not os.path.exists(get_asset_path("coin.png")): pygame.draw.circle(coin_img, (255, 215, 0), (24, 24), 20)
coin_mask = pygame.mask.from_surface(coin_img)
obs_pool = [img for i in range(22) if (img := load_img_scale_height(f"ob{i}.png", TARGET_HEIGHT))]
hit_sounds = [s for s in [load_snd(f"hit{i}.ogg") for i in range(1, 11)] if s]
death_sounds = [s for s in [load_snd(f"death{i}.ogg") for i in range(1, 6)] if s]
# ==================================================
# 2. 核心渲染引擎 (Render Engine)
# ==================================================
class BlurSurface:
    def __init__(self, width, height, blur_strength=8):
        self.width = width
        self.height = height
        self.small_size = (max(1, width // blur_strength), max(1, height // blur_strength))

    def get_blurred(self, source_surface):
        small = pygame.transform.smoothscale(source_surface, self.small_size)
        return pygame.transform.smoothscale(small, (self.width, self.height))
def draw_ios_glass(surface, rect, blur_surf, is_pressed=False, is_dark=False):
    if rect.width <= 0 or rect.height <= 0: return
    clip_rect = rect.clip(blur_surf.get_rect())
    if clip_rect.width <= 0 or clip_rect.height <= 0: return
    glass_img = blur_surf.subsurface(clip_rect).copy()

    overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    if is_dark:
        overlay.fill((20, 25, 35, 150) if is_pressed else (30, 35, 45, 120))
    else:
        overlay.fill((200, 210, 220, 130) if is_pressed else (255, 255, 255, 110))
    glass_img.blit(overlay, (0, 0))

    surface.blit(glass_img, rect.topleft)
    pygame.draw.rect(surface, (255, 255, 255, 30), rect, 1)
class GlassButton:
    def __init__(self, rect, text, font_size=font, is_dark=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font_size
        self.is_dark = is_dark
        self.pressed = False
        self.font_surf = self.font.render(self.text, True, (255, 255, 255))
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 鼠标坐标已经提前转换为虚拟画布坐标
            if self.rect.collidepoint(event.pos): self.pressed = True
        elif event.type == pygame.FINGERDOWN:
            tx, ty = event.x * DESIGN_W, event.y * DESIGN_H
            if self.rect.collidepoint((tx, ty)): self.pressed = True
        elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
            if self.pressed:
                self.pressed = False
                pos = event.pos if event.type == pygame.MOUSEBUTTONUP else (event.x * DESIGN_W, event.y * DESIGN_H)
                if self.rect.collidepoint(pos): return True
        elif event.type == pygame.MOUSEMOTION and self.pressed:
            if not self.rect.collidepoint(event.pos): self.pressed = False
        return False
    def draw(self, screen, blur_surf):
        draw_ios_glass(screen, self.rect, blur_surf, is_pressed=self.pressed, is_dark=self.is_dark)
        screen.blit(self.font_surf, self.font_surf.get_rect(center=(self.rect.centerx, self.rect.centery + 1)))
class InputBox:
    def __init__(self, x, y, w, h, default_text="", is_int=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = default_text
        self.is_int = is_int
        self.active = False
        self.font_surf = None
        self.last_text = ""

        btn_size = 44
        self.btn_minus = GlassButton((x - btn_size - 10, y, btn_size, h), "-", font_size=font, is_dark=True)
        self.btn_plus = GlassButton((x + w + 10, y, btn_size, h), "+", font_size=font, is_dark=True)
    def handle_event(self, event):
        #如果是整数参数，按 1 步进；如果是小数，按 0.5 步进
        step = 1 if self.is_int else 0.5

        if self.btn_minus.handle_event(event):
            try:
                val = max(-9999.5, float(self.text) - step)
                self.text = str(int(val)) if self.is_int else str(round(val, 2))
                return True
            except ValueError: pass
        if self.btn_plus.handle_event(event):
            try:
                val = min(9999.5, float(self.text) + step)
                self.text = str(int(val)) if self.is_int else str(round(val, 2))
                return True
            except ValueError: pass
        if event.type == pygame.MOUSEBUTTONDOWN: self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.FINGERDOWN:
            tx, ty = event.x * DESIGN_W, event.y * DESIGN_H
            self.active = self.rect.collidepoint((tx, ty))

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.unicode in "0123456789.-": self.text += event.unicode
        return False
    def update(self):
        if self.text != self.last_text:
            self.last_text = self.text
            self.font_surf = font_input.render(self.text, True, (255, 255, 255))
    def draw(self, screen, blur_surf):
        self.btn_minus.draw(screen, blur_surf)
        self.btn_plus.draw(screen, blur_surf)

        if not self.font_surf: return
        draw_ios_glass(screen, self.rect, blur_surf, is_pressed=False, is_dark=True)
        if self.active: pygame.draw.rect(screen, (0, 122, 255), self.rect, 2)
        screen.blit(self.font_surf, (self.rect.x + 15, self.rect.centery - self.font_surf.get_height()//2))
class Slider:
    RANGE_MIN, RANGE_MAX = -9999.5, 9999.5
    def __init__(self, x, y, width, height, init_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_w = 10
        self.knob_h = 26
        self.value = float(init_val)
        self.dragging = False
    def val_to_x(self, val):
        return self.rect.x + ((val - self.RANGE_MIN) / (self.RANGE_MAX - self.RANGE_MIN)) * self.rect.width
    def x_to_val(self, px):
        ratio = max(0.0, min(1.0, (px - self.rect.x) / self.rect.width))
        return self.RANGE_MIN + ratio * (self.RANGE_MAX - self.RANGE_MIN)
    def set_value(self, v):
        self.value = max(self.RANGE_MIN, min(self.RANGE_MAX, float(v)))
    def handle_event(self, event):
        pos = event.pos if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION) else \
              (event.x * DESIGN_W, event.y * DESIGN_H) if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION) else (-1, -1)
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            if self.rect.inflate(20, 20).collidepoint(pos):
                self.dragging = True
                self.value = self.x_to_val(pos[0])
                return True
        elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP): self.dragging = False
        elif self.dragging and pos[0] != -1:
            self.value = self.x_to_val(pos[0])
            return True
        return False
    def draw(self, screen, blur_surf):
        draw_ios_glass(screen, self.rect, blur_surf, is_pressed=False, is_dark=True)
        fill_w = int(self.val_to_x(self.value) - self.rect.x)
        if fill_w > 0:
            pygame.draw.rect(screen, (255, 255, 255, 200), pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height))

        kx = self.val_to_x(self.value)
        knob_rect = pygame.Rect(kx - self.knob_w//2, self.rect.centery - self.knob_h//2, self.knob_w, self.knob_h)
        pygame.draw.rect(screen, (0, 0, 0, 60), knob_rect.move(2, 2))
        pygame.draw.rect(screen, (255, 255, 255), knob_rect)
        pygame.draw.rect(screen, (150, 150, 150), knob_rect, 1)
# ==================================================
# 3. 数据与全局配置 (Configs)
# ==================================================
cfg_run = {"obs_speed": 20, "gravity": 1.8, "jump_power": -40.0, "spawn_interval": 90, "max_hp": 5, "hurt_duration": 15, "player_x": 200, "anim_speed": 8, "obs_scale": 1.0, "bg_scroll_speed_scale": 1.0, "score_rate": 0.5, "jump_damping": 0.0, "jitter": 45}
labels_run = ["游戏速度：", "重力：", "跳跃初速度：", "障碍生成间隔：", "最大HP：", "受伤无敌帧：", "玩家X坐标：", "动画速度：", "障碍缩放：", "背景速度：", "得分倍率：", "跳跃空气阻尼：", "障碍随机偏移："]
cfg_free = {"obs_speed": 20, "gravity": 1.8, "jump_power": -32.0, "spawn_interval": 100, "max_hp": 5, "hurt_duration": 15, "anim_speed": 8, "obs_scale": 1.0, "bg_scroll_speed_scale": 1.0, "score_rate": 0.5, "jump_damping": 30.0, "move_accel": 1.5, "friction": 0.85, "jitter": 30}
labels_free = ["障碍速度：", "重力：", "跳跃初速度：", "障碍生成间隔：", "最大HP：", "受伤无敌帧：", "动画速度：", "障碍缩放：", "背景速度：", "得分倍率：", "跳跃空气阻尼：", "起步加速度：", "水平摩擦力（0急停）：", "障碍随机偏移："]
cfg_mario = {"move_speed": 20, "gravity": 1.8, "jump_power": -34.0, "spawn_interval": 180, "max_hp": 5, "hurt_duration": 45, "anim_speed": 8, "obs_scale": 1.0, "score_rate": 0.5, "jump_damping": 40.0, "move_accel": 2.0, "friction": 0.85, "jitter": 115}
labels_mario = ["移动速度上限：", "重力：", "跳跃初速度：", "障碍生成间隔：", "最大HP：", "受伤无敌帧：", "动画速度：", "障碍缩放：", "得分倍率：", "跳跃空气阻尼：", "起步加速度：", "水平摩擦力（0急停）：", "障碍随机偏移："]
default_cfgs = [cfg_run.copy(), cfg_free.copy(), cfg_mario.copy()]
input_boxes, sliders, box_labels, reset_button_rects, reset_glass_btns = [], [], [], [], []
def build_ui_for_mode(mode):
    global input_boxes, sliders, box_labels, reset_button_rects, reset_glass_btns
    cfg = [cfg_run, cfg_free, cfg_mario][mode]
    box_labels = [labels_run, labels_free, labels_mario][mode]

    input_boxes = []
    sliders = []
    for i, (k, v) in enumerate(cfg.items()):
        # 扩大整数参数判定范围
        is_int = k in ["spawn_interval", "max_hp", "hurt_duration", "jitter", "anim_speed", "player_x"]
        # 输入框宽度设为 280，字体设为 26
        box = InputBox(0, 0, 280, 44, str(v), is_int)
        input_boxes.append(box)
        sliders.append(Slider(0, 0, 450, 22, float(v)))

    reset_button_rects = [None] * len(cfg)
    reset_glass_btns = [GlassButton((0,0,10,10), "重置", font_size=font_reset, is_dark=True) for _ in range(len(cfg))]
# --- 按钮矩阵 ---
start_btn_rect = pygame.Rect(0, 0, 360, 80)
all_reset_btn_rect = pygame.Rect(0, 0, 360, 80)
exit_btn_rect = pygame.Rect(0, 0, 360, 80)
control_btn_rect = pygame.Rect(0, 0, 360, 80)
button_rect = pygame.Rect(DESIGN_W//2 - 130, DESIGN_H//2 + 100, 260, 90)
pause_button_rect = pygame.Rect(DESIGN_W - 160, 20, 140, 60)
mode_btn_rect = pygame.Rect(DESIGN_W - 350, 40, 300, 60)
resume_btn_rect = pygame.Rect(DESIGN_W//2 - 150, DESIGN_H//2 - 120, 300, 80)
pause_control_btn_rect = pygame.Rect(DESIGN_W//2 - 150, DESIGN_H//2 - 20, 300, 80)
pause_quit_btn_rect = pygame.Rect(DESIGN_W//2 - 150, DESIGN_H//2 + 80, 300, 80)
back_btn_rect = pygame.Rect(DESIGN_W//2 - 150, DESIGN_H//2 + 180, 300, 80)
kbd_btn_rect = pygame.Rect(DESIGN_W//2 - 350, DESIGN_H//2 - 50, 300, 100)
tch_btn_rect = pygame.Rect(DESIGN_W//2 + 50, DESIGN_H//2 - 50, 300, 100)
left_btn_rect = pygame.Rect(60, DESIGN_H - 180, 120, 120)
right_btn_rect = pygame.Rect(210, DESIGN_H - 180, 120, 120)
jump_btn_rect = pygame.Rect(DESIGN_W - 200, DESIGN_H - 200, 150, 150)
btn_start = GlassButton(start_btn_rect, "开始游戏", font_size=font_big, is_dark=False)
btn_reset_all = GlassButton(all_reset_btn_rect, "一键全部重置", font_size=font, is_dark=False)
btn_exit = GlassButton(exit_btn_rect, "退出游戏", font_size=font, is_dark=False)
btn_mode = GlassButton(mode_btn_rect, "跑步鸡", font_size=font, is_dark=False)
btn_retry = GlassButton(button_rect, "重试", font_size=font, is_dark=False)
btn_pause = GlassButton(pause_button_rect, "暂停", font_size=font, is_dark=True)
btn_left = GlassButton(left_btn_rect, "◀", font_size=font_big, is_dark=True)
btn_right = GlassButton(right_btn_rect, "▶", font_size=font_big, is_dark=True)
btn_jump = GlassButton(jump_btn_rect, "▲", font_size=font_big, is_dark=True)
btn_control = GlassButton(control_btn_rect, "控制设置", font_size=font, is_dark=False)
btn_resume = GlassButton(resume_btn_rect, "继续游戏", font_size=font, is_dark=True)
btn_pause_control = GlassButton(pause_control_btn_rect, "控制设置", font_size=font, is_dark=True)
btn_quit = GlassButton(pause_quit_btn_rect, "返回主菜单", font_size=font, is_dark=True)
btn_back = GlassButton(back_btn_rect, "返回", font_size=font, is_dark=True)
btn_kbd = GlassButton(kbd_btn_rect, "键盘操控", font_size=font_big, is_dark=False)
btn_tch = GlassButton(tch_btn_rect, "触屏操控", font_size=font_big, is_dark=False)
game_state = {
    "game_mode": 0, "input_mode": 0, # 0 = 键盘, 1 = 触屏
    "score": 0, "hp": 5, "coin_cnt": 0,
    "player_x": 200, "player_y": GROUND_Y, "player_vx": 0, "player_vy": 0,
    "on_ground": True, "facing_right": True, "is_moving": False,
    "anim_timer": 0, "anim_index": 0, "hurt_timer": 0, "player_dead_angle": 0,
    "touch_left": False, "touch_right": False, "jump_held": False,
    "bg_x": 0, "cam_x": 0, "spawn_timer": 0, "obs_list": [], "coin_list": [], "popups": []
}
build_ui_for_mode(0)
blur_engine = BlurSurface(DESIGN_W, DESIGN_H, blur_strength=6.5)
# ==================================================
# 4. 物理与逻辑引擎 (Physics & Logic)
# ==================================================
def apply_gravity_and_floor():
    g = game_state["gravity"]
    if game_state["jump_held"] and game_state["player_vy"] < 0:
        g *= (1 - game_state["jump_damping"] * 0.01)
    game_state["player_vy"] += g
    game_state["player_y"] += game_state["player_vy"]
    if game_state["player_y"] >= GROUND_Y:
        game_state["player_y"] = GROUND_Y
        game_state["player_vy"] = 0
        game_state["on_ground"] = True
    else: game_state["on_ground"] = False
def update_horizontal_movement(accel_key, friction_key, speed_limit):
    if game_state["input_mode"] == 0:
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_a]
        right = keys[pygame.K_d]
    else:
        left = game_state["touch_left"]
        right = game_state["touch_right"]
    accel, friction = game_state[accel_key], game_state[friction_key]

    if left:
        game_state["player_vx"] = max(game_state["player_vx"] - accel, -speed_limit)
        game_state["facing_right"] = False
    elif right:
        game_state["player_vx"] = min(game_state["player_vx"] + accel, speed_limit)
        game_state["facing_right"] = True
    else:
        game_state["player_vx"] *= friction
        if abs(game_state["player_vx"]) < 0.2: game_state["player_vx"] = 0
    return left or right or abs(game_state["player_vx"]) > 0
def spawn_obstacle(is_scrolling=False):
    pick = random.choice(obs_pool)
    ow, oh = int(pick.get_width() * game_state["obs_scale"]), int(pick.get_height() * game_state["obs_scale"])
    scaled_obs = pygame.transform.scale(pick, (ow, oh))

    if is_scrolling:
        last_x = max((o["x"] for o in game_state["obs_list"]), default=game_state["cam_x"] + DESIGN_W)
        spawn_x = max(game_state["cam_x"] + DESIGN_W + 300, last_x) + random.randint(0, 500)
    else:
        spawn_x = DESIGN_W

    game_state["obs_list"].append({"x": spawn_x, "y": DESIGN_H - oh, "w": ow, "h": oh, "img": scaled_obs, "mask": pygame.mask.from_surface(scaled_obs)})
def process_collisions():
    cur_mask = (hurt_masks_right if game_state["facing_right"] else hurt_masks_left)[game_state["anim_index"]] if (game_state["hurt_timer"] > 0 or state == "gameover") else (player_masks_right if game_state["facing_right"] else player_masks_left)[game_state["anim_index"]]
    cam_offset = game_state["cam_x"] if game_state["game_mode"] == 2 else 0
    px, py = game_state["player_x"] - cam_offset, game_state["player_y"]

    for i in range(len(game_state["obs_list"]) - 1, -1, -1):
        obs = game_state["obs_list"][i]
        ox = obs["x"] - cam_offset
        if ox + obs["w"] < 0:
            game_state["obs_list"].pop(i)
            continue
        if cur_mask.overlap(obs["mask"], (int(ox - px), int(obs["y"] - py))):
            game_state["hp"] -= 1
            game_state["hurt_timer"] = int(game_state["hurt_duration"])
            game_state["obs_list"].pop(i)
            if hit_sounds: random.choice(hit_sounds).play()
            if game_state["hp"] <= 0: return False
    return True
def process_coin_collisions():
    cur_mask = (player_masks_right if game_state["facing_right"] else player_masks_left)[game_state["anim_index"]]
    cam_offset = game_state["cam_x"] if game_state["game_mode"] == 2 else 0
    px, py = game_state["player_x"] - cam_offset, game_state["player_y"]
    pw, ph = player_frames_right[0].get_width(), player_frames_right[0].get_height()

    for i in range(len(game_state["coin_list"]) - 1, -1, -1):
        c = game_state["coin_list"][i]
        if c["x"] < game_state["cam_x"] - 100:
            game_state["coin_list"].pop(i)
            continue
        if cur_mask.overlap(coin_mask, (int(c["x"] - cam_offset - px), int(c["y"] - py))):
            game_state["coin_list"].pop(i)
            amount = random.randint(5, 100)
            game_state["score"] += amount
            game_state["coin_cnt"] += 1
            game_state["popups"].append({"x": int(px + pw / 2), "y": int(py), "text": f"+{amount}", "t": 0})
            if hit_sounds: random.choice(hit_sounds).play()
def reset_game():
    def get_val(idx, defv, is_int=False):
        try:
            v_str = input_boxes[idx].text.strip()
            if not v_str or v_str in (".", "-", "-."): return defv
            v = max(-9999.5, min(9999.5, float(v_str)))
            return round(v) if is_int else v
        except Exception: return defv
    cfg = [cfg_run, cfg_free, cfg_mario][game_state["game_mode"]]
    for i, key in enumerate(cfg.keys()):
        is_int = key in ["spawn_interval", "max_hp", "hurt_duration", "jitter", "anim_speed", "player_x"]
        v = get_val(i, cfg[key], is_int)
        game_state[key] = v
        cfg[key] = v

    px = 200 if game_state["game_mode"] == 0 else (400 if game_state["game_mode"] == 1 else 200)
    game_state.update({
        "player_x": px, "player_y": GROUND_Y, "player_vy": 0, "player_vx": 0, "on_ground": True,
        "facing_right": True, "spawn_timer": 0, "bg_x": 0, "cam_x": 0, "anim_timer": 0, "anim_index": 0,
        "score": 0, "hp": game_state["max_hp"], "hurt_timer": 0, "player_dead_angle": 0,
        "touch_left": False, "touch_right": False, "jump_held": False, "is_moving": False, "coin_cnt": 0
    })
    game_state["obs_list"].clear(); game_state["coin_list"].clear(); game_state["popups"].clear()
def draw_player(screen):
    draw_x = game_state["player_x"] - game_state["cam_x"] if game_state["game_mode"] == 2 else game_state["player_x"]
    is_hurt = game_state["hurt_timer"] > 0 or state == "gameover"
    frames = (hurt_frames_right if game_state["facing_right"] else hurt_frames_left) if is_hurt else (player_frames_right if game_state["facing_right"] else player_frames_left)
    draw_img = frames[game_state["anim_index"]].copy()

    if state == "gameover":
        draw_img = pygame.transform.rotate(draw_img, game_state["player_dead_angle"])
        screen.blit(draw_img, draw_img.get_rect(center=(draw_x + draw_img.get_width()//2, game_state["player_y"] + draw_img.get_height()//2)))
    else: screen.blit(draw_img, (draw_x, game_state["player_y"]))
# ==================================================
# 5. 事件路由处理器 (Event Handlers)
# ==================================================
def handle_setup_events(event):
    cfg = [cfg_run, cfg_free, cfg_mario][game_state["game_mode"]]

    for i, box in enumerate(input_boxes):
        if box.handle_event(event):
            try:
                sliders[i].set_value(float(box.text))
                cfg[list(cfg.keys())[i]] = float(box.text)
            except ValueError: pass

    for i, slider in enumerate(sliders):
        if slider.handle_event(event):
            is_int = box.is_int
            input_boxes[i].text = str(round(slider.value)) if is_int else f"{slider.value:.2f}"
            cfg[list(cfg.keys())[i]] = slider.value

    if btn_mode.handle_event(event):
        game_state["game_mode"] = (game_state["game_mode"] + 1) % 3
        build_ui_for_mode(game_state["game_mode"])
        btn_mode.text = ["跑步鸡", "滑步鸡", "吴国鸡"][game_state["game_mode"]]
        btn_mode.font_surf = btn_mode.font.render(btn_mode.text, True, (255, 255, 255))
        return "setup"
    if btn_start.handle_event(event): reset_game(); return "game"
    elif btn_reset_all.handle_event(event):
        default_cfg = default_cfgs[game_state["game_mode"]]
        cfg.clear()
        cfg.update(default_cfg.copy())
        build_ui_for_mode(game_state["game_mode"])

    elif btn_control.handle_event(event):
        global prev_state
        prev_state = "setup"
        return "control_settings"
    elif btn_exit.handle_event(event): pygame.event.post(pygame.event.Event(pygame.QUIT))
    else:
        for idx, btn in enumerate(reset_glass_btns):
            if btn.handle_event(event):
                default_v = default_cfgs[game_state["game_mode"]][list(cfg.keys())[idx]]
                input_boxes[idx].text = str(default_v)
                sliders[idx].set_value(float(default_v))
                cfg[list(cfg.keys())[idx]] = default_v
                break
    return "setup"
def handle_game_events(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "paused"

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if pause_button_rect.collidepoint(event.pos): return "paused"
        if game_state["game_mode"] == 0:
            if game_state["on_ground"]: game_state["player_vy"] = game_state["jump_power"]; game_state["on_ground"] = False
        elif game_state["input_mode"] == 1:
            if left_btn_rect.collidepoint(event.pos): game_state["touch_left"] = True
            elif right_btn_rect.collidepoint(event.pos): game_state["touch_right"] = True
            elif jump_btn_rect.collidepoint(event.pos):
                game_state["jump_held"] = True
                if game_state["on_ground"]: game_state["player_vy"] = game_state["jump_power"]; game_state["on_ground"] = False

    if event.type == pygame.FINGERDOWN:
        pos = (event.x * DESIGN_W, event.y * DESIGN_H)
        if pause_button_rect.collidepoint(pos): return "paused"
        if game_state["game_mode"] == 0:
            if game_state["on_ground"]: game_state["player_vy"] = game_state["jump_power"]; game_state["on_ground"] = False
        elif game_state["input_mode"] == 1:
            if left_btn_rect.collidepoint(pos): game_state["touch_left"] = True
            elif right_btn_rect.collidepoint(pos): game_state["touch_right"] = True
            elif jump_btn_rect.collidepoint(pos):
                game_state["jump_held"] = True
                if game_state["on_ground"]: game_state["player_vy"] = game_state["jump_power"]; game_state["on_ground"] = False
    if event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
        game_state["touch_left"] = False; game_state["touch_right"] = False
        if game_state["game_mode"] != 0:
            game_state["jump_held"] = False
            if game_state["player_vy"] < 0: game_state["player_vy"] *= 0.5
    if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_w):
        if game_state["game_mode"] != 0: game_state["jump_held"] = True
        if game_state["on_ground"]: game_state["player_vy"] = game_state["jump_power"]; game_state["on_ground"] = False
    if event.type == pygame.KEYUP and event.key in (pygame.K_SPACE, pygame.K_w) and game_state["game_mode"] != 0:
        game_state["jump_held"] = False
        if game_state["player_vy"] < 0: game_state["player_vy"] *= 0.5
    return "game"
def handle_paused_events(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "game"
    if btn_resume.handle_event(event): return "game"
    if btn_pause_control.handle_event(event):
        global prev_state
        prev_state = "paused"
        return "control_settings"
    if btn_quit.handle_event(event): return "setup"
    return "paused"
def handle_gameover_events(event):
    if btn_retry.handle_event(event): return "setup"
    return "gameover"
def handle_control_events(event):
    global prev_state
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "paused" if prev_state == "paused" else "setup"
    if btn_back.handle_event(event):
        return "paused" if prev_state == "paused" else "setup"
    if btn_kbd.handle_event(event): game_state["input_mode"] = 0
    if btn_tch.handle_event(event): game_state["input_mode"] = 1
    return "control_settings"
event_handlers = {
    "setup": handle_setup_events,
    "game": handle_game_events,
    "paused": handle_paused_events,
    "gameover": handle_gameover_events,
    "control_settings": handle_control_events
}
# ==================================================
# 6. 主循环 (Main Loop)
# ==================================================
state = "setup"
running = True
prev_state = "setup"
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ---------- 窗口事件处理 ----------
        if event.type == pygame.WINDOWFOCUSLOST:
            # 窗口失焦，切暂停，复用已有暂停界面
            if state == "game":
                state = "paused"

        if event.type == pygame.VIDEORESIZE:
            ww, wh = event.w, event.h
            s = min(ww / DESIGN_W, wh / DESIGN_H)
            fixed_w = int(DESIGN_W * s)
            fixed_h = int(DESIGN_H * s)
            win = pygame.display.set_mode((fixed_w, fixed_h), pygame.RESIZABLE)
            update_mapping(fixed_w, fixed_h)
            # 调整窗口完成，切暂停
            if state == "game":
                state = "paused"

        # 鼠标坐标转换：把窗口屏幕坐标转为虚拟画布坐标，替换event.pos
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            orig_mx, orig_my = event.pos
            virt_mx = (orig_mx - off_x) / scale
            virt_my = (orig_my - off_y) / scale
            event.pos = (virt_mx, virt_my)

        # 分发事件到业务处理器
        new_state = event_handlers[state](event)
        if new_state != state:
            state = new_state

    # 逻辑更新
    if state == "game":
        if game_state["hurt_timer"] > 0: game_state["hurt_timer"] -= 1
        for p_ in game_state["popups"][:]:
            p_["y"] -= 1.5; p_["t"] += 1
            if p_["t"] > 45: game_state["popups"].remove(p_)
        mode = game_state["game_mode"]
        if mode == 0:
            game_state["score"] += game_state["score_rate"]
            game_state["bg_x"] = (game_state["bg_x"] - game_state["obs_speed"] * game_state["bg_scroll_speed_scale"]) % -DESIGN_W
            apply_gravity_and_floor()
            game_state["anim_timer"] += 1
            if game_state["anim_timer"] >= game_state["anim_speed"]: game_state["anim_timer"] = 0; game_state["anim_index"] = (game_state["anim_index"] + 1) % len(player_frames_right)
            game_state["spawn_timer"] += 1
            if game_state["spawn_timer"] >= game_state["spawn_interval"] + random.randint(-int(game_state["jitter"]), int(game_state["jitter"])):
                spawn_obstacle(False); game_state["spawn_timer"] = 0
            for obs in game_state["obs_list"]: obs["x"] -= game_state["obs_speed"]
            if not process_collisions():
                game_state["player_dead_angle"] = 90;
                if death_sounds: random.choice(death_sounds).play()
                state = "gameover"
        elif mode == 1:
            is_moving = update_horizontal_movement("move_accel", "friction", 10.0)
            game_state["player_x"] = max(0, min(DESIGN_W - player_frames_right[0].get_width(), game_state["player_x"] + game_state["player_vx"]))
            apply_gravity_and_floor()
            if is_moving or not game_state["on_ground"]:
                game_state["anim_timer"] += 1
                if game_state["anim_timer"] >= game_state["anim_speed"]: game_state["anim_timer"] = 0; game_state["anim_index"] = (game_state["anim_index"] + 1) % len(player_frames_right)
            else: game_state["anim_timer"], game_state["anim_index"] = 0, 0
            game_state["spawn_timer"] += 1
            if game_state["spawn_timer"] >= game_state["spawn_interval"] + random.randint(-int(game_state["jitter"]), int(game_state["jitter"])):
                spawn_obstacle(False); game_state["spawn_timer"] = 0
            if random.random() < 0.02: game_state["coin_list"].append({"x": DESIGN_W, "y": random.randint(220, GROUND_Y - 90)})
            for obs in game_state["obs_list"]: obs["x"] -= game_state["obs_speed"]
            for c in game_state["coin_list"]: c["x"] -= game_state["obs_speed"]
            game_state["bg_x"] = (game_state["bg_x"] - game_state["obs_speed"] * game_state["bg_scroll_speed_scale"]) % -DESIGN_W
            process_coin_collisions()
            if not process_collisions():
                game_state["player_dead_angle"] = 90
                if death_sounds: random.choice(death_sounds).play()
                state = "gameover"
        elif mode == 2:
            is_moving = update_horizontal_movement("move_accel", "friction", game_state["move_speed"])
            game_state["player_x"] = max(game_state["cam_x"], game_state["player_x"] + game_state["player_vx"])
            apply_gravity_and_floor()
            if is_moving or not game_state["on_ground"]:
                game_state["anim_timer"] += 1
                if game_state["anim_timer"] >= game_state["anim_speed"]: game_state["anim_timer"] = 0; game_state["anim_index"] = (game_state["anim_index"] + 1) % len(player_frames_right)
            else: game_state["anim_timer"], game_state["anim_index"] = 0, 0
            game_state["spawn_timer"] += 1
            if game_state["spawn_timer"] >= game_state["spawn_interval"] + random.randint(-int(game_state["jitter"]), int(game_state["jitter"])):
                spawn_obstacle(True); game_state["spawn_timer"] = 0

            if random.random() < 0.05:
                spawn_coin_x = max(game_state["cam_x"] + DESIGN_W + 200, max((c["x"] for c in game_state["coin_list"]), default=0)) + random.randint(100, 400)
                game_state["coin_list"].append({"x": spawn_coin_x, "y": random.randint(220, GROUND_Y - 90)})

            game_state["cam_x"] = max(game_state["cam_x"], game_state["player_x"] - DESIGN_W // 3)
            game_state["bg_x"] = -(game_state["cam_x"] % DESIGN_W)
            process_coin_collisions()
            if not process_collisions():
                game_state["player_dead_angle"] = 90
                if death_sounds: random.choice(death_sounds).play()
                state = "gameover"
    for box in input_boxes: box.update()

    # ============ 渲染阶段：全部绘制到虚拟画布 game_surf(screen) ============
    screen.fill((0,0,0))
    screen.blit(bg_img, (game_state["bg_x"], 0))
    screen.blit(bg_img, (game_state["bg_x"] + DESIGN_W, 0))
    if state in ("game", "paused", "gameover"):
        cam = int(game_state["cam_x"]) if game_state["game_mode"] == 2 else 0
        for c in game_state["coin_list"]: screen.blit(coin_img, (c["x"] - cam, c["y"]))
        for obs in game_state["obs_list"]: screen.blit(obs["img"], (obs["x"] - cam, obs["y"]))
        draw_player(screen)
        for p_ in game_state["popups"]:
            psurf = font.render(p_["text"], True, (255, 215, 60))
            screen.blit(psurf, (p_["x"] - psurf.get_width() // 2, p_["y"] - 55))
        screen.blit(font.render(f"分数:{int(game_state['score'])}", True, (255,255,255)), (30, 30))
        screen.blit(font.render(f"HP:{game_state['hp']}/{game_state['max_hp']}", True, (255,80,80)), (30, 80))
        if game_state["game_mode"] != 0: screen.blit(font.render(f"金币:{game_state['coin_cnt']}", True, (255, 215, 60)), (30, 130))
    # 渲染 UI
    if state == "setup":
        blur_surf = blur_engine.get_blurred(screen)
        blur_surf.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(blur_surf, (0, 0))

        title = font_big.render("自定义本局参数 (-9999.5 ~ 9999.5)", True, (255, 255, 255))
        screen.blit(title, (DESIGN_W//2 - title.get_width()//2, 30))

        info_lines = ["当前游戏模式影响键位和玩法", "【跑步鸡】空格/触摸跳跃，障碍物向你飞来", "【滑步鸡】A/D，移动键移动，空格/按钮跳跃", "【吴国鸡】A/D，移动键移动，空格/触摸跳跃"]
        for idx, line in enumerate(info_lines):
            txt = font_small.render(line, True, (220, 220, 220))
            screen.blit(txt, (DESIGN_W//2 - txt.get_width()//2, 85 + idx*26))

        total_w = 1250 # 稍微加宽整体容器
        start_x = DESIGN_W//2 - total_w//2

        top_y = 210
        bottom_y = DESIGN_H - 140
        num_params = len(input_boxes)
        line_gap = min(60, (bottom_y - top_y) // num_params)

        col1_x = start_x
        col2_x = col1_x + 450 + 25
        col3_x = col2_x + 260 + 25

        for i, box in enumerate(input_boxes):
            center_y = top_y + i * line_gap + 22

            sliders[i].rect.x = col1_x
            sliders[i].rect.centery = center_y

            label_surf = font.render(box_labels[i], True, (255, 255, 255))
            label_rect = label_surf.get_rect(left=col2_x, centery=center_y)

            box.rect.x = col3_x + 44 + 10
            box.rect.centery = center_y
            box.btn_minus.rect.x, box.btn_minus.rect.y = col3_x, box.rect.y
            box.btn_plus.rect.x, box.btn_plus.rect.y = box.rect.right + 10, box.rect.y

            reset_rect = pygame.Rect(box.btn_plus.rect.right + 20, box.rect.centery - 16, 64, 32)

            sliders[i].draw(screen, blur_surf)
            screen.blit(label_surf, label_rect)
            box.draw(screen, blur_surf)

            if i < len(reset_glass_btns):
                reset_glass_btns[i].rect = reset_rect
                reset_glass_btns[i].draw(screen, blur_surf)
        btn_base_y = bottom_y + 20
        group_left_x = DESIGN_W//2 - (360*4 + 25*3)//2
        btn_start.rect.update(group_left_x, btn_base_y, 360, 80)
        btn_reset_all.rect.update(group_left_x + 360 + 25, btn_base_y, 360, 80)
        btn_control.rect.update(group_left_x + (360+25)*2, btn_base_y, 360, 80)
        btn_exit.rect.update(group_left_x + (360+25)*3, btn_base_y, 360, 80)

        btn_start.draw(screen, blur_surf)
        btn_reset_all.draw(screen, blur_surf)
        btn_control.draw(screen, blur_surf)
        btn_exit.draw(screen, blur_surf)
        btn_mode.draw(screen, blur_surf)
    elif state == "game":
        b_surf = blur_engine.get_blurred(screen)
        btn_pause.draw(screen, b_surf)

        if game_state["game_mode"] != 0 and game_state["input_mode"] == 1:
            btn_left.draw(screen, b_surf)
            btn_right.draw(screen, b_surf)
            btn_jump.draw(screen, b_surf)
    elif state == "paused":
        blur_surf = blur_engine.get_blurred(screen)
        blur_surf.fill((0, 0, 0, 140), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(blur_surf, (0, 0))
        p_text = font_big.render("游戏暂停", True, (255, 255, 255))
        screen.blit(p_text, p_text.get_rect(center=(DESIGN_W//2, DESIGN_H//2 - 200)))

        btn_resume.draw(screen, blur_surf)
        btn_pause_control.draw(screen, blur_surf)
        btn_quit.draw(screen, blur_surf)
    elif state == "gameover":
        blur_surf = blur_engine.get_blurred(screen)
        blur_surf.fill((90, 0, 0, 160), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(blur_surf, (0, 0))
        over_text = font_big.render("你死了", True, (255,255,255))
        screen.blit(over_text, over_text.get_rect(center=(DESIGN_W//2, DESIGN_H//2 - 50)))

        result_text = f"分数:{int(game_state['score'])}" if game_state["game_mode"] == 0 else f"分数:{int(game_state['score'])}  金币:{game_state['coin_cnt']}"
        result_line = font.render(result_text, True, (255, 255, 255))
        screen.blit(result_line, result_line.get_rect(center=(DESIGN_W//2, DESIGN_H//2)))
        btn_retry.draw(screen, blur_surf)
    elif state == "control_settings":
        blur_surf = blur_engine.get_blurred(screen)
        blur_surf.fill((0, 0, 0, 160), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(blur_surf, (0, 0))

        c_text = font_big.render("选择操作模式", True, (255, 255, 255))
        screen.blit(c_text, c_text.get_rect(center=(DESIGN_W//2, DESIGN_H//2 - 200)))

        if game_state["input_mode"] == 0:
            btn_kbd.is_dark = False
            btn_tch.is_dark = True
        else:
            btn_kbd.is_dark = True
            btn_tch.is_dark = False

        btn_kbd.draw(screen, blur_surf)
        btn_tch.draw(screen, blur_surf)
        btn_back.draw(screen, blur_surf)

    # ============ 将虚拟画布缩放绘制到真实窗口win ============
    win.fill((20,20,20))
    scaled_surf = pygame.transform.smoothscale(game_surf, (draw_w, draw_h))
    win.blit(scaled_surf, (off_x, off_y))
    pygame.display.flip()

pygame.quit()
