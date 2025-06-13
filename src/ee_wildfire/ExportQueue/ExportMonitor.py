import threading, time, ee
from ee_wildfire.UserInterface.UserInterface import ConsoleUI

class ExportMonitor:
    def __init__(self, tasks, poll_interval=10):
        self.tasks = tasks
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._monitor, daemon=False)

    def start(self):
        ConsoleUI.debug("Starting export monitor thread.")
        self.thread.start()

    def _monitor(self):
        unfinished = set(self.tasks)
        while unfinished and not self._stop.is_set():
            for task in list(unfinished):
                st = task.status()
                state = st.get("state")
                ConsoleUI.debug(f"Task {st.get('id')} state: {state}")
                if state in ("COMPLETED", "FAILED", "CANCELLED"):
                    unfinished.remove(task)
                    ConsoleUI.print(f"Task {st['description']} finished: {state}")
                    if state == "FAILED":
                        ConsoleUI.error(f"Error: {st.get('error_message')}")
            time.sleep(self.poll_interval)

    def stop(self):
        self._stop.set()
        self.thread.join()

