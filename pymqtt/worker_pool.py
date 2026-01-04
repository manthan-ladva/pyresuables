import json
import logging
import threading
from queue import Queue, Full
from concurrent.futures import ThreadPoolExecutor


class WorkerPool:
    """
    Queue + fixed thread pool for processing messages.

    - MQTT pushes messages here
    - Worker threads parse and call the user callback
    - Can be reused for Kafka/EventHub/etc.
    """

    def __init__(self, callback, workers: int = 16, max_queue: int = 10000):
        """
        :param callback: function(payload_dict, topic_str)
        :param workers: number of worker threads
        :param max_queue: max backlog to apply backpressure
        """
        self._callback = callback
        self._queue = Queue(maxsize=max_queue)
        self._stop_flag = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=workers)

        for _ in range(workers):
            self._executor.submit(self._worker_loop)

    def push(self, msg):
        """Non-blocking push into queue. Drop if full."""
        try:
            self._queue.put_nowait(msg)
        except Full:
            logging.warning("Queue full, dropping MQTT message")

    def _worker_loop(self):
        while not self._stop_flag.is_set():
            try:
                msg = self._queue.get(timeout=0.5)
            except Exception:
                continue

            try:
                payload = msg.payload.decode("utf-8").strip()
                if payload:
                    data = json.loads(payload)
                    self._callback(data, msg.topic)
            except Exception as e:
                logging.exception(f"Error during message processing: {e}")
            finally:
                self._queue.task_done()

    def queue_size(self) -> int:
        return self._queue.qsize()

    def stop(self):
        self._stop_flag.set()
        self._executor.shutdown(wait=False)
