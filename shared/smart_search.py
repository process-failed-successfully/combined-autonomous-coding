"""
Smart Search (BM25)
===================

Implements a local, TF-IDF / BM25 based search engine for the codebase.
This allows finding relevant files based on keywords without needing exact matches.
"""

import math
import re
import os
import shutil
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import Counter
import subprocess  # nosec

# Basic set of English stopwords
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for",
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm",
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't",
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't",
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's",
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
}

# Programming specific stopwords (often noise in search)
CODE_STOPWORDS = {
    "import", "from", "def", "class", "return", "if", "else", "elif", "for", "while", "try", "except", "finally",
    "with", "as", "pass", "break", "continue", "lambda", "yield", "async", "await", "raise", "print",
    "none", "null", "undefined", "var", "let", "const", "function", "public", "private", "protected", "int", "str",
    "float", "bool", "list", "dict", "self", "this"
}

ALL_STOPWORDS = STOPWORDS.union(CODE_STOPWORDS)

class SmartSearchEngine:
    """
    Implements BM25 algorithm for ranking documents.
    """
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.documents = []  # List of dicts: {path, content, tokens, len}
        self.avg_doc_len = 0
        self.doc_freqs = Counter() # Term -> number of docs containing it
        self.num_docs = 0

        # BM25 parameters
        self.k1 = 1.5
        self.b = 0.75

    def _tokenize(self, text: str) -> List[str]:
        """Splits text into tokens, lowercases, and removes stopwords."""
        # Split by non-alphanumeric characters
        raw_tokens = re.split(r'[^a-zA-Z0-9]+', text)
        tokens = []
        for t in raw_tokens:
            lowered = t.lower()
            if lowered and len(lowered) > 2 and lowered not in ALL_STOPWORDS:
                tokens.append(lowered)
        return tokens

    def index(self, file_pattern: Optional[str] = None):
        """
        Scans and indexes the codebase.
        """
        import fnmatch

        # Helper to check ignores
        git_path = shutil.which("git")
        is_git_repo = (self.project_dir / ".git").is_dir()

        def is_ignored(path: Path) -> bool:
            if is_git_repo and git_path:
                try:
                    res = subprocess.run(  # nosec
                        [git_path, "-C", str(self.project_dir), "check-ignore", "-q", str(path)],
                        capture_output=True
                    )
                    return res.returncode == 0
                except Exception:
                    return False
            return False

        ignore_dirs = {'.git', '__pycache__', '.venv', 'node_modules', 'dist', 'build', '.agent_trash', '.agent_archives'}

        total_len = 0

        for root, dirs, files in os.walk(self.project_dir):
            root_path = Path(root)
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not is_ignored(root_path / d)]

            for file in files:
                if file_pattern and not fnmatch.fnmatch(file, file_pattern):
                    continue

                file_path = root_path / file
                if is_ignored(file_path):
                    continue

                # Basic check for binary files (skip likely binaries)
                if file.endswith(('.pyc', '.so', '.o', '.exe', '.dll', '.class', '.jpg', '.png', '.sqlite', '.db')):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Limit file size to avoid memory issues (e.g. max 1MB)
                        f.seek(0, 2)
                        size = f.tell()
                        if size > 1024 * 1024:
                            continue
                        f.seek(0)

                        content = f.read()

                        tokens = self._tokenize(content)
                        if not tokens:
                            continue

                        doc_entry = {
                            "path": str(file_path.relative_to(self.project_dir)),
                            "tokens": tokens,
                            "len": len(tokens),
                            "term_freqs": Counter(tokens),
                            # Store a snippet/preview later? We don't need full content in memory if we read file on demand
                            # But for simplicity, we store path.
                        }
                        self.documents.append(doc_entry)

                        # Update global stats
                        unique_tokens = set(tokens)
                        for token in unique_tokens:
                            self.doc_freqs[token] += 1

                        total_len += len(tokens)

                except Exception:  # nosec
                    continue

        self.num_docs = len(self.documents)
        if self.num_docs > 0:
            self.avg_doc_len = total_len / self.num_docs

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Performs BM25 search.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = []

        for doc in self.documents:
            score = 0
            for term in query_tokens:
                if term not in doc["term_freqs"]:
                    continue

                freq = doc["term_freqs"][term]
                # Inverse Document Frequency (IDF)
                # IDF = log((N - n + 0.5) / (n + 0.5) + 1)
                n = self.doc_freqs[term]
                idf = math.log(((self.num_docs - n + 0.5) / (n + 0.5)) + 1)

                # Term Frequency component (BM25)
                # ((k1 + 1) * freq) / (k1 * (1 - b + b * (doc_len / avg_doc_len)) + freq)
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc["len"] / (self.avg_doc_len or 1)))

                score += idf * (numerator / denominator)

            if score > 0:
                scores.append((score, doc))

        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)

        # Format results
        results = []
        for score, doc in scores[:limit]:
            # Generate a snippet
            snippet = self._generate_snippet(doc["path"], query_tokens)
            results.append({
                "file": doc["path"],
                "score": score,
                "snippet": snippet
            })

        return results

    def _generate_snippet(self, file_path: str, query_tokens: List[str]) -> str:
        """Reads the file and extracts a relevant snippet."""
        try:
            full_path = self.project_dir / file_path
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Find the best line (most query terms)
            best_line_idx = -1
            max_matches = 0

            for i, line in enumerate(lines):
                # Tokenize line simply
                line_tokens = set(self._tokenize(line))
                matches = sum(1 for t in query_tokens if t in line_tokens)
                if matches > max_matches:
                    max_matches = matches
                    best_line_idx = i

            if best_line_idx != -1:
                # Return context around the line
                start = max(0, best_line_idx - 1)
                end = min(len(lines), best_line_idx + 2)
                snippet_lines = [l.strip() for l in lines[start:end]]
                return " ... ".join(snippet_lines)

            # Fallback: first few lines
            return " ... ".join([l.strip() for l in lines[:3]])

        except Exception:
            return "(Could not read file for snippet)"
