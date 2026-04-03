import base64
import json
import sys
from typing import Dict, Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.backends import default_backend


class JwkManager:
    """Manages JWK (JSON Web Key) generation and conversion."""

    @staticmethod
    def _int_to_base64url(val: int) -> str:
        """Converts an integer to a base64url encoded string."""
        # Convert integer to bytes using minimum required length
        val_bytes = val.to_bytes((val.bit_length() + 7) // 8, byteorder='big')
        return base64.urlsafe_b64encode(val_bytes).rstrip(b'=').decode('utf-8')

    @staticmethod
    def _base64url_to_int(val_str: str) -> int:
        """Converts a base64url encoded string to an integer."""
        padding = 4 - (len(val_str) % 4)
        if padding != 4:
            val_str += '=' * padding
        val_bytes = base64.urlsafe_b64decode(val_str)
        return int.from_bytes(val_bytes, byteorder='big')

    def generate_rsa_key(self, key_size: int = 2048) -> rsa.RSAPrivateKey:
        """Generates an RSA private key."""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

    def generate_ec_key(self, curve_name: str = "P-256") -> ec.EllipticCurvePrivateKey:
        """Generates an EC private key."""
        curves = {
            "P-256": ec.SECP256R1(),
            "P-384": ec.SECP384R1(),
            "P-521": ec.SECP521R1()
        }
        if curve_name not in curves:
            raise ValueError(f"Unsupported curve: {curve_name}")
        return ec.generate_private_key(
            curve=curves[curve_name],
            backend=default_backend()
        )

    def _rsa_to_jwk(self, key: rsa.RSAPrivateKey | rsa.RSAPublicKey) -> Dict[str, Any]:
        """Converts an RSA key to JWK dictionary."""
        is_private = isinstance(key, rsa.RSAPrivateKey)
        public_key = key.public_key() if is_private else key
        public_numbers = public_key.public_numbers()

        jwk: Dict[str, Any] = {
            "kty": "RSA",
            "n": self._int_to_base64url(public_numbers.n),
            "e": self._int_to_base64url(public_numbers.e)
        }

        if is_private:
            private_numbers = key.private_numbers()
            jwk.update({
                "d": self._int_to_base64url(private_numbers.d),
                "p": self._int_to_base64url(private_numbers.p),
                "q": self._int_to_base64url(private_numbers.q),
                "dp": self._int_to_base64url(private_numbers.dmp1),
                "dq": self._int_to_base64url(private_numbers.dmq1),
                "qi": self._int_to_base64url(private_numbers.iqmp)
            })

        return jwk

    def _ec_to_jwk(self, key: ec.EllipticCurvePrivateKey | ec.EllipticCurvePublicKey) -> Dict[str, Any]:
        """Converts an EC key to JWK dictionary."""
        is_private = isinstance(key, ec.EllipticCurvePrivateKey)
        public_key = key.public_key() if is_private else key
        public_numbers = public_key.public_numbers()

        curve_name = key.curve.name
        crv_map = {
            "secp256r1": "P-256",
            "secp384r1": "P-384",
            "secp521r1": "P-521"
        }
        crv = crv_map.get(curve_name)
        if not crv:
            raise ValueError(f"Unsupported EC curve: {curve_name}")

        # The size of coordinates depends on the curve length in bytes
        coord_len = (key.curve.key_size + 7) // 8

        def pad_coord(val: int, length: int) -> str:
            val_bytes = val.to_bytes(length, byteorder='big')
            return base64.urlsafe_b64encode(val_bytes).rstrip(b'=').decode('utf-8')

        jwk: Dict[str, Any] = {
            "kty": "EC",
            "crv": crv,
            "x": pad_coord(public_numbers.x, coord_len),
            "y": pad_coord(public_numbers.y, coord_len)
        }

        if is_private:
            private_numbers = key.private_numbers()
            jwk["d"] = pad_coord(private_numbers.private_value, coord_len)

        return jwk

    def pem_to_jwk(self, pem_data: str, password: str | None = None) -> Dict[str, Any]:
        """Converts a PEM string to a JWK dictionary."""
        try:
            # Try parsing as private key first
            key = serialization.load_pem_private_key(
                pem_data.encode('utf-8'),
                password=password.encode('utf-8') if password else None,
                backend=default_backend()
            )
        except ValueError:
            try:
                # If that fails, try parsing as public key
                key = serialization.load_pem_public_key(
                    pem_data.encode('utf-8'),
                    backend=default_backend()
                )
            except ValueError:
                raise ValueError("Could not parse PEM data as RSA or EC key.")

        if isinstance(key, (rsa.RSAPrivateKey, rsa.RSAPublicKey)):
            return self._rsa_to_jwk(key)
        elif isinstance(key, (ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey)):
            return self._ec_to_jwk(key)
        else:
            raise ValueError(f"Unsupported key type: {type(key).__name__}")

    def jwk_to_pem(self, jwk_dict: Dict[str, Any], password: str | None = None) -> str:
        """Converts a JWK dictionary to a PEM string."""
        kty = jwk_dict.get("kty")
        if not kty:
            raise ValueError("JWK is missing 'kty' parameter.")

        if kty == "RSA":
            if "d" in jwk_dict:
                # Private Key
                n = self._base64url_to_int(jwk_dict["n"])
                e = self._base64url_to_int(jwk_dict["e"])
                d = self._base64url_to_int(jwk_dict["d"])
                p = self._base64url_to_int(jwk_dict.get("p", "AA")) if "p" in jwk_dict else None
                q = self._base64url_to_int(jwk_dict.get("q", "AA")) if "q" in jwk_dict else None
                dmp1 = self._base64url_to_int(jwk_dict.get("dp", "AA")) if "dp" in jwk_dict else None
                dmq1 = self._base64url_to_int(jwk_dict.get("dq", "AA")) if "dq" in jwk_dict else None
                iqmp = self._base64url_to_int(jwk_dict.get("qi", "AA")) if "qi" in jwk_dict else None

                # if primes are missing, calculate them if possible or error
                if not (p and q and dmp1 and dmq1 and iqmp):
                    # For simplicity, we require the full RSA private JWK here.
                    # It is possible to reconstruct them from n, e, d, but it's complex and usually full JWK is provided.
                    raise ValueError("RSA JWK missing prime factors (p, q, dp, dq, qi). Reconstructing them is not supported.")

                public_numbers = rsa.RSAPublicNumbers(e, n)
                private_numbers = rsa.RSAPrivateNumbers(
                    p=p,
                    q=q,
                    d=d,
                    dmp1=dmp1,
                    dmq1=dmq1,
                    iqmp=iqmp,
                    public_numbers=public_numbers
                )
                key = private_numbers.private_key(default_backend())

                encryption = serialization.BestAvailableEncryption(password.encode('utf-8')) if password else serialization.NoEncryption()
                pem = key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=encryption
                )
            else:
                # Public Key
                n = self._base64url_to_int(jwk_dict["n"])
                e = self._base64url_to_int(jwk_dict["e"])
                public_numbers = rsa.RSAPublicNumbers(e, n)
                key = public_numbers.public_key(default_backend())

                pem = key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
        elif kty == "EC":
            crv_map = {
                "P-256": ec.SECP256R1(),
                "P-384": ec.SECP384R1(),
                "P-521": ec.SECP521R1()
            }
            crv_str = jwk_dict.get("crv")
            if crv_str not in crv_map:
                raise ValueError(f"Unsupported EC curve: {crv_str}")
            curve = crv_map[crv_str]

            x = self._base64url_to_int(jwk_dict["x"])
            y = self._base64url_to_int(jwk_dict["y"])
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, curve)

            if "d" in jwk_dict:
                # Private Key
                d = self._base64url_to_int(jwk_dict["d"])
                private_numbers = ec.EllipticCurvePrivateNumbers(d, public_numbers)
                key = private_numbers.private_key(default_backend())

                encryption = serialization.BestAvailableEncryption(password.encode('utf-8')) if password else serialization.NoEncryption()
                pem = key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=encryption
                )
            else:
                # Public Key
                key = public_numbers.public_key(default_backend())
                pem = key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
        else:
            raise ValueError(f"Unsupported kty: {kty}")

        return pem.decode('utf-8')


