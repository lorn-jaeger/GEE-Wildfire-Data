import subprocess
from datetime import datetime
from pathlib import Path

import pytest
import yaml
from utils import *

from ee_wildfire.command_line_args import parse
from ee_wildfire.constants import *


@pytest.mark.unit
def test_parse_minimal_args():
    args = parse(["-c", YAML_FILE])
    assert str(args.config) == YAML_FILE
    assert args.export is False
    assert args.download is False
    assert args.min_size == DEFAULT_MIN_SIZE
    assert args.max_size == DEFAULT_MAX_SIZE
