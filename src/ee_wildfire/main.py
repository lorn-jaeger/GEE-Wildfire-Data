from ee_wildfire.command_line_args import parse, run

def main():
    config = parse()
    run(config)


if __name__ == "__main__":
    main()
