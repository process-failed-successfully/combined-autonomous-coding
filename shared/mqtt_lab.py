import sys
import threading
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

class MqttLabManager:
    """
    Manages MQTT operations: connect, subscribe, publish, message handling.
    """
    def __init__(self):
        self.client: Any = None
        self.connected = False
        self.messages: List[Dict[str, Any]] = []
        self.on_message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.lock = threading.Lock()

    def is_available(self) -> bool:
        return mqtt is not None

    def connect(self, host: str, port: int, client_id: str = "", username: str = "", password: str = "") -> bool:
        if not self.is_available():
            return False

        try:
            # Create client
            if not client_id:
                import uuid
                client_id = f"agent-tui-{uuid.uuid4().hex[:8]}"

            # Using default protocol (MQTTv311 usually)
            self.client = mqtt.Client(client_id=client_id)

            if username:
                self.client.username_pw_set(username, password)

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_publish = self._on_publish
            self.client.on_subscribe = self._on_subscribe

            self.client.connect(host, port, 60)
            self.client.loop_start() # Start background thread

            # Wait for connection (simple timeout)
            for _ in range(20):
                if self.connected:
                    return True
                time.sleep(0.1)

            return self.connected # Might be false if timeout
        except Exception as e:
            print(f"Error connecting to MQTT: {e}", file=sys.stderr)
            return False

    def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.client = None

    def subscribe(self, topic: str, qos: int = 0) -> bool:
        if not self.connected or not self.client:
            return False
        try:
            result, mid = self.client.subscribe(topic, qos)
            return result == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"Error subscribing: {e}", file=sys.stderr)
            return False

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        if not self.connected or not self.client:
            return False
        try:
            info = self.client.publish(topic, payload, qos, retain)
            info.wait_for_publish(timeout=5) # Wait a bit
            return info.is_published()
        except Exception as e:
            print(f"Error publishing: {e}", file=sys.stderr)
            return False

    def _on_connect(self, client, userdata, flags, rc, *args):
        if rc == 0:
            self.connected = True
        else:
            self.connected = False

    def _on_disconnect(self, client, userdata, rc, *args):
        self.connected = False

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8', errors='replace')
        except Exception:
            payload = str(msg.payload)

        message = {
            "topic": msg.topic,
            "payload": payload,
            "qos": msg.qos,
            "retain": msg.retain,
            "timestamp": time.time()
        }

        with self.lock:
            self.messages.append(message)
            # Keep limit
            if len(self.messages) > 1000:
                self.messages.pop(0)

        if self.on_message_callback:
            try:
                self.on_message_callback(message)
            except Exception:
                pass

    def _on_publish(self, client, userdata, mid):
        pass

    def _on_subscribe(self, client, userdata, mid, granted_qos, *args):
        pass

    def get_messages(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.messages)

    def clear_messages(self):
        with self.lock:
            self.messages = []

def run_mqtt_lab_logic(args):
    """CLI logic for MQTT Lab."""
    manager = MqttLabManager()
    if not manager.is_available():
        print("❌ Error: 'paho-mqtt' library not found. Please install it with 'pip install paho-mqtt'.", file=sys.stderr)
        return False

    # Common connect args
    host = args.host
    port = args.port
    username = args.username
    password = args.password

    # Connect
    if not manager.connect(host, port, username=username, password=password):
        print(f"❌ Failed to connect to {host}:{port}")
        return False

    if args.action == "check":
        print(f"✅ Successfully connected to {host}:{port}")
        manager.disconnect()
        return True

    elif args.action == "pub":
        if manager.publish(args.topic, args.message, qos=args.qos, retain=args.retain):
            print(f"✅ Published to '{args.topic}': {args.message}")
            manager.disconnect()
            return True
        else:
            print(f"❌ Failed to publish to '{args.topic}'")
            manager.disconnect()
            return False

    elif args.action == "sub":
        if manager.subscribe(args.topic, qos=args.qos):
            print(f"✅ Subscribed to '{args.topic}'. Listening for messages (Ctrl+C to stop)...")
            try:
                last_count = 0
                while True:
                    messages = manager.get_messages()
                    if len(messages) > last_count:
                        # New messages
                        for i in range(last_count, len(messages)):
                            msg = messages[i]
                            ts = datetime.fromtimestamp(msg['timestamp']).strftime('%H:%M:%S')
                            print(f"[{ts}] {msg['topic']}: {msg['payload']}")
                        last_count = len(messages)
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopping subscription...")
                manager.disconnect()
                return True
        else:
            print(f"❌ Failed to subscribe to '{args.topic}'")
            manager.disconnect()
            return False

    # Default fallback
    manager.disconnect()
    return True
