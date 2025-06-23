import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import ee
import ee.batch
import ee.data
from ee import Image  # type: ignore

from ee_wildfire.constants import (
    CRS_CODE,
    DEFAULT_GOOGLE_DRIVE_DIR,
    EXPORT_QUEUE_SIZE,
    USA_COORDS,
)
from ee_wildfire.UserInterface.UserInterface import ConsoleUI

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # seconds
WORKER_COUNT = 4


class QueueManager:
    _task_queue = []
    _active_tasks = []
    _failed_tasks = []
    _completed_tasks = []
    _failed_exports = []
    _threads = []
    _shutdown_event = threading.Event()
    _lock = threading.Lock()
    _export_jobs = queue.Queue()

    # ========================================
    #              Dunder Methods
    # ========================================

    def __str__(self) -> str:
        return str(cls._active_tasks)

    # ========================================
    #              Threading Methods
    # ========================================

    @classmethod
    def start_workers(cls, num_workers=WORKER_COUNT):
        if cls._threads:
            return  # already running

        for _ in range(num_workers):
            t = threading.Thread(target=cls._worker, daemon=True)
            t.start()
            cls._threads.append(t)

    @classmethod
    def stop_workers(cls):
        cls._shutdown_event.set()
        for _ in cls._threads:
            cls._export_jobs.put(None)  # signal shutdown to each thread
        for t in cls._threads:
            t.join()
        cls._threads.clear()
        cls._shutdown_event.clear()

    @classmethod
    def _worker(cls):
        while not cls._shutdown_event.is_set():
            job = cls._export_jobs.get()
            if job is None:
                break

            for attempt in range(MAX_RETRIES):
                if cls._check_full():
                    ConsoleUI.print("Queue full, waiting...")
                    time.sleep(5)
                    cls.update_queue()
                    continue

                try:
                    task = ee.batch.Export.image.toDrive(
                        image=job["image"],
                        description=job["description"],
                        folder=job["folder"],
                        region=job["region"],
                        crs=job["crs"],
                        scale=job["scale"],
                        maxPixels=job["max_pixels"],
                        fileNamePrefix=job["filename_prefix"] or job["description"],
                    )
                    task.start()
                    with cls._lock:
                        cls._task_queue.append(task)
                    ConsoleUI.update_bar("export_queue")
                    break  # Success
                except Exception as e:
                    wait_time = RETRY_DELAY_BASE**attempt
                    ConsoleUI.warn(
                        f"Retry {attempt+1}/{MAX_RETRIES} for {job['description']}: {e}"
                    )
                    time.sleep(wait_time)
            else:
                with cls._lock:
                    cls._failed_exports.append(job)
                ConsoleUI.error(
                    f"Failed to export {job['description']} after {MAX_RETRIES} attempts."
                )

            cls._export_jobs.task_done()

    # ========================================
    #              Private Methods
    # ========================================
    @classmethod
    def _check_full(cls) -> bool:
        num_tasks = len(cls._task_queue)
        return (EXPORT_QUEUE_SIZE - 1) <= num_tasks

    @classmethod
    def _count_ee_active_tasks(cls) -> None:
        """
        Count the number of currently active Earth Engine export tasks.
        """
        ConsoleUI.print("Querying Google Earth Queue...")
        tasks = ee.data.getTaskList()
        active_task_dicts = [t for t in tasks if t["state"] in ["READY", "RUNNING"]]
        cls._task_queue = [
            ee.batch.Task(t["id"], t["task_type"], t["state"])
            for t in active_task_dicts
        ]
        ConsoleUI.debug(f"Active tasks: {cls._task_queue}")
        ConsoleUI.set_bar_position(key="export_queue", value=len(cls._task_queue))

    # ========================================
    #              Public Methods
    # ========================================

    @classmethod
    def get_task_filename(cls) -> [str]:
        """
        Attempt to extract the filename or description associated with an Earth Engine task.

        Returns:
            A human-readable filename string, or 'unknown_filename' if none is found.
        """
        files = []
        tasks = cls._completed_tasks

        for task in tasks:
            config = getattr(task, "config", {})
            filename = (
                # Try common export fields
                config.get("fileNamePrefix")
                or config.get("driveFileNamePrefix")
                or config.get("description")
                or f"task_{task.id}"
                or "unknown_filename"
            )
            files.append(filename + ".tif")

        return files

    @classmethod
    def add_export(
        cls,
        image,
        description,
        max_pixels,
        scale,
        filename_prefix=None,
        region=None,
        crs=None,
        folder=None,
    ):
        cls.start_workers()
        job = {
            "image": image,
            "description": description,
            "max_pixels": max_pixels,
            "scale": scale,
            "filename_prefix": filename_prefix,
            "region": region,
            "crs": crs,
            "folder": folder,
        }
        cls._export_jobs.put(job)

    @classmethod
    def wait_for_exports(cls):
        cls._export_jobs.join()

        while cls._task_queue:
            cls.update_queue()
            ConsoleUI.print("Waiting for export to finish...")

        time.sleep(60)  # wait for last item to export

    @classmethod
    def update_queue(cls, max_workers: int = 8):
        """
        Update the export task queue by querying task statuses in parallel.
        Categorizes tasks into active, completed, and failed.
        """

        def fetch_status(task):
            try:
                status = task.status()
                return task, status.get("state")
            except Exception as e:
                ConsoleUI.error(f"Could not fetch status for task {task.id}: {e}")
                return task, None

        remaining_tasks = []
        active_tasks = []
        failed_tasks = []
        completed_tasks = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_status, task) for task in cls._task_queue]

            for future in as_completed(futures):
                task, state = future.result()
                if state is None:
                    continue  # Skip failed status calls

                if state in ["READY", "RUNNING"]:
                    active_tasks.append(task)
                    remaining_tasks.append(task)
                elif state == "COMPLETED":
                    completed_tasks.append(task)
                elif state in ["FAILED", "CANCELLED"]:
                    failed_tasks.append(task)
                else:
                    ConsoleUI.warn(f"Unknown task state '{state}' for task {task.id}")
                    remaining_tasks.append(task)

        with cls._lock:
            cls._task_queue = remaining_tasks  # okay to overwrite
            cls._active_tasks.extend(active_tasks)
            cls._completed_tasks.extend(completed_tasks)
            cls._failed_tasks.extend(failed_tasks)

        ConsoleUI.set_bar_position(key="export_queue", value=len(cls._task_queue))
        ConsoleUI.debug(f"Task queue: {[t.id for t in cls._task_queue]}")
        ConsoleUI.debug(f"Active tasks: {[t.id for t in cls._active_tasks]}")
        ConsoleUI.debug(f"Completed tasks: {[t.id for t in cls._completed_tasks]}")
        ConsoleUI.debug(f"Failed tasks: {[t.id for t in cls._failed_tasks]}")
