import subprocess

tests_to_run = [
    "tests/test_tui.py::TestTUIComponents::test_interact_tab_submit",
    "tests/test_tui_codemap.py::TestCodeMapTab::test_codemap_population",
    "tests/test_tui_codereview.py::TestCodeReviewTab::test_review_all",
    "tests/test_tui_codereview.py::TestCodeReviewTab::test_review_selected",
    "tests/test_tui_config.py::TestConfigTab::test_load_config_ui",
    "tests/test_tui_docs.py::TestTUIDocs::test_check_links",
    "tests/test_tui_docs.py::TestTUIDocs::test_docstrings_scan",
    "tests/test_tui_docs.py::TestTUIDocs::test_generate_openapi",
    "tests/test_tui_health.py::TestTuiHealth::test_run_health_check",
    "tests/test_tui_plan.py::TestPlanTab::test_generate_plan",
    "tests/test_tui_playground.py::TestTUIPlayground::test_create_file",
    "tests/test_tui_playground.py::TestTUIPlayground::test_load_files",
    "tests/test_tui_playground.py::TestTUIPlayground::test_run_file",
    "tests/test_tui_profile.py::TestTUIProfile::test_analyze_profile",
    "tests/test_tui_profile.py::TestTUIProfile::test_run_profile",
    "tests/test_tui_recipes.py::TestRecipesTab::test_compose_and_load",
    "tests/test_tui_recipes.py::TestRecipesTab::test_create_recipe",
    "tests/test_tui_recipes.py::TestRecipesTab::test_run_recipe",
    "tests/test_tui_recipes_learn.py::TestRecipesLearn::test_learn_recipe_ui",
    "tests/test_tui_refactor.py::TestTUIRefactor::test_apply_changes",
    "tests/test_tui_refactor.py::TestTUIRefactor::test_preview_refactor",
    "tests/test_tui_release.py::TestReleaseTab::test_dry_run",
    "tests/test_tui_release.py::TestReleaseTab::test_execute_release",
    "tests/test_tui_release.py::TestReleaseTab::test_generate_preview",
    "tests/test_tui_release.py::TestReleaseTab::test_load_status",
    "tests/test_tui_replace.py::TestTuiReplace::test_apply_replace",
    "tests/test_tui_replace.py::TestTuiReplace::test_preview_replace",
    "tests/test_tui_scaffold.py::TestTUIScaffold::test_create_project_ai",
    "tests/test_tui_scaffold.py::TestTUIScaffold::test_generate_preview",
    "tests/test_tui_search.py::TestTuiSearch::test_perform_search",
    "tests/test_tui_session.py::TestTUISession::test_create_session",
    "tests/test_tui_session.py::TestTUISession::test_load_sessions",
    "tests/test_tui_session.py::TestTUISession::test_select_session",
    "tests/test_tui_tasks.py::TestTUITasks::test_tasks_filter",
    "tests/test_tui_tasks.py::TestTUITasks::test_tasks_load",
    "tests/test_tui_tasks.py::TestTUITasks::test_tasks_refresh",
    "tests/test_tui_testgen.py::TestTUITestGen::test_generate_tests_success",
    "tests/test_tui_testgen.py::TestTUITestGen::test_save_tests",
    "tests/test_tui_troubleshoot.py::TestTUITroubleshoot::test_run_analysis",
    "tests/test_tui_troubleshoot.py::TestTUITroubleshoot::test_run_diagnosis",
    "tests/test_tui_troubleshoot.py::TestTUITroubleshoot::test_run_fix"
]

for t in tests_to_run:
    print(f"Running {t}")
    res = subprocess.run(["python3", "-m", "pytest", t, "-q"], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FAILED: {t}")
        print(res.stdout)
    else:
        print(f"PASSED: {t}")
