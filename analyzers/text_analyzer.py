import re
import difflib
from typing import List, Dict, Any, Tuple

class TextAnalyzer:
    """Analyzes textual similarity between two code snippets using normalization,

    token-level n-gram fingerprinting, and sequence matching.
    """

    @staticmethod
    def strip_comments_and_docstrings(code: str, language: str) -> str:
        """Removes single-line and multi-line comments and docstrings based on language."""
        if not code:
            return ""

        lang = language.lower()
        if lang == "python":
            # Remove multi-line triple quoted docstrings
            code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\')', '', code, flags=re.DOTALL)
            # Remove single line comments
            lines = []
            for line in code.splitlines():
                if "#" in line:
                    line = line.split("#", 1)[0]
                lines.append(line)
            return "\n".join(lines)
        else:
            # C, C++, Java, JavaScript (/* ... */ and // ...)
            # Remove block comments
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            # Remove single-line comments
            lines = []
            for line in code.splitlines():
                if "//" in line:
                    line = line.split("//", 1)[0]
                lines.append(line)
            return "\n".join(lines)

    @staticmethod
    def normalize_text(code: str, language: str) -> List[str]:
        """Strips comments and normalizes lines, preserving non-empty meaningful lines."""
        cleaned = TextAnalyzer.strip_comments_and_docstrings(code, language)
        normalized_lines = []
        for line in cleaned.splitlines():
            stripped = " ".join(line.split())
            if stripped:
                normalized_lines.append(stripped)
        return normalized_lines

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Splits code text into lexical tokens (identifiers, keywords, operators, symbols)."""
        return re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|\d+|==|!=|<=|>=|&&|\|\||[-+*/%=<>(){}\[\],;.]', text)

    @classmethod
    def compute_similarity(cls, code_a: str, code_b: str, language: str) -> Dict[str, Any]:
        """Computes text similarity percentage and identifies matching line spans."""
        if not code_a or not code_b or not code_a.strip() or not code_b.strip():
            return {
                "score": 0.0,
                "matching_spans": [],
                "matched_token_ratio": 0.0,
                "summary": "One or both code snippets are empty."
            }

        lines_a_orig = code_a.splitlines()
        lines_b_orig = code_b.splitlines()

        norm_lines_a = cls.normalize_text(code_a, language)
        norm_lines_b = cls.normalize_text(code_b, language)

        if not norm_lines_a or not norm_lines_b:
            return {
                "score": 0.0,
                "matching_spans": [],
                "matched_token_ratio": 0.0,
                "summary": "No non-empty code lines after stripping comments."
            }

        # 1. Line-level SequenceMatcher on normalized lines
        matcher = difflib.SequenceMatcher(None, norm_lines_a, norm_lines_b)
        line_ratio = matcher.ratio()

        # 2. Token-level Winnowing / Jaccard similarity
        tokens_a = cls.tokenize(" ".join(norm_lines_a))
        tokens_b = cls.tokenize(" ".join(norm_lines_b))

        token_ratio = 0.0
        if tokens_a and tokens_b:
            # 4-gram tokens
            k = 4
            if len(tokens_a) >= k and len(tokens_b) >= k:
                ngrams_a = set(tuple(tokens_a[i:i+k]) for i in range(len(tokens_a) - k + 1))
                ngrams_b = set(tuple(tokens_b[i:i+k]) for i in range(len(tokens_b) - k + 1))
                intersection = len(ngrams_a & ngrams_b)
                union = len(ngrams_a | ngrams_b)
                token_ratio = (intersection / union) if union > 0 else 0.0
            else:
                set_a = set(tokens_a)
                set_b = set(tokens_b)
                union = len(set_a | set_b)
                token_ratio = (len(set_a & set_b) / union) if union > 0 else 0.0

        # Weighted text similarity score
        raw_score = (line_ratio * 0.6 + token_ratio * 0.4) * 100.0
        score = min(100.0, max(0.0, round(raw_score, 2)))

        # 3. Find matching line blocks mapped to original line numbers (1-indexed)
        # We match original lines by stripped content to highlight exact lines in UI
        orig_stripped_a = [l.strip() for l in lines_a_orig]
        orig_stripped_b = [l.strip() for l in lines_b_orig]

        # Ignore trivial lines like single brackets, braces, or includes
        def is_trivial(line: str) -> bool:
            clean = line.strip()
            return clean in {"", "{", "}", "(", ")", ";", "};", "return 0;", "pass"}

        orig_matcher = difflib.SequenceMatcher(
            lambda x: is_trivial(x),
            orig_stripped_a,
            orig_stripped_b
        )

        matching_spans = []
        for match in orig_matcher.get_matching_blocks():
            if match.size >= 2:  # at least 2 consecutive lines
                student_start = match.a + 1
                student_end = match.a + match.size
                hist_start = match.b + 1
                hist_end = match.b + match.size
                
                # Check that at least one non-trivial line is contained
                block_lines = orig_stripped_a[match.a : match.a + match.size]
                if any(not is_trivial(l) for l in block_lines):
                    matching_spans.append({
                        "student_start": student_start,
                        "student_end": student_end,
                        "historical_start": hist_start,
                        "historical_end": hist_end,
                        "size": match.size,
                        "preview": "\n".join(lines_a_orig[match.a : match.a + min(3, match.size)])
                    })

        summary = f"Text comparison matched {len(matching_spans)} continuous block(s) with {round(token_ratio * 100, 1)}% token overlap."

        return {
            "score": score,
            "matching_spans": matching_spans,
            "matched_token_ratio": round(token_ratio * 100, 2),
            "line_similarity_ratio": round(line_ratio * 100, 2),
            "summary": summary
        }
