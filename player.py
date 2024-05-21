from constants import *
from hex_utility import *
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game
    from vehicle import Vehicle
REWARD_FOR_CORRECT_MOVE = 2


class Player:
    def __init__(self, name, color, index):
        self.name = name
        self.points = 0
        self.kill_points = 0
        self.capture_points = 0
        self.color = color
        self.index = index
        self.vehicles = []
        self.enemies_to_be_shot_dead = []
        self.tiles_reserved = []

    def make_action(
        self, map: "Game", current_tank_index: int, players: list["Player"], action: int
    ) -> tuple[str, int]:
        """Action works by first going through all tanks and reserving moves."""
        vehicle_map = {}
        for vehicle in map.vehicles:
            vehicle_map[vehicle.position] = vehicle

        if current_tank_index == 0:
            # Reset reserved moves
            for vehicle in self.vehicles:
                vehicle.reserved_move = ()

            # Eeserve capture and shooting moves
            self.any_vehicles_can_shoot(map)
            self.any_vehicles_can_capture_move(
                map, current_tank_index, vehicle_map, players
            )

        for vehicle in self.vehicles:
            if vehicle.vehicleIndex == current_tank_index:
                if len(vehicle.reserved_move) != 0:
                    if vehicle.reserved_move[0] == "move":
                        map.move_vehicle(vehicle, vehicle.reserved_move[1])
                        return "Tank moved to position " + str(vehicle.position), 0
                    else:
                        shooting_target = vehicle.reserved_move[1]
                        map.shoot(vehicle, vehicle.reserved_move[1])
                        return "Tank shot at " + str(shooting_target), 0
                return "Tank didn't move from position " + str(vehicle.position), 0

    def any_vehicles_can_capture_move(
        self,
        map: "Game",
        current_tank_index: int,
        vehicle_map: set[tuple[int, int]],
        players: list["Player"],
    ):
        "Reserve moves for capturing points."
        tiles_reserved = []
        for vehicle in self.vehicles:
            if vehicle.position in map.capture_area:
                continue
            enemy_fire_hexagons = []
            for enemy_vehicle in map.vehicles:
                if enemy_vehicle.owning_player.index != vehicle.owning_player.index:
                    if enemy_vehicle.type == TANK_DESTROYER:
                        enemy_fire_hexagons += map.get_tank_destroyer_shootable_tiles(
                            enemy_vehicle.position
                        )
                    else:
                        enemy_fire_hexagons += map.get_tiles_in_radius(
                            enemy_vehicle.position, enemy_vehicle.shooting_range
                        )

            immediate_movement_tiles = map.get_tiles_in_radius_true(
                vehicle.position, vehicle.sp
            )
            enemy_fire_hexagon_tiles = [
                x for x in enemy_fire_hexagons if x in immediate_movement_tiles
            ]

            lst = [0, 0, 0]
            for all_vehicle in map.vehicles:
                lst[all_vehicle.owning_player.index] += all_vehicle.capture_points

            for player, points in zip(players, lst):
                player.capture_points = points

            for index, element in enumerate(lst):
                if element >= 3 and index != self.index:
                    enemy_fire_hexagon_tiles = []

            if len(tiles_reserved) > 0:
                enemy_fire_hexagon_tiles += tiles_reserved

            lol = map.find_best_path_multiple_goals(
                vehicle, map.capture_area, vehicle_map, 10, enemy_fire_hexagon_tiles
            )

            if lol is not None:
                if len(lol) >= 2 and len(vehicle.reserved_move) == 0:
                    temporary = lol[1]
                    tiles_reserved.append(lol[1])
                    vehicle.reserved_move = ("move", lol[1])

    def any_vehicles_can_shoot(self, map: "Game"):
        "Reserve moves for shooting."
        enemies_to_be_shot_dead = []
        for vehicle in self.vehicles:
            move_to_reserve = None
            shooting_target_position = None
            shooting_target_vehicle = None
            poguus = vehicle.get_shootable_vehicles(
                map.obstacles, map.vehicles, map.neutrality_matrix
            )

            for list in poguus:
                # If 2 or more vehicles to be hit, shoot there
                if len(list[1]) > 1:
                    shooting_target_position = list[0]
                    break
                for target_vehicle in list[1]:
                    # If no target yet
                    if shooting_target_position == None:
                        shooting_target_position = list[0]
                        shooting_target_vehicle = target_vehicle
                    # If current in capture area and old not in capture area.
                    elif (target_vehicle.position in map.capture_area) and not (
                        shooting_target_position in map.capture_area
                    ):
                        shooting_target_position = list[0]
                        shooting_target_vehicle = target_vehicle
                    # If old not in capture area, check hp. Choose always ones with lower
                    elif not (shooting_target_position in map.capture_area) and (
                        shooting_target_vehicle.hp > target_vehicle.hp
                    ):
                        shooting_target_position = list[0]
                        shooting_target_vehicle = target_vehicle
                    # If both in capture area check hp
                    elif (
                        (shooting_target_position in map.capture_area)
                        and (target_vehicle.position in map.capture_area)
                        and (shooting_target_vehicle.hp > target_vehicle.hp)
                    ):
                        shooting_target_position = list[0]
                        shooting_target_vehicle = target_vehicle
            if shooting_target_position != None:
                move_to_reserve = ("shoot", shooting_target_position)
                vehicle.reserved_move = move_to_reserve
                if len(list[1]) == 1:
                    if shooting_target_vehicle.hp <= vehicle.damage:
                        enemies_to_be_shot_dead.append(shooting_target_vehicle)
                else:
                    for hittable_target_vehicle in list[1]:
                        if hittable_target_vehicle.hp <= vehicle.damage:
                            enemies_to_be_shot_dead.append(hittable_target_vehicle)


