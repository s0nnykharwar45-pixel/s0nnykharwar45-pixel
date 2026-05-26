import pygame
import chess
import random
import sys

pygame.init()

WIDTH, HEIGHT = 640, 640
SQ_SIZE = WIDTH // 8

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess GUI - Fixed")

clock = pygame.time.Clock()
board = chess.Board()

# Colors
LIGHT = (240, 217, 181)
DARK = (181, 136, 99)

SELECTED = (80, 140, 255)
MOVE_HINT = (90, 200, 110)

WHITE_PIECE = (245, 245, 245)   # softer white
BLACK_PIECE = (20, 20, 20)

OUTLINE = (0, 0, 0)
SHADOW = (120, 120, 120)

font = pygame.font.SysFont("Segoe UI Symbol", 56)

selected_square = None
animation = None

ANIM_SPEED = 0.2
ai_timer = 0


# -------------------------
# Helpers
# -------------------------
def square_to_xy(square):
    col = square % 8
    row = 7 - (square // 8)
    return col * SQ_SIZE, row * SQ_SIZE


def xy_to_square(pos):
    x, y = pos
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return None
    return chess.square(x // SQ_SIZE, 7 - (y // SQ_SIZE))


def lerp(a, b, t):
    return a + (b - a) * t


def start_animation(move):
    global animation
    piece = board.piece_at(move.from_square)
    if not piece:
        return

    sx, sy = square_to_xy(move.from_square)
    ex, ey = square_to_xy(move.to_square)

    animation = {
        "move": move,
        "piece": piece,
        "symbol": piece.unicode_symbol(),
        "start": (sx, sy),
        "end": (ex, ey),
        "progress": 0
    }


# -------------------------
# Drawing
# -------------------------
def draw_board():
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            pygame.draw.rect(screen, color, (c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_move_hints():
    if selected_square is None:
        return

    for move in board.legal_moves:
        if move.from_square == selected_square:
            x, y = square_to_xy(move.to_square)

            overlay = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
            overlay.fill((90, 200, 110, 60))
            screen.blit(overlay, (x, y))

            pygame.draw.circle(screen, MOVE_HINT,
                               (x + SQ_SIZE//2, y + SQ_SIZE//2), 9)


def draw_selected():
    if selected_square is None:
        return

    x, y = square_to_xy(selected_square)
    overlay = pygame.Surface((SQ_SIZE, SQ_SIZE), pygame.SRCALPHA)
    overlay.fill((80, 140, 255, 90))
    screen.blit(overlay, (x, y))


def draw_piece_with_outline(symbol, color, x, y):
    # shadow
    shadow = font.render(symbol, True, SHADOW)
    screen.blit(shadow, (x + 2, y + 2))

    # outline
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2),(-2,2),(2,-2)]:
        outline = font.render(symbol, True, OUTLINE)
        screen.blit(outline, (x + dx, y + dy))

    # main
    text = font.render(symbol, True, color)
    screen.blit(text, (x, y))


def draw_pieces():
    for square in chess.SQUARES:
        if animation and square in (animation["move"].from_square, animation["move"].to_square):
            continue

        piece = board.piece_at(square)
        if not piece:
            continue

        x, y = square_to_xy(square)

        color = WHITE_PIECE if piece.color == chess.WHITE else BLACK_PIECE

        text = font.render(piece.unicode_symbol(), True, color)
        rect = text.get_rect(center=(x + SQ_SIZE//2, y + SQ_SIZE//2))

        draw_piece_with_outline(piece.unicode_symbol(), color, rect.x, rect.y)


def draw_animation():
    global animation

    if not animation:
        return

    animation["progress"] += ANIM_SPEED
    if animation["progress"] > 1:
        animation["progress"] = 1

    sx, sy = animation["start"]
    ex, ey = animation["end"]

    x = lerp(sx, ex, animation["progress"])
    y = lerp(sy, ey, animation["progress"])

    color = WHITE_PIECE if animation["piece"].color == chess.WHITE else BLACK_PIECE

    text = font.render(animation["symbol"], True, color)
    rect = text.get_rect(center=(x + SQ_SIZE//2, y + SQ_SIZE//2))

    draw_piece_with_outline(animation["symbol"], color, rect.x, rect.y)

    if animation["progress"] >= 1:
        board.push(animation["move"])
        animation = None


# -------------------------
# Main loop
# -------------------------
running = True

while running:
    dt = clock.tick(60) / 1000

    screen.fill((0, 0, 0))

    draw_board()
    draw_move_hints()
    draw_selected()
    draw_pieces()
    draw_animation()

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if animation:
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and board.turn == chess.WHITE:
            sq = xy_to_square(pygame.mouse.get_pos())
            if sq is None:
                continue

            if selected_square is None:
                piece = board.piece_at(sq)
                if piece and piece.color == chess.WHITE:
                    selected_square = sq
            else:
                # 🔥 FIXED PROMOTION LOGIC
                move = chess.Move(selected_square, sq)

                legal_moves = list(board.legal_moves)

                # try all promotion types if needed
                for promo in [None, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                    test_move = chess.Move(selected_square, sq, promotion=promo)
                    if test_move in legal_moves:
                        start_animation(test_move)
                        break

                selected_square = None

    # AI move
    if board.turn == chess.BLACK and not board.is_game_over() and not animation:
        ai_timer += dt
        if ai_timer > 0.5:
            move = random.choice(list(board.legal_moves))
            start_animation(move)
            ai_timer = 0


pygame.quit()
sys.exit()