import logging
from pathlib import Path
from typing import Optional, List, Dict

from shared.config import Config
from agents.gemini import GeminiAgent
from agents.cursor import CursorAgent
from agents.local import LocalAgent
from agents.openrouter import OpenRouterAgent
from shared.knowledge import KnowledgeManager
from shared.verify import run_lint, run_tests, run_type_check

logger = logging.getLogger(__name__)


class TroubleshootManager:
    def __init__(self, project_dir: Path, agent_type: str = "gemini", model: str = None):
        self.project_dir = project_dir
        self.knowledge_manager = KnowledgeManager()

        # Init Agent
        config = Config(
            project_dir=self.project_dir,
            agent_type=agent_type,
            model=model,
            max_iterations=1,
            stream_output=True,
        )

        agent_class_map = {
            "gemini": GeminiAgent,
            "cursor": CursorAgent,
            "local": LocalAgent,
            "openrouter": OpenRouterAgent,
        }
        agent_class = agent_class_map.get(agent_type, GeminiAgent)
        self.agent = agent_class(config)

    def detect_issues(self) -> Dict[str, Dict]:
        """Runs verification checks and returns failures."""
        issues = {}

        # Lint
        lint_res = run_lint(self.project_dir)
        if not lint_res["success"]:
            issues["lint"] = lint_res

        # Test
        test_res = run_tests(self.project_dir)
        if not test_res["success"]:
            issues["test"] = test_res

        # Type Check
        type_res = run_type_check(self.project_dir)
        if not type_res["success"]:
            issues["type"] = type_res

        return issues

    def search_knowledge(self, query: str) -> List[str]:
        """Simple keyword search in knowledge base."""
        items = self.knowledge_manager.list_knowledge()
        results = []
        if not query:
            return []
        q_lower = query.lower()
        for item in items:
            if item.content and (q_lower in item.content.lower() or q_lower in item.category.lower()):
                results.append(f"[{item.category}] {item.content}")
        return results

    async def diagnose(self, issues: Dict[str, Dict], user_query: str = None) -> str:
        """
        Diagnoses the issue using the agent.
        """
        # Prepare context
        context = "Detected Issues:\n"
        search_terms = []

        if user_query:
            context += f"User Report: {user_query}\n"
            search_terms.append(user_query)

        for check, res in issues.items():
            context += f"\n--- {check.upper()} FAILURE ---\n"
            context += res.get("stdout", "")[:2000]  # Truncate
            context += res.get("stderr", "")[:2000]
            search_terms.append(f"{check} failure")

        relevant_knowledge = []
        for term in search_terms:
            relevant_knowledge.extend(self.search_knowledge(term))

        knowledge_text = "\n".join(set(relevant_knowledge))

        prompt = f"""
You are an expert Troubleshooter.
Diagnose the following issues.

{context}

RELEVANT KNOWLEDGE BASE:
{knowledge_text}

INSTRUCTIONS:
1. Analyze the root cause.
2. Propose a fix (provide code blocks).
3. DO NOT execute any write_file or bash commands yet. Just propose.
4. If you are unsure, ask for more information.
"""
        status, response, actions = await self.agent.run_agent_session(prompt)
        return response

    async def apply_fix(self) -> str:
        """
        Asks the agent to apply the previously proposed fix.
        """
        prompt = "Please apply the fix you proposed using write_file or bash commands."
        status, response, actions = await self.agent.run_agent_session(prompt)
        return response

    def learn(self, issue_summary: str, fix_summary: str):
        """
        Saves the solution to the knowledge base.
        """
        content = f"Issue: {issue_summary}\nFix: {fix_summary}"
        self.knowledge_manager.add_knowledge(content, category="TROUBLESHOOTING", source="troubleshoot_agent")


async def run_troubleshoot_logic(
    project_dir: Path,
    issue: Optional[str] = None,
    agent_type: str = "gemini",
    model: Optional[str] = None,
    yes: bool = False
) -> bool:
    print(f"--- Troubleshooting in {project_dir} ---")
    manager = TroubleshootManager(project_dir, agent_type, model)

    # 1. Detect
    print("Detecting issues...")
    issues = manager.detect_issues()

    if not issues and not issue:
        print("✅ No automated issues found.")
        # If user provided no issue and no checks failed, maybe ask user?
        if not issue:
            # Check if interactive session
            if not yes:
                try:
                    issue = input("No automated errors found. Describe the issue (or press Enter to exit): ").strip()
                except (EOFError, KeyboardInterrupt):
                    issue = ""

            if not issue:
                return True

    if issues:
        print(f"⚠️  Found {len(issues)} automated check failures.")

    # 2. Diagnose
    print("Diagnosing with AI...")
    response = await manager.diagnose(issues, user_query=issue)

    print("\n--- Diagnosis & Plan ---")
    print(response)

    # 3. Apply
    if not yes:
        try:
            confirm = input("\nDo you want to apply the proposed fix? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                return True
        except (EOFError, KeyboardInterrupt):
            print("Aborted.")
            return True

    print("Applying fix...")
    await manager.apply_fix()

    # 4. Verify (Optional, reusing detect)
    print("Verifying fix...")
    new_issues = manager.detect_issues()
    if not new_issues:
        print("✅ Issues resolved!")
        # 5. Learn
        should_learn = yes
        if not yes:
            try:
                confirm_learn = input("Save this solution to Knowledge Base? [Y/n]: ").strip().lower()
                if confirm_learn in ['y', '']:
                    should_learn = True
            except (EOFError, KeyboardInterrupt):
                should_learn = False

        if should_learn:
            manager.learn(issue or "Automated Errors", "Fixed by Agent")
            print("✅ Saved to Knowledge Base.")
    else:
        print("⚠️  Issues still persist.")
        # Retry loop could go here

    return True
