#!/usr/bin/env python3
"""
This leverages the curses library to make a terminal based game
"""
import curses
import random
from curses import wrapper
from enum import Enum
from time import sleep

# Frames Per Second
FPS = 30

# little random bullets cuz why not?
BULLETS = [
    ".",
    "-",
    "_",
    ":",
    "!",
    "*",
    "#",
    "@",
    ")",
    "]",
    "}",
    ">",
]

# Variety is the spice of life!
ENEMIES = [
    "<",
    "O",
    "X",
    "W",
    "V",
    "A",
    "Z",
    "|",
    "\\",
    "/",
    ",",
    ";",
]


class Axis(Enum):
    """shortcut for the axis"""

    X = 1
    Y = 2


class ColorScheme(int, Enum):
    """Shortcuts for the different color schemes"""

    PLAYER_REGULAR = 1
    BULLET = 2
    ENEMY_REGULAR = 3
    INVISIBLE = 4
    SCOREBOARD = 5


class Coordinate:
    """Abstract class of something that can exist on screen as well as move across it"""

    def __init__(self, screen, y, x, icon, color_scheme):
        self.screen = screen
        self.y = y
        self.x = x
        self.icon = icon
        self.color_scheme = color_scheme

    def bind(self, coord, lower_bound, upper_bound):
        """moves a thing without allowing it to go outside the bounds"""
        return min(max(coord, lower_bound), upper_bound)

    def bind_x_to_screen(self, x):
        """moves along the x axis preventing from going off screen"""
        if self.y == curses.LINES - 1:
            offset = 1
        else:
            offset = 0
        return self.bind(x, 0, curses.COLS - (len(self.icon) + offset))

    def bind_y_to_screen(self, y):
        """moves along the y axis preventing from going off screen"""
        return self.bind(y, 0, curses.LINES - 1)

    def _move(self, axis, distance):
        """move a thing a direction"""
        if axis == Axis.X:
            self.x = self.bind_x_to_screen(self.x + distance)
        if axis == Axis.Y:
            self.y = self.bind_y_to_screen(self.y + distance)

    def move_left(self, distance):
        """move it left"""
        self._move(Axis.X, -1 * distance)

    def move_right(self, distance):
        """move it right"""
        self._move(Axis.X, distance)

    def move_up(self, distance):
        """move it up"""
        self._move(Axis.Y, -1 * distance)

    def move_down(self, distance):
        """move it down"""
        self._move(Axis.Y, distance)

    def render(self):
        """render the object on screen"""
        self.screen.addstr(self.y, self.x, self.icon, curses.color_pair(self.color_scheme))


class Bullet(Coordinate):
    """Class for the launch-able projectiles!"""

    def __init__(
        self,
        screen,
        y: int = 0,
        x: int = 0,
        fired=False,
        speed=1,
        icon=BULLETS[0],
        color_scheme=ColorScheme.BULLET,
    ):
        super().__init__(screen, y, x, icon, color_scheme)
        self.fired = fired
        self.speed = speed

    def fire(self, player):
        """initializes the bullet on screen"""
        self.y = player.y
        self.x = player.x
        self.fired = True
        self.render()

    def keep_shooting(self):
        """Either moves the bullet forward or stops if it hits the wall"""
        if self.x >= curses.COLS - len(self.icon) or (
            self.y == curses.LINES - 1 and self.x >= curses.COLS - (len(self.icon) + 1)
        ):
            self.stop()
        else:
            self.move_right(self.speed)
            self.render()

    def stop(self):
        """stops the bullet and resets its coordinates"""
        self.fired = False
        self.x = 0
        self.y = 0


class Creature(Coordinate):
    """Abstract class for a thing that can die"""

    def __init__(self, screen, y, x, icon, color_scheme, alive):
        super().__init__(screen, y, x, icon, color_scheme)
        self.alive = alive

    def die(self):
        self.alive = False


class Enemy(Creature):
    def __init__(self, screen, y=0, x=0, icon=ENEMIES[0]):
        super().__init__(
            screen, y, x, icon=icon, color_scheme=ColorScheme.ENEMY_REGULAR, alive=True
        )

    def move_random(self):
        """Make erratic movements slightly favoring standing still and moving left"""
        where_to = random.random()
        if where_to > 0.35:
            pass
        else:
            how_bout_now = random.random()
            if how_bout_now > 0.5:
                if how_bout_now > 0.70:
                    self.move_left(1)
                else:
                    self.move_right(1)
            else:
                if how_bout_now > 0.25:
                    self.move_up(1)
                else:
                    self.move_down(1)


