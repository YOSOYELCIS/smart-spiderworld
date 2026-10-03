import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spiderworld import Game, ParseError, load_level, parse_program


class SpiderWorldTests(unittest.TestCase):
    def test_level_one_solution_completes(self):
        game = Game(load_level(1)); game.run(parse_program('REPEAT 2 { F }'))
        self.assertTrue(game.complete)
    def test_rock_blocks_motion(self):
        game = Game(load_level(3)); game.direction = 2; game.x, game.y = 2, 1; game.run(parse_program('F'))
        self.assertEqual((game.x, game.y), (2, 1))
    def test_painting_targets_is_required(self):
        game = Game(load_level(7)); game.x, game.y = game.level.goal; self.assertFalse(game.complete)
    def test_repeat_and_procedure_execute(self):
        game = Game(load_level(1)); game.run(parse_program('PROC STEP { F } REPEAT 2 { CALL STEP }'))
        self.assertTrue(game.complete)
    def test_parser_rejects_bad_programs(self):
        with self.assertRaises(ParseError): parse_program('REPEAT nope { F }')
        with self.assertRaises(ParseError): parse_program('F }')


if __name__ == '__main__': unittest.main()
