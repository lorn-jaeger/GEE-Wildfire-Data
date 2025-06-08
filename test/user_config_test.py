import unittest
from unittest.mock import patch
from datetime import datetime
from ee_wildfire.command_line_args import parse
from ee_wildfire.constants import *


SERVICE_ACCOUNT = "/home/kyle/NRML/OAuth/service-account-credentials.json"
DATA_DIR = "/home/kyle/opt"
TIFF_DIR = "/home/kyle/opt/google-cloud-sdk"
DRIVE_DIR = "test_dir"

def dict_to_cli_args(args_dict):
    cli_args = []
    for key, value in args_dict.items():
        if isinstance(value, bool):
            if value:  # Only include flags that are True
                cli_args.append(key)
        else:
            cli_args.extend([key, str(value)])
    return cli_args


class TestArgparse(unittest.TestCase):
    def test_dict_style_arguments(self):
        args_dict = {
            '--export': True,
            '--download': True,
            '--retry-failed': True,
            '--data-dir': DATA_DIR,
            '--tiff-dir': TIFF_DIR,
            '--start-date': '2021-01-01',
            '--end-date': '2021-01-14',
            '--silent': None,
            '--credentials': SERVICE_ACCOUNT,
            '--google-drive-dir': DRIVE_DIR,
            '--purge-after': True,
            '--purge-before': True,
            '--min-size': 10,
            '--max-size': 100,
        }

        test_args = ['prog'] + dict_to_cli_args(args_dict)

        with patch('sys.argv', test_args):
            config = parse()

        self.assertTrue(config.silent, "Expected `config.silent` to be True")
        self.assertTrue(config.purge_after, "Expected `config.purge_after` to be True")
        self.assertTrue(config.purge_before, "Expected `config.purge_before` to be True")
        self.assertTrue(config.export, "Expected `config.export` to be True")
        self.assertTrue(config.download, "Expected `config.download` to be True")
        self.assertTrue(config.retry_failed, "Expected `config.retry_failed` to be True")

        self.assertEqual(config.tiff_dir, TIFF_DIR, f"Expected `config.tiff_dir` to be {TIFF_DIR}")
        self.assertEqual(config.data_dir, DATA_DIR, f"Expected `config.data_dir` to be {DATA_DIR}")
        self.assertEqual(config.start_date, datetime(2021, 1, 1), "Expected `config.start_date` to be 2021-01-01")
        self.assertEqual(config.end_date, datetime(2021, 1, 14), "Expected `config.end_date` to be 2021-01-14")
        self.assertEqual(config.credentials, SERVICE_ACCOUNT, f"Expected `config.credentials` to be {SERVICE_ACCOUNT}")
        self.assertEqual(config.google_drive_dir, DRIVE_DIR, f"Expected `config.google_drive_dir` to be {DRIVE_DIR}")
        self.assertEqual(config.min_size, 10, "Expected `config.min_size` to be 10")
        self.assertEqual(config.max_size, 100, "Expected `config.max_size` to be 100")

    def test_internal_config_after_arg_change(self):
        args_dict = {
            "--silent": None,
        }
        test_args = ['prog'] + dict_to_cli_args(args_dict)

        with patch('sys.argv', test_args):
            config = parse()

        self.assertTrue(config.silent, "Expected `config.silent` to be True")
        self.assertFalse(config.export, "Expected `config.export` to be False")
        self.assertFalse(config.download, "Expected `config.download` to be False")
        self.assertFalse(config.retry_failed, "Expected `config.retry_failed` to be False")
        self.assertFalse(config.purge_after, "Expected `config.purge_after` to be False")
        self.assertFalse(config.purge_before, "Expected `config.purge_before` to be False")

        self.assertEqual(config.tiff_dir, TIFF_DIR, f"Expected `config.tiff_dir` to be {TIFF_DIR}")
        self.assertEqual(config.data_dir, DATA_DIR, f"Expected `config.data_dir` to be {DATA_DIR}")
        self.assertEqual(config.start_date, datetime(2021, 1, 1), "Expected `config.start_date` to be 2021-01-01")
        self.assertEqual(config.end_date, datetime(2021, 1, 14), "Expected `config.end_date` to be 2021-01-14")
        self.assertEqual(config.credentials, SERVICE_ACCOUNT, f"Expected `config.credentials` to be {SERVICE_ACCOUNT}")
        self.assertEqual(config.google_drive_dir, DRIVE_DIR, f"Expected `config.google_drive_dir` to be {DRIVE_DIR}")
        self.assertEqual(config.min_size, 10, "Expected `config.min_size` to be 10")
        self.assertEqual(config.max_size, 100, "Expected `config.max_size` to be 100")




if __name__ == '__main__':
    unittest.main()
