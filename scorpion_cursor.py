import math
import random
import pygame

# =========================================================
# LIMSYSTEM - Python implementation inspired by the reference
# Mouse-following creature with connected skeletal segments
# =========================================================

pygame.init()

WIDTH, HEIGHT = 1100, 760
FPS = 60
BACKGROUND = (3, 3, 7)
SILVER = (160, 170, 180)
WHITE = (225, 235, 245)
CYAN = (90, 190, 230)

screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.RESIZABLE
)
pygame.display.set_caption("LimSystem | Scorpion Cursor")
clock = pygame.time.Clock()

rng = random.Random(42)
font = pygame.font.SysFont("consolas", 15)
title_font = pygame.font.SysFont("consolas", 25, bold=True)


def clamp(value, low, high):
    return max(low, min(high, value))


def draw_glow(surface, position, radius, color):
    radius = max(2, int(radius))
    layer = pygame.Surface(
        (radius * 4, radius * 4),
        pygame.SRCALPHA
    )
    center = (radius * 2, radius * 2)

    for i in range(5, 0, -1):
        r = max(1, int(radius * i / 5))
        alpha = int(7 * (6 - i))

        pygame.draw.circle(
            layer,
            (*color, alpha),
            center,
            r
        )

    surface.blit(
        layer,
        (int(position[0] - center[0]),
         int(position[1] - center[1])),
        special_flags=pygame.BLEND_RGBA_ADD
    )


def draw_line(surface, start, end, color=SILVER, width=1):
    pygame.draw.line(surface, color, start, end, width)


def draw_joint(surface, position, radius=2):
    draw_glow(surface, position, radius * 4, CYAN)
    pygame.draw.circle(surface, SILVER, position, radius)
    pygame.draw.circle(
        surface,
        WHITE,
        position,
        max(1, radius - 1)
    )


class Node:
    """One point in a connected creature skeleton."""

    def __init__(self, x, y, parent=None, is_segment=True):
        self.position = pygame.Vector2(x, y)
        self.parent = parent
        self.is_segment = is_segment


class LimSystem:
    """
    Controls a chain of connected nodes.

    Reference concepts:
    - creature
    - nodes
    - length
    - update()
    - move_to()
    """

    def __init__(self, end, length, speed, creature):
        self.creature = creature
        self.length = length
        self.speed = speed
        self.nodes = []

        # Create connected nodes extending from the starting point.
        position = pygame.Vector2(end)

        for i in range(length):
            node = Node(
                position.x - i * 17,
                position.y + math.sin(i * 0.3) * 4
            )

            if self.nodes:
                node.parent = self.nodes[-1]

            self.nodes.append(node)

        self.target = pygame.Vector2(end)

    def move_to(self, x, y, dt):
        """Move the leading node toward the mouse cursor."""
        self.target.update(x, y)

        head = self.nodes[0]
        head.position = head.position.lerp(
            self.target,
            clamp(self.speed * dt, 0, 1)
        )

        # Each node follows its parent at a fixed distance.
        segment_length = 17

        for i in range(1, len(self.nodes)):
            parent = self.nodes[i - 1]
            node = self.nodes[i]

            direction = node.position - parent.position

            if direction.length_squared() < 0.001:
                direction = pygame.Vector2(-1, 0)
            else:
                direction = direction.normalize()

            node.position = (
                parent.position + direction * segment_length
            )

    def update(self, mouse_x, mouse_y, dt):
        self.move_to(mouse_x, mouse_y, dt)


