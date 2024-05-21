from constants import *
from hex_utility import *


class Vehicle:
    def __init__(
        self,
        owning_player,
        v_type,
        spawn_position,
        vehicleIndex,
        hp,
        sp,
        damage,
        destruction_points,
        shooting_range,
    ):
        self.owning_player = owning_player
        self.vehicleIndex = vehicleIndex
        self.type = v_type
        self.position = spawn_position
        self.spawn_position = spawn_position
        self.hp = hp
        self.spawn_hp = hp
        self.sp = sp
        self.damage = damage
        self.destruction_points = destruction_points
        self.shooting_range = shooting_range
        self.capture_points = 0
        self.reserved_move = ()
        self.gui_last_move = ()  # Only for GUI
        self.shooting_range_bonus = False

    def get_shootable_hexes(self, position=None):
        if position == None:
            position = self.position
        hexes = cube_ring(position, self.shooting_range)
        if self.shooting_range_bonus:
            hexes.extend(cube_ring(position, self.shooting_range + 1))
        list = []
        list.append(hexes)
        return list

    def get_shootable_vehicles(self, obstacles, vehicles, attack_matrix, position=None):
        results = []
        if position:
            target_lists = self.get_shootable_hexes(position)
        else:
            target_lists = self.get_shootable_hexes()
        for targets in target_lists:
            for shootable_hex in targets:
                for enemy_vehicle in vehicles:
                    if (
                        enemy_vehicle.position == shootable_hex
                        and enemy_vehicle.owning_player != self.owning_player
                        and check_neutrality(
                            self.owning_player.index,
                            enemy_vehicle.owning_player.index,
                            attack_matrix,
                        )
                    ):
                        results.append((enemy_vehicle.position, [enemy_vehicle]))
        return results


class Light_Tank(Vehicle):
    def __init__(self, owning_player, spawn_position, vehicleIndex):
        super().__init__(
            owning_player, LIGHT_TANK, spawn_position, vehicleIndex, 1, 3, 1, 1, 2
        )


class Medium_Tank(Vehicle):
    def __init__(self, owning_player, spawn_position, vehicleIndex):
        super().__init__(
            owning_player, MEDIUM_TANK, spawn_position, vehicleIndex, 2, 2, 1, 2, 2
        )


class Heavy_Tank(Vehicle):
    def __init__(self, owning_player, spawn_position, vehicleIndex):
        super().__init__(
            owning_player, HEAVY_TANK, spawn_position, vehicleIndex, 3, 1, 1, 3, 1
        )

    def get_shootable_hexes(self):
        hexes = cube_ring(self.position, self.shooting_range)
        hexes = cube_ring(self.position, self.shooting_range + 1)
        if self.shooting_range_bonus:
            hexes.extend(cube_ring(self.position, self.shooting_range + 1 + 1))
        list = []
        list.append(hexes)
        return list


class Tank_Destroyer(Vehicle):
    def __init__(self, owning_player, spawn_position, vehicleIndex):
        super().__init__(
            owning_player, TANK_DESTROYER, spawn_position, vehicleIndex, 2, 1, 1, 2, 3
        )

    def get_shootable_hexes(self, position=None):
        if position == None:
            position = self.position
        range_buff = 0
        if self.shooting_range_bonus:
            range_buff = 1
        res = [[] for i in range(6)]
        for radius in range(1, self.shooting_range + 1 + range_buff):
            direction_values = self.star_shape(position, radius)
            for i in range(6):
                res[i].append(direction_values[i])
        return res

    def star_shape(self, position, radius: int):
        return [
            (position[0], position[1] - radius),
            (position[0], position[1] + radius),
            (position[0] - radius, position[1]),
            (position[0] - radius, position[1] + radius),
            (position[0] + radius, position[1]),
            (position[0] + radius, position[1] - radius),
        ]

    def get_shootable_vehicles(self, obstacles, vehicles, attack_matrix, position=None):
        results = []
        if position:
            shootable_hexes_by_direction_vector = self.get_shootable_hexes(position)
        else:
            shootable_hexes_by_direction_vector = self.get_shootable_hexes()

        for one_direction_shootable_hexes in shootable_hexes_by_direction_vector:
            vehicles_in_direction = []
            for hexagon in one_direction_shootable_hexes:
                if hexagon in obstacles:
                    break
                else:
                    for enemy_vehicle in vehicles:
                        if (
                            enemy_vehicle.position == hexagon
                            and enemy_vehicle.owning_player != self.owning_player
                            and check_neutrality(
                                self.owning_player.index,
                                enemy_vehicle.owning_player.index,
                                attack_matrix,
                            )
                        ):
                            vehicles_in_direction.append(enemy_vehicle)
            if vehicles_in_direction:
                results.append(
                    (one_direction_shootable_hexes[0], vehicles_in_direction)
                )
        return results


class Spg(Vehicle):
    def __init__(self, owning_player, spawn_position, vehicleIndex):
        super().__init__(
            owning_player, SPG, spawn_position, vehicleIndex, 1, 1, 1, 1, 3
        )
