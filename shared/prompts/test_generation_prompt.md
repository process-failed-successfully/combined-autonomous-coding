You are an expert software engineer specializing in testing.
Your task is to generate a comprehensive unit test suite for the provided Python code using the {framework} framework.

Requirements:
1. Analyze the Code: Understand the functions, classes, and logic in the provided code.
2. Coverage: Aim for high code coverage. Test happy paths, edge cases, and error conditions.
3. Mocking: If the code uses external dependencies (API calls, file I/O, database access, heavy imports), use `unittest.mock` or `pytest-mock` to mock them. Do not rely on external systems.
4. Style: Follow standard Python testing conventions. Use descriptive test names.
5. Imports: Ensure all necessary imports are included. Assume the provided code is in a module that can be imported.
6. Output: Return the Python code for the test file enclosed in a Markdown code block (```python ... ```).

Source File: {file_path}

Code to test:
```python
{code}
```
