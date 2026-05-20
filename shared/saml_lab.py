import sys
import argparse
import base64
import zlib
import urllib.parse
import defusedxml.minidom


class SamlLabManager:
    """Manager for SAML operations."""

    def decode(self, saml_string: str, inflate: bool = False) -> str:
        """
        Decodes a SAML string.
        Optionally inflates it (used for HTTP-Redirect binding).
        Returns pretty-printed XML if valid, else returns the decoded string or throws.
        """
        if not saml_string:
            raise ValueError("Empty SAML string provided.")

        # Sometimes users copy URL-encoded strings
        if "%" in saml_string:
            saml_string = urllib.parse.unquote(saml_string)

        # Strip common SAML parameter prefixes if present
        if saml_string.startswith("SAMLRequest="):
            saml_string = saml_string[len("SAMLRequest="):]
        elif saml_string.startswith("SAMLResponse="):
            saml_string = saml_string[len("SAMLResponse="):]

        # Base64 decode
        try:
            # Add padding if missing
            padding_needed = len(saml_string) % 4
            if padding_needed:
                saml_string += "=" * (4 - padding_needed)

            decoded_bytes = base64.b64decode(saml_string, validate=True)
        except Exception as e:
            raise ValueError(f"Base64 decoding failed: {e}")

        # Inflate if requested (or auto-detect)
        # HTTP-Redirect binding uses DEFLATE (without zlib header, usually wbits=-15)
        if inflate:
            try:
                # Try raw deflate first
                decoded_bytes = zlib.decompress(decoded_bytes, -15)
            except zlib.error:
                try:
                    # Try with zlib header
                    decoded_bytes = zlib.decompress(decoded_bytes)
                except Exception as e:
                    raise ValueError(f"Decompression failed: {e}")

        try:
            decoded_str = decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback for some weird encodings, but typically it's utf-8
            decoded_str = decoded_bytes.decode('latin-1', errors='replace')

        # Pretty print if it's XML
        try:
            dom = defusedxml.minidom.parseString(decoded_str)
            return dom.toprettyxml(indent="  ")
        except Exception:
            # Not valid XML, just return the decoded string
            return decoded_str


def run_saml_lab_logic(args: argparse.Namespace):
    """CLI handler for SAML Lab."""
    manager = SamlLabManager()

    if getattr(args, 'decode', None) or getattr(args, 'file', None):
        saml_str = ""
        if getattr(args, 'decode', None):
            saml_str = args.decode
        elif getattr(args, 'file', None):
            try:
                with open(args.file, 'r') as f:
                    saml_str = f.read().strip()
            except IOError as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)

        try:
            result = manager.decode(saml_str, inflate=getattr(args, 'inflate', False))
            print(result)
        except Exception as e:
            print(f"Error decoding SAML: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Must provide --decode or --file.", file=sys.stderr)
        sys.exit(1)
