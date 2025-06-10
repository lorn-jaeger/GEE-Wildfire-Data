from ee_wildfire.UserInterface import ConsoleUI
from ee_wildfire.command_line_args import parse, run

def main():
    config = parse()
    run(config)
    # ConsoleUI.clear_screen()


if __name__ == "__main__":
    main()
