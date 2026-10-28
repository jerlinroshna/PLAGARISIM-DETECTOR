import ast
import difflib
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseASTAnalyzer

class PythonASTNormalizer(ast.NodeVisitor):
    """Walks Python AST and extracts a sequence of normalized structural tokens

    where variable names and identifiers are anonymized.
    """

    def __init__(self):
        self.var_map: Dict[str, str] = {}
        self.var_counter = 0
        self.tokens: List[str] = []
        self.node_counts: Dict[str, int] = {}
        self.builtins = {
            "print", "len", "range", "int", "str", "float", "list", "dict", "set",
            "tuple", "min", "max", "sum", "sorted", "enumerate", "zip", "open",
            "input", "isinstance", "type", "abs", "round"
        }

    def get_var_token(self, name: str) -> str:
        if name in self.builtins:
            return f"BUILTIN_{name}"
        if name not in self.var_map:
            self.var_map[name] = f"VAR_{self.var_counter}"
            self.var_counter += 1
        return self.var_map[name]

    def record_node(self, node_type: str):
        self.tokens.append(node_type)
        self.node_counts[node_type] = self.node_counts.get(node_type, 0) + 1

    def generic_visit(self, node):
        node_name = node.__class__.__name__

        # Record control flow and statement structure
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.record_node("FUNC_DEF")
            self.tokens.append(self.get_var_token(node.name))
        elif isinstance(node, ast.ClassDef):
            self.record_node("CLASS_DEF")
            self.tokens.append(self.get_var_token(node.name))
        elif isinstance(node, ast.arg):
            self.record_node("ARG")
            self.tokens.append(self.get_var_token(node.arg))
        elif isinstance(node, ast.For):
            self.record_node("LOOP_FOR")
        elif isinstance(node, ast.While):
            self.record_node("LOOP_WHILE")
        elif isinstance(node, ast.If):
            self.record_node("BRANCH_IF")
        elif isinstance(node, ast.Assign):
            self.record_node("ASSIGN")
        elif isinstance(node, ast.AugAssign):
            op_name = node.op.__class__.__name__
            self.record_node(f"AUG_ASSIGN_{op_name}")
        elif isinstance(node, ast.Return):
            self.record_node("RETURN")
        elif isinstance(node, ast.Call):
            self.record_node("CALL")
        elif isinstance(node, ast.BinOp):
            op_name = node.op.__class__.__name__
            self.record_node(f"BINOP_{op_name}")
        elif isinstance(node, ast.UnaryOp):
            op_name = node.op.__class__.__name__
            self.record_node(f"UNARY_{op_name}")
        elif isinstance(node, ast.Compare):
            ops = "_".join(op.__class__.__name__ for op in node.ops)
            self.record_node(f"COMPARE_{ops}")
        elif isinstance(node, ast.Name):
            self.record_node(f"NAME_{self.get_var_token(node.id)}")
        elif isinstance(node, ast.Constant):
            val_type = type(node.value).__name__
            self.record_node(f"LIT_{val_type}")
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            self.record_node(f"CONTAINER_{node_name}")
        elif isinstance(node, (ast.Break, ast.Continue, ast.Pass)):
            self.record_node(f"FLOW_{node_name}")

        super().generic_visit(node)


class PythonASTAnalyzer(BaseASTAnalyzer):
    """AST Structural Analyzer for Python source code using Python's native `ast` library."""

    def __init__(self):
        super().__init__("python")

    def parse_and_extract_structure(self, code: str) -> Tuple[List[str], Dict[str, int], bool, str]:
        """Parses Python code into normalized AST tokens.

        Returns (tokens, node_counts, success, error_message).
        """
        try:
            tree = ast.parse(code)
            normalizer = PythonASTNormalizer()
            normalizer.visit(tree)
            return normalizer.tokens, normalizer.node_counts, True, ""
        except SyntaxError as e:
            return [], {}, False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return [], {}, False, f"AST parsing error: {str(e)}"

    def compute_similarity(self, code_a: str, code_b: str) -> Dict[str, Any]:
        tokens_a, counts_a, success_a, err_a = self.parse_and_extract_structure(code_a)
        tokens_b, counts_b, success_b, err_b = self.parse_and_extract_structure(code_b)

        if not success_a or not success_b:
            err_msg = err_a if not success_a else err_b
            return {
                "score": 0.0,
                "success": False,
                "error": err_msg,
                "summary": f"Python AST analysis limitation: {err_msg}",
                "tokens_a_count": len(tokens_a),
                "tokens_b_count": len(tokens_b)
            }

        if not tokens_a or not tokens_b:
            return {
                "score": 0.0,
                "success": True,
                "summary": "Empty AST structure extracted.",
                "tokens_a_count": 0,
                "tokens_b_count": 0
            }

        # 1. Structural token sequence alignment (LCS via SequenceMatcher)
        matcher = difflib.SequenceMatcher(None, tokens_a, tokens_b)
        seq_ratio = matcher.ratio()

        # 2. Structural feature histogram similarity
        all_keys = set(counts_a.keys()) | set(counts_b.keys())
        dot_product = sum(counts_a.get(k, 0) * counts_b.get(k, 0) for k in all_keys)
        norm_a = sum(counts_a.get(k, 0) ** 2 for k in all_keys) ** 0.5
        norm_b = sum(counts_b.get(k, 0) ** 2 for k in all_keys) ** 0.5
        cosine_sim = (dot_product / (norm_a * norm_b)) if (norm_a * norm_b) > 0 else 0.0

        # Weighted combination: 70% structural token sequence + 30% node histogram
        combined_ast = (seq_ratio * 0.70 + cosine_sim * 0.30) * 100.0
        score = min(100.0, max(0.0, round(combined_ast, 2)))

        summary = (
            f"Normalized Python AST extracted {len(tokens_a)} and {len(tokens_b)} structural nodes. "
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
