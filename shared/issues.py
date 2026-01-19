
import sys
import argparse
import subprocess
from pathlib import Path
from shared.config_loader import load_config_from_file
from shared.github_client import GitHubClient
from shared.git import get_current_branch

def _run_issues_logic(args):
    """
    Logic for the 'issues' command.
    Lists issues and allows interactive selection to start work.
    """
    project_dir = args.project_dir.resolve()

    # Load config to get GitHub token
    file_config = load_config_from_file(profile=getattr(args, 'profile', None))
    github_token = file_config.get("github_token")
    github_host = file_config.get("github_host")

    import os
    if not github_token:
        github_token = os.environ.get("GITHUB_TOKEN")

    if not github_token:
        print("❌ Error: GitHub token not found. Please set GITHUB_TOKEN environment variable or run 'configure'.", file=sys.stderr)
        return False

    client = GitHubClient(token=github_token, host=github_host or "github.com")

    # Fetch issues
    print(f"--- Fetching {args.state} issues for {project_dir.name} ---")
    try:
        issues = client.get_issues(project_dir, state=args.state, assignee=args.assignee)
    except Exception as e:
        print(f"❌ Error fetching issues: {e}", file=sys.stderr)
        return False

    if not issues:
        print("No issues found.")
        return True

    # Display issues
    print(f"\n{'#':<6} | {'Title':<50} | {'Assignee':<15} | {'Labels'}")
    print("-" * 90)

    for i, issue in enumerate(issues):
        number = str(issue['number'])
        title = issue['title']
        if len(title) > 47:
            title = title[:47] + "..."

        assignee = "Unassigned"
        if issue.get('assignee'):
            assignee = issue['assignee']['login']
        if len(assignee) > 15:
            assignee = assignee[:12] + "..."

        labels = ", ".join([l['name'] for l in issue.get('labels', [])])

        print(f"{number:<6} | {title:<50} | {assignee:<15} | {labels}")

    # Interactive mode
    if args.interactive:
        print("\nEnter issue number to start working on it, or 'q' to quit.")
        while True:
            choice = input("> ").strip().lower()
            if choice == 'q':
                break

            # Check if choice is a valid issue number from the list
            selected_issue = next((i for i in issues if str(i['number']) == choice), None)

            if selected_issue:
                _start_work_on_issue(project_dir, selected_issue)
                break
            else:
                print("Invalid issue number. Please try again.")

    return True

def _start_work_on_issue(project_dir, issue):
    """
    Helper to create a branch and switch to it for a selected issue.
    """
    number = issue['number']
    title = issue['title']

    # Sanitize title for branch name
    import re
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    branch_name = f"issue-{number}-{slug}"

    # Truncate branch name if too long
    if len(branch_name) > 50:
        branch_name = branch_name[:50].rstrip('-')

    print(f"\n--- Starting work on Issue #{number} ---")
    print(f"Proposed branch name: {branch_name}")

    confirm = input("Create and checkout this branch? [Y/n]: ").strip().lower()
    if confirm not in ['y', '']:
        print("Aborted.")
        return

    git_path = "git" # Assuming git is in path, verified earlier in main.py usually

    try:
        # Check if branch exists
        subprocess.run(
            [git_path, "-C", str(project_dir), "rev-parse", "--verify", branch_name],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        print(f"Branch '{branch_name}' already exists. Checking out...")
        subprocess.run(
            [git_path, "-C", str(project_dir), "checkout", branch_name],
            check=True
        )
    except subprocess.CalledProcessError:
        # Branch does not exist, create it
        print(f"Creating branch '{branch_name}'...")
        try:
            subprocess.run(
                [git_path, "-C", str(project_dir), "checkout", "-b", branch_name],
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating branch: {e}", file=sys.stderr)
            return

    print(f"✅ Switched to branch '{branch_name}'.")
    print("You can now start coding!")
