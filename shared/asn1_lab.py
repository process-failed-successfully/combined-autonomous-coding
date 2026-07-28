import base64
import binascii
from typing import Dict, Any, Union
from pyasn1.codec.der import decoder as der_decoder
from pyasn1.error import PyAsn1Error

class Asn1LabManager:
    """Manages ASN.1 parsing and decoding operations."""

    def __init__(self):
        pass

    def decode(self, payload: str, input_format: str = "auto") -> Dict[str, Any]:
        """
        Decodes a PEM, Base64, or Hex encoded ASN.1 string.
        Returns a dictionary with 'success', 'output' (human-readable string),
        and 'error' (if applicable).
        """
        payload = payload.strip()
        if not payload:
            return {"success": False, "error": "Empty payload provided."}

        raw_bytes = b""

        if input_format == "auto":
            # Heuristic detection
            if "-----BEGIN" in payload:
                input_format = "pem"
            elif all(c in "0123456789abcdefABCDEF \r\n" for c in payload):
                input_format = "hex"
            else:
                input_format = "base64"

        try:
            if input_format == "pem":
                # Strip PEM headers/footers
                lines = [line for line in payload.splitlines() if line and not line.startswith("-----")]
                b64_data = "".join(lines)
                raw_bytes = base64.b64decode(b64_data, validate=True)
            elif input_format == "hex":
                hex_data = payload.replace(" ", "").replace("\n", "").replace("\r", "")
                raw_bytes = binascii.unhexlify(hex_data)
            elif input_format == "base64":
                raw_bytes = base64.b64decode(payload, validate=True)
            else:
                return {"success": False, "error": f"Unknown format: {input_format}"}
        except (ValueError, binascii.Error) as e:
            return {"success": False, "error": f"Error decoding {input_format} data: {e}"}

        if not raw_bytes:
             return {"success": False, "error": "Could not extract binary data from payload."}

        try:
            # Decode using pyasn1 der decoder
            # The 'any' asn1Spec allows decoding without knowing the schema.
            asn1_obj, rest_of_input = der_decoder.decode(raw_bytes)
            output = asn1_obj.prettyPrint()
            if rest_of_input:
                output += f"\n\n[Warning] Unparsed trailing data: {len(rest_of_input)} bytes"

            return {"success": True, "output": output}
        except PyAsn1Error as e:
            return {"success": False, "error": f"ASN.1 decoding failed: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error during decoding: {e}"}
