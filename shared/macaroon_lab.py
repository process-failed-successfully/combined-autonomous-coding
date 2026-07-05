import argparse
from typing import Dict, Any, List, Optional
from pymacaroons import Macaroon, Verifier


class MacaroonManager:
    @staticmethod
    def generate(location: str, identifier: str, secret: str) -> Dict[str, Any]:
        try:
            m = Macaroon(location=location, identifier=identifier, key=secret)
            return {"success": True, "token": m.serialize()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def inspect(token: str) -> Dict[str, Any]:
        try:
            m = Macaroon.deserialize(token)
            caveats = [c.caveat_id.decode('utf-8') if isinstance(c.caveat_id, bytes) else c.caveat_id for c in m.caveats]
            return {
                "success": True,
                "location": m.location,
                "identifier": m.identifier.decode('utf-8') if isinstance(m.identifier, bytes) else m.identifier,
                "signature": m.signature,
                "caveats": caveats
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def add_caveat(token: str, caveat: str) -> Dict[str, Any]:
        try:
            m = Macaroon.deserialize(token)
            m.add_first_party_caveat(caveat)
            return {"success": True, "token": m.serialize()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def verify(token: str, secret: str, caveats: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            m = Macaroon.deserialize(token)
            v = Verifier()
            if caveats:
                for c in caveats:
                    v.satisfy_exact(c)
            v.verify(m, secret)
            return {"success": True, "message": "Macaroon is valid."}
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_macaroon_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for macaroon-lab."""
    if args.action == "generate" or args.action == "gen":
        result = MacaroonManager.generate(args.location, args.identifier, args.secret)
        if result["success"]:
            print(f"Token: {result['token']}")
            return True
        else:
            print(f"Error: {result['error']}")
            return False

    elif args.action == "inspect":
        result = MacaroonManager.inspect(args.token)
        if result["success"]:
            print(f"Location: {result['location']}")
            print(f"Identifier: {result['identifier']}")
            print(f"Signature: {result['signature']}")
            if result['caveats']:
                print("Caveats:")
                for c in result['caveats']:
                    print(f"  - {c}")
            else:
                print("Caveats: None")
            return True
        else:
            print(f"Error: {result['error']}")
            return False

    elif args.action == "caveat" or args.action == "add-caveat":
        result = MacaroonManager.add_caveat(args.token, args.caveat)
        if result["success"]:
            print(f"New Token: {result['token']}")
            return True
        else:
            print(f"Error: {result['error']}")
            return False

    elif args.action == "verify":
        caveats = args.satisfy if hasattr(args, 'satisfy') and args.satisfy else []
        result = MacaroonManager.verify(args.token, args.secret, caveats)
        if result["success"]:
            print(result["message"])
            return True
        else:
            print(f"Verification Failed: {result['error']}")
            return False

    return False
