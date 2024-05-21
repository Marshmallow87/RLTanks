import pygame
import math
import game
from constants import *


class Gui:
    def __init__(
        self,
        hex_size,
        map_radius,
        vehicles,
        obstacles,
        capture_area,
        light_repair_stations,
        heavy_repair_stations,
        catapults,
    ):
        self.hex_size = hex_size
        self.map_radius = map_radius
        self.vehicles = vehicles
        self.obstacles = obstacles
        self.capture_area = capture_area
        self.light_repair_stations = light_repair_stations
        self.heavy_repair_stations = heavy_repair_stations
        self.catapults = catapults
        self.hex_images = {}
        self.screen_width = int(3 / 2 * self.hex_size * (2 * self.map_radius + 1))
        self.screen_height = int(
            math.sqrt(3) * self.hex_size * (2 * self.map_radius + 1)
        )
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2

        pygame.init()
        self.screen = pygame.display.set_mode((1920, 1080))
        pygame.display.set_caption("Hexagonal Map")
        self.font = pygame.font.Font(None, 36)
        self.screen.fill(WHITE)
        self.load_images()
        pygame.display.flip()
        self.load_images()

    def load_images(self):
        spg_image = pygame.image.load("Images/SPG.png").convert_alpha()
        light_tank_image = pygame.image.load("Images/Light_Tank.png").convert_alpha()
        heavy_tank_image = pygame.image.load("Images/Heavy_Tank.png").convert_alpha()
        medium_tank_image = pygame.image.load("Images/Medium_Tank.png").convert_alpha()
        tank_destroyer_image = pygame.image.load(
            "Images/Tank_Destroyer.png"
        ).convert_alpha()

        self.catapult_image = pygame.image.load("Images/Catapult.png").convert_alpha()
        self.light_repair_station_image = pygame.image.load(
            "Images/Light_Repair_Plant.png"
        ).convert_alpha()
        self.heavy_repair_station_image = pygame.image.load(
            "Images/Heavy_Repair_Plant.png"
        ).convert_alpha()

        self.hex_images[SPG] = spg_image
        self.hex_images[LIGHT_TANK] = light_tank_image
        self.hex_images[HEAVY_TANK] = heavy_tank_image
        self.hex_images[MEDIUM_TANK] = medium_tank_image
        self.hex_images[TANK_DESTROYER] = tank_destroyer_image

    def convert_image_color(self, image, color):

        # Resize image to fit within hexagon
        converted_image = pygame.transform.scale(
            image, (int(self.hex_size) + 10, int(self.hex_size) + 10)
        )
        colored_surface = pygame.Surface(converted_image.get_size(), pygame.SRCALPHA)
        colored_surface.fill(color)

        # Blit the colored surface onto the transparent image using a blending mode
        colored_image = converted_image.copy()
        colored_image.blit(
            colored_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT
        )
        return colored_image

    def draw_hexagon(self, center_x, center_y, q, r, r1, r2, players):

        rounded_ammount_from_edge = round((self.map_radius + 1 - 5) / 2)
        points = []

        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.radians(angle_deg)
            x = center_x + self.hex_size * math.cos(angle_rad)
            y = center_y + self.hex_size * math.sin(angle_rad)
            points.append((x, y))

        pygame.draw.polygon(self.screen, YELLOW, points)

        for light_repair_station in self.light_repair_stations:
            if light_repair_station == (q, r):
                pygame.draw.polygon(self.screen, DARKER_YELLOW, points)
                pygame.draw.polygon(self.screen, BLACK, points, 2)
                self.draw_image(self.screen, (q, r), self.light_repair_station_image)
        for heavy_repair_station in self.heavy_repair_stations:
            if heavy_repair_station == (q, r):
                pygame.draw.polygon(self.screen, DARKER_YELLOW, points)
                pygame.draw.polygon(self.screen, BLACK, points, 2)
                self.draw_image(self.screen, (q, r), self.heavy_repair_station_image)
        for catapult in self.catapults:
            if catapult == (q, r):
                pygame.draw.polygon(self.screen, DARKER_YELLOW, points)
                pygame.draw.polygon(self.screen, BLACK, points, 2)
                self.draw_image(self.screen, (q, r), self.catapult_image)

        for vehicle in self.vehicles:
            if vehicle.position == (q, r):
                if vehicle.type == SPG:
                    image = self.hex_images.get(SPG)
                elif vehicle.type == LIGHT_TANK:
                    image = self.hex_images.get(LIGHT_TANK)
                elif vehicle.type == HEAVY_TANK:
                    image = self.hex_images.get(HEAVY_TANK)
                elif vehicle.type == MEDIUM_TANK:
                    image = self.hex_images.get(MEDIUM_TANK)
                elif vehicle.type == TANK_DESTROYER:
                    image = self.hex_images.get(TANK_DESTROYER)
                if vehicle.owning_player.index == 0:
                    colored_image = self.convert_image_color(
                        image, vehicle.owning_player.color
                    )
                elif vehicle.owning_player.index == 1:
                    colored_image = self.convert_image_color(
                        image, vehicle.owning_player.color
                    )
                else:
                    colored_image = self.convert_image_color(
                        image, vehicle.owning_player.color
                    )
                image_rect = colored_image.get_rect(center=(center_x, center_y))
                self.screen.blit(colored_image, image_rect)

        if (
            self.map_radius - rounded_ammount_from_edge
            >= (-r)
            >= rounded_ammount_from_edge
            and q == self.map_radius
        ):
            # Blit image onto hexagon
            pygame.draw.polygon(self.screen, (255, 0, 0), points, 2)
        elif (
            self.map_radius - rounded_ammount_from_edge
            >= -q
            >= rounded_ammount_from_edge
            and self.map_radius - rounded_ammount_from_edge
            >= -r
            >= rounded_ammount_from_edge
            and q + r == -self.map_radius
        ):
            pygame.draw.polygon(self.screen, (0, 255, 0), points, 2)
        elif (
            r == self.map_radius
            and self.map_radius - rounded_ammount_from_edge
            >= -q
            >= rounded_ammount_from_edge
        ):
            pygame.draw.polygon(self.screen, (0, 0, 255), points, 2)
        elif (q, r) in self.capture_area:
            pygame.draw.polygon(self.screen, (0, 255, 255), points, 2)
        else:
            if (q, r) in self.obstacles:
                pygame.draw.polygon(self.screen, (0, 120, 125), points)

            pygame.draw.polygon(self.screen, BLACK, points, 2)

        draw_coordinates = True
        if draw_coordinates:
            # Draw coordinates
            font = pygame.font.Font(None, 20)
            text = font.render(f"{q},{r}", True, BLACK)
            text_rect = text.get_rect(center=(center_x, center_y))
            self.screen.blit(text, text_rect)

    def draw_image(self, surface: pygame.Surface, location, image):
        center_x, center_y = self.calculate_map_position_from_coordinates(location)

        colored_image = self.convert_image_color(image, BLACK)
        image_rect = colored_image.get_rect(center=(center_x, center_y))
        surface.blit(colored_image, image_rect)

    def calculate_map_position_from_coordinates(self, location):
        center_x = self.center_x + 3 / 2 * self.hex_size * location[0]
        center_y = self.center_y + math.sqrt(3) * self.hex_size * (
            location[1] + location[0] / 2
        )

        return center_x, center_y

    def draw_hexagonal_map(self, game):
        for q in range(-self.map_radius, self.map_radius + 1):
            r1 = max(-self.map_radius, -q - self.map_radius)
            r2 = min(self.map_radius, -q + self.map_radius)
            for r in range(r1, r2 + 1):
                x = self.center_x + 3 / 2 * self.hex_size * q
                y = self.center_y + math.sqrt(3) * self.hex_size * (r + q / 2)
                self.draw_hexagon(x, y, q, r, r1, r2, game.players)
        self.draw_extra_info(
            game.players,
            game.vehicles,
            game.neutrality_matrix,
            game.num_turns,
            game.action_result,
            game.current_index,
            game.current_tank_index,
        )

    def draw_extra_info(
        self,
        players,
        vehicles,
        neutrality_matrix,
        num_turns,
        action_result,
        current_index,
        current_tank_index,
    ):
        # Render player points on the right side of the screen
        text_y = 10
        for player in players:
            text = self.font.render(
                f"{player.name} has: {player.kill_points} kill points and {player.capture_points} capture points",
                True,
                player.color,
            )
            text_rect = text.get_rect(right=self.screen.get_width() - 10, top=text_y)
            self.screen.blit(text, text_rect)
            text_y += 40
            for vehicle in vehicles:
                if vehicle.owning_player == player:
                    text = self.font.render(
                        f"Last move: {vehicle.gui_last_move} || {vehicle.type} at {vehicle.position} position. Hp: {vehicle.hp} CP: {vehicle.capture_points}",
                        True,
                        player.color,
                    )
                    text_rect = text.get_rect(
                        right=self.screen.get_width() - 10, top=text_y
                    )
                    self.screen.blit(text, text_rect)
                    if (
                        players[current_index] == player
                        and vehicle.owning_player == player
                        and vehicle.vehicleIndex == current_tank_index
                    ):
                        text = self.font.render(f"Current tank", True, player.color)
                        text_rect = text.get_rect(
                            right=self.screen.get_width() - 980, top=text_y
                        )
                        self.screen.blit(text, text_rect)
                    text_y += 40
        text = self.font.render(f"Last action result: {action_result}", True, BLACK)
        text_rect = text.get_rect(right=self.screen.get_width() - 600, top=text_y)
        self.screen.blit(text, text_rect)

        neutrality_text = text_y + 50

        for row in neutrality_matrix:
            text = self.font.render(f"{row}", True, BLACK)
            text_rect = text.get_rect(
                right=self.screen.get_width() - 650, top=neutrality_text
            )
            self.screen.blit(text, text_rect)
            neutrality_text += 30

        text = self.font.render(f"turn: {num_turns}", True, BLACK)
        text_rect = text.get_rect(right=self.screen.get_width() - 650, top=text_y + 150)
        self.screen.blit(text, text_rect)

        pygame.display.flip()
