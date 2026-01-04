import json
import random
import logging
import socket
import signal
import threading
from datetime import datetime
from threading import Thread
from paho.mqtt import client as mqtt_client
from datetime import datetime
import sys
import os
import time

from src.config.settings import settings
from .worker_pool import WorkerPool




# ----------------------------------------------------------------------------- #
#                            MQTT Subscriber                                    #
# ----------------------------------------------------------------------------- #
class MQTTSubscriber:
    """
    High-level MQTT subscriber:
    - Mosquitto
    - QoS 1 (configurable)
    - Backpressure via WorkerPool
    """

    def __init__(
        self,
        config: dict,
        topic: str,
        callback,
        qos: int = 1,
        workers: int = 16,
        max_queue: int = 10000,
        keepalive: int = 60,
    ):
        """
        config = {
            "broker": "...",
            "port": 1883,
            "username": "...",
            "password": "..."
        }
        """
        self.config = settings.mqtt_credentials(config)
        self.topic = topic
        self.qos = qos

        hostname = socket.gethostname()
        pid = os.getpid()
        self.client_id = f"mqtt-sub-{hostname}-{topic}-{pid}"

        # MQTT network client
        self._client = mqtt_client.Client(client_id=self.client_id, clean_session=True)
        # Use resolved credentials from settings
        self._client.username_pw_set(self.config["username"], self.config["password"])
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

        # Worker pool for processing messages
        self._pool = WorkerPool(callback, workers=workers, max_queue=max_queue)

        # Reconnect backoff
        self._client.reconnect_delay_set(min_delay=1, max_delay=120)
        self.keepalive = keepalive

    def start(self):
        logging.info(
            f"MQTTSubscriber connecting to {self.config['broker']}:{self.config['port']} "
            f"topic={self.topic} qos={self.qos}"
        )
        self._client.connect(self.config["broker"], self.config["port"])
        self._client.loop_start()
        return self

    def stop(self):
        logging.info("Stopping MQTT subscriber...")
        self._pool.stop()
        self._client.loop_stop()
        self._client.disconnect()

    def queue_size(self):
        return self._pool.queue_size()

    # ---------- MQTT callbacks ----------

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"[{self.client_id}] Connected")
            client.subscribe(self.topic, qos=self.qos)
        else:
            logging.error(f"Connect failed rc={rc}")

    def _on_message(self, client, userdata, msg):
        # Only queue push, very fast
        self._pool.push(msg)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logging.warning("Unexpected disconnect, auto-reconnect")
        else:
            logging.info("Clean disconnect")

