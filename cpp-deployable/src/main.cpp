#include <algorithm>
#include <cctype>
#include <cmath>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using Point = std::pair<int, int>;

struct Level {
  int number, size, startX, startY, startDir;
  std::string name, hint;
  Point goal;
  std::set<Point> rocks;
  std::map<Point, std::string> targets;
};

static const int DX[] = {0, 1, 0, -1};
static const int DY[] = {-1, 0, 1, 0};
static const char FACE[] = {'^', '>', 'v', '<'};

Level dynamicLevel(int number, int size = 0) {
  std::vector<int> choices = number == 12 ? std::vector<int>{5, 7, 9} : number == 11 ? std::vector<int>{3, 4, 5, 6} : std::vector<int>{3, 4, 5};
  int n = size ? size : choices[(number - 8) % choices.size()];
  std::map<Point, std::string> targets;
  if (number == 8) { targets[{n - 1, 0}] = targets[{n - 1, n - 1}] = "red"; return {8, n, 0, 0, 0, "Procedure Power", "Use PROC name { ... } and CALL name.", {0, n - 1}, {}, targets}; }
  if (number == 9) { for (int i = 0; i < n; ++i) targets[{0, i}] = targets[{i, n - 1}] = "red"; return {9, n, 0, 0, 1, "Dynamic L-Shape", "Paint a red L before the goal.", {n - 1, n - 1}, {}, targets}; }
  if (number == 10) { for (int i = 0; i < n; ++i) { targets[{i, 0}] = targets[{i, n - 1}] = "red"; targets[{n - 1 - i, i}] = "red"; } return {10, n, 0, 0, 1, "Dynamic Z-Shape", "Paint a red Z before the goal.", {n - 1, n - 1}, {}, targets}; }
  if (number == 11) { for (int i = 0; i < n; ++i) targets[{i, i}] = "red"; for (int i = 0; i < n - 1; ++i) targets[{i + 1, i}] = "blue"; return {11, n, 0, 0, 1, "Dynamic Diagonals", "Paint red and blue diagonals.", {n - 1, n - 1}, {}, targets}; }
  for (int i = 0; i < n; ++i) { targets[{i, 0}] = targets[{i, n - 1}] = "blue"; targets[{0, i}] = targets[{n - 1, i}] = "blue"; }
  for (int i = 1; i < n - 1; ++i) { targets[{i, i}] = "red"; targets[{n - 1 - i, i}] = "red"; }
  return {12, n, 0, 0, 1, "Dynamic X in the Box", "Paint a blue box with a red X.", {n - 1, n / 2}, {}, targets};
}

Level levelFor(int n, int size = 0) {
  if (n == 1) return {1, 3, 1, 2, 0, "Getting Started", "Use F twice.", {1, 0}, {}, {}};
  if (n == 2) return {2, 3, 0, 0, 0, "Turn! Turn!", "Turn right, then move.", {1, 1}, {}, {}};
  if (n == 3) return {3, 4, 0, 0, 0, "First Obstacle", "Plan around the rocks.", {3, 3}, {{2, 2}, {3, 0}}, {}};
  if (n == 4) return {4, 6, 0, 0, 0, "Rocky Road", "Loops help with longer paths.", {4, 4}, {{1,0},{1,1},{1,2},{1,3},{1,5},{3,2},{3,4},{5,5},{4,3}}, {}};
  if (n == 5) return {5, 6, 4, 0, 1, "Just Keep Turning", "Navigate the zigzag maze.", {4, 5}, {{5,0},{4,1},{2,0},{1,1},{2,3},{3,2},{1,4},{3,5},{4,4},{0,2}}, {}};
  if (n == 6) return {6, 6, 0, 0, 0, "Spiral Challenge", "Solve without relying on a right-turn block.", {2, 3}, {{1,1},{1,3},{1,4},{2,1},{3,1},{4,1},{0,1},{4,4},{4,3},{4,2},{3,4},{2,4}}, {}};
  if (n == 7) return {7, 5, 0, 0, 0, "Paint the Town", "Paint every target then reach G.", {4, 4}, {}, {{{1,1},"red"},{{2,1},"blue"},{{3,1},"green"},{{1,2},"green"},{{2,2},"red"},{{3,2},"blue"}}};
  if (n >= 8 && n <= 12) return dynamicLevel(n, size);
  throw std::runtime_error("Level must be 1 through 12.");
}

struct Command { std::string op, value; int count = 0; std::vector<Command> body; };

std::vector<std::string> tokenize(const std::string& text) {
  std::vector<std::string> out; std::string current;
  auto flush = [&] { if (!current.empty()) { for (char& c : current) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c))); out.push_back(current); current.clear(); } };
  for (char c : text) { if (c == '{' || c == '}') { flush(); out.push_back(std::string(1, c)); } else if (std::isspace(static_cast<unsigned char>(c))) flush(); else current += c; } flush(); return out;
}

