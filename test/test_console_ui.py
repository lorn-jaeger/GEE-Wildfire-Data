import logging
import threading
import time
from pathlib import Path

import pytest

from ee_wildfire.UserInterface.UserInterface import ConsoleUI

DATA_DIR = Path("/tmp/ee_wildfire_logs/")
LOG_DIR = DATA_DIR / "log_test"


@pytest.mark.unit
def test_multithreaded_logging(tmp_path):
    # Setup logging to a temporary directory
    log_dir = LOG_DIR
    log_dir.mkdir(exist_ok=True)
    ConsoleUI.setup_logging(log_dir, log_level="debug", file_tag="threaded-test")

    # Function for threads to log messages
    def log_messages(thread_id):
        for i in range(5):
            ConsoleUI.log(f"[Thread-{thread_id}] log {i}")
            ConsoleUI.debug(f"[Thread-{thread_id}] debug {i}")
            ConsoleUI.warn(f"[Thread-{thread_id}] warn {i}")
            ConsoleUI.error(f"[Thread-{thread_id}] error {i}")
            time.sleep(0.01)  # Small delay to encourage context switching

    # Start multiple threads
    threads = [threading.Thread(target=log_messages, args=(i,)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Ensure the log file exists
    log_files = list(log_dir.glob("*.log"))
    assert log_files, "No log files were created"

    log_file = log_files[0]
    log_content = log_file.read_text()

    # Check that all expected logs are present
    for thread_id in range(3):
        for i in range(5):
            assert f"[Thread-{thread_id}] log {i}" in log_content
            assert f"[Thread-{thread_id}] debug {i}" in log_content
            assert f"[Thread-{thread_id}] warn {i}" in log_content
            assert f"[Thread-{thread_id}] error {i}" in log_content


@pytest.mark.unit
def test_multithreaded_progress_bars(capfd):
    ConsoleUI.set_verbose(True)  # Enable printing
    ConsoleUI._bars.clear()  # Clean slate for test

    num_threads = 3
    updates_per_thread = 10

    # Add bars for each thread
    for i in range(num_threads):
        ConsoleUI.add_bar(key=f"bar-{i}", total=updates_per_thread, desc=f"Thread-{i}")

    # Each thread updates its bar multiple times
    def update_bar_loop(i):
        for _ in range(updates_per_thread):
            ConsoleUI.update_bar(f"bar-{i}")
            time.sleep(0.01)  # simulate work

    threads = [
        threading.Thread(target=update_bar_loop, args=(i,)) for i in range(num_threads)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # After threads finish, check that bars are fully updated
    for i in range(num_threads):
        bar = ConsoleUI._bars[f"bar-{i}"]
        assert bar.n == updates_per_thread
        assert bar.total == updates_per_thread

    # Optionally capture output (just make sure it didn't error)
    captured = capfd.readouterr()
    assert (
        "Thread-0" in captured.out
        or "Thread-1" in captured.out
        or "Thread-2" in captured.out
    )
