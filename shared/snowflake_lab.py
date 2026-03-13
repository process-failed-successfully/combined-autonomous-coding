import sys
import time
from typing import List, Dict, Any
from datetime import datetime, timezone


class SnowflakeManager:
    """Manages Snowflake ID operations (generation, parsing)."""

    DEFAULT_EPOCH = 1288834974657  # Twitter epoch (Nov 04, 2010)

    def __init__(self, epoch: int = DEFAULT_EPOCH):
        self.epoch = epoch
        self.sequence = 0
        self.last_timestamp = -1

        # Bit allocations
        self.worker_id_bits = 5
        self.datacenter_id_bits = 5
        self.sequence_bits = 12

        # Max values
        self.max_worker_id = -1 ^ (-1 << self.worker_id_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_id_bits)
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)

        # Shifts
        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_id_bits
        self.timestamp_left_shift = self.sequence_bits + self.worker_id_bits + self.datacenter_id_bits

    def _current_time_millis(self) -> int:
        return int(time.time() * 1000)

    def _wait_for_next_millis(self, last_timestamp: int) -> int:
        timestamp = self._current_time_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_time_millis()
        return timestamp

    def generate_one(self, worker_id: int = 1, datacenter_id: int = 1) -> int:
        """Generates a single Snowflake ID."""
        if worker_id > self.max_worker_id or worker_id < 0:
            raise ValueError(f"worker_id can't be greater than {self.max_worker_id} or less than 0")
        if datacenter_id > self.max_datacenter_id or datacenter_id < 0:
            raise ValueError(f"datacenter_id can't be greater than {self.max_datacenter_id} or less than 0")

        timestamp = self._current_time_millis()

        if timestamp < self.last_timestamp:
            raise ValueError(f"Clock moved backwards. Refusing to generate id for {self.last_timestamp - timestamp} milliseconds")

        if self.last_timestamp == timestamp:
            self.sequence = (self.sequence + 1) & self.max_sequence
            if self.sequence == 0:
                timestamp = self._wait_for_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        snowflake = ((timestamp - self.epoch) << self.timestamp_left_shift) | \
                    (datacenter_id << self.datacenter_id_shift) | \
                    (worker_id << self.worker_id_shift) | \
                    self.sequence

        return snowflake

    def generate(self, count: int = 1, worker_id: int = 1, datacenter_id: int = 1) -> List[int]:
        """Generates multiple Snowflake IDs."""
        return [self.generate_one(worker_id, datacenter_id) for _ in range(count)]

    def parse(self, snowflake: int) -> Dict[str, Any]:
        """Decodes and inspects a Snowflake ID."""
        if snowflake < 0:
            return {"valid": False, "error": "Snowflake ID cannot be negative"}

        sequence = snowflake & self.max_sequence
        worker_id = (snowflake >> self.worker_id_shift) & self.max_worker_id
        datacenter_id = (snowflake >> self.datacenter_id_shift) & self.max_datacenter_id
        timestamp_diff = snowflake >> self.timestamp_left_shift

        timestamp = timestamp_diff + self.epoch

        try:
            dt = datetime.fromtimestamp(timestamp / 1000.0, tz=timezone.utc).isoformat()
        except (ValueError, OverflowError):
            dt = "Invalid Date"

        return {
            "valid": True,
            "snowflake": str(snowflake),
            "timestamp": timestamp,
            "datetime": dt,
            "datacenter_id": datacenter_id,
            "worker_id": worker_id,
            "sequence": sequence,
            "epoch_used": self.epoch
        }

def run_snowflake_lab_logic(args) -> bool:
    """CLI handler for Snowflake Lab."""
    # Use specified epoch or fallback to Twitter default
    epoch = getattr(args, 'epoch', None)
    if epoch is None:
        epoch = SnowflakeManager.DEFAULT_EPOCH

    manager = SnowflakeManager(epoch=epoch)

    if args.action == "generate":
        count = getattr(args, 'count', 1)
        worker_id = getattr(args, 'worker_id', 1)
        datacenter_id = getattr(args, 'datacenter_id', 1)

        try:
            results = manager.generate(count=count, worker_id=worker_id, datacenter_id=datacenter_id)
            for res in results:
                print(res)
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "parse":
        snowflake_id = getattr(args, 'snowflake', None)
        if not snowflake_id:
            print("Error: snowflake ID is required for parse action.", file=sys.stderr)
            return False

        try:
            snowflake_int = int(snowflake_id)
        except ValueError:
            print("Error: Snowflake ID must be an integer.", file=sys.stderr)
            return False

        info = manager.parse(snowflake_int)
        if not info["valid"]:
            print(f"Error: {info['error']}", file=sys.stderr)
            return False

        print(f"--- Snowflake Inspection: {snowflake_id} ---")
        print(f"  Valid:         {info['valid']}")
        print(f"  Timestamp:     {info['timestamp']}")
        print(f"  Date:          {info['datetime']}")
        print(f"  Datacenter ID: {info['datacenter_id']}")
        print(f"  Worker ID:     {info['worker_id']}")
        print(f"  Sequence:      {info['sequence']}")
        print(f"  Epoch Used:    {info['epoch_used']}")
        return True

    return False