std::vector<Command> parseBlock(const std::vector<std::string>& tokens, size_t& pos, bool closing = false) {
  std::vector<Command> out;
  while (pos < tokens.size()) {
    std::string op = tokens[pos++];
    if (op == "}") { if (closing) return out; throw std::runtime_error("Unexpected }."); }
    if (op == "F" || op == "L" || op == "R" || op == "PR" || op == "PB" || op == "PG") out.push_back({op});
    else if (op == "CALL") { if (pos == tokens.size()) throw std::runtime_error("CALL needs a name."); out.push_back({op, tokens[pos++]}); }
    else if (op == "PROC") { if (pos + 1 >= tokens.size() || tokens[pos + 1] != "{") throw std::runtime_error("Use PROC name { ... }."); std::string name = tokens[pos++]; ++pos; out.push_back({op, name, 0, parseBlock(tokens, pos, true)}); }
    else if (op == "REPEAT") { if (pos + 1 >= tokens.size()) throw std::runtime_error("Use REPEAT number { ... }."); int count; try { count = std::stoi(tokens[pos++]); } catch (...) { throw std::runtime_error("REPEAT needs a number."); } if (count < 0 || count > 100 || tokens[pos++] != "{") throw std::runtime_error("Invalid REPEAT."); out.push_back({op, "", count, parseBlock(tokens, pos, true)}); }
    else if (op == "UNTIL") { if (pos == tokens.size() || tokens[pos++] != "{") throw std::runtime_error("Use UNTIL { ... }."); out.push_back({op, "", 0, parseBlock(tokens, pos, true)}); }
    else throw std::runtime_error("Unknown instruction: " + op);
  }
  if (closing) throw std::runtime_error("Missing }."); return out;
}

std::vector<Command> parse(const std::string& text) { auto tokens = tokenize(text); size_t pos = 0; return parseBlock(tokens, pos); }

class Game {
 public:
  explicit Game(Level input) : level(std::move(input)), x(level.startX), y(level.startY), direction(level.startDir) {}
  bool canMove() const { int nx = x + DX[direction], ny = y + DY[direction]; return nx >= 0 && nx < level.size && ny >= 0 && ny < level.size && !level.rocks.count({nx, ny}); }
  void run(const std::vector<Command>& commands) { events.clear(); execute(commands, 0); events.push_back(complete() ? "SUCCESS: level complete!" : "Program finished."); }
  bool complete() const { if (Point{x,y} != level.goal) return false; for (const auto& [cell, color] : level.targets) { auto it = paint.find(cell); if (it == paint.end() || it->second != color) return false; } return true; }
  std::string board() const {
    std::ostringstream out;
    for (int row = 0; row < level.size; ++row) { for (int col = 0; col < level.size; ++col) { Point p{col,row}; char c = '.'; if (p == Point{x,y}) c = FACE[direction]; else if (level.rocks.count(p)) c = '#'; else if (p == level.goal) c = 'G'; else if (paint.count(p)) c = paint.at(p) == "red" ? 'r' : paint.at(p) == "blue" ? 'b' : 'g'; else if (level.targets.count(p)) c = level.targets.at(p) == "red" ? 'R' : level.targets.at(p) == "blue" ? 'B' : 'N'; out << c << ' '; } out << '\n'; } return out.str();
  }
  Level level; std::vector<std::string> events;
 private:
  int x, y, direction; std::map<Point, std::string> paint; std::map<std::string, std::vector<Command>> procedures;
  void execute(const std::vector<Command>& commands, int depth) {
    if (depth > 20) throw std::runtime_error("Procedure nesting is too deep.");
    for (const auto& c : commands) {
      if (c.op == "F") { if (canMove()) { x += DX[direction]; y += DY[direction]; events.push_back("move"); } else events.push_back("blocked"); }
      else if (c.op == "L") direction = (direction + 3) % 4;
      else if (c.op == "R") direction = (direction + 1) % 4;
      else if (c.op == "PR" || c.op == "PB" || c.op == "PG") paint[{x,y}] = c.op == "PR" ? "red" : c.op == "PB" ? "blue" : "green";
      else if (c.op == "PROC") procedures[c.value] = c.body;
      else if (c.op == "CALL") { if (!procedures.count(c.value)) throw std::runtime_error("Unknown procedure: " + c.value); execute(procedures[c.value], depth + 1); }
      else if (c.op == "REPEAT") for (int i = 0; i < c.count; ++i) execute(c.body, depth + 1);
      else if (c.op == "UNTIL") { int loops = 0; while (canMove()) { execute(c.body, depth + 1); if (++loops > 100) throw std::runtime_error("UNTIL made no progress."); } }
    }
  }
};

void printHelp() { std::cout << "Commands: F, L, R, PR/PB/PG, REPEAT n { ... }, UNTIL { ... }, PROC name { ... }, CALL name.\nFinish a multi-line program with END. Other commands: level N, reset, help, quit.\nLegend: # rock, G goal, R/B/N targets, r/b/g paint.\n"; }

int main(int argc, char** argv) {
  if (argc > 1 && std::string(argv[1]) == "--self-test") { Game test(levelFor(1)); test.run(parse("REPEAT 2 { F }")); return test.complete() ? 0 : 1; }
  int number = 1; if (argc > 2 && std::string(argv[1]) == "--level") number = std::stoi(argv[2]);
  try {
    Game game(levelFor(number)); std::cout << "SpiderWorld — standalone C++ edition\n"; printHelp();
    for (;;) {
      std::cout << "\nLevel " << game.level.number << ": " << game.level.name << "\n" << game.level.hint << "\n" << game.board() << "spiderworld> ";
      std::string line; if (!std::getline(std::cin, line)) break;
      if (line == "quit" || line == "exit" || line == "q") break;
      if (line == "help") { printHelp(); continue; }
      if (line == "reset") { game = Game(game.level); continue; }
      if (line.rfind("level ", 0) == 0) { game = Game(levelFor(std::stoi(line.substr(6)))); continue; }
      std::string program = line; while (line != "END" && std::getline(std::cin, line)) { if (line != "END") program += '\n' + line; }
      game.run(parse(program)); for (const auto& event : game.events) std::cout << event << '\n';
    }
  } catch (const std::exception& error) { std::cerr << "SpiderWorld error: " << error.what() << '\n'; return 1; }
  return 0;
}
