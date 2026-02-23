import unittest
from unittest.mock import MagicMock, patch
import io
import sys
from shared.maze_lab import Maze, MazeGenerator, MazeSolver, run_maze_lab_logic

class TestMazeLab(unittest.TestCase):
    def test_maze_init(self):
        maze = Maze(11, 11)
        self.assertEqual(maze.width, 11)
        self.assertEqual(maze.height, 11)
        self.assertEqual(maze.get_cell(0, 0), Maze.WALL)

    def test_maze_generator_dfs(self):
        maze = Maze(11, 11)
        gen = MazeGenerator()
        gen.generate(maze, "dfs")

        # Check start and end
        self.assertEqual(maze.get_cell(1, 1), Maze.START)
        self.assertEqual(maze.get_cell(9, 9), Maze.END)

        # Check if there are paths (not all walls)
        path_count = sum(row.count(Maze.PATH) for row in maze.grid)
        self.assertGreater(path_count, 0)

    def test_maze_solver_bfs(self):
        maze = Maze(11, 11)
        gen = MazeGenerator()
        gen.generate(maze, "dfs")

        solver = MazeSolver()
        path = solver.solve(maze, "bfs")

        self.assertIsNotNone(path)
        self.assertEqual(path[0], maze.start)
        self.assertEqual(path[-1], maze.end)

    def test_cli_generate(self):
        args = MagicMock()
        args.width = 11
        args.height = 11
        args.action = "generate"
        args.algo = "dfs"
        args.solve = False

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            run_maze_lab_logic(args)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Generating maze", output)
        self.assertIn("#", output)
        self.assertIn("S", output)
        self.assertIn("E", output)

    def test_cli_solve(self):
        args = MagicMock()
        args.width = 11
        args.height = 11
        args.action = "generate"
        args.algo = "dfs"
        args.solve = True

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            run_maze_lab_logic(args)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("Solving...", output)
        self.assertIn("*", output)

if __name__ == '__main__':
    unittest.main()
