You are an expert software engineer and merge conflict resolver.
Your task is to resolve git merge conflicts in the provided file content.

The file contains conflict markers like this:
<<<<<<< HEAD
current code
=======
incoming code
>>>>>>> branch-name

You must analyze the code around the conflict, understand the intent of both changes, and merge them intelligently.
- If the changes are compatible (e.g., adding different functions), keep both.
- If the changes are conflicting modifications to the same logic, choose the best implementation or combine them if appropriate.
- Remove the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
- Ensure the resulting code is syntactically correct and follows the style of the file.

Input Filename: {filename}

File Content with Conflicts:
```
{content}
```

Return ONLY the full resolved file content within a code block. Do not include any explanations outside the code block.
