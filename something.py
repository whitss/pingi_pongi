from pygame import *
import random
import time as py_time

# Inicialización de módulos
mixer.init()
font.init()

# Cargar música de fondo (canción proporcionada)
mixer.music.load('videoplayback.mp3')
mixer.music.play(-1)

# Intentar cargar sonido de rebote
try:
    bounce_sound = mixer.Sound('bounce.mp3')
except:
    bounce_sound = None

# Clases requeridas

# Clase principal para sprites
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

# Clase específica para la pelota con rotación visual sin alterar hitbox
class BallSprite(GameSprite):
    def __init__(self, player_image, player_x, player_y, player_speed, wight, height):
        super().__init__(player_image, player_x, player_y, player_speed, wight, height)
        self.angle = 0
        self.base_width = wight
        self.base_height = height

    def reset(self):
        # Rotar visualmente sin alterar el rect (hitbox)
        self.angle = (self.angle + 6) % 360
        rotated_image = transform.rotate(self.original_image, self.angle)
        old_center = self.rect.center
        self.rect = rotated_image.get_rect(center=old_center)
        window.blit(rotated_image, self.rect.topleft)

# Clase Power-Up
class PowerUp(GameSprite):
    def __init__(self, player_image, player_x, player_y, wight, height):
        super().__init__(player_image, player_x, player_y, 0, wight, height)
        self.active = False

# La clase heredera del sprite del jugador (controlada por flechas / W-S)
class Player(GameSprite):
    def __init__(self, player_image, player_x, player_y, player_speed, wight, height):
        super().__init__(player_image, player_x, player_y, player_speed, wight, height)
        self.orig_w = wight
        self.orig_h = height
        self.current_w = wight
        self.current_h = height
        self.max_w = wight * 1.5
        self.max_h = height * 1.5

    def grow(self):
        if self.current_h < self.max_h:
            self.current_w = min(self.max_w, self.current_w + 3)
            self.current_h = min(self.max_h, self.current_h + 8)
            old_center = self.rect.center
            self.original_image = transform.scale(image.load('racket.png'), (int(self.current_w), int(self.current_h)))
            self.rect = self.original_image.get_rect(center=old_center)

    def reset_size(self):
        self.current_w = self.orig_w
        self.current_h = self.orig_h
        old_center = self.rect.center
        self.original_image = transform.scale(image.load('racket.png'), (int(self.current_w), int(self.current_h)))
        self.rect = self.original_image.get_rect(center=old_center)

    def update_r(self):
        keys = key.get_pressed()
        if keys[K_UP] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_DOWN] and self.rect.y < win_height - self.rect.height - 5:
            self.rect.y += self.speed

    def update_l(self):
        keys = key.get_pressed()
        if keys[K_w] and self.rect.y > 5:
            self.rect.y -= self.speed
        if keys[K_s] and self.rect.y < win_height - self.rect.height - 5:
            self.rect.y += self.speed

# Escena del juego:
back = (200, 255, 255)
win_width = 600
win_height = 500
window = display.set_mode((win_width, win_height))
window.fill(back)

# Banderas responsables del estado del juego
game = True
finish = False
paused = False
clock = time.Clock()
FPS = 60

# Creando una pelota y raquetas (raquetas a la mitad de su tamaño original: 25x75)
racket1 = Player('racket.png', 30, 200, 4, 25, 75)
racket2 = Player('racket.png', 520, 200, 4, 25, 75)
ball = BallSprite('tenis_ball.png', 200, 200, 4, 50, 50)
powerup = PowerUp('tenis_ball.png', 280, 220, 30, 30) # Icono de power up temporal

font = font.Font(None, 35)
lose1 = font.render('PLAYER 1 LOSE!', True, (180, 0, 0))
lose2 = font.render('PLAYER 2 LOSE!', True, (180, 0, 0))
pause_text = font.render('JUEGO PAUSADO (Presiona M)', True, (0, 0, 180))
fury_text = font.render('¡MODO FURIA ACTIVADO!', True, (200, 0, 200))

speed_x = 3
speed_y = 3
last_hitter = None # Para saber a qué raqueta aplicar el power-up

# Variables para el control de toques consecutivos
last_player_touch = None
consecutive_hits = 0

# Variables de tiempo para eventos
start_time = py_time.time()
last_powerup_check = start_time
fury_timer = start_time
fury_active = False

