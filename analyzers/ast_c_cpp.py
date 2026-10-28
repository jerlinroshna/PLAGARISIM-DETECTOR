import re
import difflib
from typing import List, Dict, Any, Tuple
from analyzers.base import BaseASTAnalyzer

class CCppASTAnalyzer(BaseASTAnalyzer):
    """Structural AST & Grammar Analyzer for C and C++ source code."""

    def __init__(self, language: str = "c"):
        super().__init__(language)
        self.keywords = {
            "if", "else", "for", "while", "do", "switch", "case", "default",
            "return", "break", "continue", "goto", "struct", "class", "union",
            "enum", "typedef", "sizeof", "new", "delete", "try", "catch", "throw",
            "public", "private", "protected", "virtual", "override", "namespace",
            "template", "typename", "const", "static", "volatile", "inline"
        }
        self.types = {
            "int", "char", "float", "double", "void", "long", "short", "unsigned",
            "signed", "bool", "size_t", "uint32_t", "int32_t", "auto", "string"
        }
        self.standard_calls = {
            "printf", "scanf", "cout", "cin", "endl", "malloc", "free", "calloc",
            "realloc", "strlen", "strcpy", "strcmp", "memcpy", "memset", "getline",
            "push_back", "pop_back", "size", "clear", "begin", "end"
        }

    def _strip_preprocessor(self, code: str) -> str:
        """Removes preprocessor directives (#include, #define, etc.) and comments."""
        # Strip block comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Strip single line comments
        code = re.sub(r'//.*', '', code)
        
        lines = []
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # Skip #include, #define, #pragma
            lines.append(line)
        return "\n".join(lines)

    def _tokenize_code(self, clean_code: str) -> List[str]:
        """Lexes C/C++ tokens while identifying identifiers, numbers, operators, and punctuation."""
        token_pattern = re.compile(
            r'([a-zA-Z_][a-zA-Z0-9_]*|::|\+\+|--|->|==|!=|<=|>=|&&|\|\||<<|>>|\+=|-=|\*=|/=|%=|[0-9]+\.?[0-9]*|[-+*/%=<>(){}\[\],;.|&!^~])'
        )
        return token_pattern.findall(clean_code)

    def parse_and_extract_structure(self, code: str) -> Tuple[List[str], Dict[str, int], bool, str]:
        if not code or not code.strip():
            return [], {}, False, "Empty source code."

        clean = self._strip_preprocessor(code)
        raw_tokens = self._tokenize_code(clean)

        if not raw_tokens:
            return [], {}, False, "No tokens remaining after preprocessing."

        structural_tokens: List[str] = []
        counts: Dict[str, int] = {}
        var_map: Dict[str, str] = {}
        var_counter = 0

        def get_var_token(ident: str) -> str:
            nonlocal var_counter
            if ident in self.standard_calls:
                return f"STDCALL_{ident}"
            if ident not in var_map:
                var_map[ident] = f"ID_{var_counter}"
                var_counter += 1
            return var_map[ident]

        def record(tok: str):
            structural_tokens.append(tok)
            counts[tok] = counts.get(tok, 0) + 1

        idx = 0
        total = len(raw_tokens)

        while idx < total:
            tok = raw_tokens[idx]

            if tok in self.keywords:
                if tok in ("if", "else", "switch", "case"):
                    record(f"BRANCH_{tok.upper()}")
                elif tok in ("for", "while", "do"):
                    record(f"LOOP_{tok.upper()}")
                elif tok in ("return", "break", "continue"):
                    record(f"FLOW_{tok.upper()}")
                elif tok in ("struct", "class"):
                    record(f"TYPE_{tok.upper()}")
                else:
                    record(f"KW_{tok.upper()}")

            elif tok in self.types:
                record(f"TYPE_{tok.upper()}")

            elif tok in ("(", ")", "{", "}", "[", "]"):
                record(f"BRACKET_{tok}")

            elif tok in (";", ","):
                record(f"PUNCT_{tok}")

            elif tok in ("=", "+=", "-=", "*=", "/=", "%="):
                record("ASSIGN")

            elif tok in ("==", "!=", "<", ">", "<=", ">="):
                record("COMPARE")

            elif tok in ("&&", "||", "!"):
                record("LOGICAL")

            elif tok in ("+", "-", "*", "/", "%", "++", "--"):
                record("ARITHMETIC")

            elif tok in ("<<", ">>", "&", "|", "^", "~"):
                record("BITWISE")

            elif re.match(r'^[0-9]+', tok):
                record("LITERAL_NUM")

            elif tok.startswith('"') or tok.startswith("'"):
                record("LITERAL_STR")

            elif re.match(r'^[a-zA-Z_]', tok):
                # Check if it is a function call or declaration
                next_tok = raw_tokens[idx + 1] if idx + 1 < total else ""
                var_tok = get_var_token(tok)
                if next_tok == "(":
                    record(f"CALL_{var_tok}")
                else:
                    record(f"VAR_{var_tok}")
            else:
                record(f"SYM_{tok}")

            idx += 1

        return structural_tokens, counts, True, ""

    def compute_similarity(self, code_a: str, code_b: str) -> Dict[str, Any]:
        tokens_a, counts_a, success_a, err_a = self.parse_and_extract_structure(code_a)
        tokens_b, counts_b, success_b, err_b = self.parse_and_extract_structure(code_b)

        if not success_a or not success_b:
            err_msg = err_a if not success_a else err_b
            return {
                "score": 0.0,
                "success": False,
                "error": err_msg,
                "summary": f"C/C++ Structural analysis limitation: {err_msg}",
                "tokens_a_count": len(tokens_a),
                "tokens_b_count": len(tokens_b)
            }

        if not tokens_a or not tokens_b:
            return {
                "score": 0.0,
                "success": True,
                "summary": "Empty structural representation.",
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
            f"C/C++ structural AST parser extracted {len(tokens_a)} and {len(tokens_b)} structural tokens. "
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
