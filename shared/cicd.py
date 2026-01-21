from pathlib import Path
from typing import Dict


class CICDGenerator:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def detect_project_type(self) -> str:
        if (self.project_dir / "package.json").exists():
            return "node"
        if (self.project_dir / "requirements.txt").exists() or (self.project_dir / "pyproject.toml").exists():
            return "python"
        if (self.project_dir / "go.mod").exists():
            return "go"
        return "unknown"

    def generate(self, platform: str) -> Dict[str, str]:
        project_type = self.detect_project_type()
        if project_type == "unknown":
            return {}

        if platform == "github":
            return self._generate_github(project_type)
        elif platform == "gitlab":
            return self._generate_gitlab(project_type)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def _generate_github(self, project_type: str) -> Dict[str, str]:
        content = ""
        filename = ".github/workflows/ci.yml"

        if project_type == "python":
            content = """name: Python CI

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi
    - name: Lint with flake8
      run: |
        pip install flake8
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    - name: Test with pytest
      run: |
        pip install pytest
        pytest
"""
        elif project_type == "node":
            content = """name: Node.js CI

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [18.x, 20.x]

    steps:
    - uses: actions/checkout@v3
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: npm ci
    - run: npm run build --if-present
    - run: npm test
"""
        elif project_type == "go":
            content = """name: Go

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'

    - name: Build
      run: go build -v ./...

    - name: Test
      run: go test -v ./...
"""
        return {filename: content}

    def _generate_gitlab(self, project_type: str) -> Dict[str, str]:
        content = ""
        filename = ".gitlab-ci.yml"

        if project_type == "python":
            content = """image: python:3.10

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

before_script:
  - python -V
  - pip install virtualenv
  - virtualenv venv
  - source venv/bin/activate

stages:
  - test

test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pip install pytest flake8
    - flake8 .
    - pytest
"""
        elif project_type == "node":
            content = """image: node:latest

stages:
  - build
  - test

cache:
  paths:
    - node_modules/

build:
  stage: build
  script:
    - npm install
    - npm run build --if-present

test:
  stage: test
  script:
    - npm install
    - npm test
"""
        elif project_type == "go":
            content = """image: golang:latest

stages:
  - test
  - build

format:
  stage: test
  script:
    - go fmt $(go list ./... | grep -v /vendor/)
    - go vet $(go list ./... | grep -v /vendor/)
    - go test -race $(go list ./... | grep -v /vendor/)

compile:
  stage: build
  script:
    - mkdir -p mybin
    - go build -o mybin ./...
  artifacts:
    paths:
      - mybin
"""
        return {filename: content}
