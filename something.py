from pygame import *
import random
import time as py_time
import math
import json
import os

# Inicialización de módulos
mixer.init()
font.init()

# Cargar música según escena
def play_music(track_name, fallback_track='videoplayback.mp3'):
    try:
        if os.path.exists(f"{track_name}.mp3"):
            mixer.music.load(f"{track_name}.mp3")
        elif os.path.exists(f"{track_name}.wav"):
            mixer.music.load(f"{track_name}.wav")
        elif os.path.exists(fallback_track):
            mixer.music.load(fallback_track)
        else:
            return
        mixer.music.play(-1)
    except:
        pass

# Cargar sonido de rebote
try:
    bounce_sound = mixer.Sound('bounce.mp3')
except:
    bounce_sound = None

# Dimensiones de la ventana
win_width = 600
win_height = 500
window = display.set_mode((win_width, win_height))
display.set_caption("ping pong en esteroides")

# Cargar imágenes de fondo
bg_image = None
if os.path.exists('background.png'):
    try:
        bg_image = transform.scale(image.load('background.png'), (win_width, win_height))
    except:
        bg_image = None

bg2_image = None
if os.path.exists('background2.png'):
    try:
        bg2_image = transform.scale(image.load('background2.png'), (win_width, win_height))
    except:
        bg2_image = None

# Cargar fuentes en color NEGRO (0, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

try:
    font_large = font.Font('VPPixelPro-Outline.otf', 35)
    font_medium = font.Font('VPPixelPro-Outline.otf', 22)
    font_small = font.Font('VPPixelPro-Outline.otf', 16)
except:
    font_large = font.Font(None, 35)
    font_medium = font.Font(None, 22)
    font_small = font.Font(None, 16)

# Persistencia de Datos
DATA_FILE = "game_data.json"
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"p1_power": None, "p2_power": None, "fury_mode": False}

game_data = load_data()
fury_mode_enabled = game_data.get("fury_mode", False)

POWER_LIST = [
    "Ninguno",
    "Magnus Shot",
    "Unpredictable Shot",
    "Aceleracion Explosiva",
    "Shadow Tenis",
    "Big Racket",
    "Watch Dog",
    "Ballstreak",
    "Obliterate Shot"
]

# Clases de Sprites
class GameSprite(sprite.Sprite):
    def __init__(self, player_image, player_x, player_y, player_speed, wight, height):
        super().__init__()
        self.original_image = transform.scale(image.load(player_image), (wight, height))
        self.image = self.original_image.copy()
        self.speed = player_speed
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y

    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))

class BallSprite(GameSprite):
    def __init__(self, player_image, player_x, player_y, player_speed, wight, height):
        super().__init__(player_image, player_x, player_y, player_speed, wight, height)
        self.angle = 0

    def reset(self):
        self.angle = (self.angle + 6) % 360
        rotated_image = transform.rotate(self.original_image, self.angle)
        old_center = self.rect.center
        self.rect = rotated_image.get_rect(center=old_center)
        window.blit(rotated_image, self.rect.topleft)

    def set_size(self, w, h):
        self.original_image = transform.scale(image.load('tenis_ball.png'), (w, h))

