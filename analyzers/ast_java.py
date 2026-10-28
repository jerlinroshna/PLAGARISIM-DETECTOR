import difflib
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseASTAnalyzer

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

class JavaASTAnalyzer(BaseASTAnalyzer):
    """AST Structural Analyzer for Java source code using javalang."""

    def __init__(self):
        super().__init__("java")

    def _extract_from_tree(self, tree) -> Tuple[List[str], Dict[str, int]]:
        tokens = []
        counts = {}
        var_map = {}
        var_counter = 0

        def get_var_token(name: str) -> str:
            nonlocal var_counter
            if name not in var_map:
                var_map[name] = f"VAR_{var_counter}"
                var_counter += 1
            return var_map[name]

        for path, node in tree:
            node_name = node.__class__.__name__
            tokens.append(node_name)
            counts[node_name] = counts.get(node_name, 0) + 1

            if hasattr(node, "name") and node.name:
                tokens.append(f"NAME_{get_var_token(node.name)}")
            if hasattr(node, "operator") and node.operator:
                tokens.append(f"OP_{node.operator}")

        return tokens, counts

    def _fallback_tokenize(self, code: str) -> Tuple[List[str], Dict[str, int]]:
        """Fallback lexical-structural tokenizer for Java snippets."""
        tokens = []
        counts = {}
        var_map = {}
        var_counter = 0

        try:
            raw_tokens = list(javalang.tokenizer.tokenize(code))
            for tok in raw_tokens:
                tok_type = tok.__class__.__name__
                if tok_type == "Identifier":
                    if tok.value not in var_map:
                        var_map[tok.value] = f"VAR_{var_counter}"
                        var_counter += 1
                    t = f"ID_{var_map[tok.value]}"
                elif tok_type == "Keyword":
                    t = f"KW_{tok.value}"
                elif tok_type == "Operator":
                    t = f"OP_{tok.value}"
                elif tok_type in ("Integer", "DecimalInteger", "String", "FloatingPoint"):
                    t = "LITERAL"
                else:
                    t = tok_type

                tokens.append(t)
                counts[t] = counts.get(t, 0) + 1
        except Exception:
            pass

        return tokens, counts

    def parse_and_extract_structure(self, code: str) -> Tuple[List[str], Dict[str, int], bool, str]:
        if not JAVALANG_AVAILABLE:
            return [], {}, False, "javalang library not installed."

        # Attempt standard compilation unit parse
        try:
            tree = javalang.parse.parse(code)
            tokens, counts = self._extract_from_tree(tree)
            return tokens, counts, True, ""
        except Exception as e_direct:
            # If code is a classless snippet, try wrapping in dummy class
            try:
                wrapped_code = f"public class DummyClassWrapper {{\n{code}\n}}"
                tree = javalang.parse.parse(wrapped_code)
                tokens, counts = self._extract_from_tree(tree)
                return tokens, counts, True, ""
            except Exception:
                # Fallback to structural Java token stream
                tokens, counts = self._fallback_tokenize(code)
                if tokens:
                    return tokens, counts, True, "Parsed via structural token fallback"
                return [], {}, False, f"Java parse error: {str(e_direct)}"

    def compute_similarity(self, code_a: str, code_b: str) -> Dict[str, Any]:
        tokens_a, counts_a, success_a, err_a = self.parse_and_extract_structure(code_a)
        tokens_b, counts_b, success_b, err_b = self.parse_and_extract_structure(code_b)

        if not success_a or not success_b:
            err_msg = err_a if not success_a else err_b
            return {
                "score": 0.0,
                "success": False,
                "error": err_msg,
                "summary": f"Java AST analysis limitation: {err_msg}",
                "tokens_a_count": len(tokens_a),
                "tokens_b_count": len(tokens_b)
            }

        if not tokens_a or not tokens_b:
            return {
                "score": 0.0,
                "success": True,
                "summary": "Empty structural AST representation.",
                "tokens_a_count": 0,
                "tokens_b_count": 0
            }

        matcher = difflib.SequenceMatcher(None, tokens_a, tokens_b)
        seq_ratio = matcher.ratio()

        all_keys = set(counts_a.keys()) | set(counts_b.keys())
        dot_product = sum(counts_a.get(k, 0) * counts_b.get(k, 0) for k in all_keys)
        norm_a = sum(counts_a.get(k, 0) ** 2 for k in all_keys) ** 0.5
        norm_b = sum(counts_b.get(k, 0) ** 2 for k in all_keys) ** 0.5
        cosine_sim = (dot_product / (norm_a * norm_b)) if (norm_a * norm_b) > 0 else 0.0

        combined = (seq_ratio * 0.70 + cosine_sim * 0.30) * 100.0
        score = min(100.0, max(0.0, round(combined, 2)))

        summary = (
            f"Java structural AST extracted {len(tokens_a)} and {len(tokens_b)} nodes. "
            f"Sequence alignment: {round(seq_ratio * 100, 1)}%, Feature similarity: {round(cosine_sim * 100, 1)}%."
        )

        return {
            "score": score,
            "success": True,
            "sequence_ratio": round(seq_ratio * 100, 2),
            "feature_similarity": round(cosine_sim * 100, 2),
            "summary": summary,
            "tokens_a_count": len(tokens_a),
            "tokens_b_count": len(tokens_b)
        }
