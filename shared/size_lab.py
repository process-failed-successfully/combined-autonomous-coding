import sys
import re

def parse_size(size_str: str) -> dict:
    """Parses a string like '1.5GB' to bytes, returning a dict with details."""
    size_str = size_str.strip()
    match = re.match(r"^([\d\.]+)\s*([a-zA-Z]+)?$", size_str)

    if not match:
        return {"success": False, "error": f"Invalid format: '{size_str}'. Expected e.g., '1.5 GB'."}

    try:
        value = float(match.group(1))
    except ValueError:
        return {"success": False, "error": f"Invalid number in: '{size_str}'"}

    unit = match.group(2)
    if not unit:
        # Default to bytes
        return {"success": True, "bytes": int(value)}

    unit = unit.lower()

    # SI Units (decimal)
    si_multipliers = {
        'b': 1,
        'k': 1000, 'kb': 1000,
        'm': 1000**2, 'mb': 1000**2,
        'g': 1000**3, 'gb': 1000**3,
        't': 1000**4, 'tb': 1000**4,
        'p': 1000**5, 'pb': 1000**5,
        'e': 1000**6, 'eb': 1000**6,
    }

    # IEC Units (binary)
    iec_multipliers = {
        'ki': 1024, 'kib': 1024,
        'mi': 1024**2, 'mib': 1024**2,
        'gi': 1024**3, 'gib': 1024**3,
        'ti': 1024**4, 'tib': 1024**4,
        'pi': 1024**5, 'pib': 1024**5,
        'ei': 1024**6, 'eib': 1024**6,
    }

    if unit in iec_multipliers:
        return {"success": True, "bytes": int(value * iec_multipliers[unit])}
    elif unit in si_multipliers:
        return {"success": True, "bytes": int(value * si_multipliers[unit])}
    else:
        return {"success": False, "error": f"Unknown unit: '{unit}'"}


def format_size(bytes_val: int, use_iec: bool = True, precision: int = 2) -> dict:
    """Formats bytes into human readable string."""
    if bytes_val < 0:
        return {"success": False, "error": "Bytes cannot be negative."}

    if bytes_val == 0:
        return {"success": True, "formatted": "0 B"}

    if use_iec:
        units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']
        base = 1024.0
    else:
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
        base = 1000.0

    val = float(bytes_val)
    unit_index = 0

    while val >= base and unit_index < len(units) - 1:
        val /= base
        unit_index += 1

    format_str = f"{{:.{precision}f}} {{}}"

    # If it's bytes, we don't need precision
    if unit_index == 0:
        format_str = "{:.0f} {}"

    formatted = format_str.format(val, units[unit_index])

    return {"success": True, "formatted": formatted, "value": val, "unit": units[unit_index]}


def run_size_lab_logic(args) -> bool:
    """CLI handler for size lab."""
    if args.action == "parse":
        if not args.size:
            print("Error: --size is required.", file=sys.stderr)
            return False

        res = parse_size(args.size)
        if res["success"]:
            print(f"{res['bytes']}")
            return True
        else:
            print(f"Error: {res['error']}", file=sys.stderr)
            return False

    elif args.action == "format":
        if args.bytes is None:
            print("Error: --bytes is required.", file=sys.stderr)
            return False

        try:
            bytes_val = int(args.bytes)
        except ValueError:
            print("Error: --bytes must be an integer.", file=sys.stderr)
            return False

        res = format_size(bytes_val, use_iec=not args.si)
        if res["success"]:
            print(f"{res['formatted']}")
            return True
        else:
            print(f"Error: {res['error']}", file=sys.stderr)
            return False

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        return False