def run_jwk_lab_logic(args) -> bool:
    """CLI logic for JWK Lab."""
    manager = JwkManager()

    try:
        if args.action == "generate":
            if args.type.upper() == "RSA":
                key = manager.generate_rsa_key(key_size=args.size)
                jwk_dict = manager._rsa_to_jwk(key)
            elif args.type.upper() == "EC":
                key = manager.generate_ec_key(curve_name=args.curve)
                jwk_dict = manager._ec_to_jwk(key)
            else:
                print(f"Error: Unsupported key type {args.type}", file=sys.stderr)
                return False

            if args.kid:
                jwk_dict["kid"] = args.kid

            print(json.dumps(jwk_dict, indent=2))
            return True

        elif args.action == "pem2jwk":
            if not args.pem:
                print("Error: --pem argument is required (provide PEM string).", file=sys.stderr)
                return False
            jwk_dict = manager.pem_to_jwk(args.pem, password=getattr(args, 'password', None))
            if args.kid:
                jwk_dict["kid"] = args.kid
            print(json.dumps(jwk_dict, indent=2))
            return True

        elif args.action == "jwk2pem":
            if not args.jwk:
                print("Error: --jwk argument is required (provide JSON string).", file=sys.stderr)
                return False
            try:
                jwk_dict = json.loads(args.jwk)
            except json.JSONDecodeError as e:
                print(f"Error parsing JWK JSON: {e}", file=sys.stderr)
                return False

            pem_str = manager.jwk_to_pem(jwk_dict, password=getattr(args, 'password', None))
            print(pem_str, end='')
            return True

        else:
            print(f"Error: Unknown action {args.action}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
