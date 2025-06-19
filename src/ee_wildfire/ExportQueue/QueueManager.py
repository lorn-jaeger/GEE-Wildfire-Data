import ee
import ee.data
import ee.batch
from ee import Image #type: ignore

from ee_wildfire.constants import CRS_CODE, DEFAULT_GOOGLE_DRIVE_DIR, EXPORT_QUEUE_SIZE, USA_COORDS
from ee_wildfire.UserInterface.UserInterface import ConsoleUI

import time


class QueueManager:
    _task_queue = []
    _active_tasks = []
    _failed_tasks = []
    _completed_tasks = []
    _failed_exports = []



    @classmethod
    def _check_full(cls) -> bool:
        num_tasks = len(cls._task_queue)
        if num_tasks < EXPORT_QUEUE_SIZE:
            return False
        return True
    

    @classmethod
    def _count_ee_active_tasks(cls) -> None:
        """
        Count the number of currently active Earth Engine export tasks.
        """
        ConsoleUI.print("Querying Google Earth Queue...")
        tasks = ee.data.getTaskList()
        active_task_dicts = [t for t in tasks if t['state'] in ['READY', 'RUNNING']]
        cls._task_queue = [ee.batch.Task(t['id'], t['task_type'], t['state']) for t in active_task_dicts]
        ConsoleUI.debug(f"Active tasks: {cls._task_queue}")
        ConsoleUI.set_bar_position(key="export_queue",value=len(cls._task_queue))


    @classmethod
    def add_export(cls,
                   image: Image,
                   description: str,
                   max_pixels:float,
                   scale,
                   filename_prefix=None,
                   region=USA_COORDS,
                   crs=CRS_CODE,
                   folder=DEFAULT_GOOGLE_DRIVE_DIR):
        """
        Queue an export task to Google Drive.
        """
        # TODO: invalidate this stuff yo


        if filename_prefix:
            task = ee.batch.Export.image.toDrive(
                image=image,
                description=description,
                folder=folder,
                region=region,
                fileNamePrefix=filename_prefix,
                crs=crs,
                scale=scale,
                maxPixels=max_pixels,
            )
        else:
            task = ee.batch.Export.image.toDrive(
                image=image,
                description=description,
                folder=folder,
                region=region,
                scale=scale,
                crs=crs,
                maxPixels=max_pixels,
            )

        # Querry google earth queue for current tasks
        if len(cls._task_queue) == 0:
            cls._count_ee_active_tasks()

        while True:

            if cls._check_full():
                ConsoleUI.print("Google Earth export queue is full!")
                cls._count_ee_active_tasks()
                continue

            try:
                t = task.start()
                cls._task_queue.append(task)
                ConsoleUI.update_bar(key="export_queue")

            except Exception as e:
                ConsoleUI.warn(f"Could not export {image} : {str(e)}")
                cls._failed_exports.append(task)

            break

    @classmethod
    def wait_for_exports(cls):

        while cls._task_queue:
            cls._count_ee_active_tasks()
            ConsoleUI.print("Waiting for export to finish...")
            time.sleep(10)


    #FIX: Slow......
    @classmethod
    def update_queue(cls):
        remaining_tasks = []
        for task in cls._task_queue:
            try:
                status = task.status()
                state = status.get("state")
            except Exception as e:
                ConsoleUI.error(f"Could not fetch status for task {task.id}: {e}")
                continue

            if state in ['READY', 'RUNNING']:
                cls._active_tasks.append(task)
                remaining_tasks.append(task)  # Keep in main queue
            elif state == 'COMPLETED':
                cls._completed_tasks.append(task)
            elif state in ['FAILED', 'CANCELLED']:
                cls._failed_tasks.append(task)
            else:
                ConsoleUI.warn(f"Unknown task state '{state}' for task {task.id}")
                remaining_tasks.append(task)  # Conservatively keep unknowns

        cls._task_queue = remaining_tasks  # Update main queue

        ConsoleUI.set_bar_position(key="export_queue", value=len(cls._task_queue))
        ConsoleUI.debug(f"Task queue: {[t.id for t in cls._task_queue]}")
        ConsoleUI.debug(f"Active tasks: {[t.id for t in cls._active_tasks]}")
        ConsoleUI.debug(f"Completed tasks: {[t.id for t in cls._completed_tasks]}")
        ConsoleUI.debug(f"Failed tasks: {[t.id for t in cls._failed_tasks]}")
