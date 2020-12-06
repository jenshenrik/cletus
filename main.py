import pygame
import os
import time
import random

from typing import Tuple, List

pygame.font.init()

WIDTH: int = 1280
HEIGHT: int = 960
TILE_SIZE: Tuple[int, int] = (int(WIDTH / 20), int(WIDTH / 20))

WIN: pygame.Surface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cookies for Cletus")


# Load images
CLETUS: pygame.Surface = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "cletus_walk_01.png")), TILE_SIZE
)
CLETUS_WALK_ANIMATION: List[pygame.Surface] = [
    pygame.transform.scale(
        pygame.image.load(os.path.join("assets", "cletus_walk_01.png")), TILE_SIZE
    ),
    pygame.transform.scale(
        pygame.image.load(os.path.join("assets", "cletus_walk_02.png")), TILE_SIZE
    ),
]
CLETUS_SHOT_ANIMATION: List[pygame.Surface] = [
    pygame.transform.scale(
        pygame.image.load(os.path.join("assets", "cletus_shoot.png")), TILE_SIZE
    ),
    CLETUS,
]
HIPPIE: pygame.Surface = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "hippie.png")), TILE_SIZE
)
HIPPIE_WALK_ANIMATION: List[pygame.Surface] = [
    pygame.transform.scale(
        pygame.image.load(os.path.join("assets", "hippie_walk_01.png")), TILE_SIZE
    ),
    pygame.transform.scale(
        pygame.image.load(os.path.join("assets", "hippie_walk_02.png")), TILE_SIZE
    ),
]
COOKIE: pygame.Surface = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "cookie.png")), TILE_SIZE
)
BULLET: pygame.Surface = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "bullet.png")), TILE_SIZE
)

# Background
BG: pygame.Surface = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "background.png")), (WIDTH, HEIGHT)
)


TOP_MARGIN: int = 2 * CLETUS.get_height()
BOTTOM_MARGIN: int = CLETUS.get_height()


class Drawable:
    def __init__(self, x: int, y: int, image: pygame.Surface):
        self.x = x
        self.y = y
        self.image = image
        self.mask: pygame.Mask = pygame.mask.from_surface(self.image)

    def draw(self, window) -> None:
        window.blit(self.image, (self.x, self.y))


class Projectile(Drawable):
    def __init__(self, x: int, y: int, image: pygame.Surface):
        super().__init__(x, y, image)

    def move(self, xy: Tuple[int, int]) -> None:
        x, y = xy
        self.x += x
        self.y += y

    def collision(self, other) -> bool:
        return collide(self, other)


class Cookie(Drawable):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, COOKIE)
        self.point_value = -10

    def move(self, velocity: Tuple[int, int]) -> None:
        x, y = velocity
        self.x += x
        self.y += y

    def get_points(self, level: int) -> int:
        return self.point_value * level

    def collision(self, other) -> bool:
        return collide(self, other)


