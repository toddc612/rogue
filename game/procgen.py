from __future__ import annotations

from typing import Iterator, List, Tuple

import tcod

import game.engine
import game.entity
import game.game_map

WALL = 0
FLOOR = 1


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """Return the center coordinates of the room."""
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2

    @property
    def inner(self) -> Tuple[slice, slice]:
        """Return the inner area of this room as a 2D array index."""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """Return True if this room overlaps with another RectangularRoom."""
        return self.x1 <= other.x2 and self.x2 >= other.x1 and self.y1 <= other.y2 and self.y2 >= other.y1


def tunnel_between(
    engine: game.engine.Engine, start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if engine.rng.random() < 0.5:  # 50% chance.
        corner_x, corner_y = x2, y1  # Move horizontally, then vertically.
    else:
        corner_x, corner_y = x1, y2  # Move vertically, then horizontally.

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: game.engine.Engine,
) -> game.game_map.GameMap:
    """Generate a new dungeon map."""
    dungeon = game.game_map.GameMap(engine, map_width, map_height)

    rooms: List[RectangularRoom] = []

    for _ in range(max_rooms):
        room_width = engine.rng.randint(room_min_size, room_max_size)
        room_height = engine.rng.randint(room_min_size, room_max_size)

        x = engine.rng.randint(0, dungeon.width - room_width - 1)
        y = engine.rng.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with.
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = FLOOR

        if len(rooms) == 0:
            # The first room, where the player starts.
            dungeon.enter_xy = new_room.center
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(engine, rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = FLOOR

        # Finally, append the new room to the list.
        rooms.append(new_room)

    return dungeon