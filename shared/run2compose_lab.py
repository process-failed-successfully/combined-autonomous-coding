import sys
import yaml
import shlex
import argparse
from typing import Dict, Any


class Run2ComposeManager:
    """Manages parsing of docker run commands and generating docker-compose.yml content."""

    def __init__(self):
        # We define an internal argument parser to parse the docker run string
        self.parser = argparse.ArgumentParser(add_help=False)
        self.parser.add_argument('-d', '--detach', action='store_true')
        self.parser.add_argument('--name')
        self.parser.add_argument('-p', '--publish', action='append', default=[])
        self.parser.add_argument('-v', '--volume', action='append', default=[])
        self.parser.add_argument('-e', '--env', action='append', default=[])
        self.parser.add_argument('--env-file', action='append', default=[])
        self.parser.add_argument('--network')
        self.parser.add_argument('--restart')
        self.parser.add_argument('--user', '-u')
        self.parser.add_argument('--workdir', '-w')
        self.parser.add_argument('--privileged', action='store_true')
        self.parser.add_argument('--rm', action='store_true')
        self.parser.add_argument('-it', action='store_true')  # combined -i and -t
        self.parser.add_argument('-i', '--interactive', action='store_true')
        self.parser.add_argument('-t', '--tty', action='store_true')

    def parse(self, run_command: str) -> Dict[str, Any]:
        """Parses a docker run command string into a compose dict."""
        # Clean up the string
        run_command = run_command.strip()
        if run_command.startswith("docker run"):
            run_command = run_command[len("docker run"):].strip()
        elif run_command.startswith("docker container run"):
            run_command = run_command[len("docker container run"):].strip()

        try:
            tokens = shlex.split(run_command)
        except ValueError as e:
            return {"error": f"Error parsing command string: {e}"}

        if not tokens:
            return {"error": "Empty command string."}

        # We need to separate known args from image and command
        # Parse known args
        parsed, unknown = self.parser.parse_known_args(tokens)

        if not unknown:
            return {"error": "No image specified."}

        # The first unknown argument should be the image name. Everything after is the command.
        image = unknown[0]
        command = unknown[1:] if len(unknown) > 1 else []

        service_name = parsed.name if parsed.name else "app"

        service_def: Dict[str, Any] = {
            "image": image
        }

        if parsed.restart:
            service_def["restart"] = parsed.restart

        if parsed.publish:
            service_def["ports"] = parsed.publish

        if parsed.volume:
            service_def["volumes"] = parsed.volume

        if parsed.env:
            service_def["environment"] = parsed.env

        if parsed.env_file:
            service_def["env_file"] = parsed.env_file

        if parsed.network:
            service_def["networks"] = [parsed.network]

        if parsed.user:
            service_def["user"] = parsed.user

        if parsed.workdir:
            service_def["working_dir"] = parsed.workdir

        if parsed.privileged:
            service_def["privileged"] = True

        if parsed.tty or getattr(parsed, 'it', False):
            service_def["tty"] = True

        if parsed.interactive or getattr(parsed, 'it', False):
            service_def["stdin_open"] = True

        if command:
            service_def["command"] = command

        compose_dict: Dict[str, Any] = {
            "version": "3.8",
            "services": {
                service_name: service_def
            }
        }

        # Add top-level networks if needed
        if parsed.network:
            compose_dict["networks"] = {
                parsed.network: {"external": True}
            }

        return {"success": True, "compose": compose_dict}

    def to_yaml(self, compose_dict: Dict[str, Any]) -> str:
        """Converts a compose dict to a YAML string."""
        return yaml.dump(compose_dict, sort_keys=False, default_flow_style=False)


def run_run2compose_lab_logic(args):
    """CLI Entry point for Run2Compose Lab."""
    # Run2Compose might not have a separate 'action' for CLI, just take input
    if getattr(args, "action", None) == "convert":
        if not args.command_str:
            print("Error: --command is required.", file=sys.stderr)
            sys.exit(1)

        manager = Run2ComposeManager()
        result = manager.parse(args.command_str)
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        yaml_str = manager.to_yaml(result["compose"])

        if args.output:
            try:
                with open(args.output, "w") as f:
                    f.write(yaml_str)
                print(f"✅ Successfully wrote compose file to {args.output}")
            except Exception as e:
                print(f"❌ Error writing to {args.output}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(yaml_str)
        sys.exit(0)
    else:
        print("Invalid action.", file=sys.stderr)
        sys.exit(1)