class Scorpion:
    """Draws the body, articulated legs, claws, and tail."""

    def __init__(self, x, y):
        self.system = LimSystem(
            end=(x, y),
            length=17,
            speed=3.8,
            creature=self
        )
        self.phase = 0.0

    def update(self, mouse, dt):
        self.system.update(mouse[0], mouse[1], dt)
        self.phase += dt

    def draw_body(self, surface):
        nodes = self.system.nodes

        # Draw the main segmented spine.
        for i in range(len(nodes) - 1):
            a = nodes[i].position
            b = nodes[i + 1].position

            start = (int(a.x), int(a.y))
            end = (int(b.x), int(b.y))

            draw_line(surface, start, end, SILVER, 2)

            midpoint = (
                int((a.x + b.x) / 2),
                int((a.y + b.y) / 2)
            )

            pygame.draw.line(
                surface,
                (90, 100, 115),
                (midpoint[0], midpoint[1] - 5),
                (midpoint[0], midpoint[1] + 5),
                1
            )

            draw_joint(surface, start, 2)

        draw_joint(
            surface,
            (
                int(nodes[-1].position.x),
                int(nodes[-1].position.y)
            ),
            3
        )

    def draw_legs(self, surface):
        nodes = self.system.nodes

        # Four pairs of legs attached to the middle body.
        for i, index in enumerate((3, 5, 7, 9)):
            anchor = nodes[index].position

            swing = math.sin(
                self.phase * 7 + i * 1.6
            ) * 10

            lift = abs(math.cos(
                self.phase * 7 + i * 1.6
            )) * 5

            for side in (-1, 1):
                hip = pygame.Vector2(
                    anchor.x,
                    anchor.y
                )

                knee = pygame.Vector2(
                    anchor.x + swing - 10,
                    anchor.y + side * (24 + lift)
                )

                foot = pygame.Vector2(
                    anchor.x - 23 - swing * 0.6,
                    anchor.y + side * (45 + lift)
                )

                hip_point = (int(hip.x), int(hip.y))
                knee_point = (int(knee.x), int(knee.y))
                foot_point = (int(foot.x), int(foot.y))

                draw_line(
                    surface, hip_point, knee_point, SILVER, 2
                )
                draw_line(
                    surface, knee_point, foot_point, WHITE, 1
                )

                # Small pointed barbs.
                barb = (
                    int(knee.x + 7),
                    int(knee.y + side * 8)
                )

                draw_line(
                    surface, knee_point, barb, (100, 120, 140), 1
                )

                draw_joint(surface, knee_point, 2)
                draw_joint(surface, foot_point, 2)

    def draw_claws(self, surface):
        head = self.system.nodes[0].position

        for side in (-1, 1):
            shoulder = (
                int(head.x),
                int(head.y + side * 4)
            )

            elbow = (
                int(head.x + 17),
                int(head.y + side * 13)
            )

            base = (
                int(head.x + 31),
                int(head.y + side * 20)
            )

            tip1 = (
                int(head.x + 48),
                int(head.y + side * 12)
            )

            tip2 = (
                int(head.x + 49),
                int(head.y + side * 29)
            )

            draw_line(surface, shoulder, elbow, SILVER, 2)
            draw_line(surface, elbow, base, WHITE, 2)
            draw_line(surface, base, tip1, SILVER, 2)
            draw_line(surface, base, tip2, SILVER, 2)

            draw_joint(surface, elbow, 2)

    def draw_tail(self, surface):
        nodes = self.system.nodes
        tail_base = nodes[-1].position

        # Tail arches behind the last body segment.
        sway = math.sin(self.phase * 1.5) * 9

        points = [
            (tail_base.x, tail_base.y),
            (tail_base.x - 16, tail_base.y - 9),
            (tail_base.x - 30, tail_base.y - 25),
            (tail_base.x - 34, tail_base.y - 43),
            (tail_base.x - 24 + sway, tail_base.y - 59),
            (tail_base.x - 8 + sway, tail_base.y - 70),
            (tail_base.x + 8 + sway, tail_base.y - 78),
        ]

        for i in range(len(points) - 1):
            start = tuple(map(int, points[i]))
            end = tuple(map(int, points[i + 1]))

            draw_line(surface, start, end, SILVER, 2)
            draw_joint(surface, end, 2)

        # Glowing stinger.
        tip = (
            int(points[-1][0] + 7),
            int(points[-1][1] - 14)
        )

        base = tuple(map(int, points[-1]))

        draw_glow(surface, tip, 13, CYAN)
        draw_line(surface, base, tip, CYAN, 2)
        draw_joint(surface, tip, 3)

    def draw(self, surface):
        self.draw_tail(surface)
        self.draw_legs(surface)
        self.draw_body(surface)
        self.draw_claws(surface)


def draw_background(surface, t):
    surface.fill(BACKGROUND)

    # Twinkling stars.
    for i in range(90):
        x = (i * 137 + 31) % surface.get_width()
        y = (i * 89 + 17) % surface.get_height()

        pulse = 0.5 + 0.5 * math.sin(t * 1.4 + i)

        brightness = int(25 + pulse * 55)

        pygame.draw.circle(
            surface,
            (brightness, brightness, brightness + 8),
            (x, y),
            1
        )


def main():
    running = True
    paused = False
    t = 0.0

    design = pygame.Surface((WIDTH, HEIGHT))

    scorpion = Scorpion(
        WIDTH * 0.55,
        HEIGHT * 0.55
    )

    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.04)
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_s:
                    pygame.image.save(
                        screen,
                        "limsystem-screenshot.png"
                    )
                    print("Screenshot saved.")

                elif event.key == pygame.K_r:
                    scorpion = Scorpion(
                        WIDTH * 0.55,
                        HEIGHT * 0.55
                    )

        if not paused:
            t += dt
            scorpion.update(mouse, dt)

        draw_background(design, t)
        scorpion.draw(design)

        # Cursor target.
        pygame.draw.circle(
            design,
            CYAN,
            mouse,
            7,
            1
        )

        pygame.draw.circle(
            design,
            WHITE,
            mouse,
            2
        )

        design.blit(
            title_font.render(
                "LIMSYSTEM",
                True,
                WHITE
            ),
            (28, 22)
        )

        design.blit(
            font.render(
                "PROCEDURAL CREATURE / PYTHON + PYGAME",
                True,
                (110, 140, 165)
            ),
            (30, 55)
        )

        status = "PAUSED" if paused else "LIVE"

        design.blit(
            font.render(
                f"{status} | SPACE pause | S screenshot | R reset | ESC quit",
                True,
                CYAN
            ),
            (28, HEIGHT - 30)
        )

        scaled = pygame.transform.smoothscale(
            design,
            screen.get_size()
        )

        screen.blit(scaled, (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()