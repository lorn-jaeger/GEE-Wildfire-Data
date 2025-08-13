from ee_wildfire.command_line_args import apply_to_user_config, parse, run
from ee_wildfire.UserInterface.UserInterface import ConsoleUI


def main():
    config = parse()
    uf = apply_to_user_config(config)
    ConsoleUI.clear_screen()
    ConsoleUI.write(str(uf))
    run(uf)


if __name__ == "__main__":
    main()
