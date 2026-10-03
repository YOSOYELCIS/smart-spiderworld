# Standalone SpiderWorld — C++

An independent, terminal-based C++17 SpiderWorld implementation. It has no CoBlop, browser, Firebase, or third-party runtime dependency.

## Linux build and run

```bash
cmake -S . -B build
cmake --build build
./build/spiderworld
ctest --test-dir build --output-on-failure
```

Start another level with `./build/spiderworld --level 7`.

Use `help` inside the application for the small programming language: movement, turns, painting, `REPEAT`, `UNTIL`, `PROC`, and `CALL`. End entered programs with `END`.
