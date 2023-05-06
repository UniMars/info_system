import logging
import threading
import time
from queue import Queue

from django.apps import AppConfig

from datas.utils.utils import add_task

file_upload_queue = Queue()
file_upload_start_event = threading.Event()

logger = logging.getLogger('django')


class DataDemoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datas"

    def ready(self):
        queue_thread = threading.Thread(target=process_upload_queue)
        queue_thread.daemon = True
        queue_thread.start()


def process_upload_queue():
    while True:
        if file_upload_start_event.is_set():
            task, args = file_upload_queue.get()
            logger.info(f"process_upload_queue:task:{task}, args:{args}")
            add_task(task, delay=1200, args=args)
            # task.apply_async(args=args)
            if file_upload_queue.empty():
                logger.info("file_upload_queue is empty")
                file_upload_start_event.clear()
        else:
            time.sleep(60)
