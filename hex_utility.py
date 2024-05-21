# used to get neighbor values
CUBE_DIRECTIONS = [
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
]


def hexagon_neighbor(hexagon, direction: int):
    """
    Get Neighbor coordinate as `Vector2` using direction
    """
    val1 = hexagon[0] + CUBE_DIRECTIONS[direction][0]
    val2 = hexagon[1] + CUBE_DIRECTIONS[direction][1]
    return (val1, val2)


def cube_ring(center, k):
    """
    Get all hexagons that are part of ring formed around center hexagon
    """
    results = []
    temp = (CUBE_DIRECTIONS[4][0], CUBE_DIRECTIONS[4][1])
    scaled = (temp[0] * k, temp[1] * k)
    hexagon = (center[0] + scaled[0], center[1] + scaled[1])

    for i in range(0, 6):
        for j in range(0, k):
            results.append(hexagon)
            hexagon = hexagon_neighbor(hexagon, i)
    return results


def cube_spiral(center, radius):
    """
    Get All neighbor hexagons around center
    """
    results = []
    for i in range(1, radius + 1):
        results.extend(cube_ring(center, i))
    return results


def check_neutrality(
    attacking_player,
    target_player,
    matrix: list[list[int]],
) -> bool:
    """Check if attacker vehicle can attack target vehicle based on attack matrix"""
    gotAttackedByTarget = matrix[target_player][attacking_player]
    targetGotAttacked = False
    for list in matrix:
        if list[target_player] == 1:
            targetGotAttacked = True
    return gotAttackedByTarget == 1 or (not targetGotAttacked)
