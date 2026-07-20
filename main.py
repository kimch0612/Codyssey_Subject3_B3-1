"""CLI entry point for Mini Redis."""

from command_processor import CommandProcessor
from mini_redis import MiniRedis


def main():
    redis = MiniRedis()
    processor = CommandProcessor(redis)

    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if line.strip().lower() in ("exit", "quit"):
            break

        result = processor.execute(line)
        if result is not None:
            print(result)


if __name__ == "__main__":
    main()

