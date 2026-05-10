import sys
import time
from typing import Optional, Dict, Any, Generator

try:
    import pika
    from pika.exceptions import AMQPError
except ImportError:
    pika = None
    AMQPError = None

class AmqpLabManager:
    """
    Manages AMQP operations: publish, consume, declare_queue, declare_exchange, bind.
    """
    def __init__(self, url: str = "amqp://guest:guest@localhost:5672/"):
        self.url = url

    def _check_pika(self) -> bool:
        if pika is None:
            return False
        return True

    def is_available(self) -> bool:
        return self._check_pika()

    def _get_connection(self):
        if not self._check_pika():
            raise RuntimeError("pika library not installed.")
        parameters = pika.URLParameters(self.url)
        return pika.BlockingConnection(parameters)

    def declare_queue(self, queue: str, durable: bool = True) -> bool:
        if not self._check_pika(): return False
        try:
            connection = self._get_connection()
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=durable)
            connection.close()
            return True
        except Exception as e:
            print(f"Error declaring queue: {e}", file=sys.stderr)
            return False

    def declare_exchange(self, exchange: str, exchange_type: str = 'direct', durable: bool = True) -> bool:
        if not self._check_pika(): return False
        try:
            connection = self._get_connection()
            channel = connection.channel()
            channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=durable)
            connection.close()
            return True
        except Exception as e:
            print(f"Error declaring exchange: {e}", file=sys.stderr)
            return False

    def bind(self, queue: str, exchange: str, routing_key: str = "") -> bool:
        if not self._check_pika(): return False
        try:
            connection = self._get_connection()
            channel = connection.channel()
            channel.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)
            connection.close()
            return True
        except Exception as e:
            print(f"Error binding queue to exchange: {e}", file=sys.stderr)
            return False

    def publish(self, exchange: str, routing_key: str, body: str) -> bool:
        if not self._check_pika(): return False
        try:
            connection = self._get_connection()
            channel = connection.channel()

            # Simple publish
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2, # make message persistent
                )
            )
            connection.close()
            return True
        except Exception as e:
            print(f"Error publishing message: {e}", file=sys.stderr)
            return False

    def consume_messages(self, queue: str, limit: int = 0) -> Generator[Dict[str, Any], None, None]:
        if not self._check_pika(): return

        try:
            connection = self._get_connection()
            channel = connection.channel()

            # Ensure queue exists before consuming? Actually let basic_consume fail or user must declare it first.

            count = 0
            # For simplicity in generator without blocking forever unpredictably, we'll use basic_get if we just want a few,
            # or basic_consume with a timeout. Let's use basic_consume and connection.sleep or just a simple loop.
            # actually basic_get is easier for a finite loop.

            while True:
                method_frame, header_frame, body = channel.basic_get(queue=queue, auto_ack=True)
                if method_frame:
                    yield {
                        'routing_key': method_frame.routing_key,
                        'exchange': method_frame.exchange,
                        'delivery_tag': method_frame.delivery_tag,
                        'body': body.decode('utf-8', errors='replace') if body else ""
                    }
                    count += 1
                    if limit > 0 and count >= limit:
                        break
                else:
                    # no more messages right now
                    break

            connection.close()

        except Exception as e:
            print(f"Error consuming messages: {e}", file=sys.stderr)

    def consume(self, queue: str, limit: int = 0):
        print(f"Consuming from queue: {queue}...")
        for msg in self.consume_messages(queue, limit):
            print(f"[Exchange: {msg['exchange']} | Routing Key: {msg['routing_key']}] {msg['body']}")


def run_amqp_lab_logic(args):
    """CLI logic for AMQP Lab."""

    manager = AmqpLabManager(url=args.url)

    if not manager.is_available():
        print("Error: 'pika' library not installed. Please run 'pip install pika'.", file=sys.stderr)
        sys.exit(1)

    if args.action == "declare-queue":
        if not args.queue:
            print("Error: --queue required.", file=sys.stderr)
            sys.exit(1)

        if manager.declare_queue(args.queue):
            print(f"✅ Queue '{args.queue}' declared.")
        else:
            sys.exit(1)

    elif args.action == "declare-exchange":
        if not args.exchange:
            print("Error: --exchange required.", file=sys.stderr)
            sys.exit(1)

        if manager.declare_exchange(args.exchange, exchange_type=getattr(args, 'exchange_type', 'direct')):
            print(f"✅ Exchange '{args.exchange}' declared.")
        else:
            sys.exit(1)

    elif args.action == "bind":
        if not args.queue or not args.exchange:
            print("Error: --queue and --exchange required.", file=sys.stderr)
            sys.exit(1)

        routing_key = args.routing_key or ''
        if manager.bind(args.queue, args.exchange, routing_key):
            print(f"✅ Queue '{args.queue}' bound to exchange '{args.exchange}' with routing key '{routing_key}'.")
        else:
            sys.exit(1)

    elif args.action == "publish":
        if not args.exchange and not getattr(args, 'routing_key', None):
            print("Error: at least --exchange or --routing-key (as queue name for default exchange) required.", file=sys.stderr)
            sys.exit(1)

        exchange = args.exchange or ""
        routing_key = args.routing_key or ""

        if not args.body:
            print("Reading from stdin (Press Ctrl+D to finish, one line per message)...")
            try:
                for line in sys.stdin:
                    line = line.strip()
                    if line:
                        if manager.publish(exchange, routing_key, line):
                            print(f"Sent: {line}")
            except KeyboardInterrupt:
                pass
        else:
            if manager.publish(exchange, routing_key, args.body):
                print(f"Sent message to Exchange: '{exchange}', Routing Key: '{routing_key}'")

    elif args.action == "consume":
        if not args.queue:
            print("Error: --queue required.", file=sys.stderr)
            sys.exit(1)

        manager.consume(args.queue, limit=getattr(args, 'limit', 0))

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
