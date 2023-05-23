import paho.mqtt.client as mqtt
import logging
import hashlib
# Basic functionality implemented, however callback functions are not since they depend on per client basis


class Client:
    def __init__(self, mqtt_name, username, password):
        self.client_id = mqtt_name
        self.client = mqtt.Client(mqtt_name)
        self.client.username_pw_set(username, password)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        self.connected = False
        self.lost_connection = False

        self.logger = logging.getLogger()

    def connect(self, rp_ip):
        self.log_message("NOTICE", f"{self.client_id} is connecting to MQTT broker on RP...")
        result_code = self.client.connect(rp_ip, 1883, 20)
        if result_code != mqtt.CONNACK_ACCEPTED:
            self.log_message("ERROR", f"{self.client_id} failed MQTT connection with result code {result_code}.")
            self.log_message("ERROR", "Make sure MQTT broker is running on PI!")
            return False
        self.client.loop_start()
        return True

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log_message("NOTICE", f"{self.client_id} successfully connected to broker!")
            self.connected = True
        else:
            self.log_message("ERROR", f"{self.client_id} failed to connect to broker. Retrying...")

    def publish_message(self, topic, message):
        if self.connected:
            self.client.publish(topic, message + self.generate_hash(message))
            self.log_message("NOTICE", f"{self.client_id} published message: {message}")
        else:
            self.log_message("ERROR", f"{self.client_id} is not connected to broker!")

    def subscribe_to_topic(self, topic):
        self.client.subscribe(topic)
        self.log_message("NOTICE", f"{self.client_id} subscribed to topic: {topic}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        self.lost_connection = True
        self.log_message("NOTICE", f"{self.client_id} has disconnected from broker!")

    def purpose_disconnect(self):
        self.log_message("NOTICE", f"{self.client_id} has purposely disconnected!")
        if not self.connected:
            return
        self.connected = False
        self.client.loop_stop()

    def is_connected(self):
        return self.connected

    def log_message(self, log_level, message_to_log):
        if log_level == 'NOTICE':
            self.logger.log(logging.NOTICE, message_to_log)
        elif log_level == 'WARNING':
            self.logger.log(logging.WARNING, message_to_log)
        elif log_level == 'ERROR':
            self.logger.log(logging.ERROR, message_to_log)
        elif log_level == 'CRITICAL':
            self.logger.log(logging.CRITICAL, message_to_log)

    @staticmethod
    def generate_hash(message_to_hash):
        hash_object = hashlib.sha256(message_to_hash.encode())
        return hash_object.hexdigest()
