import re
import sys
from typing import Dict, Any, Optional

class ArnLabManager:
    """Manages parsing, validating, and constructing AWS ARNs."""

    # Base pattern for an ARN
    ARN_PATTERN = re.compile(
        r"^arn:(?P<partition>[^:]+):(?P<service>[^:]+):(?P<region>[^:]*):(?P<account_id>[^:]*):(?P<resource>.*)$"
    )

    def parse(self, arn: str) -> Dict[str, Any]:
        """
        Parses an ARN into its constituent parts.
        """
        match = self.ARN_PATTERN.match(arn)
        if not match:
            return {
                "success": False,
                "error": "Invalid ARN format. Must start with 'arn:' and have 6 colon-separated sections."
            }

        data = match.groupdict()

        # Further split the resource part if possible
        resource_part = data["resource"]
        resource_type = None
        resource_id = None

        # Some resources use / or : to separate type and ID
        if ":" in resource_part:
            parts = resource_part.split(":", 1)
            resource_type = parts[0]
            resource_id = parts[1]
        elif "/" in resource_part:
            parts = resource_part.split("/", 1)
            resource_type = parts[0]
            resource_id = parts[1]
        else:
            resource_id = resource_part

        return {
            "success": True,
            "partition": data["partition"],
            "service": data["service"],
            "region": data["region"] or None,
            "account_id": data["account_id"] or None,
            "resource": resource_part,
            "resource_type": resource_type,
            "resource_id": resource_id
        }

    def construct(self, service: str, resource: str, partition: str = "aws", region: str = "", account_id: str = "") -> Dict[str, Any]:
        """
        Constructs an ARN from components.
        """
        if not service or not resource:
            return {
                "success": False,
                "error": "Service and resource are required to construct an ARN."
            }

        arn = f"arn:{partition}:{service}:{region}:{account_id}:{resource}"

        # Basic validation of the constructed ARN
        if not self.ARN_PATTERN.match(arn):
            return {
                "success": False,
                "error": f"Failed to construct a valid ARN. Result: {arn}"
            }

        return {
            "success": True,
            "arn": arn
        }

def run_arn_lab_logic(args):
    """
    CLI handler for ARN Lab.
    """
    manager = ArnLabManager()

    if args.action == "parse":
        if not args.arn:
            print("Error: --arn is required for 'parse' action.", file=sys.stderr)
            sys.exit(1)

        result = manager.parse(args.arn)
        if result["success"]:
            import json
            # Remove success key before printing
            del result["success"]
            print(json.dumps(result, indent=2))
            sys.exit(0)
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "construct":
        if not args.service or not args.resource:
            print("Error: --service and --resource are required for 'construct' action.", file=sys.stderr)
            sys.exit(1)

        partition = args.partition if hasattr(args, "partition") and args.partition else "aws"
        region = args.region if hasattr(args, "region") and args.region else ""
        account = args.account if hasattr(args, "account") and args.account else ""

        result = manager.construct(
            service=args.service,
            resource=args.resource,
            partition=partition,
            region=region,
            account_id=account
        )

        if result["success"]:
            print(result["arn"])
            sys.exit(0)
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown action '{args.action}'.", file=sys.stderr)
        sys.exit(1)
