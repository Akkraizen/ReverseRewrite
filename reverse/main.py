from reverse.core.reverse_bot import ReverseBot
from reverse.utils.logger import setup_logger


def main() -> None:
    setup_logger()
    ReverseBot().run()

if __name__ == "__main__":
    main()