class Player(Creature):
    """This is you"""

    def __init__(self, screen, y=0, x=0, shots=None):
        super().__init__(
            screen, y, x, icon=" ", color_scheme=ColorScheme.PLAYER_REGULAR, alive=True
        )
        self.shots = shots or [Bullet(self.screen, icon=random.choice(BULLETS))]

    def parse_keys(self, key):
        """Parse key presses for movement and stuff"""
        if key == ord("w") or key == curses.KEY_UP:
            self.move_up(1)
        if key == ord("s") or key == curses.KEY_DOWN:
            self.move_down(1)
        if key == ord("a") or key == curses.KEY_LEFT:
            self.move_left(1)
        if key == ord("d") or key == curses.KEY_RIGHT:
            self.move_right(1)
        if key == ord(" "):
            self.fire()

    def update_background_attributes(self, enemies):
        """Updates your bullets and stuff"""
        for e in enemies:
            if e.alive:
                e.move_random()
                e.render()
                if e.y == self.y and e.x == self.x:
                    self.die()
                    break
                for bullet in self.shots:
                    if bullet.y == e.y and bullet.x == e.x:
                        e.die()
                        bullet.stop()
                        self.shots.append(Bullet(self.screen, icon=random.choice(BULLETS)))
                        break
        if not any([e.alive for e in enemies]):
            current_enemy_death_toll = len(enemies)
            for _ in range(current_enemy_death_toll):
                enemies.append(
                    Enemy(
                        self.screen,
                        random.randint(0, curses.LINES - 1),
                        random.randint(5, curses.COLS - 2),
                        icon=random.choice(ENEMIES),
                    )
                )

        for bullet in self.shots:
            if bullet.fired:
                bullet.keep_shooting()

        self.render()

    def fire(self):
        """Shoot any available bullets you have left!"""
        for bullet in self.shots:
            if not bullet.fired:
                bullet.fire(self)
                break
        else:
            pass


class Game:
    """Wrapper for the game so you can keep the score"""

    def __init__(self, kills=0):
        self.kills = kills

    def main(self, screen):
        """
        Main program
        """
        screen.nodelay(1)
        screen.clear()
        curses.init_pair(ColorScheme.PLAYER_REGULAR, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(ColorScheme.ENEMY_REGULAR, curses.COLOR_BLACK, curses.COLOR_RED)
        curses.init_pair(ColorScheme.BULLET, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(ColorScheme.INVISIBLE, curses.COLOR_BLACK, curses.COLOR_BLACK)
        curses.init_pair(ColorScheme.SCOREBOARD, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        player = Player(screen, 0, 0)
        enemies = [
            Enemy(screen, y=curses.LINES - 1, x=curses.COLS // 2, icon=random.choice(ENEMIES))
        ]
        while player.alive:
            key = screen.getch()
            player.parse_keys(key)
            screen.clear()
            player.update_background_attributes(enemies)
            self.kills = len([1 for e in enemies if not e.alive])
            kills_message = f"K: {self.kills:0>6}"
            screen.addstr(
                0,
                curses.COLS - len(kills_message) - 1,
                kills_message,
                curses.color_pair(ColorScheme.SCOREBOARD),
            )
            screen.addstr(
                curses.LINES - 1, curses.COLS - 2, " ", curses.color_pair(ColorScheme.INVISIBLE)
            )
            screen.refresh()
            sleep(1 / FPS)

    def print_score(self):
        print(f"but got {game.kills} kills")
        if self.kills < 3:
            print("too bad you suck")
        elif self.kills < 10:
            print("were you even trying?")
        elif self.kills < 20:
            print("not great")
        elif self.kills < 50:
            print("not terrible")
        elif self.kills < 100:
            print("decent")
        elif self.kills < 1000:
            print("wow very nice")
        else:
            print("wait, what how?! Did you cheat?")


if __name__ == "__main__":
    game = Game()
    wrapper(game.main)
    print("YA DIED")
    game.print_score()
