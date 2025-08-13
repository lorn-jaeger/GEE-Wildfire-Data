from pathlib import Path

import yaml

YAML_FILE = str(Path.home() / "NRML" / "testing_config.yml")


def load_yaml_file() -> dict:
    try:
        with open(YAML_FILE, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: {YAML_FILE} not found.")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
