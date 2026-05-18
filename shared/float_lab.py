import struct
import sys
from typing import Dict, Any

class FloatLabManager:
    def encode(self, value: float, precision: str = "single") -> Dict[str, Any]:
        try:
            if precision == "single":
                packed = struct.pack('>f', value)
                bits = 32
            elif precision == "double":
                packed = struct.pack('>d', value)
                bits = 64
            else:
                return {"success": False, "error": f"Unknown precision: {precision}"}

            hex_str = packed.hex()
            bin_str = bin(int.from_bytes(packed, 'big'))[2:].zfill(bits)

            if precision == "single":
                sign = bin_str[0]
                exponent = bin_str[1:9]
                mantissa = bin_str[9:]
            else:
                sign = bin_str[0]
                exponent = bin_str[1:12]
                mantissa = bin_str[12:]

            return {
                "success": True,
                "value": value,
                "precision": precision,
                "hex": hex_str,
                "bin": f"{sign} {exponent} {mantissa}",
                "sign": sign,
                "exponent": exponent,
                "mantissa": mantissa
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def decode(self, hex_str: str, precision: str = "single") -> Dict[str, Any]:
        try:
            hex_str = hex_str.strip().replace("0x", "").replace(" ", "")
            if precision == "single":
                if len(hex_str) != 8:
                    return {"success": False, "error": "Single precision requires exactly 8 hex characters."}
                packed = bytes.fromhex(hex_str)
                value = struct.unpack('>f', packed)[0]
                bits = 32
            elif precision == "double":
                if len(hex_str) != 16:
                    return {"success": False, "error": "Double precision requires exactly 16 hex characters."}
                packed = bytes.fromhex(hex_str)
                value = struct.unpack('>d', packed)[0]
                bits = 64
            else:
                return {"success": False, "error": f"Unknown precision: {precision}"}

            bin_str = bin(int.from_bytes(packed, 'big'))[2:].zfill(bits)

            if precision == "single":
                sign = bin_str[0]
                exponent = bin_str[1:9]
                mantissa = bin_str[9:]
            else:
                sign = bin_str[0]
                exponent = bin_str[1:12]
                mantissa = bin_str[12:]

            return {
                "success": True,
                "value": value,
                "precision": precision,
                "hex": hex_str,
                "bin": f"{sign} {exponent} {mantissa}",
                "sign": sign,
                "exponent": exponent,
                "mantissa": mantissa
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

def run_float_lab_logic(args) -> bool:
    manager = FloatLabManager()

    if getattr(args, "action", None) == "encode":
        if args.value is None:
            print("Error: --value is required for encode.", file=sys.stderr)
            return False
        res = manager.encode(args.value, args.precision)
        if res["success"]:
            print(f"Value:     {res['value']}")
            print(f"Precision: {res['precision']}")
            print(f"Hex:       {res['hex']}")
            print(f"Binary:    {res['bin']}")
            return True
        else:
            print(f"Error: {res['error']}", file=sys.stderr)
            return False

    elif getattr(args, "action", None) == "decode":
        if args.hex is None:
            print("Error: --hex is required for decode.", file=sys.stderr)
            return False
        res = manager.decode(args.hex, args.precision)
        if res["success"]:
            print(f"Hex:       {res['hex']}")
            print(f"Precision: {res['precision']}")
            print(f"Value:     {res['value']}")
            print(f"Binary:    {res['bin']}")
            return True
        else:
            print(f"Error: {res['error']}", file=sys.stderr)
            return False

    return False
