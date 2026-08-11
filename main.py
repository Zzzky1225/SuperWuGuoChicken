# -*- coding: utf-8 -*-
import pygame
import os
import random
import sys

def get_asset_path(file_name):
    if hasattr(sys, "getandroidapilevel"):
        base_dir = sys.path[0]
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, "assets", file_name)

pygame.init()
if hasattr(sys, "getandroidapilevel"):
    import android
    W, H = android.get_window_size()
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
else:
    W, H = 1920, 1080
    screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("超级吴国鸡跑酷")
clock = pygame.time.Clock()


def load_img_scale_height(filename, target_h):
    full_path = get_asset_path(filename)
    try:
        img = pygame.image.load(full_path).convert_alpha()
        ow, oh = img.get_size()
        scale = target_h / oh
        new_w = int(ow * scale)
        new_h = int(oh * scale)
        return pygame.transform.scale(img, (new_w, new_h))
    except Exception:
        return None

def load_img(filename, w=None, h=None):
    full_path = get_asset_path(filename)
    try:
        img = pygame.image.load(full_path).convert_alpha()
        if w and h:
            img = pygame.transform.scale(img, (w, h))
        return img
    except Exception:
        return None

def load_snd(filename):
    full_path = get_asset_path(filename)
    try:
        snd = pygame.mixer.Sound(full_path)
        snd.set_volume(1)
        return snd
    except Exception:
        return None

def get_chinese_font(size=36):
    try:
        return pygame.font.Font(get_asset_path("NotoSansSC.ttf"), size)
    except Exception:
        try:
            return pygame.font.SysFont("Microsoft YaHei", size)
        except Exception:
            return pygame.font.Font(None, size)

font = get_chinese_font(32)
font_big = get_chinese_font(48)
font_small = get_chinese_font(24)
font_reset = get_chinese_font(28)
bg_img = load_img("bg.jpg", W, H)
TARGET_HEIGHT = 425
player_frames = [
    load_img_scale_height("run0.png", TARGET_HEIGHT),
    load_img_scale_height("run1.png", TARGET_HEIGHT),
    load_img_scale_height("run2.png", TARGET_HEIGHT),
]
obs_pool = []
for i in range(22):
    img = load_img_scale_height(f"ob{i}.png", TARGET_HEIGHT)
    if img:
        obs_pool.append(img)
