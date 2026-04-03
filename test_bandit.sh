bandit -r . -c "pyproject.toml" -ll -b bandit_baseline.json -f custom > bandit_out.txt
cat bandit_out.txt
