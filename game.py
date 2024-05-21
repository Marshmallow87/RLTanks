import heapq
from gui import *
from vehicle import *
from constants import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from vehicle import Vehicle

REWARD_FOR_WIN = 400
REWARD_FOR_DRAW = 200
REWARD_FOR_SUCCESSFULL_SHOT = 8
REWARD_FOR_SHOT_DESTROYING_TANK = 20

MAX_TURNS = 45
HEX_SIZE = 25
MAP_RADIUS = 10

tank_destroyer_shooting_directions = [
    [(0, -1), (0, -2), (0, -3)],
    [(1, -1), (2, -2), (3, -3)],
    [(1, 0), (2, 0), (3, 0)],
    [(0, 1), (0, 2), (0, 3)],
    [(-1, 1), (-2, 2), (-3, 3)],
    [(-1, 0), (-2, 0), (-3, 0)],
]


class Game:
    def __init__(self, use_gui, rl_player_index):
        self.max_turns = MAX_TURNS
        self.num_turns = 0
        self.hex_size = HEX_SIZE
        self.map_radius = MAP_RADIUS
        self.current_index = 0
        self.rl_player_index = rl_player_index
        self.current_tank_index = 0
        self.done = False
        self.use_gui = use_gui
        self.capture_area = [(0, 0), (1, 0), (-1, 1), (0, 1), (1, -1), (-1, 0), (0, -1)]
        self.light_repair_stations = [(-3, -3), (-3, 6), (6, -3)]
        self.heavy_repair_stations = [(-2, -2), (4, -2), (-2, 4)]
        self.catapults = [(3, -6), (-6, 3), (3, 3)]
        self.catapult_usage_history = []
        self.vehicles: list[Vehicle] = []
        self.players: list["Player"] = []
        layout = "obstacle_layout_stage4"
        self.obstacles = obstacle_layouts.get(layout)
        self.neutrality_matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    def setup(self):
        if self.use_gui:
            self.gui = Gui(
                self.hex_size,
                self.map_radius,
                self.vehicles,
                self.obstacles,
                self.capture_area,
                self.light_repair_stations,
                self.heavy_repair_stations,
                self.catapults,
            )

    def make_game_action(self, action: int = 0) -> int:
        """Make a game action for the current player and tank index. Return reward gained from the action."""
        total_reward = 0
        # Game ended by maximum turns
        if self.num_turns >= self.max_turns:
            total_reward += self.determine_winner_max_turns()
            self.done = True
            return total_reward

        # If first tank action of player, reset their row in neutrality matrix of what they attacked.
        if self.current_tank_index == 0:
            self.neutrality_matrix[self.current_index] = [0] * len(
                self.neutrality_matrix[self.current_index]
            )

        self.action_result, reward_gained_from_action = self.players[
            self.current_index
        ].make_action(self, self.current_tank_index, self.players, action)
        self.players[self.current_index].vehicles[
            self.current_tank_index
        ].gui_last_move = self.action_result
        total_reward += reward_gained_from_action

        self.current_tank_index += 1
        # Check if last tank of the player
        if self.current_tank_index == self.count_player_vehicles(
            self.players[self.current_index]
        ):  # The ammount of vehicles a player has
            self.num_turns += 1
            self.current_tank_index = 0
            # Respawn vehicles
            for vehicle in self.vehicles:
                if vehicle.hp <= 0:
                    vehicle.position = vehicle.spawn_position
                    vehicle.hp = vehicle.spawn_hp
            # Check if end of round, last player did their last turn
            if self.current_index + 1 == len(self.players):
                total_reward += self.end_of_round()

            # Update current player index
            self.current_index = (self.current_index + 1) % len(self.players)

        if self.use_gui:
            self.gui.screen.fill(WHITE)
            self.gui.draw_hexagonal_map(self)

        return total_reward

    def determine_winner_max_turns(self) -> int:
        """Determine the winner of the game based on the player with the most kill points. Return reward for the winner."""
        reward = -100
        kill_points_count = {}

        for player in self.players:
            kill_points_count[player] = player.kill_points

        max_kill_points = max(kill_points_count.values())

        players_with_max_kill_points = [
            player
            for player, points in kill_points_count.items()
            if points == max_kill_points
        ]

        if len(players_with_max_kill_points) > 1:
            for player in self.players:
                if (
                    player.index == self.rl_player_index
                    and player not in players_with_max_kill_points
                ):
                    return -REWARD_FOR_DRAW
                else:
                    return REWARD_FOR_DRAW
        else:
            # No draw, find the winner
            winner = max(kill_points_count, key=kill_points_count.get)
            if winner.index == self.rl_player_index:
                return REWARD_FOR_WIN
            else:
                return -REWARD_FOR_WIN
        return reward

    def end_of_round(self) -> int:
        """End of round, award points and check if game is over"""

        total_reward = 0
        total_reward += self.award_capture_points()

        winners_indexes = self.check_win(self.players)

        # If more than one winner
        if len(winners_indexes) > 1:
            print(f"Laimejo {winners_indexes}")
            self.done = True
            if (
                self.players[winners_indexes[0]].kill_points
                > self.players[winners_indexes[1]].kill_points
            ):
                if winners_indexes[0] == self.rl_player_index:
                    return REWARD_FOR_WIN
                else:
                    return -REWARD_FOR_WIN
            else:
                if winners_indexes[1] == self.rl_player_index:
                    return REWARD_FOR_WIN
                else:
                    return -REWARD_FOR_WIN

        elif len(winners_indexes) > 0:
            print(f"Laimejo {winners_indexes}")
            self.done = True
            if winners_indexes[0] == self.rl_player_index:
                return REWARD_FOR_WIN
            else:
                return -REWARD_FOR_WIN

        return total_reward

    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)

    # Place and add vehicles
    def place_vehicles(self, players: list["Player"]):
        rounded_amount_from_edge = round((self.map_radius + 1 - 5) / 2)
        firstVehicleIndex = 0
        secondVehicleIndex = 0
        thirdVehicleIndex = 0
        for q in range(-self.map_radius, self.map_radius + 1):
            r1 = max(-self.map_radius, -q - self.map_radius)
            r2 = min(self.map_radius, -q + self.map_radius)
            for r in range(r1, r2 + 1):
                # Place and add vehicle for Player1
                if (
                    self.map_radius - rounded_amount_from_edge
                    >= (-r)
                    >= rounded_amount_from_edge
                    and q == self.map_radius
                ):
                    if firstVehicleIndex == 0:
                        vehicle_to_add = Spg(players[0], (q, r), firstVehicleIndex)
                    elif firstVehicleIndex == 1:
                        vehicle_to_add = Light_Tank(
                            players[0], (q, r), firstVehicleIndex
                        )
                    elif firstVehicleIndex == 2:
                        vehicle_to_add = Heavy_Tank(
                            players[0], (q, r), firstVehicleIndex
                        )
                    elif firstVehicleIndex == 3:
                        vehicle_to_add = Medium_Tank(
                            players[0], (q, r), firstVehicleIndex
                        )
                    elif firstVehicleIndex == 4:
                        vehicle_to_add = Tank_Destroyer(
                            players[0], (q, r), firstVehicleIndex
                        )
                    players[0].vehicles.append(vehicle_to_add)
                    self.add_vehicle(vehicle_to_add)
                    firstVehicleIndex += 1
                # Place and add vehicle for Player2
                elif (
                    self.map_radius - rounded_amount_from_edge
                    >= -q
                    >= rounded_amount_from_edge
                    and self.map_radius - rounded_amount_from_edge
                    >= -r
                    >= rounded_amount_from_edge
                    and q + r == -self.map_radius
                ):
                    if secondVehicleIndex == 0:
                        vehicle_to_add = Spg(players[1], (q, r), secondVehicleIndex)
                    elif secondVehicleIndex == 1:
                        vehicle_to_add = Light_Tank(
                            players[1], (q, r), secondVehicleIndex
                        )
                    elif secondVehicleIndex == 2:
                        vehicle_to_add = Heavy_Tank(
                            players[1], (q, r), secondVehicleIndex
                        )
                    elif secondVehicleIndex == 3:
                        vehicle_to_add = Medium_Tank(
                            players[1], (q, r), secondVehicleIndex
                        )
                    elif secondVehicleIndex == 4:
                        vehicle_to_add = Tank_Destroyer(
                            players[1], (q, r), secondVehicleIndex
                        )
                    players[1].vehicles.append(vehicle_to_add)
                    self.add_vehicle(vehicle_to_add)
                    secondVehicleIndex += 1
                # Place and add vehicle for Player3
                elif (
                    r == self.map_radius
                    and self.map_radius - rounded_amount_from_edge
                    >= -q
                    >= rounded_amount_from_edge
                ):
                    if thirdVehicleIndex == 0:
                        vehicle_to_add = Spg(players[2], (q, r), thirdVehicleIndex)
                    elif thirdVehicleIndex == 1:
                        vehicle_to_add = Light_Tank(
                            players[2], (q, r), thirdVehicleIndex
                        )
                    elif thirdVehicleIndex == 2:
                        vehicle_to_add = Heavy_Tank(
                            players[2], (q, r), thirdVehicleIndex
                        )
                    elif thirdVehicleIndex == 3:
                        vehicle_to_add = Medium_Tank(
                            players[2], (q, r), thirdVehicleIndex
                        )
                    elif thirdVehicleIndex == 4:
                        vehicle_to_add = Tank_Destroyer(
                            players[2], (q, r), thirdVehicleIndex
                        )
                    players[2].vehicles.append(vehicle_to_add)
                    self.add_vehicle(vehicle_to_add)
                    thirdVehicleIndex += 1

    def check_collision(self, new_position: tuple[int, int]) -> bool:
        for vehicle in self.vehicles:
            if vehicle.position == new_position:
                print(f"Collision detected in position {new_position}")
                return True  # Collision detected
        if new_position in self.obstacles:
            return True  # Collision detected
        return False  # No collision

    def is_move_out_of_bounds(self, new_position):
        """Check if legal move"""
        if -10 <= new_position[0] <= 10 and -10 <= new_position[0] <= 10:
            return True  # Illegal move
        return False  # Legal move

    def move_vehicle(self, vehicle: Vehicle, new_position: tuple[int, int]) -> bool:
        """Move the vehicle to the new position if no collision occurs."""
        if not self.check_collision(new_position) and self.is_move_out_of_bounds(
            new_position
        ):
            vehicle.position = new_position
            if new_position in self.catapults:
                vehicle.shooting_range_bonus = True
            if new_position in self.heavy_repair_stations and (
                vehicle.type == HEAVY_TANK or vehicle.type == TANK_DESTROYER
            ):
                vehicle.hp = vehicle.spawn_hp
            if (
                new_position in self.light_repair_stations
                and vehicle.type == MEDIUM_TANK
            ):
                vehicle.hp = vehicle.spawn_hp
            return True  # Move successful
        # print("Couldn't move, another vehicle already in place")
        return False  # Collision occurred, unable to move

    def check_win(self, players: list["Player"]) -> list[int]:
        lst = [0, 0, 0]
        winners = []
        for vehicle in self.vehicles:
            lst[vehicle.owning_player.index] += vehicle.capture_points
        for player, points in zip(players, lst):
            player.capture_points = points
        for index, element in enumerate(lst):
            if element >= 5:  # capture points to win
                winners.append(index)
        return winners

    # I don't check for repair hexes at the end of a round on shoot, because I don't think there will be a situation of getting shot while at repair hex
    def shoot(self, vehicle: Vehicle, shooting_target: tuple[int, int]) -> int:
        reward_gained = 0

        if vehicle.type == TANK_DESTROYER:
            hit_vehicles = self.get_tank_destroyer_shot_vehicles(
                vehicle, shooting_target
            )
            for hit_vehicle in hit_vehicles:
                self.neutrality_matrix[vehicle.owning_player.index][
                    hit_vehicle.owning_player.index
                ] = 1
                hit_vehicle.hp -= vehicle.damage
                if vehicle.owning_player.index == self.rl_player_index:
                    reward_gained += REWARD_FOR_SUCCESSFULL_SHOT
                if hit_vehicle.hp <= 0:
                    if vehicle.owning_player.index == self.rl_player_index:
                        reward_gained = REWARD_FOR_SHOT_DESTROYING_TANK
                    vehicle.owning_player.kill_points += hit_vehicle.destruction_points
            if vehicle.position not in self.catapults:
                vehicle.shooting_range_bonus = False
            else:
                self.catapult_usage_history.append(vehicle.position)
            return reward_gained
        else:
            for target_vehicle in self.vehicles:
                if target_vehicle.position == shooting_target:
                    self.neutrality_matrix[vehicle.owning_player.index][
                        target_vehicle.owning_player.index
                    ] = 1

                    target_vehicle.hp -= vehicle.damage
                    if vehicle.owning_player.index == self.rl_player_index:
                        reward_gained = REWARD_FOR_SUCCESSFULL_SHOT

                    # if enemy tank destroyed, give points
                    if target_vehicle.hp <= 0:
                        if vehicle.owning_player.index == self.rl_player_index:
                            reward_gained = REWARD_FOR_SHOT_DESTROYING_TANK
                        vehicle.owning_player.kill_points += (
                            target_vehicle.destruction_points
                        )
                    if vehicle.position not in self.catapults:
                        vehicle.shooting_range_bonus = False
                    else:
                        self.catapult_usage_history.append(vehicle.position)
                    return reward_gained

    def get_tank_destroyer_shot_vehicles(
        self, vehicle: Vehicle, shooting_target
    ) -> list[Vehicle]:
        shot_vehicles = []
        shootable_hexes_by_direction_vector = vehicle.get_shootable_hexes()

        for one_direction_shootable_hexes in shootable_hexes_by_direction_vector:
            if one_direction_shootable_hexes[0] == shooting_target:
                vehicles_in_direction = []
                for hexagon in one_direction_shootable_hexes:
                    if hexagon in self.obstacles:
                        break
                    else:
                        for enemy_vehicle in self.vehicles:
                            if (
                                enemy_vehicle.position == hexagon
                                and enemy_vehicle.owning_player != vehicle.owning_player
                                and check_neutrality(
                                    vehicle.owning_player.index,
                                    enemy_vehicle.owning_player.index,
                                    self.neutrality_matrix,
                                )
                            ):
                                shot_vehicles.append(enemy_vehicle)
        return shot_vehicles

    def find_path_single_goal(
        self,
        vehicle: Vehicle,
        goal: tuple[int, int],
        map_size: int,
        hexes_to_avoid: list[tuple[int, int]] | None = None,
        max_iterations: int = 100,
    ) -> list[tuple[int, int]] | None:
        """
        Find the shortest path from vehicle position to the goal using A* algorithm.
        * `map_size` is map radius (in GameMap) used to check if coordinate is outside map.
        * `hex_map` and `vehicle_map` are used to check for obstacles and other vehicles in O(1).
        * `hexes_to_avoid` are initialized before calling this function, they will be treated like occupied coordinates
        (Vehicle may pass this position but will never end it's move action on it).

        Algorithm uses A* for path finding, but to find neighbor hexagons BFS is used first.
        Returns the shortest path or None, user should only use path[1] to make Move Action.
        For testing purposes whole shortest path is returned.
        """

        vehicle_position = vehicle.position
        if vehicle_position == goal:
            return None  # Vehicle is already at goal

        speed_points = vehicle.sp
        shortest_path_length = (
            3 * map_size * map_size
        )  # Max value (path length can't be longer than amount of hexes on map)
        shortest_path = None

        open_list = []
        closed_set = set()
        if hexes_to_avoid is not None:
            for coordinate in hexes_to_avoid:
                closed_set.add(coordinate)
        g_costs = {}
        parents = {}

        start = vehicle_position

        # Initialize start node
        g_costs[start] = 0
        f_cost = self.hex_distance(start, goal)
        heapq.heappush(open_list, (f_cost, start))

        iterations = 0
        while open_list and iterations < max_iterations:
            _, current = heapq.heappop(open_list)

            if current == goal:
                # Reconstruct the path
                path = [current]
                while current in parents:
                    current = parents[current]
                    path.append(current)
                path.reverse()
                if len(path) < shortest_path_length:
                    shortest_path_length = len(path)
                    shortest_path = path
            closed_set.add(current)
            neighbors = self.get_neighbors(
                current, speed_points, map_size
            )  # This will add neighbors to closed_set and return valid neighbors

            for neighbor in neighbors:
                # Skip if neighbor is specified as hex to avoid
                if hexes_to_avoid is not None and neighbor in hexes_to_avoid:
                    continue

                tentative_g_cost = g_costs[current] + 1
                if neighbor not in g_costs or tentative_g_cost < g_costs[neighbor]:
                    g_costs[neighbor] = tentative_g_cost
                    f_cost = tentative_g_cost + self.hex_distance(neighbor, goal)
                    heapq.heappush(open_list, (f_cost, neighbor))
                    parents[neighbor] = current
            iterations += 1
        return shortest_path

    def find_best_path_multiple_goals_non_vehicle(
        self,
        position: tuple[int, int],
        vehicle: Vehicle,
        goals: list[tuple[int, int]],
        vehicle_map: dict[tuple[int, int], Vehicle],
        map_size: int,
        hexes_to_avoid: list[tuple[int, int]] | None = None,
        max_iterations: int = 500,
    ) -> list[tuple[int, int]] | None:
        """
        Returns the shortest path or None, user should only use path[1] to make Move Action.
        For testing purposes whole shortest path is returned.
        """

        vehicle_position = position
        if vehicle_position in goals:
            return None  # Vehicle is already at goal
        speed_points = vehicle.sp

        parents = {}
        neighbors_heap = []
        heapq.heappush(neighbors_heap, (0, vehicle_position))

        visited = set()
        visited.add(vehicle_position)

        if hexes_to_avoid is not None:
            for coordinate in hexes_to_avoid:
                visited.add(coordinate)

        iteration = 0
        while neighbors_heap and iteration < max_iterations:
            distance, current = heapq.heappop(neighbors_heap)
            if current in goals:
                path = [current]
                while current in parents:
                    current = parents[current]
                    path.append(current)
                path.reverse()
                return path

            neighbors = self.get_neighbors_ignore_goals(
                vehicle_position, current, vehicle_map, goals, speed_points, map_size
            )
            for neighbor in neighbors:
                if neighbor not in visited:
                    heapq.heappush(neighbors_heap, (distance + 1, neighbor))
                    visited.add(neighbor)
                    parents[neighbor] = current
            iteration += 1
        return None

    def find_best_path_multiple_goals(
        self,
        vehicle: Vehicle,
        goals: list[tuple[int, int]],
        vehicle_map: dict[tuple[int, int], Vehicle],
        map_size: int,
        hexes_to_avoid: list[tuple[int, int]] | None = None,
        max_iterations: int = 500,
    ) -> list[tuple[int, int]] | None:
        """
        Returns the shortest path or None, user should only use path[1] to make Move Action.
        For testing purposes whole shortest path is returned.
        """
        vehicle_position = vehicle.position
        if vehicle_position in goals:
            return None  # Vehicle is already at goal

        speed_points = vehicle.sp

        parents = {}
        neighbors_heap = []
        heapq.heappush(neighbors_heap, (0, vehicle_position))

        visited = set()
        visited.add(vehicle_position)

        if hexes_to_avoid is not None:
            for coordinate in hexes_to_avoid:
                visited.add(coordinate)

        iteration = 0
        while neighbors_heap and iteration < max_iterations:
            distance, current = heapq.heappop(neighbors_heap)

            if current in goals:
                path = [current]
                while current in parents:
                    current = parents[current]
                    path.append(current)
                path.reverse()
                return path

            neighbors = self.get_neighbors_ignore_goals(
                vehicle_position, current, vehicle_map, goals, speed_points, map_size
            )

            for neighbor in neighbors:
                if neighbor not in visited:
                    heapq.heappush(neighbors_heap, (distance + 1, neighbor))
                    visited.add(neighbor)
                    parents[neighbor] = current
            iteration += 1
        return None

    def get_valid_immediate_neighbors(
        self, position: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """Get list of valid neighbors next to position coordinate (neighbors that are not OBSTACLES)!!!"""
        neighbors = []
        for direction in self.get_tiles_in_radius_true((0, 0), 1):
            neighbors.append((position[0] + direction[0], position[1] + direction[1]))
        res = []

        # Remove obstacles
        for neighbor in neighbors:
            if neighbor not in self.obstacles:
                res.append(neighbor)
        return res

    def get_neighbors(
        self,
        position: tuple[int, int],
        vehicle_map: dict[tuple[int, int], Vehicle],
        speed_points: int,
        map_size: int,
    ):
        """
        Get neighbor hexes based on vehicle speed. Only valid neighbors are returned.

        Returns and array of neighbors that vehicle can reach in one MoveAction.
        There are no coordinates that are occupied by another vehicle and obstacle.

        Algorithm uses BFS to find neighbors.
        """

        neighbors_heap = []
        heapq.heappush(neighbors_heap, (0, position))

        visited = set()  # Set of visited hex coordinates
        visited.add(position)

        max_dist = speed_points
        res = []
        while neighbors_heap:
            neighbor = heapq.heappop(neighbors_heap)
            if vehicle_map.get(neighbor[1]) is None:
                res.append(neighbor[1])  # Not occupied by vehicle

            if neighbor[0] == max_dist:
                continue  # Neighbors of this hexagon can't be reached with this tank's speed points

            current_neighbors = self.get_valid_immediate_neighbors(neighbor[1])
            for coordinate in current_neighbors:
                # Remove coordinates that are outside map
                if (
                    coordinate in visited
                    or coordinate[0] <= -map_size
                    or coordinate[0] >= map_size
                    or coordinate[1] <= -map_size
                    or coordinate[1] >= map_size
                ):
                    continue
                visited.add(coordinate)
                heapq.heappush(neighbors_heap, (neighbor[0] + 1, coordinate))
        return res

    def get_neighbors_ignore_goals(
        self,
        starting_vehicle_position: tuple[int, int],
        position: tuple[int, int],
        vehicle_map: dict[tuple[int, int], Vehicle],
        goals: list[tuple[int, int]],
        speed_points: int,
        map_size: int,
    ):
        """
        Get neighbor hexes based on vehicle speed. Only valid neighbors are returned.

        Returns and array of neighbors that vehicle can reach in one MoveAction.
        There are no coordinates that are occupied by another vehicle and obstacle.

        Algorithm uses BFS to find neighbors.
        """
        immediate_movement_hexes = cube_spiral(starting_vehicle_position, speed_points)
        neighbors_heap = []
        heapq.heappush(neighbors_heap, (0, position))

        visited = set()  # Set of visited hex coordinates
        visited.add(position)

        max_dist = speed_points
        res = []
        while neighbors_heap:
            neighbor = heapq.heappop(neighbors_heap)
            if vehicle_map.get(neighbor[1]) is None:
                res.append(neighbor[1])  # Not occupied by vehicle
            # If occupied but it's the goal, add it to neighbors
            elif neighbor[1] in goals and (neighbor[1] not in immediate_movement_hexes):
                res.append(neighbor[1])
            if neighbor[0] == max_dist:
                continue  # Neighbors of this hexagon can't be reached with this tank's speed points

            current_neighbors = self.get_valid_immediate_neighbors(neighbor[1])
            for coordinate in current_neighbors:
                # Remove coordinates that are outside map
                if (
                    coordinate in visited
                    or coordinate[0] <= -map_size
                    or coordinate[0] >= map_size
                    or coordinate[1] <= -map_size
                    or coordinate[1] >= map_size
                ):
                    continue
                visited.add(coordinate)
                heapq.heappush(neighbors_heap, (neighbor[0] + 1, coordinate))
        return res

    def hex_distance(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        return (
            abs(a[0] - b[0]) + abs(a[0] + a[1] - b[0] - b[1]) + abs(a[1] - b[1])
        ) // 2

    def count_player_vehicles(self, player: "Player") -> int:
        count = 0
        for vehicle in self.vehicles:
            if vehicle.owning_player == player:
                count += 1
        return count

    # Award and remove capture points from vehicles
    def award_capture_points(self) -> int:
        reward_gained = 0
        players_in_capture_area = set()
        for vehicle in self.vehicles:
            if vehicle.position in self.capture_area:
                players_in_capture_area.add(vehicle.owning_player.index)
            else:
                vehicle.capture_points = 0
        if len(players_in_capture_area) < 3:
            for vehicle in self.vehicles:
                if vehicle.position in self.capture_area:
                    vehicle.capture_points += 1
                    if vehicle.owning_player.index == 0:
                        reward_gained += 30
                else:
                    vehicle.capture_points = 0
        return reward_gained

    def get_tank_destroyer_shootable_tiles(
        self, center_coords: tuple[int, int]
    ) -> list[tuple[int, int]]:
        center_q, center_r = center_coords
        tiles = []
        direction_blocked = False
        for direction in tank_destroyer_shooting_directions:
            direction_blocked = False
            for tile in direction:
                hexagon = (tile[0] + center_q, tile[1] + center_r)
                if (hexagon) in self.obstacles:
                    direction_blocked = True
                    continue
                elif direction_blocked == False:
                    tiles.append(hexagon)
        return tiles

    def get_tank_destroyer_shot_results(
        self, center_coords: tuple[int, int], shoot_tile: tuple[int, int]
    ) -> list[tuple[int, int]]:
        center_q, center_r = center_coords
        tiles = []
        hit_tiles = []
        tempdirection = []
        for direction in tank_destroyer_shooting_directions:
            tempdirection = direction
            found_obstacle = False
            for tile in direction:
                hexagon = (tile[0] + center_q, tile[1] + center_r)
                if hexagon in self.obstacles:
                    found_obstacle = True
                if hexagon == shoot_tile and found_obstacle == False:
                    for shooting in tempdirection:
                        hexagon = (tile[0] + center_q, tile[1] + center_r)
                        if hexagon in self.obstacles:
                            return hit_tiles
                        hit_tiles.append(hexagon)
                    return hit_tiles
        return []

    def get_tiles_in_radius(
        self, center_coords: tuple[int, int], radius: int
    ) -> list[tuple[int, int]]:
        center_q, center_r = center_coords
        tiles = []
        bad_tiles = []
        for dq in range(-radius, radius + 1):
            for dr in range(max(-radius, -dq - radius), min(radius, -dq + radius) + 1):
                if abs(dq) + abs(dr) + abs(-dq - dr) <= radius:
                    bad_tiles.append((center_q + dq, center_r + dr))

        for dq in range(-radius, radius + 1):
            for dr in range(max(-radius, -dq - radius), min(radius, -dq + radius) + 1):
                if abs(dq) + abs(dr) + abs(-dq - dr) >= radius:
                    tiles.append((center_q + dq, center_r + dr))
        true_tiles = [x for x in tiles if x not in bad_tiles]
        return true_tiles

    def get_tiles_in_radius_true(
        self, center_coords: tuple[int, int], radius: int
    ) -> list[tuple[int, int]]:
        center_q, center_r = center_coords
        tiles = []

        for dq in range(-radius, radius + 1):
            for dr in range(max(-radius, -dq - radius), min(radius, -dq + radius) + 1):
                if abs(dq) + abs(dr) + abs(-dq - dr) <= radius:
                    tiles.append((center_q + dq, center_r + dr))

        for dq in range(-radius, radius + 1):
            for dr in range(max(-radius, -dq - radius), min(radius, -dq + radius) + 1):
                if abs(dq) + abs(dr) + abs(-dq - dr) >= radius:
                    tiles.append((center_q + dq, center_r + dr))
        return tiles
