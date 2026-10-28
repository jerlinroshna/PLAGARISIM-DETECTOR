import unittest
from analyzers.text_analyzer import TextAnalyzer
from analyzers.ast_python import PythonASTAnalyzer
from analyzers.ast_c_cpp import CCppASTAnalyzer
from analyzers.ast_java import JavaASTAnalyzer
from analyzers.ast_javascript import JavaScriptASTAnalyzer
from analyzers.comparator import CodeComparator

class AnalyzersTestCase(unittest.TestCase):

    def test_text_analyzer_normalization_and_comments(self):
        code1 = """
        // Calculate sum
        int sum = 0;
        /* multi-line
           comment */
        for(int i=0; i<10; i++) {
            sum += i;
        }
        """
        code2 = """
        int sum = 0;
        for (int i = 0; i < 10; i++) {
            sum += i;
        }
        """
        result = TextAnalyzer.compute_similarity(code1, code2, "c")
        self.assertGreaterEqual(result["score"], 80.0)
        self.assertGreaterEqual(len(result["matching_spans"]), 1)

    def test_python_ast_variable_renaming(self):
        """total = a + b vs result = x + y must yield 100% AST structural similarity."""
        code1 = "total = a + b"
        code2 = "result = x + y"
        analyzer = PythonASTAnalyzer()
        res = analyzer.compute_similarity(code1, code2)
        self.assertTrue(res["success"])
        self.assertEqual(res["score"], 100.0)

    def test_python_ast_functions_and_loops(self):
        code1 = """
def compute_fibonacci(limit):
    first = 0
    second = 1
    seq = []
    for step in range(limit):
        seq.append(first)
        nxt = first + second
        first = second
        second = nxt
    return seq
"""
        code2 = """
def generate_fib(count):
    a = 0
    b = 1
    out = []
    for i in range(count):
        out.append(a)
        c = a + b
        a = b
        b = c
    return out
"""
        analyzer = PythonASTAnalyzer()
        res = analyzer.compute_similarity(code1, code2)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["score"], 90.0)

    def test_c_cpp_ast_renaming_and_loops(self):
        code1 = """
#include <stdio.h>
int main() {
    int num, temp, sum = 0, rem;
    scanf("%d", &num);
    temp = num;
    while (temp > 0) {
        rem = temp % 10;
        sum = sum + rem;
        temp = temp / 10;
    }
    printf("%d", sum);
    return 0;
}
"""
        code2 = """
#include <stdio.h>
int main() {
    int val, copy, total = 0, digit;
    scanf("%d", &val);
    copy = val;
    while (copy > 0) {
        digit = copy % 10;
        total = total + digit;
        copy = copy / 10;
    }
    printf("%d", total);
    return 0;
}
"""
        analyzer = CCppASTAnalyzer("c")
        res = analyzer.compute_similarity(code1, code2)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["score"], 85.0)

    def test_java_ast_renaming(self):
        code1 = """
public class Calc {
    public int add(int a, int b) {
        return a + b;
    }
}
"""
        code2 = """
public class Arithmetic {
    public int sum(int x, int y) {
        return x + y;
    }
}
"""
        analyzer = JavaASTAnalyzer()
        res = analyzer.compute_similarity(code1, code2)
        self.assertTrue(res["success"])
        self.assertEqual(res["score"], 100.0)

    def test_javascript_ast_renaming(self):
        code1 = """
function checkPalindrome(str) {
    let len = str.length;
    for (let i = 0; i < len / 2; i++) {
        if (str[i] !== str[len - 1 - i]) return false;
    }
    return true;
}
"""
        code2 = """
function isPal(text) {
    let n = text.length;
    for (let idx = 0; idx < n / 2; idx++) {
        if (text[idx] !== text[n - 1 - idx]) return false;
    }
    return true;
}
"""
        analyzer = JavaScriptASTAnalyzer()
        res = analyzer.compute_similarity(code1, code2)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["score"], 90.0)

    def test_dissimilar_code_yields_low_score(self):
        code1 = "print('Hello, World!')"
        code2 = """
class Matrix:
    def __init__(self, rows, cols):
        self.data = [[0]*cols for _ in range(rows)]
    def transpose(self):
        return [list(x) for x in zip(*self.data)]
"""
        res = CodeComparator.compare_code_pair(code1, code2, "python")
        self.assertLess(res["combined_score"], 30.0)
        self.assertEqual(res["similarity_label"], "Low Similarity")

    def test_syntax_error_resilience(self):
        malformed = "def broken_code(:"
        valid = "def valid(): pass"
        res = CodeComparator.compare_code_pair(malformed, valid, "python")
        # Ensure it does not throw an exception and handles gracefully
        self.assertIn("Syntax error", res["ast_summary"])

if __name__ == "__main__":
    unittest.main()