class ReinforcementLearningPlayer(Player):
    def make_action(
        self, map: "Game", current_tank_index: int, players: list["Player"], action: int
    ) -> tuple[str, int]:
        """Makes an action based on model"""
        if action != 36:  # move
            directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1),
                (2, -1), (1, -2), (-1, -1), (-2, 0), (-1, 2), (1, 1),
                (2, 0), (2, -2), (0, -2), (-2, 1), (-2, 2), (0, 2),
                (0,-3), (1,-3), (2,-3), (3,-3), (3,-2), (3,-1), (3, 0), (2, 1), (1,2), (0, 3), (-1, 3), (-2, 3), (-3, 3), (-3,2), (-3,1), (-3, 0), (-2, -1), (-1,-2)]

            directions2Tile = [
                (2, -1), (1, -2), (-1, -1), (-2, 0), (-1, 2), (1, 1),
                (2, 0), (2, -2), (0, -2), (-2, 1), (-2, 2), (0, 2)]
            
            directions3Tile = [
                (0,-3), (1,-3), (2,-3), (3,-3), (3,-2), (3,-1), (3, 0), (2, 1), (1,2), (0, 3), (-1, 3), (-2, 3), (-3, 3), (-3,2), (-3,1), (-3, 0), (-2, -1), (-1,-2)]
            

            directions_mapping = {
                direction: index for index, direction in enumerate(directions)
            }
            reverse_directions_mapping = {
                index: direction for direction, index in directions_mapping.items()
            }

            for vehicle in map.vehicles:
                if (
                    vehicle.owning_player == self
                    and vehicle.vehicleIndex == current_tank_index
                ):
                    old_position = vehicle.position

                    # Move action
                    action = int(action)  # So load works
                    direction = reverse_directions_mapping.get(action)

                    if direction in directions2Tile and vehicle.sp < 2:
                        return "Tank didn't move, illegal action", -(
                            REWARD_FOR_CORRECT_MOVE
                        )
                    if direction in directions3Tile and vehicle.sp < 3:
                        return "Tank didn't move, illegal action", -(
                            REWARD_FOR_CORRECT_MOVE
                        )

                    place_to_move_to = (
                        vehicle.position[0] + direction[0],
                        vehicle.position[1] + direction[1],
                    )

                    distance_before = map.hex_distance(vehicle.position, (0, 0))
                    map.move_vehicle(vehicle, place_to_move_to)
                    distance_after = map.hex_distance(vehicle.position, (0, 0))
                    new_position = vehicle.position

                    if distance_after < distance_before:
                        if distance_before - distance_after == 3:
                            return (
                                "Tank moved to position " + str(vehicle.position),
                                REWARD_FOR_CORRECT_MOVE * 10,
                            )
                        elif distance_before - distance_after == 2:
                            return (
                                "Tank moved to position " + str(vehicle.position),
                                REWARD_FOR_CORRECT_MOVE * 5,
                            )
                        else:
                            return (
                                "Tank moved to position " + str(vehicle.position),
                                REWARD_FOR_CORRECT_MOVE * 2,
                            )
                    elif distance_after > distance_before:
                        return "Tank moved to position " + str(vehicle.position), -(
                            REWARD_FOR_CORRECT_MOVE * 4
                        )
                    elif old_position == new_position:
                        return "Tank moved to position " + str(vehicle.position), -(
                            REWARD_FOR_CORRECT_MOVE * 0.5
                        )
                    else:
                        return (
                            "Tank moved to position " + str(vehicle.position),
                            (REWARD_FOR_CORRECT_MOVE) * 0.1,
                        )
        # shoot
        else:
            for vehicle in map.vehicles:
                if (
                    vehicle.owning_player == self
                    and vehicle.vehicleIndex == current_tank_index
                ):
                    shooting_target_position = None
                    shooting_target_vehicle = None
                    poguus = vehicle.get_shootable_vehicles(
                        map.obstacles, map.vehicles, map.neutrality_matrix
                    )

                    for list in poguus:
                        # If 2 or more vehicles to be hit, shoot there
                        if len(list[1]) > 1:
                            shooting_target_position = list[0]
                            break
                        for target_vehicle in list[1]:
                            # If no target yet
                            if shooting_target_position == None:
                                shooting_target_position = list[0]
                                shooting_target_vehicle = target_vehicle
                            # If current in capture area and old not in capture area.
                            elif (target_vehicle.position in map.capture_area) and not (
                                shooting_target_position in map.capture_area
                            ):
                                shooting_target_position = list[0]
                                shooting_target_vehicle = target_vehicle
                            # If old not in capture area, check hp. Choose always ones with lower
                            elif not (
                                shooting_target_position in map.capture_area
                            ) and (shooting_target_vehicle.hp > target_vehicle.hp):
                                shooting_target_position = list[0]
                                shooting_target_vehicle = target_vehicle
                            # If both in capture area check hp
                            elif (
                                (shooting_target_position in map.capture_area)
                                and (target_vehicle.position in map.capture_area)
                                and (shooting_target_vehicle.hp > target_vehicle.hp)
                            ):
                                shooting_target_position = list[0]
                                shooting_target_vehicle = target_vehicle

                    if shooting_target_position != None:
                        reward_gained_from_action = map.shoot(
                            vehicle, shooting_target_position
                        )
                        return (
                            "Tank shot at " + str(shooting_target_position),
                            reward_gained_from_action,
                        )

            return "Nothing to shoot", 0
