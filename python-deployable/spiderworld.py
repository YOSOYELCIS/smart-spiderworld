#!/usr/bin/env python3
"""Standalone SpiderWorld programming game. Requires Python 3.10+ only."""

from __future__ import annotations

import argparse
import re
import textwrap
from dataclasses import dataclass, field


DIRS = ((0, -1, "^"), (1, 0, ">"), (0, 1, "v"), (-1, 0, "<"))
COLORS = {"PR": "red", "PB": "blue", "PG": "green"}


@dataclass(frozen=True)
class Level:
    number: int
    name: str
    size: int
    start: tuple[int, int, int]
    goal: tuple[int, int]
    rocks: frozenset[tuple[int, int]] = frozenset()
    targets: dict[tuple[int, int], str] = field(default_factory=dict)
    hint: str = ""


def static_levels() -> dict[int, Level]:
    return {
        1: Level(1, "Getting Started", 3, (1, 2, 0), (1, 0), hint="Use F twice."),
        2: Level(2, "Turn! Turn!", 3, (0, 0, 0), (1, 1), hint="Turn right, then move."),
        3: Level(3, "First Obstacle", 4, (0, 0, 0), (3, 3), frozenset({(2, 2), (3, 0)}), hint="Plan a safe route around the rocks."),
        4: Level(4, "Rocky Road", 6, (0, 0, 0), (4, 4), frozenset({(1, 0), (1, 1), (1, 2), (1, 3), (1, 5), (3, 2), (3, 4), (5, 5), (4, 3)}), hint="REPEAT can make a long route clearer."),
        5: Level(5, "Just Keep Turning", 6, (4, 0, 1), (4, 5), frozenset({(5, 0), (4, 1), (2, 0), (1, 1), (2, 3), (3, 2), (1, 4), (3, 5), (4, 4), (0, 2)}), hint="Use F, L, R and loops to navigate the maze."),
        6: Level(6, "Spiral Challenge", 6, (0, 0, 0), (2, 3), frozenset({(1, 1), (1, 3), (1, 4), (2, 1), (3, 1), (4, 1), (0, 1), (4, 4), (4, 3), (4, 2), (3, 4), (2, 4)}), hint="This challenge intentionally has no right turn in its original toolbox."),
        7: Level(7, "Paint the Town", 5, (0, 0, 0), (4, 4), targets={(1, 1): "red", (2, 1): "blue", (3, 1): "green", (1, 2): "green", (2, 2): "red", (3, 2): "blue"}, hint="Paint every marked bug in its required color before the goal."),
    }