hit_sounds = [load_snd(f"hit{i}.wav") for i in range(1, 11)]
death_sounds = [load_snd(f"death{i}.wav") for i in range(1, 6)]
class InputBox:
    def __init__(self, x, y, w, h, default_text=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = default_text
        self.active = False
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.FINGERDOWN:
            tx = event.x * W
            ty = event.y * H
            self.active = self.rect.collidepoint((tx, ty))
        if event.type == pygame.FINGERUP:
            self.active = False
        if event.type == pygame.MOUSEBUTTONUP:
            pass
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                c = event.unicode
                if c in "0123456789.-":
                    self.text += c
    def draw(self, screen):
        color = (220, 60, 60) if self.active else (80, 80, 80)
        pygame.draw.rect(screen, color, self.rect, 3)
        t_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(t_surf, (self.rect.x + 8, self.rect.y + 4))
class Slider:
    RANGE_MIN = -9999
    RANGE_MAX = 9999
    def __init__(self, x, y, width, height, init_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob_w = 16
        self.value = float(init_val)
        self.dragging = False
    def val_to_x(self, val):
        ratio = (val - self.RANGE_MIN) / (self.RANGE_MAX - self.RANGE_MIN)
        return self.rect.x + ratio * self.rect.width
    def x_to_val(self, px):
        ratio = max(0.0, min(1.0, (px - self.rect.x) / self.rect.width))
        v = self.RANGE_MIN + ratio * (self.RANGE_MAX - self.RANGE_MIN)
        return v
    def set_value(self, v):
        self.value = max(self.RANGE_MIN, min(self.RANGE_MAX, float(v)))
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.value = self.x_to_val(event.pos[0])
                return True
        if event.type == pygame.FINGERDOWN:
            tx = event.x * W
            ty = event.y * H
            if self.rect.collidepoint((tx, ty)):
                self.dragging = True
                self.value = self.x_to_val(tx)
                return True
        if event.type == pygame.MOUSEBUTTONUP or event.type == pygame.FINGERUP:
            self.dragging = False
        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.value = self.x_to_val(event.pos[0])
            return True
        if event.type == pygame.FINGERMOTION and self.dragging:
            tx = event.x * W
            self.value = self.x_to_val(tx)
            return True
        return False
    def draw(self, screen):
        pygame.draw.rect(screen,(60,60,60),self.rect)
        pygame.draw.rect(screen,(200,200,200),self.rect,2)
        knob_x = self.val_to_x(self.value)
        knob_rect = pygame.Rect(knob_x - self.knob_w//2, self.rect.y-4, self.knob_w, self.rect.height+8)
        pygame.draw.rect(screen,(220,80,40),knob_rect)
        pygame.draw.rect(screen,(255,255,255),knob_rect,2)
GROUND_Y = H - TARGET_HEIGHT
player_x = 200
obs_list = []
spawn_timer = 2
bg_x = 0
anim_timer = 0
anim_index = 0
score = 0
MAX_HP = 20
hp = MAX_HP
hurt_timer = 0
HURT_DURATION = 15
player_dead_angle = 0
state = "setup"
default_cfg = {
    "obs_speed":20,
    "gravity":1.8,
    "jump_power":-40,
    "spawn_interval":90,
    "max_hp":5,
    "hurt_duration":15,
    "player_x":200,
    "anim_speed":8,
    "obs_scale":1.0,
    "bg_scroll_speed_scale":1.0,
    "score_rate":1.0,
    "jump_damping":0.0
}
default_values = [
    "20",
    "1.8",
    "-40",
    "90",
    "5",
    "15",
    "200",
    "8",
    "1.0",
    "1.0",
    "1.0",
    "0.0"
]
input_boxes = [
    InputBox(0,0,260,50,str(default_cfg["obs_speed"])),
    InputBox(0,0,260,50,str(default_cfg["gravity"])),
    InputBox(0,0,260,50,str(default_cfg["jump_power"])),
    InputBox(0,0,260,50,str(default_cfg["spawn_interval"])),
    InputBox(0,0,260,50,str(default_cfg["max_hp"])),
    InputBox(0,0,260,50,str(default_cfg["hurt_duration"])),
    InputBox(0,0,260,50,str(default_cfg["player_x"])),
    InputBox(0,0,260,50,str(default_cfg["anim_speed"])),
    InputBox(0,0,260,50,str(default_cfg["obs_scale"])),
    InputBox(0,0,260,50,str(default_cfg["bg_scroll_speed_scale"])),
    InputBox(0,0,260,50,str(default_cfg["score_rate"])),
    InputBox(0,0,260,50,str(default_cfg["jump_damping"])),
]
box_labels = [
    "游戏速度：",
    "重力：",
    "跳跃初速度（向上跳为负数）：",
    "障碍生成间隔（按帧算 30就是0.5秒）：",
    "最大HP（低于1都是碰一下就死）：",
    "受伤无敌帧数：",
    "玩家X坐标（吴国鸡在画面中的位置）：",
    "动画速度（越小越快）：",
    "障碍物缩放（太大和负数会卡死）：",
    "背景滚动速度（调不好会很奇怪）：",
    "得分增长倍率：",
    "跳跃空气阻尼："
]
sliders = []
for s_text in default_values:
    sliders.append(Slider(0,0,420,22,float(s_text)))
start_btn_rect = pygame.Rect(0,0, 360, 80)
all_reset_btn_rect = pygame.Rect(0,0, 360, 80)
exit_btn_rect = pygame.Rect(0,0, 360, 80)
btn_w, btn_h = 260,90
btn_x = W//2 - btn_w//2
btn_y = H//2+100
button_rect = pygame.Rect(btn_x,btn_y,btn_w,btn_h)
panic_btn_w, panic_btn_h = 140,60
panic_btn_x = W - panic_btn_w - 20
panic_btn_y = 20
panic_button_rect = pygame.Rect(panic_btn_x,panic_btn_y,panic_btn_w,panic_btn_h)
reset_button_rects = [None]*12
mask_surface = pygame.Surface((W,H), pygame.SRCALPHA)
def reset_game():
    global player_y,player_vy,on_ground,obs_speed,gravity,jump_power,spawn_interval
    global spawn_timer,obs_list,bg_x,anim_timer,anim_index,score,hp,hurt_timer,player_dead_angle
    global MAX_HP,HURT_DURATION,player_x,anim_speed,obs_scale,bg_scroll_speed_scale,score_rate,jump_damping
    def get_val(idx,defv):
        try:
            v = float(input_boxes[idx].text.strip())
            v = max(-9999,min(9999,v))
            return v
        except Exception:
            return defv
    obs_speed = get_val(0,default_cfg["obs_speed"])
    gravity = get_val(1,default_cfg["gravity"])
    jump_power = get_val(2,default_cfg["jump_power"])
    spawn_interval = int(get_val(3,default_cfg["spawn_interval"]))
    MAX_HP = int(get_val(4,default_cfg["max_hp"]))
    HURT_DURATION = int(get_val(5,default_cfg["hurt_duration"]))
    player_x = get_val(6,default_cfg["player_x"])
    anim_speed = get_val(7,default_cfg["anim_speed"])
    obs_scale = get_val(8,default_cfg["obs_scale"])
    bg_scroll_speed_scale = get_val(9,default_cfg["bg_scroll_speed_scale"])
    score_rate = get_val(10,default_cfg["score_rate"])
    jump_damping = get_val(11,default_cfg["jump_damping"])
    input_boxes[0].text = str(obs_speed)
    input_boxes[1].text = str(gravity)
    input_boxes[2].text = str(jump_power)
    input_boxes[3].text = str(spawn_interval)
    input_boxes[4].text = str(MAX_HP)
    input_boxes[5].text = str(HURT_DURATION)
    input_boxes[6].text = str(player_x)
    input_boxes[7].text = str(anim_speed)
    input_boxes[8].text = str(obs_scale)
    input_boxes[9].text = str(bg_scroll_speed_scale)
    input_boxes[10].text = str(score_rate)
    input_boxes[11].text = str(jump_damping)
    for i in range(len(input_boxes)):
        try:
            sliders[i].set_value(float(input_boxes[i].text))
        except:
            pass
    player_y = GROUND_Y
    player_vy = 0
    on_ground = True
    obs_list.clear()
    spawn_timer = 0
    bg_x = 0
    anim_timer = 0
    anim_index = 0
    score = 0
    hp = MAX_HP
    hurt_timer = 0
    player_dead_angle = 0
running = True
while running:
    dt = clock.tick(60)/1000.0
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
            if state == "game" and panic_button_rect.collidepoint(event.pos):
                state = "setup"
            if state == "setup":
                for idx,r_rect in enumerate(reset_button_rects):
                    if r_rect is not None and r_rect.collidepoint(event.pos):
                        input_boxes[idx].text = default_values[idx]
                        sliders[idx].set_value(float(default_values[idx]))
                if all_reset_btn_rect.collidepoint(event.pos):
                    for i in range(len(input_boxes)):
                        input_boxes[i].text = default_values[i]
                        sliders[i].set_value(float(default_values[i]))
                if exit_btn_rect.collidepoint(event.pos):
                    running = False
        if event.type == pygame.FINGERDOWN:
            tx = event.x*W
            ty = event.y*H
            if state == "game" and panic_button_rect.collidepoint((tx,ty)):
                state = "setup"
        if state == "setup":
            for idx,slider in enumerate(sliders):
                if slider.handle_event(event):
                    input_boxes[idx].text = f"{slider.value:.2f}"
            for box in input_boxes:
                box.handle_event(event)
            if event.type == pygame.FINGERUP:
                for box in input_boxes:
                    box.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
                if start_btn_rect.collidepoint(mouse_pos):
                    reset_game()
                    state = "game"
            if event.type == pygame.FINGERDOWN:
                tx = event.x*W
                ty = event.y*H
                if start_btn_rect.collidepoint((tx,ty)):
                    reset_game()
                    state = "game"
        elif state == "game":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and on_ground:
                    player_vy = jump_power
                    on_ground = False
            if event.type == pygame.FINGERDOWN:
                tx = event.x*W
                ty = event.y*H
                if on_ground:
                    player_vy = jump_power
                    on_ground = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
                if on_ground:
                    player_vy = jump_power
                    on_ground = False
        elif state == "gameover":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button ==1:
                if button_rect.collidepoint(mouse_pos):
                    state = "setup"
            if event.type == pygame.FINGERDOWN:
                tx = event.x*W
                ty = event.y*H
                if button_rect.collidepoint((tx,ty)):
                    state = "setup"
    if state == "game":
        score += score_rate
        bg_x -= obs_speed * bg_scroll_speed_scale
        if bg_x <= -W:
            bg_x = 0
        if hurt_timer>0:
            hurt_timer -= 1
        anim_timer +=1
        if anim_timer >= anim_speed:
            anim_timer =0
            anim_index = (anim_index+1)%len(player_frames)
        if not on_ground:
            player_vy *= (1 - jump_damping*0.01)
        player_vy += gravity
        player_y += player_vy
        if player_y >= GROUND_Y:
            player_y = GROUND_Y
            player_vy = 0
            on_ground = True
        spawn_timer +=1
        if spawn_timer >= spawn_interval and len(obs_pool)>0:
            pick_img = random.choice(obs_pool)
            ow0,oh0 = pick_img.get_size()
            ow = int(ow0*obs_scale)
            oh = int(oh0*obs_scale)
            scaled_obs = pygame.transform.scale(pick_img,(ow,oh))
            obs_list.append({"x":W,"y":H-oh,"w":ow,"h":oh,"img":scaled_obs,"mask":pygame.mask.from_surface(scaled_obs)})
            spawn_timer =0
        for obs in obs_list[:]:
            obs["x"] -= obs_speed
            if obs["x"]+obs["w"] <0:
                obs_list.remove(obs)
        cur_frame = player_frames[anim_index]
        player_mask = pygame.mask.from_surface(cur_frame)
        for obs in obs_list[:]:
            offset = (obs["x"]-player_x, obs["y"]-player_y)
            if player_mask.overlap(obs["mask"],offset):
                hp -=1
                hurt_timer = HURT_DURATION
                obs_list.remove(obs)
                s = random.choice(hit_sounds)
                if s: s.play()
                if hp <=0:
                    state = "gameover"
                    player_dead_angle =90
                    s_death = random.choice(death_sounds)
                    if s_death: s_death.play()
                break
    if bg_img:
        screen.blit(bg_img,(bg_x,0))
        screen.blit(bg_img,(bg_x+W,0))
    else:
        screen.fill((30,80,150))
    if state == "setup":
        mask_surface.fill((0,0,0,140))
        screen.blit(mask_surface,(0,0))
    elif state == "gameover":
        mask_surface.fill((90,0,0,110))
        screen.blit(mask_surface,(0,0))
    if state == "setup":
        title = font_big.render("自定义本局参数 (-9999 ~ 9999)",True,(255,255,255))
        screen.blit(title,(W//2-title.get_width()//2, 50))
        info_lines = [
            "触摸屏幕进行跳跃 出现问题直接返回设置 把搞错的参数重置就好了",
            "人物为什么不像吴国鸡？ 我不知道 瞎几把整的",
            "为什么滑块这么长？ 为了精细调整 手机端的文本框好像不好使"
        ]
        info_start_y = 115
        for idx,line in enumerate(info_lines):
            txt = font_small.render(line,True,(220,220,220))
            screen.blit(txt,(W//2 - txt.get_width()//2, info_start_y + idx*26))
        container_total_w = 1820
        container_left = W//2 - container_total_w//2
        slider_w = 900
        label_gap_after_slider = 16
        inputbox_gap_after_label = 30
        reset_btn_gap_after_input = 14
        input_box_w = 260
        reset_btn_w = 64
        reset_btn_h = 32
        base_y = 210
        line_gap = 56
        for i,box in enumerate(input_boxes):
            y_pos = base_y + i * line_gap
            s_x = container_left
            s_y = y_pos + 14
            sliders[i].rect.x = s_x
            sliders[i].rect.y = s_y
            sliders[i].rect.width = slider_w
            label_left = s_x + slider_w + label_gap_after_slider
            label_surf = font.render(box_labels[i],True,(255,255,255))
            label_rect = label_surf.get_rect(left = label_left, centery = y_pos + 22)
            box.rect.x = label_rect.right + inputbox_gap_after_label
            box.rect.y = y_pos
            reset_rect = pygame.Rect(
                box.rect.right + reset_btn_gap_after_input,
                box.rect.centery - reset_btn_h //2,
                reset_btn_w,
                reset_btn_h
            )
            reset_button_rects[i] = reset_rect
            sliders[i].draw(screen)
            screen.blit(label_surf, label_rect)
            box.draw(screen)
            pygame.draw.rect(screen, (60, 80, 160), reset_rect)
            pygame.draw.rect(screen, (255, 255, 255), reset_rect, 2)
            rt = font_reset.render("重置", True, (255, 255, 255))
            rt_rect = rt.get_rect(center=reset_rect.center)
            screen.blit(rt, rt_rect)
        btn_base_y = base_y + len(input_boxes)*line_gap + 30
        gap_between = 25
        btn_w = 360
        btn_h = 80
        total_width = btn_w*3 + gap_between*2
        group_left_x = W//2 - (total_width // 2)
        start_btn_rect.x = group_left_x
        start_btn_rect.y = btn_base_y
        start_btn_rect.w = btn_w
        start_btn_rect.h = btn_h
        all_reset_btn_rect.x = group_left_x + btn_w + gap_between
        all_reset_btn_rect.y = btn_base_y
        all_reset_btn_rect.w = btn_w
        all_reset_btn_rect.h = btn_h
        exit_btn_rect.x = group_left_x + (btn_w+gap_between)*2
        exit_btn_rect.y = btn_base_y
        exit_btn_rect.w = btn_w
        exit_btn_rect.h = btn_h
        pygame.draw.rect(screen,(40,120,220),start_btn_rect)
        pygame.draw.rect(screen,(255,255,255),start_btn_rect,4)
        btn_text = font_big.render("开始游戏",True,(255,255,255))
        btn_text_rect = btn_text.get_rect(center = start_btn_rect.center)
        screen.blit(btn_text, btn_text_rect)
        pygame.draw.rect(screen,(180,70,40),all_reset_btn_rect)
        pygame.draw.rect(screen,(255,255,255),all_reset_btn_rect,4)
        all_reset_text = font.render("一键全部重置",True,(255,255,255))
        all_reset_text_rect = all_reset_text.get_rect(center = all_reset_btn_rect.center)
        screen.blit(all_reset_text, all_reset_text_rect)
        pygame.draw.rect(screen,(80,30,30),exit_btn_rect)
        pygame.draw.rect(screen,(255,255,255),exit_btn_rect,4)
        exit_text = font.render("退出游戏",True,(255,255,255))
        exit_text_rect = exit_text.get_rect(center = exit_btn_rect.center)
        screen.blit(exit_text, exit_text_rect)
    elif state in ("game","gameover"):
        if state == "game":
            pygame.draw.rect(screen,(180,20,20),panic_button_rect)
            pygame.draw.rect(screen,(255,255,255),panic_button_rect,3)
            back_text = font.render("返回设置",True,(255,255,255))
            screen.blit(back_text, back_text.get_rect(center = panic_button_rect.center))
        current_frame = player_frames[anim_index]
        draw_img = current_frame.copy()
        if hurt_timer>0:
            mask = pygame.mask.from_surface(draw_img)
            red_overlay = pygame.Surface(draw_img.get_size(),pygame.SRCALPHA)
            red_overlay.fill((255,0,0,90))
            red_overlay = mask.to_surface(surface=red_overlay,setcolor=(255,0,0,90),unsetcolor=(0,0,0,0))
            draw_img.blit(red_overlay,(0,0))
        if state == "gameover":
            draw_img = pygame.transform.rotate(draw_img,player_dead_angle)
        rect = draw_img.get_rect()
        rect.topleft = (player_x,player_y)
        screen.blit(draw_img,rect)
        for obs in obs_list:
            screen.blit(obs["img"],(obs["x"],obs["y"]))
        score_text = font.render(f"分数:{int(score)}",True,(255,255,255))
        screen.blit(score_text,(30,30))
        hp_text = font.render(f"HP:{hp}/{MAX_HP}",True,(255,80,80))
        screen.blit(hp_text,(30,80))
        if state == "gameover":
            over_text = font_big.render("你死了",True,(255,255,255))
            screen.blit(over_text,over_text.get_rect(center=(W//2,H//2)))
            if button_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen,(100,160,255),button_rect)
            else:
                pygame.draw.rect(screen,(40,90,180),button_rect)
            pygame.draw.rect(screen,(255,255,255),button_rect,4)
            btn_text = font.render("重试",True,(255,255,255))
            screen.blit(btn_text,btn_text.get_rect(center=button_rect.center))
    pygame.display.flip()
pygame.quit()
