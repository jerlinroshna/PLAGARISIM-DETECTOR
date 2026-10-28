import difflib
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseASTAnalyzer

try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False

class JavaScriptASTAnalyzer(BaseASTAnalyzer):
    """AST Structural Analyzer for JavaScript source code using esprima."""

    def __init__(self):
        super().__init__("javascript")

    def _traverse_node(self, node, tokens: List[str], counts: Dict[str, int], var_map: Dict[str, str], var_counter: List[int]):
        if not node or not hasattr(node, "type"):
            return

        node_type = node.type
        tokens.append(node_type)
        counts[node_type] = counts.get(node_type, 0) + 1

        if node_type == "Identifier":
            name = getattr(node, "name", "")
            if name not in var_map:
                var_map[name] = f"VAR_{var_counter[0]}"
                var_counter[0] += 1
            tokens.append(f"NAME_{var_map[name]}")

        elif node_type == "Literal":
            raw = getattr(node, "raw", "")
            tokens.append("LITERAL")

        elif node_type == "BinaryExpression":
            op = getattr(node, "operator", "")
            tokens.append(f"OP_{op}")

        # Recurse into children
        for key, val in node.__dict__.items():
            if key in ("type", "loc", "range"):
                continue
            if isinstance(val, list):
                for item in val:
                    if hasattr(item, "type"):
                        self._traverse_node(item, tokens, counts, var_map, var_counter)
            elif hasattr(val, "type"):
                self._traverse_node(val, tokens, counts, var_map, var_counter)

    def parse_and_extract_structure(self, code: str) -> Tuple[List[str], Dict[str, int], bool, str]:
        if not ESPRIMA_AVAILABLE:
            return [], {}, False, "esprima library not installed."

        try:
            tree = esprima.parseScript(code, {"tolerant": True})
            tokens = []
            counts = {}
            var_map = {}
            var_counter = [0]
            self._traverse_node(tree, tokens, counts, var_map, var_counter)
            return tokens, counts, True, ""
        except Exception as e:
            # Try parseModule
            try:
                tree = esprima.parseModule(code, {"tolerant": True})
                tokens = []
                counts = {}
                var_map = {}
                var_counter = [0]
                self._traverse_node(tree, tokens, counts, var_map, var_counter)
                return tokens, counts, True, ""
            except Exception as e2:
                return [], {}, False, f"JavaScript parse error: {str(e2)}"

    def compute_similarity(self, code_a: str, code_b: str) -> Dict[str, Any]:
        tokens_a, counts_a, success_a, err_a = self.parse_and_extract_structure(code_a)
        tokens_b, counts_b, success_b, err_b = self.parse_and_extract_structure(code_b)

        if not success_a or not success_b:
            err_msg = err_a if not success_a else err_b
            return {
                "score": 0.0,
                "success": False,
                "error": err_msg,
                "summary": f"JavaScript AST analysis limitation: {err_msg}",
                "tokens_a_count": len(tokens_a),
                "tokens_b_count": len(tokens_b)
            }

        if not tokens_a or not tokens_b:
            return {
                "score": 0.0,
                "success": True,
                "summary": "Empty structural JavaScript AST representation.",
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
            f"JavaScript AST extracted {len(tokens_a)} and {len(tokens_b)} structural nodes. "
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
