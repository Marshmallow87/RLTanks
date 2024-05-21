import pygame

WHITE = pygame.Color("white")
BLACK = pygame.Color("black")
RED = pygame.Color("red")
GREEN = pygame.Color("green")
BLUE = pygame.Color("blue")
LIGHT_BLUE = pygame.Color(173, 216, 230)
GRAY = pygame.Color(105, 105, 105)  # Dim gray
LIGHT_GREEN = pygame.Color(144, 238, 144)
DARK_GREEN = pygame.Color(0, 150, 0)  # Not too dark
YELLOW = pygame.Color(255, 250, 205)
DARKER_YELLOW = pygame.Color(255, 230, 100)

SPG = "SPG"
LIGHT_TANK = "Light_Tank"
HEAVY_TANK = "Heavy Tank"
MEDIUM_TANK = "Medium Tank"
TANK_DESTROYER = "Tank Destroyer"


obstacle_layouts = {
    "obstacle_layout_full": [
        (0,-2), (0,-3), (0,-5), (0,-6), (0,-7), (0,-8), (0,-9), (0,-10),
        (2,-2), (3,-3), (5,-5), (6,-6), (7,-7), (8,-8), (9,-9), (10,-10),
        (0,2), (0,3), (0,5), (0,6), (0,7), (0,8), (0,9), (0,10),
        (-2,2), (-3,3), (-5,5), (-6,6), (-7,7), (-8,8), (-9,9), (-10,10),
        (-2,0), (-3,0), (-5,0), (-6,0), (-7,0), (-8,0), (-9,0), (-10,0),
        (2,0), (3,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)
    ],
        "obstacle_layout_sparse": [
        (0,-2), (0,-3),
        (2,-2), (3,-3), 
        (0,2), (0,3),
        (-2,2), (-3,3),
        (-2,0), (-3,0),
        (2,0), (3,0)
    ],
        "obstacle_layout_stage4": [
        (-5,-3), (-3,-5),
        (-5,8), (-3,8), 
        (8,-3), (8,-5)
    ],
        "obstacle_layout_unfair_testing": [
        (10,-2), (9,-2), (9,-4), (9,-6), (9,-7), (8,-2), (7,-2), (7,-3), (7,-4), (7,-5), (7,-6), (7,-7),(7,-8),
        (2,-2), (3,-3), 
        (0,2), (0,3),
        (-2,2), (-3,3),
        (-2,0), (-3,0),
        (2,0), (3,0)
    ]
}
