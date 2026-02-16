import sys
import json
import time
from typing import Optional, List, Dict, Any

try:
    import kafka
    from kafka import KafkaConsumer, KafkaProducer, KafkaAdminClient
    from kafka.admin import NewTopic
    from kafka.errors import KafkaError
except ImportError:
    kafka = None

class KafkaLabManager:
    """
    Manages Kafka operations: list, consume, produce, create, delete.
    """
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers.split(',')

    def _check_kafka(self) -> bool:
        if kafka is None:
            print("Error: 'kafka-python' library not installed. Please run 'pip install kafka-python'.", file=sys.stderr)
            return False
        return True

    def list_topics(self) -> List[str]:
        """Lists all topics."""
        if not self._check_kafka(): return []

        try:
            consumer = KafkaConsumer(bootstrap_servers=self.bootstrap_servers)
            topics = consumer.topics()
            consumer.close()
            return sorted(list(topics))
        except Exception as e:
            print(f"Error listing topics: {e}", file=sys.stderr)
            return []

    def describe_topic(self, topic: str) -> Dict[str, Any]:
        """Gets topic details."""
        if not self._check_kafka(): return {}

        try:
            consumer = KafkaConsumer(bootstrap_servers=self.bootstrap_servers)
            partitions = consumer.partitions_for_topic(topic)
            consumer.close()

            if partitions is None:
                return {}

            return {
                "topic": topic,
                "partitions": list(partitions),
                "count": len(partitions)
            }
        except Exception as e:
            print(f"Error describing topic: {e}", file=sys.stderr)
            return {}

    def create_topic(self, topic: str, partitions: int = 1, replication_factor: int = 1) -> bool:
        """Creates a new topic."""
        if not self._check_kafka(): return False

        try:
            admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            new_topic = NewTopic(name=topic, num_partitions=partitions, replication_factor=replication_factor)
            admin.create_topics(new_topics=[new_topic], validate_only=False)
            admin.close()
            return True
        except Exception as e:
            print(f"Error creating topic: {e}", file=sys.stderr)
            return False

    def delete_topic(self, topic: str) -> bool:
        """Deletes a topic."""
        if not self._check_kafka(): return False

        try:
            admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            admin.delete_topics(topics=[topic])
            admin.close()
            return True
        except Exception as e:
            print(f"Error deleting topic: {e}", file=sys.stderr)
            return False

    def produce(self, topic: str, value: str, key: Optional[str] = None) -> bool:
        """Produces a message to a topic."""
        if not self._check_kafka(): return False

        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )

            future = producer.send(topic, value=value, key=key)
            result = future.get(timeout=10) # Block until sent
            producer.close()

            print(f"Sent message to {topic} (partition: {result.partition}, offset: {result.offset})")
            return True
        except Exception as e:
            print(f"Error producing message: {e}", file=sys.stderr)
            return False

    def consume(self, topic: str, group_id: Optional[str] = None, from_beginning: bool = False, limit: int = 0, follow: bool = False):
        """Consumes messages from a topic."""
        if not self._check_kafka(): return

        try:
            auto_offset_reset = 'earliest' if from_beginning else 'latest'

            # If no group_id is provided, we use a random one to avoid committing offsets or interfering with others
            # or None if we just want to subscribe?
            # kafka-python consumer needs a group_id for auto-commit, but can work without it.

            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=bool(group_id),
                value_deserializer=lambda x: x.decode('utf-8', errors='replace'),
                key_deserializer=lambda x: x.decode('utf-8', errors='replace') if x else None,
                consumer_timeout_ms=10000 if not follow else float('inf') # 10s timeout if not following
            )

            print(f"Consuming from {topic}...")
            count = 0

            try:
                for message in consumer:
                    key_str = f"Key: {message.key} | " if message.key else ""
                    print(f"[{message.partition}:{message.offset}] {key_str}{message.value}")

                    count += 1
                    if limit > 0 and count >= limit:
                        break
            except KeyboardInterrupt:
                print("\nStopped.")
            finally:
                consumer.close()

        except Exception as e:
            print(f"Error consuming messages: {e}", file=sys.stderr)

def run_kafka_lab_logic(args):
    """CLI logic for Kafka Lab."""

    # Default port check/fix
    bootstrap = args.bootstrap
    if ":" not in bootstrap:
        bootstrap += ":9092"

    manager = KafkaLabManager(bootstrap_servers=bootstrap)

    if args.action == "list":
        topics = manager.list_topics()
        if topics:
            print("--- Topics ---")
            for t in topics:
                print(f"  - {t}")
        else:
            print("No topics found or connection failed.")
            sys.exit(1)

    elif args.action == "describe":
        if not args.topic:
            print("Error: --topic required.", file=sys.stderr)
            sys.exit(1)

        info = manager.describe_topic(args.topic)
        if info:
            print(f"Topic: {info['topic']}")
            print(f"Partitions: {info['count']}")
            print(f"Ids: {info['partitions']}")
        else:
            print(f"Topic '{args.topic}' not found or error.", file=sys.stderr)
            sys.exit(1)

    elif args.action == "create":
        if not args.topic:
            print("Error: --topic required.", file=sys.stderr)
            sys.exit(1)

        if manager.create_topic(args.topic, args.partitions, args.replication):
            print(f"✅ Topic '{args.topic}' created.")
        else:
            sys.exit(1)

    elif args.action == "delete":
        if not args.topic:
            print("Error: --topic required.", file=sys.stderr)
            sys.exit(1)

        if manager.delete_topic(args.topic):
            print(f"✅ Topic '{args.topic}' deleted.")
        else:
            sys.exit(1)

    elif args.action == "produce":
        if not args.topic:
            print("Error: --topic required.", file=sys.stderr)
            sys.exit(1)

        if not args.value:
            # Read from stdin
            print("Reading from stdin (Press Ctrl+D to finish, one line per message)...")
            try:
                for line in sys.stdin:
                    line = line.strip()
                    if line:
                        manager.produce(args.topic, line, args.key)
            except KeyboardInterrupt:
                pass
        else:
            manager.produce(args.topic, args.value, args.key)

    elif args.action == "consume":
        if not args.topic:
            print("Error: --topic required.", file=sys.stderr)
            sys.exit(1)

        manager.consume(
            args.topic,
            group_id=args.group,
            from_beginning=args.from_beginning,
            limit=args.limit,
            follow=args.follow
        )

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
