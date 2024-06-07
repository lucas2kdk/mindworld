# minecraft/consumers.py

import json
from channels.generic.websocket import WebsocketConsumer
from .kube import attach_to_console, load_kube_config, get_kubernetes_client

class ConsoleConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        load_kube_config()
        v1 = get_kubernetes_client()
        self.ws_client = attach_to_console(v1, self, self.console_output_callback)

    def disconnect(self, close_code):
        if self.ws_client:
            self.ws_client.close()

    def receive(self, text_data):
        command = json.loads(text_data)['command']
        if self.ws_client:
            self.ws_client.write_stdin(command + "\n")

    def console_output_callback(self, message):
        self.send(text_data=message)
