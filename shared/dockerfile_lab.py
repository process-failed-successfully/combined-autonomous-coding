import argparse
import sys
from typing import List, Optional

class DockerfileLabManager:
    """Manages Dockerfile generation logic."""

    @staticmethod
    def generate_dockerfile(
        base_image: str,
        project_type: str = "generic",
        workdir: str = "/app",
        ports: Optional[List[str]] = None,
        env_vars: Optional[List[str]] = None,
        entrypoint: str = "",
        cmd: str = ""
    ) -> str:
        """Generates a Dockerfile based on the provided parameters."""
        lines = []

        # Base image
        lines.append(f"FROM {base_image}")
        lines.append("")

        # Working Directory
        lines.append(f"WORKDIR {workdir}")
        lines.append("")

        # Environment variables
        if env_vars:
            for env in env_vars:
                # Expecting ENV=VALUE or just ENV
                if "=" in env:
                    key, val = env.split("=", 1)
                    lines.append(f"ENV {key}=\"{val}\"")
                else:
                    lines.append(f"ENV {env}=\"\"")
            lines.append("")

        # Project specific setups
        if project_type.lower() == "python":
            lines.append("COPY requirements.txt .")
            lines.append("RUN pip install --no-cache-dir -r requirements.txt")
            lines.append("")
            lines.append("COPY . .")
            lines.append("")
        elif project_type.lower() == "node":
            lines.append("COPY package*.json ./")
            lines.append("RUN npm install")
            lines.append("")
            lines.append("COPY . .")
            lines.append("")
        elif project_type.lower() == "go":
            lines.append("COPY go.mod go.sum ./")
            lines.append("RUN go mod download")
            lines.append("")
            lines.append("COPY . .")
            lines.append("RUN go build -o main .")
            lines.append("")
        elif project_type.lower() == "rust":
            lines.append("COPY Cargo.toml Cargo.lock ./")
            lines.append("COPY src ./src")
            lines.append("RUN cargo build --release")
            lines.append("")
        else:
            lines.append("COPY . .")
            lines.append("")

        # Expose ports
        if ports:
            for port in ports:
                lines.append(f"EXPOSE {port}")
            lines.append("")

        # Entrypoint and CMD
        if entrypoint:
            lines.append(f"ENTRYPOINT {entrypoint}")

        if cmd:
            lines.append(f"CMD {cmd}")

        return "\n".join(lines).strip() + "\n"

def run_dockerfile_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Dockerfile Lab."""
    manager = DockerfileLabManager()

    if getattr(args, 'action', None) == "generate":
        try:
            ports = args.ports.split(",") if args.ports else None
            env_vars = args.env.split(",") if args.env else None

            result = manager.generate_dockerfile(
                base_image=args.base_image,
                project_type=args.type,
                workdir=args.workdir,
                ports=ports,
                env_vars=env_vars,
                entrypoint=args.entrypoint,
                cmd=args.cmd
            )

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"✅ Dockerfile written to {args.output}")
            else:
                print(result)
            return True
        except Exception as e:
            print(f"❌ Error generating Dockerfile: {e}", file=sys.stderr)
            return False
    return False