class Player(GameSprite):
    def __init__(self, player_image, player_x, player_y, player_speed, wight, height, is_left=True):
        super().__init__(player_image, player_x, player_y, player_speed, wight, height)
        self.base_w = wight
        self.base_h = height
        self.is_left = is_left
        self.power = None
        self.pending_power = False
        self.move_start_time = None  # Para la aceleración pasiva exponencial
        self.big_racket_time = 0
        self.inverted_controls = False
        self.invert_consumed = False
        self.move_dir = 0

    def update_movement(self, up_key, down_key, extra_speed=0, slow_down=False):
        keys = key.get_pressed()
        up = keys[up_key]
        down = keys[down_key]

        if self.inverted_controls and not self.invert_consumed:
            if up or down:
                up, down = down, up
                self.invert_consumed = True
                self.inverted_controls = False

        is_moving = up or down

        curr_speed = self.speed + extra_speed

        # Aceleración Explosiva Pasiva Exponencial
        if self.power == "Aceleracion Explosiva" and is_moving:
            if self.move_start_time is None:
                self.move_start_time = py_time.time()
            
            t = py_time.time() - self.move_start_time
            if t < 0.8:
                exponential_mult = math.exp(2.2 * t)
                curr_speed = self.speed * exponential_mult
            else:
                curr_speed = self.speed * 3.5
        else:
            self.move_start_time = None

        if slow_down:
            curr_speed = 1.0  # Ralentización en modo furia

        self.move_dir = 0
        if up and self.rect.y > 5:
            self.rect.y -= curr_speed
            self.move_dir = -1
        if down and self.rect.y < win_height - self.rect.height - 5:
            self.rect.y += curr_speed
            self.move_dir = 1

    def update_bot(self, ball_rect):
        bot_speed = 12
        if self.rect.centery < ball_rect.centery and self.rect.y < win_height - self.rect.height - 5:
            self.rect.y += bot_speed
        elif self.rect.centery > ball_rect.centery and self.rect.y > 5:
            self.rect.y -= bot_speed

    def set_height(self, h):
        old_center = self.rect.center
        self.image = transform.scale(self.original_image, (self.base_w, h))
        self.rect = self.image.get_rect(center=old_center)

# Instancias principales
racket1 = Player('racket.png', 30, 200, 4, 25, 75, is_left=True)
racket2 = Player('racket.png', 520, 200, 4, 25, 75, is_left=False)
ball = BallSprite('tenis_ball.png', 275, 225, 4, 50, 50)

racket1.power = game_data.get("p1_power")
racket2.power = game_data.get("p2_power")

special_shot = None
shot_owner = None
shot_timer = 0
magnus_dir = 1
total_bounces = 0
shadow_time = 0

def draw_background(use_bg2=False):
    if use_bg2 and bg2_image:
        window.blit(bg2_image, (0, 0))
    elif bg_image:
        window.blit(bg_image, (0, 0))
    else:
        color = (180, 50, 50) if use_bg2 else (200, 255, 255)
        window.fill(color)

