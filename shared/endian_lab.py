import sys
import struct
from typing import Dict, Any, Union

class EndianManager:
    """Manages endian conversions for integers and hex strings."""

    def hex_swap(self, hex_str: str) -> str:
        """Swaps the byte order of a hex string."""
        # Strip '0x' prefix if present
        prefix = ''
        if hex_str.lower().startswith('0x'):
            prefix = hex_str[:2]
            hex_str = hex_str[2:]

        # Ensure even length (pad with 0 if needed)
        if len(hex_str) % 2 != 0:
            hex_str = '0' + hex_str

        # Split into bytes and reverse
        bytes_list = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
        reversed_bytes = bytes_list[::-1]

        return prefix + ''.join(reversed_bytes).upper()

    def int_swap(self, value: int, bits: int) -> int:
        """Swaps the byte order of an integer for a given bit size."""
        if bits not in [16, 32, 64]:
            raise ValueError("Supported bit sizes are 16, 32, and 64")

        if bits == 16:
            fmt = 'H'
            mask = 0xFFFF
        elif bits == 32:
            fmt = 'I'
            mask = 0xFFFFFFFF
        else: # 64
            fmt = 'Q'
            mask = 0xFFFFFFFFFFFFFFFF

        # Mask the value to the correct bit size
        val_masked = value & mask

        # Pack as native, unpack as swapped
        # Use '<' (little-endian) and '>' (big-endian) to swap
        # Pack as little, unpack as big is equivalent to byte swap
        packed = struct.pack(f'<{fmt}', val_masked)
        swapped = struct.unpack(f'>{fmt}', packed)[0]

        return swapped

def run_endian_lab_logic(args):
    """CLI logic for Endian Lab."""
    manager = EndianManager()

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching Endian Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-endian")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return

    if args.action == "hex":
        if not args.value:
            print("Error: Hex string required.", file=sys.stderr)
            sys.exit(1)
        result = manager.hex_swap(args.value)
        print(f"Swapped: {result}")
        sys.exit(0)

    elif args.action == "int":
        if args.value is None:
            print("Error: Integer value required.", file=sys.stderr)
            sys.exit(1)
        try:
            val = int(args.value, 0) # Parses dec, hex, oct, etc.
        except ValueError:
            print("Error: Invalid integer format.", file=sys.stderr)
            sys.exit(1)

        try:
            result = manager.int_swap(val, args.bits)
            print(f"Original: {val} ({hex(val)})")
            print(f"Swapped:  {result} ({hex(result)})")
            sys.exit(0)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"Unknown action: {args.action}", file=sys.stderr)
    sys.exit(1)
