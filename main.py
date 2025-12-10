#!/usr/bin/env python3
"""
Combined Autonomous Coding Agent
================================

Main entry point for running autonomous coding agents (Gemini or Cursor).
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from shared.config import Config
from shared.logger import setup_logger

# Import agent runners
# We import these lazily or handled via dispatch to avoid circular deps if any, 
# though structure should be clean.
from agents.gemini import run_autonomous_agent as run_gemini
from agents.cursor import run_autonomous_agent as run_cursor

def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous Coding Agent")
    
    parser.add_argument(
        "--project-dir", 
        type=Path, 
        default=Path("."), 
        help="Directory where the project will be created/modified (default: current directory)"
    )
    
    parser.add_argument(
        "--agent", 
        choices=["gemini", "cursor"], 
        default="gemini", 
        help="Which agent to use (default: gemini)"
    )
    
    parser.add_argument(
        "--model", 
        type=str, 
        help="Model to use (overrides default)"
    )
    
    parser.add_argument(
        "--max-iterations", 
        type=int, 
        help="Maximum number of agent iterations"
    )
    
    parser.add_argument(
        "--spec", 
        type=Path, 
        help="Path to app_spec.txt (required for new projects)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--verify-creation",
        action="store_true",
        help="Run verification test (dummy mode)"
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output"
    )
    
    return parser.parse_args()

async def main():
    args = parse_args()
    
    # Setup Logger
    # We might want to log to a file in the project directory, but we need to ensure it exists first
    args.project_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = args.project_dir / f"{args.agent}_agent_debug.log"
    logger = setup_logger(log_file=log_file, verbose=args.verbose)
    
    logger.info(f"Starting {args.agent.capitalize()} Agent on {args.project_dir}")
    
    # Create Config
    config = Config(
        project_dir=args.project_dir,
        agent_type=args.agent,
        model=args.model,
        max_iterations=args.max_iterations,
        verbose=args.verbose,
        stream_output=not args.no_stream,
        spec_file=args.spec,
        verify_creation=args.verify_creation
    )
    
    # Function to resolve spec file
    if args.spec is None:
        default_spec = args.project_dir / "app_spec.txt"
        if default_spec.exists():
            args.spec = default_spec
            logger.info(f"Using default spec file: {args.spec}")

    # Check spec requirement for fresh projects
    # We check if feature list exists to determine if it's a fresh run
    is_fresh = not config.feature_list_path.exists()
    if is_fresh and not args.spec:
        logger.error("Error: --spec argument is required for new projects! (or place 'app_spec.txt' in directory)")
        sys.exit(1)
        
    # Dispatch
    try:
        if args.agent == "gemini":
            await run_gemini(config)
        elif args.agent == "cursor":
            await run_cursor(config)
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
