from pathlib import Path

import pytest

from ee_wildfire.UserConfig.authentication import AuthManager


def test_singleton_behavior(tmp_path, mocker):
    fake_json = tmp_path / "service.json"
    fake_json.write_text('{"client_email": "fake@example.com"}')

    # Mock Google Earth Engine and Drive behavior
    mocker.patch("ee.Initialize")
    mocker.patch("ee.ServiceAccountCredentials", autospec=True)
    mocker.patch("google.oauth2.service_account.Credentials.from_service_account_file")
    mocker.patch("googleapiclient.discovery.build")

    # First instance
    auth1 = AuthManager(fake_json)

    # Second instance — should be same object
    auth2 = AuthManager(fake_json)

    assert auth1 is auth2
    assert auth1.get_drive_service() is auth2.get_drive_service()