def draw_text_center(text, font_obj, color, y):
    rendered = font_obj.render(text, True, color)
    window.blit(rendered, (win_width // 2 - rendered.get_width() // 2, y))

def reset_ball_and_rackets():
    global speed_x, speed_y, special_shot, shot_owner, total_bounces
    ball.rect.x = 275
    ball.rect.y = 225
    racket1.rect.y = 200
    racket2.rect.y = 200
    racket1.pending_power = False
    racket2.pending_power = False
    
    base_spd = 9 if fury_mode_enabled else 3
    speed_x = base_spd if random.choice([True, False]) else -base_spd
    speed_y = random.choice([-base_spd, base_spd])
    
    if fury_mode_enabled:
        ball.set_size(25, 25)
    else:
        ball.set_size(50, 50)
        
    reset_shot_effects()
    total_bounces = 0

def reset_shot_effects():
    global special_shot, shot_owner, speed_x, speed_y
    base_spd = 9 if fury_mode_enabled else 3
    # Resetea la velocidad a la base normal de forma limpia e independiente de la fuerza anterior
    speed_x = base_spd if speed_x > 0 else -base_spd
    speed_y = base_spd if speed_y > 0 else -base_spd
    special_shot = None
    shot_owner = None

speed_x = 3
speed_y = 3

def start_countdown():
    for i in range(3, 0, -1):
        draw_background()
        racket1.reset()
        racket2.reset()
        ball.reset()
        draw_text_center(str(i), font_large, BLACK, win_height // 2 - 20)
        display.update()
        py_time.sleep(1)

def power_shop_menu():
    selected_p1 = POWER_LIST.index(racket1.power) if racket1.power in POWER_LIST else 0
    selected_p2 = POWER_LIST.index(racket2.power) if racket2.power in POWER_LIST else 0

    in_shop = True
    clock = time.Clock()

    while in_shop:
        draw_background()
        draw_text_center("TIENDA DE PODERES", font_large, BLACK, 20)
        
        p1_ctrl = font_small.render("P1: W/S Seleccionar | ESPACIO Confirmar", True, BLACK)
        p2_ctrl = font_small.render("P2: Flechas Seleccionar | ENTER Confirmar", True, BLACK)
        window.blit(p1_ctrl, (10, 60))
        window.blit(p2_ctrl, (310, 60))

        draw_text_center("JUGADOR 1", font_medium, BLACK, 100)
        for i, pow_name in enumerate(POWER_LIST):
            prefix = "> " if i == selected_p1 else "  "
            txt = font_small.render(prefix + pow_name, True, BLACK)
            window.blit(txt, (20, 130 + i * 32))

        draw_text_center("JUGADOR 2", font_medium, BLACK, 100)
        for i, pow_name in enumerate(POWER_LIST):
            prefix = "> " if i == selected_p2 else "  "
            txt = font_small.render(prefix + pow_name, True, BLACK)
            window.blit(txt, (320, 130 + i * 32))

        back_txt = font_small.render("Presiona ESC para volver al menu principal", True, BLACK)
        window.blit(back_txt, (win_width // 2 - back_txt.get_width() // 2, 460))

        display.update()

        for e in event.get():
            if e.type == QUIT:
                save_data({"p1_power": racket1.power, "p2_power": racket2.power, "fury_mode": fury_mode_enabled})
                exit()
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    in_shop = False
                elif e.key == K_w:
                    selected_p1 = (selected_p1 - 1) % len(POWER_LIST)
                elif e.key == K_s:
                    selected_p1 = (selected_p1 + 1) % len(POWER_LIST)
                elif e.key == K_SPACE:
                    racket1.power = POWER_LIST[selected_p1] if POWER_LIST[selected_p1] != "Ninguno" else None
                elif e.key == K_UP:
                    selected_p2 = (selected_p2 - 1) % len(POWER_LIST)
                elif e.key == K_DOWN:
                    selected_p2 = (selected_p2 + 1) % len(POWER_LIST)
                elif e.key == K_RETURN:
                    racket2.power = POWER_LIST[selected_p2] if POWER_LIST[selected_p2] != "Ninguno" else None

        clock.tick(30)

def main_menu():
    global fury_mode_enabled
    play_music('ruins')
    selected_option = 0
    options = ["Jugar", "Tienda de Poderes", "Cerrar Juego"]
    clock = time.Clock()

    while True:
        draw_background()
        draw_text_center("ping pong en esteroides", font_large, BLACK, 80)

        for i, opt in enumerate(options):
            prefix = "-> " if i == selected_option else "   "
            txt = font_medium.render(prefix + opt, True, BLACK)
            window.blit(txt, (win_width // 2 - 100, 220 + i * 50))

        fury_check_txt = f"[ {'X' if fury_mode_enabled else ' '} ] Modo Furia (Tecla F)"
        fury_rendered = font_small.render(fury_check_txt, True, BLACK)
        window.blit(fury_rendered, (win_width - fury_rendered.get_width() - 10, 10))

        display.update()

        for e in event.get():
            if e.type == QUIT:
                save_data({"p1_power": racket1.power, "p2_power": racket2.power, "fury_mode": fury_mode_enabled})
                exit()
            elif e.type == KEYDOWN:
                if e.key == K_f:
                    fury_mode_enabled = not fury_mode_enabled
                elif e.key == K_UP or e.key == K_w:
                    selected_option = (selected_option - 1) % len(options)
                elif e.key == K_DOWN or e.key == K_s:
                    selected_option = (selected_option + 1) % len(options)
                elif e.key == K_RETURN or e.key == K_SPACE:
                    if selected_option == 0:
                        return
                    elif selected_option == 1:
                        power_shop_menu()
                    elif selected_option == 2:
                        save_data({"p1_power": racket1.power, "p2_power": racket2.power, "fury_mode": fury_mode_enabled})
                        exit()

        clock.tick(30)

def prepare_or_activate_power(player, opponent):
    if not player.power:
        return

    pow_name = player.power

    if pow_name in ["Magnus Shot", "Unpredictable Shot", "Obliterate Shot", "Shadow Tenis"]:
        player.pending_power = True
    elif pow_name == "Big Racket":
        player.big_racket_time = py_time.time() + 5.0
        player.set_height(130)
    elif pow_name == "Watch Dog":
        opponent.inverted_controls = True
        opponent.invert_consumed = False

def execute_shot_power(player):
    global special_shot, shot_owner, shot_timer, magnus_dir, speed_x, speed_y
    pow_name = player.power

    if pow_name == "Magnus Shot":
        special_shot = "magnus"
        shot_owner = player
        shot_timer = py_time.time()
        magnus_dir = player.move_dir if player.move_dir != 0 else 1
        speed_x = 12 if player.is_left else -12

    elif pow_name == "Unpredictable Shot":
        special_shot = "unpredictable"
        shot_owner = player
        shot_timer = py_time.time()
        speed_x = 10 if player.is_left else -10

    elif pow_name == "Shadow Tenis":
        special_shot = "shadow"
        shot_owner = player
        shot_timer = py_time.time()

    elif pow_name == "Obliterate Shot":
        special_shot = "obliterate"
        shot_owner = player
        speed_x = 18 if player.is_left else -18
        speed_y = 0

    player.pending_power = False

# Bucle Global
while True:
    # Ejecutar Menú de Inicio
    main_menu()

    # Selección de música para el juego
    if fury_mode_enabled:
        play_music('rude buster')
    else:
        play_music('song')

    reset_ball_and_rackets()
    start_countdown()

    # Variables para alternar el fondo en modo furia
    map_change_timer = py_time.time()
    fury_bg_state = False

    slow_j1_timer = py_time.time()
    j1_is_slowed = False

    game = True
    finish = False
    paused = False
    return_to_main_menu = False
    clock = time.Clock()
    FPS = 60

    lose1 = font_large.render('PLAYER 1 LOSE!', True, BLACK)
    lose2 = font_large.render('PLAYER 2 LOSE!', True, BLACK)

    while game:
        for e in event.get():
            if e.type == QUIT:
                save_data({"p1_power": racket1.power, "p2_power": racket2.power, "fury_mode": fury_mode_enabled})
                exit()
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    return_to_main_menu = True
                    game = False
                elif e.key == K_m:
                    paused = not paused
                    if paused:
                        mixer.music.pause()
                    else:
                        mixer.music.unpause()
                elif e.key == K_r:
                    finish = False
                    paused = False
                    mixer.music.unpause()
                    reset_ball_and_rackets()
                    start_countdown()
                elif e.key == K_SPACE and not finish and not paused:
                    prepare_or_activate_power(racket1, racket2)
                elif e.key == K_RSHIFT and not finish and not paused and not fury_mode_enabled:
                    prepare_or_activate_power(racket2, racket1)

        if return_to_main_menu:
            break

        if paused:
            window.fill(BLACK)
            draw_text_center('JUEGO PAUSADO', font_large, WHITE, 180)
            draw_text_center('Presiona M para reanudar o R para reiniciar', font_small, WHITE, 240)
            draw_text_center('Presiona ESC para volver al Menu Principal', font_small, WHITE, 280)
            display.update()
            clock.tick(FPS)
            continue

        if not finish:
            if fury_mode_enabled:
                if py_time.time() - map_change_timer >= 0.5:
                    map_change_timer = py_time.time()
                    fury_bg_state = not fury_bg_state

                draw_background(use_bg2=fury_bg_state)

                if not j1_is_slowed and py_time.time() - slow_j1_timer >= 3.0:
                    j1_is_slowed = True
                    slow_j1_timer = py_time.time()
                elif j1_is_slowed and py_time.time() - slow_j1_timer >= 1.0:
                    j1_is_slowed = False
                    slow_j1_timer = py_time.time()

                if speed_x < 0 and random.randint(1, 20) == 1:
                    speed_y = random.choice([-10, -5, 5, 10])

                racket2.update_bot(ball.rect)
            else:
                draw_background()
                racket2.update_movement(K_UP, K_DOWN)

            extra_sp1 = total_bounces * 0.3 if racket1.power == "Ballstreak" else 0
            extra_sp2 = total_bounces * 0.3 if racket2.power == "Ballstreak" else 0

            if racket1.big_racket_time > 0 and py_time.time() > racket1.big_racket_time:
                racket1.set_height(75)
                racket1.big_racket_time = 0
            if racket2.big_racket_time > 0 and py_time.time() > racket2.big_racket_time:
                racket2.set_height(75)
                racket2.big_racket_time = 0

            racket1.update_movement(K_w, K_s, extra_sp1, slow_down=j1_is_slowed)

            shot_mult = 1.0
            if special_shot is None:
                if speed_x > 0 and racket1.power == "Ballstreak":
                    shot_mult += total_bounces * 0.08
                elif speed_x < 0 and racket2.power == "Ballstreak":
                    shot_mult += total_bounces * 0.08

            if special_shot == "magnus":
                elapsed = py_time.time() - shot_timer
                speed_y = math.sin(elapsed * 5) * 8 * magnus_dir
            elif special_shot == "unpredictable":
                speed_y = random.choice([-7, -4, 0, 4, 7])
            elif special_shot == "shadow":
                shadow_time += 1
                if shadow_time % 15 == 0:
                    ball.rect.y += random.choice([-30, 30])

            ball.rect.x += int(speed_x * shot_mult)
            ball.rect.y += int(speed_y * shot_mult)

            # Colisiones con la raqueta del Jugador 1
            if sprite.collide_rect(racket1, ball) and speed_x < 0:
                speed_x *= -1
                total_bounces += 1
                if bounce_sound: bounce_sound.play()
                
                # Resetea la velocidad previa si no activa un nuevo tiro
                reset_shot_effects()

                if racket1.pending_power:
                    execute_shot_power(racket1)

            # Colisiones con la raqueta del Jugador 2
            if sprite.collide_rect(racket2, ball) and speed_x > 0:
                speed_x *= -1
                total_bounces += 1
                if bounce_sound: bounce_sound.play()
                
                # Resetea la velocidad previa si no activa un nuevo tiro
                reset_shot_effects()

                if racket2.pending_power:
                    execute_shot_power(racket2)

            # Rebotes Superior e Inferior
            if ball.rect.y > win_height - ball.rect.height or ball.rect.y < 0:
                speed_y *= -1
                if bounce_sound: bounce_sound.play()
                reset_shot_effects()

            if ball.rect.x < 0:
                finish = True
                window.blit(lose1, (200, 200))

            if ball.rect.x > win_width:
                finish = True
                window.blit(lose2, (200, 200))

            racket1.reset()
            racket2.reset()
            ball.reset()

            p1_status = "READY!" if racket1.pending_power else (racket1.power or 'Ninguno')
            p2_status = "READY!" if racket2.pending_power else (racket2.power or 'Ninguno')
            p1_pow_txt = font_small.render(f"P1 Poder: {p1_status}", True, BLACK)
            p2_pow_txt = font_small.render(f"P2 Poder: {p2_status}", True, BLACK)
            window.blit(p1_pow_txt, (10, 10))
            window.blit(p2_pow_txt, (400, 10))

        else:
            keys = key.get_pressed()
            if keys[K_RETURN] or keys[K_SPACE]:
                finish = False
                reset_ball_and_rackets()
                start_countdown()

        display.update()
        clock.tick(FPS)

    save_data({"p1_power": racket1.power, "p2_power": racket2.power, "fury_mode": fury_mode_enabled})