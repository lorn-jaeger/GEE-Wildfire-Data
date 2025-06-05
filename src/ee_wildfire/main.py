from ee_wildfire.command_line_args import parse, run
from ee_wildfire.UserInterface import ConsoleUI

def main():
    ui = ConsoleUI()
    config = parse()

    run(config)


if __name__ == "__main__":
    main()