while game:
    for e in event.get():
        if e.type == QUIT:
            game = False
        elif e.type == KEYDOWN:
            if e.key == K_m:
                paused = not paused
                if paused:
                    mixer.music.pause()
                else:
                    mixer.music.unpause()

    if paused:
        window.blit(pause_text, (130, 230))
        display.update()
        clock.tick(FPS)
        continue

    current_time = py_time.time()

    # Gestión del Power-Up (1/6 probabilidad cada minuto / 60 segundos)
    if current_time - last_powerup_check >= 60:
        last_powerup_check = current_time
        if random.randint(1, 6) == 1:
            powerup.active = True
            powerup.rect.x = random.randint(200, 400)
            powerup.rect.y = random.randint(100, 400)

    # Gestión del Modo Furia (cada 30s se activa durante 10s -> 1/3 del tiempo)
    if current_time - fury_timer >= 30:
        fury_active = True
        if current_time - fury_timer >= 40: # Dura 10 segundos activo
            fury_timer = current_time
            fury_active = False
            racket1.speed = 4
            racket2.speed = 4
            ball.base_width = 50
            ball.base_height = 50

    if fury_active:
        racket1.reset_size()
        racket2.reset_size()
        ball.speed = 8 # 2x velocidad aproximada
        # Pelota más pequeña en modo furia
        ball.original_image = transform.scale(image.load('tenis_ball.png'), (30, 30))
    else:
        ball.speed = 4
        ball.original_image = transform.scale(image.load('tenis_ball.png'), (ball.base_width, ball.base_height))

    if not finish:
        window.fill(back)
        
        racket1.update_l()
        racket2.update_r()
        
        ball.rect.x += speed_x * (2 if fury_active else 1)
        ball.rect.y += speed_y * (2 if fury_active else 1)

        # Colisiones con raquetas (con validación de dirección para evitar bugs en esquinas)
        if sprite.collide_rect(racket1, ball) and speed_x < 0:
            speed_x *= -1
            racket1.grow()
            last_hitter = racket1
            if bounce_sound: bounce_sound.play()
            
            # Control de toques consecutivos para Jugador 1
            if last_player_touch == racket1:
                consecutive_hits += 1
            else:
                last_player_touch = racket1
                consecutive_hits = 1
            
            if consecutive_hits >= 3:
                ball.rect.x = win_width // 2 - ball.rect.width // 2
                ball.rect.y = win_height // 2 - ball.rect.height // 2
                speed_x = abs(speed_x) # Va hacia el lado contrario (derecha)
                consecutive_hits = 0
                last_player_touch = None
            
        if sprite.collide_rect(racket2, ball) and speed_x > 0:
            speed_x *= -1
            racket2.grow()
            last_hitter = racket2
            if bounce_sound: bounce_sound.play()
            
            # Control de toques consecutivos para Jugador 2
            if last_player_touch == racket2:
                consecutive_hits += 1
            else:
                last_player_touch = racket2
                consecutive_hits = 1
            
            if consecutive_hits >= 3:
                ball.rect.x = win_width // 2 - ball.rect.width // 2
                ball.rect.y = win_height // 2 - ball.rect.height // 2
                speed_x = -abs(speed_x) # Va hacia el lado contrario (izquierda)
                consecutive_hits = 0
                last_player_touch = None

        # Interacción con Power-Up
        if powerup.active and sprite.collide_rect(ball, powerup):
            powerup.active = False
            if last_hitter:
                last_hitter.speed *= 1.35 # Acelera un 1.35 la plataforma

        # Rebote en límites superior e inferior
        if ball.rect.y > win_height - ball.rect.height or ball.rect.y < 0:
            speed_y *= -1
            if bounce_sound: bounce_sound.play()
            # Al rebotar en la pared, se resetea el control de toques consecutivos
            last_player_touch = None
            consecutive_hits = 0

        # Condiciones de derrota
        if ball.rect.x < 0:
            finish = True
            window.blit(lose1, (200, 200))
            game_over = True

        if ball.rect.x > win_width:
            finish = True
            window.blit(lose2, (200, 200))
            game_over = True

        # Dibujar elementos en pantalla
        racket1.reset()
        racket2.reset()
        ball.reset()

        if powerup.active:
            powerup.reset()

        if fury_active:
            window.blit(fury_text, (160, 30))

    display.update()
    clock.tick(FPS)


   display.update()
   clock.tick(FPS)