class Entity(Drawable):
    COOLDOWN = 15

    def __init__(
        self,
        x: int,
        y: int,
        image: pygame.Surface,
        walk_animation: List[pygame.Surface],
        shot_image: pygame.Surface,
        points: int,
    ):
        super().__init__(x, y, image)
        self.walk_count: int = 0
        self.shots: List[Projectile] = []
        self.walk_animation = walk_animation
        self.shot_image = shot_image
        self.cooldown_counter: int = 0
        self.point_value = points

    def cooldown(self) -> None:
        if self.cooldown_counter >= self.COOLDOWN:
            self.cooldown_counter = 0
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1

    def draw(self, window: pygame.Surface) -> None:
        if len(self.walk_animation) > 1:
            if self.walk_count + 1 >= 10:
                self.walk_count = 0
                window.blit(self.walk_animation[0], (self.x, self.y))
            else:
                window.blit(self.walk_animation[self.walk_count // 5], (self.x, self.y))
        else:
            super().draw(window)

        for shot in self.shots:
            shot.draw(window)

    def shoot(self) -> None:
        if self.cooldown_counter == 0:
            self.is_shooting = True
            self.shots.append(Projectile(self.x, self.y, self.shot_image))
            self.cooldown_counter = 1

    def get_points(self, level: int) -> int:
        return self.point_value * level


class Hippie(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, HIPPIE, HIPPIE_WALK_ANIMATION, None, 1)

    def move(self, velocity):
        self.x -= velocity
        self.walk_count += 1


class Player(Entity):
    def __init__(self, shot_vel: Tuple[int, int]):
        self.shot_vel = shot_vel
        self.is_shooting: bool = False
        self.score: int = 0
        super().__init__(
            5,
            HEIGHT / 2 - CLETUS.get_height() / 2,
            CLETUS,
            CLETUS_WALK_ANIMATION,
            BULLET,
            0,
        )

    def draw(self, window):
        if self.is_shooting:
            window.blit(CLETUS_SHOT_ANIMATION[0], (self.x, self.y))
            self.is_shooting = False
        else:
            super().draw(window)

    def move_shots(self, hippies: List[Hippie], cookies: List[Cookie], level: int):
        for shot in self.shots:
            shot.move(self.shot_vel)
            if shot.x >= WIDTH:
                self.shots.remove(shot)
            else:
                for target in hippies + cookies:
                    if shot.collision(target):
                        if target in hippies:
                            hippies.remove(target)
                        elif target in cookies:
                            cookies.remove(target)
                        self.score += target.get_points(level)
                        if shot in self.shots:
                            self.shots.remove(shot)


def collide(obj1: Drawable, obj2: Drawable) -> bool:
    offset_x: int = int(obj2.x - obj1.x)
    offset_y: int = int(obj2.y - obj1.y)
    # overlap returns a tuple with the coordinates where the objects overlap
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


def main():
    run: bool = True
    FPS: int = 30

    lives: int = 3
    level: int = 0
    score: int = 0
    cookie_delay: int = 1000
    COOKIE_EVENT = pygame.USEREVENT + 0
    pygame.time.set_timer(COOKIE_EVENT, cookie_delay)

    lost: bool = False
    lost_count: int = 0

    main_font = pygame.font.SysFont("monospace", 40)
    lost_font = pygame.font.SysFont("monospace", 100)

    player_shot_vel: Tuple[int, int] = (5, 0)
    player = Player(player_shot_vel)
    player_vel: int = 7

    wave_length: int = 5
    hippie_vel: int = 1
    hippies: List[Hippie] = []
    cookie_vel: Tuple[int, int] = (-2, 0)
    cookies: List[Cookie] = []

    clock = pygame.time.Clock()

    def redraw_window():
        WIN.blit(BG, (0, 0))

        for hippie in hippies:
            hippie.draw(WIN)

        for cookie in cookies:
            cookie.draw(WIN)

        player.draw(WIN)

        # Draw text
        lives_label = main_font.render(f"Lives: {lives}", 0, (255, 255, 255))
        score_label = main_font.render(f"Score: {player.score}", 0, (255, 255, 255))
        WIN.blit(lives_label, (5, 5))
        WIN.blit(score_label, (WIDTH - score_label.get_width() - 5, 5))

        if lost:
            lost_label = lost_font.render("GAME OVER", 0, (255, 0, 0))
            WIN.blit(
                lost_label,
                (
                    WIDTH / 2 - lost_label.get_width() / 2,
                    HEIGHT / 2 - lost_label.get_height() / 2,
                ),
            )

        pygame.display.update()

    while run:
        clock.tick(FPS)

        redraw_window()

        if lives <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue

        if len(hippies) == 0:
            level += 1
            wave_length += 5
            hippie_vel += level // 10
            for i in range(wave_length):
                hippies.append(
                    Hippie(
                        random.randrange(WIDTH + 50, WIDTH + 500),
                        random.randrange(
                            TOP_MARGIN, HEIGHT - (BOTTOM_MARGIN + HIPPIE.get_height())
                        ),
                    )
                )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == COOKIE_EVENT:
                if random.randint(1, 100) <= 10:
                    cookies.append(
                        Cookie(
                            random.randrange(WIDTH + 50, WIDTH + 500),
                            random.randrange(
                                TOP_MARGIN,
                                HEIGHT - (BOTTOM_MARGIN + HIPPIE.get_height()),
                            ),
                        )
                    )

        keys = pygame.key.get_pressed()

        if (
            keys[pygame.K_w] or keys[pygame.K_UP]
        ) and player.y > TOP_MARGIN:  # Up: w or arrow up
            player.y -= player_vel
            player.walk_count += 1
        elif (
            keys[pygame.K_s] or keys[pygame.K_DOWN]
        ) and player.y + player.image.get_height() < HEIGHT - BOTTOM_MARGIN:  # Down: s or arrow down
            player.y += player_vel
            player.walk_count += 1

        else:
            player.walk_count = 0

        if keys[pygame.K_SPACE]:
            player.shoot()

        for hippie in hippies[:]:
            hippie.move(hippie_vel)

            if hippie.x <= -HIPPIE.get_width():
                lives -= 1
                hippies.remove(hippie)

        for cookie in cookies[:]:
            cookie.move(cookie_vel)

            if cookie.collision(player):
                lives += 1
                cookies.remove(cookie)

            if cookie.x <= -COOKIE.get_width():
                cookies.remove(cookie)

        player.cooldown()
        player.move_shots(hippies, cookies, level)


main()
