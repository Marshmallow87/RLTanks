from tankenv import TankEnv, Player
from constants import *
import pygame


def main():
    env = TankEnv(True)

    env.player0 = Player("Player1", RED, 0)
    env.player2 = Player("Player2", GREEN, 1)
    env.player1 = Player("Player3", BLUE, 2)
    env.screen = None
    env.reset_state()

    env.key_pressed = False
    env.key_timer = 100
    env.key_delay = 50
    env.key_interval = 100

    # Simple setup for the game Loop, it runs while a key pressed
    while env.game.done == False:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                env.game.done = True
            elif event.type == pygame.KEYDOWN:
                env.key_pressed = True
                env.key_timer = pygame.time.get_ticks() + env.key_delay
            elif event.type == pygame.KEYUP:
                env.key_pressed = False
        # Check if key is held down continuously
        if env.key_pressed and pygame.time.get_ticks() > env.key_timer:
            env.total_reward = 0
            env.game.make_game_action()


if __name__ == "__main__":
    main()
