from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class MatchSpan:
    student_start: int
    student_end: int
    historical_start: int
    historical_end: int
    matched_text: str = ""

@dataclass
class AnalysisResult:
    language: str
    text_score: float
    ast_score: float
    combined_score: float
    similarity_label: str
    summary: str
    matching_spans: List[Dict[str, Any]] = field(default_factory=list)
    ast_details: Dict[str, Any] = field(default_factory=dict)
    text_details: Dict[str, Any] = field(default_factory=dict)
    ast_error: Optional[str] = None

class BaseASTAnalyzer:
    """Base class for language-specific AST structural analyzers."""
    
    def __init__(self, language: str):
        self.language = language

    def parse_and_extract_structure(self, code: str) -> List[str]:
        """Parses source code and returns a list of normalized structural AST tokens."""
        raise NotImplementedError

    def compute_similarity(self, code_a: str, code_b: str) -> Dict[str, Any]:
        """Compares two code snippets structurally and returns score (0-100) and details."""
        raise NotImplementedError
