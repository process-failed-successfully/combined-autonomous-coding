import random
import sys
import collections
from typing import List, Tuple, Optional, Dict

class Maze:
    WALL = "#"
    PATH = " "
    START = "S"
    END = "E"
    VISITED = "."
    SOLUTION = "*"

    def __init__(self, width: int, height: int):
        # Ensure dimensions are odd for wall/path grid
        self.width = width if width % 2 == 1 else width + 1
        self.height = height if height % 2 == 1 else height + 1
        self.grid = [[self.WALL for _ in range(self.width)] for _ in range(self.height)]
        self.start = (1, 1)
        self.end = (self.width - 2, self.height - 2)

    def set_cell(self, x: int, y: int, char: str):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = char

    def get_cell(self, x: int, y: int) -> str:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return self.WALL

    def render(self) -> str:
        return "\n".join("".join(row) for row in self.grid)

class MazeGenerator:
    def generate(self, maze: Maze, algo: str = "dfs"):
        # Initialize grid with walls
        maze.grid = [[maze.WALL for _ in range(maze.width)] for _ in range(maze.height)]

        if algo == "dfs":
            self._recursive_backtracker(maze, 1, 1)
        elif algo == "prim":
            self._prim(maze)

        # Set start and end
        maze.set_cell(maze.start[0], maze.start[1], maze.START)
        maze.set_cell(maze.end[0], maze.end[1], maze.END)

    def _recursive_backtracker(self, maze: Maze, x: int, y: int):
        maze.set_cell(x, y, maze.PATH)
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 < nx < maze.width and 0 < ny < maze.height and maze.get_cell(nx, ny) == maze.WALL:
                # Carve path to neighbor
                maze.set_cell(x + dx // 2, y + dy // 2, maze.PATH)
                self._recursive_backtracker(maze, nx, ny)

    def _prim(self, maze: Maze):
        # Start with a grid full of walls.
        # Pick a cell, mark it as part of the maze. Add the walls of the cell to the wall list.
        # While there are walls in the list:
        #   1. Pick a random wall from the list. If only one of the two cells that the wall divides is visited, then:
        #       a. Make the wall a passage and mark the unvisited cell as part of the maze.
        #       b. Add the neighboring walls of the cell to the wall list.
        #   2. Remove the wall from the list.

        start_x, start_y = 1, 1
        maze.set_cell(start_x, start_y, maze.PATH)
        walls = []

        def add_walls(x, y):
            for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
                nx, ny = x + dx, y + dy
                if 0 < nx < maze.width and 0 < ny < maze.height:
                    walls.append((nx, ny, x + dx // 2, y + dy // 2))

        add_walls(start_x, start_y)

        while walls:
            # Pick random wall
            idx = random.randint(0, len(walls) - 1)
            tx, ty, wx, wy = walls[idx] # target, wall
            walls.pop(idx)

            if maze.get_cell(tx, ty) == maze.WALL:
                maze.set_cell(wx, wy, maze.PATH)
                maze.set_cell(tx, ty, maze.PATH)
                add_walls(tx, ty)

class MazeSolver:
    def solve(self, maze: Maze, algo: str = "bfs") -> Optional[List[Tuple[int, int]]]:
        start = maze.start
        end = maze.end

        if algo == "bfs":
            return self._bfs(maze, start, end)
        elif algo == "dfs":
            return self._dfs(maze, start, end)
        return None

    def _bfs(self, maze: Maze, start: Tuple[int, int], end: Tuple[int, int]):
        queue = collections.deque([[start]])
        visited = set([start])

        while queue:
            path = queue.popleft()
            x, y = path[-1]

            if (x, y) == end:
                return path

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < maze.width and 0 <= ny < maze.height and
                    maze.get_cell(nx, ny) != maze.WALL and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    new_path = list(path)
                    new_path.append((nx, ny))
                    queue.append(new_path)
        return None

    def _dfs(self, maze: Maze, start: Tuple[int, int], end: Tuple[int, int]):
        stack = [[start]]
        visited = set([start])

        while stack:
            path = stack.pop()
            x, y = path[-1]

            if (x, y) == end:
                return path

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < maze.width and 0 <= ny < maze.height and
                    maze.get_cell(nx, ny) != maze.WALL and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    new_path = list(path)
                    new_path.append((nx, ny))
                    stack.append(new_path)
        return None

def run_maze_lab_logic(args):
    """CLI logic for Maze Lab."""
    width = args.width if args.width else 21
    height = args.height if args.height else 21

    maze = Maze(width, height)
    gen = MazeGenerator()
    solver = MazeSolver()

    if args.action == "generate":
        algo = args.algo if args.algo else "dfs"
        print(f"Generating maze ({width}x{height}) using {algo}...")
        gen.generate(maze, algo)
        print(maze.render())

        if args.solve:
            print("\nSolving...")
            path = solver.solve(maze, "bfs")
            if path:
                # Mark solution
                for x, y in path:
                    if (x, y) != maze.start and (x, y) != maze.end:
                        maze.set_cell(x, y, maze.SOLUTION)
                print(maze.render())
            else:
                print("No solution found.")

    else:
        print("Unknown action.")
