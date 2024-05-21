import gymnasium as gym
from gymnasium import spaces

import numpy as np
from game import *
from player import *
from vehicle import *


class TankEnv(gym.Env):
    """Custom Environment that follows gym interface"""

    def __init__(self, use_gui):
        super(TankEnv, self).__init__()
        self.action_space = spaces.Discrete(37)
        self.observation_space = spaces.Box(
            low=-500, high=500, shape=(119,), dtype=np.int32
        )
        self.use_gui = use_gui

    def step(self, action: int) -> tuple[np.array, float, bool, dict]:
        """
        Gym function of a single timestep of the environment
        """
        info = {}
        self.total_reward = 0

        # While non reinforcement learning player, make actions with other players
        while (
            self.game.current_index != self.reinfocement_learning_player_index
            and self.game.done != True
        ):
            self.total_reward += self.game.make_game_action(action)

        # If game is done, return observation and reward
        if self.game.done == True:
            self.prepare_observation()
            self.reward = self.total_reward
            self.prev_reward = self.total_reward
            return self.observation, self.reward, self.game.done, False, info

        # If reinforcement learning player, make action and return observation and reward
        if (
            self.game.current_index == self.reinfocement_learning_player_index
        ):  # If own player, return observation after step
            self.total_reward += self.game.make_game_action(action)
            self.prepare_observation()
            self.reward = self.total_reward  # Calculate reward
            self.prev_reward = self.total_reward
            return self.observation, self.reward, self.game.done, False, info

    def reset(self, seed=None, options=None):
        """
        Gym function that resets the environment to the initial state
        """
        info = {}
        self.prev_reward = 0
        self.reinfocement_learning_player_index = 0
        self.player0 = ReinforcementLearningPlayer(
            "Player1", RED, self.reinfocement_learning_player_index
        )
        self.player1 = Player("Player2", GREEN, 1)
        self.player2 = Player("Player3", BLUE, 2)

        self.reset_state()
        self.prepare_observation()

        return self.observation, info

    def prepare_observation(self):
        """
        Prepares the observation space for the reinforcement learning agent
        """
        observation = []
        # Add all vehicle data to observation space
        for vehicle in self.game.vehicles:
            observation.extend(vehicle.position)
            observation.append(vehicle.owning_player.index)
            observation.append(vehicle.vehicleIndex)
            observation.append(vehicle.hp)
            observation.append(vehicle.sp)
            observation.append(vehicle.capture_points)

        # Add player data to observation space
        for player in self.game.players:
            observation.append(player.kill_points)

        # Flatten the neutrality matrix and add it to the observation space
        neutrality_matrix_flat = np.array(self.game.neutrality_matrix).flatten()
        observation.extend(neutrality_matrix_flat)

        # Add the current index and current tank index to the observation space
        observation.append(self.game.current_index)
        observation.append(self.game.current_tank_index)

        self.observation = observation
        self.observation = np.array(self.observation)

    def reset_state(self):
        """
        Resets the game state
        """
        self.reinfocement_learning_player_index = 0
        self.game = Game(self.use_gui, self.reinfocement_learning_player_index)
        self.game.setup()
        self.game.players = [self.player0, self.player1, self.player2]
        self.game.place_vehicles(self.game.players)
