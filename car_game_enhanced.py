"""
Hand Gesture Car Racing Game — Enhanced Edition
================================================
ENHANCEMENTS:
  Graphics  : Scrolling road, dashed lane marks, speed-lines, particle FX,
              detailed enemy cars, grass shoulders, animated HUD, lives icons
  Performance: Camera processed every 2nd frame, static BG pre-rendered,
               font/surface caching, capped entity count
  Bug Fixes : Rect-based collision (was lane-center distance ≤10 px — too narrow),
              game-over restart cooldown (was instant), spawn_interval reset on
              restart, enemy speed properly reset, camera cleanup on exit
"""

import cv2
import mediapipe as mp
import pygame
import numpy as np
import random
import sys
import math

# ── MediaPipe ──────────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)
mp_draw = mp.solutions.drawing_utils

# ── Layout ─────────────────────────────────────────────────────────────────────
WIN_W, WIN_H   = 800, 600
ROAD_L, ROAD_R = 80, 720          # road edges
ROAD_W         = ROAD_R - ROAD_L
LANE_COUNT     = 3
LANE_W         = ROAD_W // LANE_COUNT
LANE_X         = [ROAD_L + LANE_W * i + LANE_W // 2 for i in range(LANE_COUNT)]

CAR_W, CAR_H   = 52, 84
ENEMY_W, ENEMY_H = 52, 84

FPS            = 60
DASH_LEN       = 40            # dashed lane marker length
DASH_GAP       = 30
MAX_ENEMIES    = 12
MAX_SPEED      = 18.0
CAM_SKIP       = 2             # process camera every N frames

ENEMY_PALETTES = [
    ((220,  50,  50), (140,  20,  20)),
    ((255, 140,   0), (180,  80,   0)),
    ((160,  50, 220), (100,  20, 150)),
    (( 50, 200, 100), ( 20, 130,  50)),
    ((200, 200,  50), (130, 130,  10)),
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def hand_lane(hand_x, frame_w):
    if hand_x is None:
        return 1
    thirds = frame_w / 3
    if hand_x < thirds:
        return 0
    if hand_x < 2 * thirds:
        return 1
    return 2

# ── Drawing helpers ────────────────────────────────────────────────────────────

def draw_player_car(surf, x, y):
    """Player car — blue, detailed."""
    rx = int(x)
    ry = int(y)
    pygame.draw.rect(surf, ( 33,150,243), (rx,       ry,       CAR_W, CAR_H),       border_radius=14)
    pygame.draw.rect(surf, ( 15, 87,187), (rx+8,     ry+10,    CAR_W-16, CAR_H-48), border_radius=8)
    pygame.draw.rect(surf, (180,220,240), (rx+12,    ry+18,    CAR_W-24, 18),        border_radius=4)
    pygame.draw.circle(surf, (30,30,30),  (rx+12,    ry+CAR_H-12), 10)
    pygame.draw.circle(surf, (30,30,30),  (rx+CAR_W-12, ry+CAR_H-12), 10)
    pygame.draw.circle(surf, (80,80,80),  (rx+12,    ry+12),    8)
    pygame.draw.circle(surf, (80,80,80),  (rx+CAR_W-12, ry+12), 8)
    pygame.draw.ellipse(surf,(255,255,120),(rx+8,    ry+2,     12, 9))
    pygame.draw.ellipse(surf,(255,255,120),(rx+CAR_W-20, ry+2, 12, 9))
    pygame.draw.ellipse(surf,(255, 80, 80),(rx+8,    ry+CAR_H-10, 12, 8))
    pygame.draw.ellipse(surf,(255, 80, 80),(rx+CAR_W-20, ry+CAR_H-10, 12, 8))

def draw_enemy_car(surf, x, y, palette):
    """Enemy car — colour-coded per palette."""
    body, dark = palette
    rx, ry = int(x - ENEMY_W//2), int(y)
    pygame.draw.rect(surf, body,  (rx,    ry,    ENEMY_W, ENEMY_H),       border_radius=14)
    pygame.draw.rect(surf, dark,  (rx+8,  ry+10, ENEMY_W-16, ENEMY_H-48), border_radius=8)
    pygame.draw.rect(surf, (160,200,220),(rx+12, ry+ENEMY_H-36, ENEMY_W-24, 18), border_radius=4)
    pygame.draw.circle(surf,(30,30,30),(rx+12,   ry+12),        8)
    pygame.draw.circle(surf,(30,30,30),(rx+ENEMY_W-12, ry+12),  8)
    pygame.draw.circle(surf,(30,30,30),(rx+12,   ry+ENEMY_H-12),10)
    pygame.draw.circle(surf,(30,30,30),(rx+ENEMY_W-12,ry+ENEMY_H-12),10)
    pygame.draw.ellipse(surf,(255, 80, 80),(rx+8,  ry+2,      12, 9))
    pygame.draw.ellipse(surf,(255, 80, 80),(rx+ENEMY_W-20,ry+2,12, 9))
    pygame.draw.ellipse(surf,(255,255,120),(rx+8,  ry+ENEMY_H-10,12,8))
    pygame.draw.ellipse(surf,(255,255,120),(rx+ENEMY_W-20,ry+ENEMY_H-10,12,8))

# ── Static background (pre-rendered once) ─────────────────────────────────────

def build_background():
    surf = pygame.Surface((WIN_W, WIN_H))
    # Grass
    surf.fill((34, 85, 34))
    # Shoulder strips
    pygame.draw.rect(surf, (80,80,80), (ROAD_L-10, 0, 10, WIN_H))
    pygame.draw.rect(surf, (80,80,80), (ROAD_R,    0, 10, WIN_H))
    # Road
    pygame.draw.rect(surf, (52,52,55), (ROAD_L, 0, ROAD_W, WIN_H))
    # Edge lines
    pygame.draw.line(surf, (220,220,220), (ROAD_L,0), (ROAD_L, WIN_H), 3)
    pygame.draw.line(surf, (220,220,220), (ROAD_R,0), (ROAD_R, WIN_H), 3)
    return surf

# ── Particle system ────────────────────────────────────────────────────────────

class Particle:
    __slots__ = ('x','y','vx','vy','life','max_life','color','size')
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        angle = random.uniform(0, math.tau)
        speed = random.uniform(2, 9)
        self.vx = math.cos(angle)*speed
        self.vy = math.sin(angle)*speed
        self.life = self.max_life = random.randint(25, 50)
        self.color = color
        self.size  = random.randint(3, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.25   # gravity
        self.life -= 1

    def draw(self, surf):
        alpha = self.life / self.max_life
        r = int(self.color[0]*alpha)
        g = int(self.color[1]*alpha)
        b = int(self.color[2]*alpha)
        pygame.draw.circle(surf, (r,g,b), (int(self.x), int(self.y)), max(1, int(self.size*alpha)))

def explode(particles, x, y, palette):
    for _ in range(40):
        c = random.choice([palette[0], palette[1], (255,255,200), (255,180,0)])
        particles.append(Particle(x, y, c))

# ── HUD helpers ────────────────────────────────────────────────────────────────

def draw_hud(surf, score, lives, speed, font_big, font_sm):
    # Semi-transparent panel
    panel = pygame.Surface((200, 80), pygame.SRCALPHA)
    panel.fill((0,0,0,160))
    surf.blit(panel, (10, 10))
    score_txt = font_big.render(f"Score: {score}", True, (255,255,255))
    surf.blit(score_txt, (18, 16))
    spd_txt   = font_sm.render(f"Speed  {speed:.1f}", True, (180,220,255))
    surf.blit(spd_txt, (18, 56))
    # Lives as heart icons
    heart_x = WIN_W - 40
    for i in range(lives):
        pygame.draw.polygon(surf, (220,50,80),
            [(heart_x-12,20),(heart_x+12,20),(heart_x+12,30),(heart_x,42),(heart_x-12,30)])
        pygame.draw.circle(surf,(220,50,80),(heart_x-6,20),6)
        pygame.draw.circle(surf,(220,50,80),(heart_x+6,20),6)
        heart_x -= 36

def draw_speedlines(surf, speed, tick):
    if speed < 8:
        return
    intensity = clamp(int((speed-8)/10*180), 0, 180)
    line_surf = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    rng = random.Random(tick // 3)   # stable for 3 frames
    count = int(speed * 1.5)
    for _ in range(count):
        x  = rng.randint(ROAD_L, ROAD_R)
        y1 = rng.randint(0, WIN_H)
        ln = rng.randint(20, 60)
        pygame.draw.line(line_surf, (255,255,255,intensity), (x,y1), (x, min(WIN_H,y1+ln)), 1)
    surf.blit(line_surf, (0,0))

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Hand Gesture Racing — Enhanced")

    # Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Camera not accessible!")
        sys.exit()
    ret, frame = cap.read()
    if not ret:
        print("Cannot read from camera!")
        cap.release()
        sys.exit()

    clock      = pygame.time.Clock()
    bg_surf    = build_background()

    # Fonts (cached once)
    font_big  = pygame.font.SysFont("segoeui",   30, bold=True)
    font_sm   = pygame.font.SysFont("segoeui",   20)
    font_over = pygame.font.SysFont("impact",    72)
    font_sub  = pygame.font.SysFont("segoeui",   28)

    # ── Game state ─────────────────────────────────────────────────────────────
    def reset_state():
        return dict(
            car_lane   = 1,
            car_x_px   = float(LANE_X[1] - CAR_W//2),   # smooth pixel x
            car_y      = WIN_H - CAR_H - 24,
            score      = 0,
            lives      = 3,
            enemies    = [],              # [cx, y, palette]
            enemy_spd  = 5.0,
            spawn_cd   = 70,
            game_over  = False,
            go_timer   = 0,              # cooldown before restart
            tick       = 0,
            dash_off   = 0.0,            # scrolling dash offset
            cam_frame  = frame.copy(),
            hand_x     = None,
            particles  = [],
        )

    s = reset_state()

    cam_tick = 0     # for camera-skip logic
    cam_rgb  = None
    h, w, _  = frame.shape   # initialise once so 'w' is always defined

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0   # seconds
        s['tick'] += 1

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # ── Camera (every CAM_SKIP frames) ────────────────────────────────────
        cam_tick += 1
        ret2, raw = cap.read()
        if ret2:
            s['cam_frame'] = raw
        if cam_tick % CAM_SKIP == 0 and ret2:
            flipped   = cv2.flip(s['cam_frame'], 1)
            frame_rgb = cv2.cvtColor(flipped, cv2.COLOR_BGR2RGB)
            h, w, _   = flipped.shape
            results   = hands.process(frame_rgb)
            s['hand_x'] = None
            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0].landmark[9]
                s['hand_x'] = int(lm.x * w)
                mp_draw.draw_landmarks(
                    flipped,
                    results.multi_hand_landmarks[0],
                    mp_hands.HAND_CONNECTIONS,
                )
            cam_rgb = cv2.cvtColor(flipped, cv2.COLOR_BGR2RGB)

        # ── Background ────────────────────────────────────────────────────────
        screen.blit(bg_surf, (0, 0))

        # ── Scrolling dashed lane markers ─────────────────────────────────────
        step = DASH_LEN + DASH_GAP
        s['dash_off'] = (s['dash_off'] + s['enemy_spd'] * 0.6) % step
        for lx in LANE_X[:-1]:          # markers between lanes (not at edges)
            x = ROAD_L + (lx - ROAD_L)   # align to lane boundary
            bx = ROAD_L + (LANE_X.index(lx)+1) * LANE_W   # actual boundary
            y  = -s['dash_off']
            while y < WIN_H:
                pygame.draw.line(screen, (160,160,160), (bx, int(y)), (bx, int(y+DASH_LEN)), 2)
                y += step
        # Center yellow dash
        y = -s['dash_off']
        cx = WIN_W // 2
        while y < WIN_H:
            pygame.draw.line(screen, (255,215,0), (cx, int(y)), (cx, int(y+DASH_LEN)), 3)
            y += step

        # ── Speed lines ───────────────────────────────────────────────────────
        draw_speedlines(screen, s['enemy_spd'], s['tick'])

        # ── Game logic ────────────────────────────────────────────────────────
        if not s['game_over']:
            # Lane selection
            target_lane = hand_lane(s['hand_x'], w)
            s['car_lane'] = target_lane
            target_x     = float(LANE_X[target_lane] - CAR_W//2)
            s['car_x_px'] = lerp(s['car_x_px'], target_x, 0.25)   # smooth slide

            car_rect = pygame.Rect(int(s['car_x_px']), s['car_y'], CAR_W, CAR_H)

            # Spawn enemies
            s['spawn_cd'] -= 1
            base_interval = max(25, 70 - s['score'] // 5)
            if s['spawn_cd'] <= 0 and len(s['enemies']) < MAX_ENEMIES:
                lane    = random.randint(0, LANE_COUNT-1)
                palette = random.choice(ENEMY_PALETTES)
                s['enemies'].append([LANE_X[lane], -ENEMY_H, palette])
                s['spawn_cd'] = base_interval + random.randint(-8, 8)

            # Update enemies
            to_remove = []
            for i, (cx, ey, pal) in enumerate(s['enemies']):
                ey += s['enemy_spd']
                s['enemies'][i][1] = ey

                # FIX: proper rect collision
                erect = pygame.Rect(int(cx - ENEMY_W//2), int(ey), ENEMY_W, ENEMY_H)
                if car_rect.colliderect(erect):
                    explode(s['particles'], int(cx), int(ey + ENEMY_H//2), pal)
                    s['lives'] -= 1
                    to_remove.append(i)
                    if s['lives'] <= 0:
                        s['game_over'] = True
                        s['go_timer']  = FPS * 2   # 2-second cooldown before restart
                elif ey > WIN_H:
                    to_remove.append(i)
                    s['score'] += 1
                    # Gradually increase speed (capped)
                    if s['score'] % 8 == 0:
                        s['enemy_spd'] = min(MAX_SPEED, s['enemy_spd'] + 0.5)

            for i in reversed(sorted(set(to_remove))):
                del s['enemies'][i]

            # Draw enemies
            for cx, ey, pal in s['enemies']:
                draw_enemy_car(screen, cx, int(ey), pal)

            # Draw player
            draw_player_car(screen, s['car_x_px'], s['car_y'])

            # HUD
            draw_hud(screen, s['score'], s['lives'], s['enemy_spd'], font_big, font_sm)

        else:
            # ── Game Over screen ──────────────────────────────────────────────
            # Still draw enemies for drama
            for cx, ey, pal in s['enemies']:
                draw_enemy_car(screen, cx, int(ey), pal)

            overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            overlay.fill((0,0,0,140))
            screen.blit(overlay, (0,0))

            go_surf   = font_over.render("GAME OVER", True, (255,60,60))
            sc_surf   = font_sub.render(f"Final Score: {s['score']}", True, (255,255,255))
            rst_surf  = font_sm.render("Show your hand to restart", True, (200,200,200))

            screen.blit(go_surf,  (WIN_W//2 - go_surf.get_width()//2,  WIN_H//2 - 90))
            screen.blit(sc_surf,  (WIN_W//2 - sc_surf.get_width()//2,  WIN_H//2 - 10))
            screen.blit(rst_surf, (WIN_W//2 - rst_surf.get_width()//2, WIN_H//2 + 40))

            # FIX: restart cooldown prevents immediate re-trigger
            if s['go_timer'] > 0:
                s['go_timer'] -= 1
            elif s['hand_x'] is not None:
                s = reset_state()   # full state reset

        # ── Particles ─────────────────────────────────────────────────────────
        for p in s['particles']:
            p.update()
            p.draw(screen)
        s['particles'] = [p for p in s['particles'] if p.life > 0]

        # ── Camera preview ────────────────────────────────────────────────────
        if cam_rgb is not None:
            cam_img     = np.rot90(cam_rgb)
            cam_surface = pygame.surfarray.make_surface(cam_img)
            cam_surface = pygame.transform.scale(cam_surface, (213, 160))
            cam_panel   = pygame.Surface((219, 166))
            cam_panel.fill((20,20,20))
            screen.blit(cam_panel,   (WIN_W - 229, 6))
            screen.blit(cam_surface, (WIN_W - 226, 9))
            lbl = font_sm.render("Camera", True, (160,200,255))
            screen.blit(lbl, (WIN_W - 226, 172))

        pygame.display.flip()

    cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
