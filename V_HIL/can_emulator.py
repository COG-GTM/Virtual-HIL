
# File: can_emulator.py

import logging

class CANBus:
    def __init__(self):
        self.message_queue = []

    def send(self, msg_id, data):
        logging.debug(f"[CAN SEND] ID: {msg_id}, Data: {data}")
        self.message_queue.append((msg_id, data))

    def receive(self):
        if self.message_queue:
            msg = self.message_queue.pop(0)
            logging.debug(f"[CAN RECV] ID: {msg[0]}, Data: {msg[1]}")
            return msg
        return None