def dynamic_level(number: int, size: int | None = None) -> Level:
    choices = {8: (3, 4, 5), 9: (3, 4, 5), 10: (3, 4, 5), 11: (3, 4, 5, 6), 12: (5, 7, 9)}
    if number not in choices:
        raise ValueError("level must be between 1 and 12")
    n = size or choices[number][(number - 8) % len(choices[number])]
    targets: dict[tuple[int, int], str] = {}
    if number == 8:
        targets[(n - 1, 0)] = "red"; targets[(n - 1, n - 1)] = "red"
        return Level(number, "Procedure Power", n, (0, 0, 0), (0, n - 1), targets=targets, hint="Define a procedure with PROC and invoke it with CALL.")
    if number == 9:
        for y in range(n): targets[(0, y)] = "red"
        for x in range(n): targets[(x, n - 1)] = "red"
        return Level(number, "Dynamic L-Shape", n, (0, 0, 1), (n - 1, n - 1), targets=targets, hint="Paint a red L; UNTIL is useful on a variable-size grid.")
    if number == 10:
        for x in range(n): targets[(x, 0)] = "red"; targets[(x, n - 1)] = "red"
        for i in range(n): targets[(n - 1 - i, i)] = "red"
        return Level(number, "Dynamic Z-Shape", n, (0, 0, 1), (n - 1, n - 1), targets=targets, hint="Paint the top, diagonal, and bottom of the Z.")
    if number == 11:
        for i in range(n): targets[(i, i)] = "red"
        for i in range(n - 1): targets[(i + 1, i)] = "blue"
        return Level(number, "Dynamic Diagonals", n, (0, 0, 1), (n - 1, n - 1), targets=targets, hint="Paint the main diagonal red and upper diagonal blue.")
    for x in range(n): targets[(x, 0)] = "blue"; targets[(x, n - 1)] = "blue"
    for y in range(n): targets[(0, y)] = "blue"; targets[(n - 1, y)] = "blue"
    for i in range(1, n - 1): targets[(i, i)] = "red"; targets[(n - 1 - i, i)] = "red"
    return Level(number, "Dynamic X in the Box", n, (0, 0, 1), (n - 1, n // 2), targets=targets, hint="Paint a blue border and red X before reaching the goal.")


class ParseError(ValueError): pass


def parse_program(source: str) -> list[tuple]:
    tokens = re.findall(r"\{|\}|[^\s{}]+", source.upper())
    pos = 0
    def parse_block(stop: bool = False) -> list[tuple]:
        nonlocal pos
        output = []
        while pos < len(tokens):
            token = tokens[pos]; pos += 1
            if token == "}":
                if stop: return output
                raise ParseError("unexpected }")
            if token in {"F", "L", "R", "PR", "PB", "PG"}: output.append((token,))
            elif token == "CALL":
                if pos == len(tokens): raise ParseError("CALL needs a procedure name")
                output.append(("CALL", tokens[pos])); pos += 1
            elif token == "PROC":
                if pos >= len(tokens): raise ParseError("PROC needs a name and {")
                name = tokens[pos]; pos += 1
                if pos >= len(tokens) or tokens[pos] != "{": raise ParseError("PROC must use { }")
                pos += 1; output.append(("PROC", name, parse_block(True)))
            elif token == "REPEAT":
                if pos >= len(tokens): raise ParseError("REPEAT needs a count")
                try: count = int(tokens[pos])
                except ValueError as error: raise ParseError("REPEAT count must be a number") from error
                pos += 1
                if count < 0 or count > 100: raise ParseError("REPEAT count must be 0..100")
                if pos >= len(tokens) or tokens[pos] != "{": raise ParseError("REPEAT must use { }")
                pos += 1; output.append(("REPEAT", count, parse_block(True)))
            elif token == "UNTIL":
                if pos >= len(tokens) or tokens[pos] != "{": raise ParseError("UNTIL must use { }")
                pos += 1; output.append(("UNTIL", parse_block(True)))
            else: raise ParseError(f"unknown instruction: {token}")
        if stop: raise ParseError("missing }")
        return output
    return parse_block()


@dataclass
class Game:
    level: Level
    x: int = field(init=False); y: int = field(init=False); direction: int = field(init=False)
    paint: dict[tuple[int, int], str] = field(default_factory=dict)
    procedures: dict[str, list[tuple]] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    def __post_init__(self) -> None: self.x, self.y, self.direction = self.level.start
    def can_move(self) -> bool:
        dx, dy, _ = DIRS[self.direction]; nx, ny = self.x + dx, self.y + dy
        return 0 <= nx < self.level.size and 0 <= ny < self.level.size and (nx, ny) not in self.level.rocks
    def run(self, program: list[tuple]) -> None:
        self.events.clear(); self._run(program, 0)
        self.events.append("SUCCESS: level complete!" if self.complete else "Program finished. " + self.status())
    def _run(self, commands: list[tuple], depth: int) -> None:
        if depth > 20: raise RuntimeError("procedure nesting is too deep")
        for command in commands:
            kind = command[0]
            if kind == "F":
                if self.can_move():
                    dx, dy, _ = DIRS[self.direction]; self.x += dx; self.y += dy; self.events.append(f"move to ({self.x}, {self.y})")
                else: self.events.append("blocked")
            elif kind == "L": self.direction = (self.direction - 1) % 4; self.events.append("turn left")
            elif kind == "R": self.direction = (self.direction + 1) % 4; self.events.append("turn right")
            elif kind in COLORS: self.paint[(self.x, self.y)] = COLORS[kind]; self.events.append(f"paint {COLORS[kind]}")
            elif kind == "PROC": self.procedures[command[1]] = command[2]; self.events.append(f"defined {command[1]}")
            elif kind == "CALL":
                if command[1] not in self.procedures: raise RuntimeError(f"unknown procedure: {command[1]}")
                self._run(self.procedures[command[1]], depth + 1)
            elif kind == "REPEAT":
                for _ in range(command[1]): self._run(command[2], depth + 1)
            elif kind == "UNTIL":
                loops = 0
                while self.can_move():
                    self._run(command[1], depth + 1); loops += 1
                    if loops > 100: raise RuntimeError("UNTIL stopped after 100 iterations; its body must make progress")
    @property
    def complete(self) -> bool:
        return (self.x, self.y) == self.level.goal and all(self.paint.get(cell) == color for cell, color in self.level.targets.items())
    def status(self) -> str: return f"spider at ({self.x}, {self.y}), facing {DIRS[self.direction][2]}"
    def render(self) -> str:
        lines = []
        for y in range(self.level.size):
            row = []
            for x in range(self.level.size):
                cell = (x, y)
                if cell == (self.x, self.y): row.append(DIRS[self.direction][2])
                elif cell in self.level.rocks: row.append("#")
                elif cell == self.level.goal: row.append("G")
                elif cell in self.paint: row.append({"red": "r", "blue": "b", "green": "g"}[self.paint[cell]])
                elif cell in self.level.targets: row.append({"red": "R", "blue": "B", "green": "N"}[self.level.targets[cell]])
                else: row.append(".")
            lines.append(" ".join(row))
        return "\n".join(lines)


HELP = """Commands: F (forward), L/R (turn), PR/PB/PG (paint red/blue/green),
REPEAT n { ... }, UNTIL { ... }, PROC name { ... }, CALL name.
Enter a multi-line program and finish it with END. Other commands: level N, reset, help, quit.
Legend: ^ > v < spider, # rock, G goal, R/B/N required paint, r/b/g applied paint."""


def load_level(number: int, size: int | None = None) -> Level:
    return static_levels().get(number) or dynamic_level(number, size)


def repl(level_number: int, size: int | None) -> None:
    game = Game(load_level(level_number, size))
    print("SpiderWorld — standalone Python edition\n" + HELP)
    while True:
        print(f"\nLevel {game.level.number}: {game.level.name}\n{game.level.hint}\n{game.render()}\n{game.status()}")
        action = input("spiderworld> ").strip()
        if action.lower() in {"q", "quit", "exit"}: return
        if action.lower() == "help": print(HELP); continue
        if action.lower() == "reset": game = Game(game.level); continue
        if action.lower().startswith("level "):
            try: game = Game(load_level(int(action.split()[1]), size))
            except (ValueError, IndexError) as error: print(f"Invalid level: {error}")
            continue
        lines = [action]
        while lines[-1].strip().upper() != "END": lines.append(input("... "))
        try:
            game.run(parse_program("\n".join(lines[:-1])))
            print("\n".join(game.events))
        except (ParseError, RuntimeError) as error: print(f"Program error: {error}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run standalone SpiderWorld")
    parser.add_argument("--level", type=int, default=1, choices=range(1, 13))
    parser.add_argument("--size", type=int, help="Override dynamic level grid size")
    args = parser.parse_args()
    repl(args.level, args.size)
