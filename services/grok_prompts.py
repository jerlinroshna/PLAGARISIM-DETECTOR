from typing import Dict, Any, Tuple

def build_explanation_prompts(evidence: Dict[str, Any]) -> Tuple[str, str]:
    """Constructs system and user prompts adhering to strict academic integrity guidelines."""
    system_prompt = (
        "You are Grok, an AI academic integrity expert assistant developed by xAI. "
        "Your objective is to provide a comprehensive, objective, and easy-to-understand explanation "
        "of automated source-code plagiarism analysis results for university faculty members.\n\n"
        "STRICT COMPLIANCE RULES:\n"
        "1. ONLY explain the verified results and evidence provided in the prompt. "
        "NEVER invent, hallucinate, modify, or recalculate any similarity percentages or metrics.\n"
        "2. DO NOT make the final plagiarism determination, accusation of cheating, or disciplinary judgment. "
        "Explicitly emphasize to faculty that similarity scores are decision-support indicators, "
        "and the final academic integrity determination rests entirely with the instructor.\n"
        "3. Clearly explain what the Text Similarity score measures (normalized token sequences, string matches, winnowing) "
        "vs what the AST Structural Similarity score measures (normalized Abstract Syntax Tree hierarchy, statement sequences, "
        "control flow, and identifier normalization which detects plagiarism even when variables and functions are renamed).\n"
        "4. Walk through what the matching code segments demonstrate and identify what structural or logic differences exist.\n"
        "5. Structure your output clearly using standard Markdown headings:\n"
        "   ### 1. Executive Summary\n"
        "   ### 2. Metric Breakdown: Text vs. AST Structural Similarity\n"
        "   ### 3. Matched Code Logic & Structural Evidence\n"
        "   ### 4. Code Differences & Distinguishing Logic\n"
        "   ### 5. Recommended Faculty Next Steps\n"
        "Be professional, clear, evidence-grounded, and concise."
    )

    user_content = [
        "Here is the verified plagiarism detection evidence computed by CodeGuard for faculty evaluation:\n",
        f"- **Programming Language**: {evidence.get('language', 'N/A').upper()}",
        f"- **Course Subject**: {evidence.get('assignment_subject', 'N/A')}",
        f"- **Assignment Title**: {evidence.get('assignment_topic', 'N/A')}",
        f"- **Combined Plagiarism Score**: {evidence.get('combined_similarity_score', 0)}% ({evidence.get('similarity_label', 'N/A')})",
        f"- **Formula Weighting**: 40% Text Similarity + 60% AST Structural Similarity",
        f"- **Text Similarity Score**: {evidence.get('text_similarity_score', 0)}%",
        f"- **AST Structural Similarity Score**: {evidence.get('ast_similarity_score', 0)}%",
        f"- **AST Engine Summary**: {evidence.get('analysis_summary', 'N/A')}",
        f"- **Student Submission Scope**: {evidence.get('student_total_lines', 0)} total lines",
    ]

    if evidence.get('has_historical_match'):
        user_content.append(f"- **Matched Historical Reference**: Academic Year {evidence.get('historical_academic_year', 'N/A')} - '{evidence.get('historical_assignment', 'N/A')}' ({evidence.get('historical_total_lines', 0)} total lines)")
        user_content.append(f"- **Total Matched Lines**: ~{evidence.get('matched_lines_count', 0)} lines across {evidence.get('matched_blocks_count', 0)} continuous block(s)")

        if evidence.get('matched_sections'):
            user_content.append("\n**Key Matched Code Sections:**")
            for i, sec in enumerate(evidence['matched_sections'], 1):
                user_content.append(f"\n[Block {i}] Student ({sec['student_lines']}) vs Historical ({sec['historical_lines']}):")
                user_content.append(f"Student code:\n```\n{sec['student_snippet']}\n```")
                if sec.get('historical_snippet'):
                    user_content.append(f"Historical archive:\n```\n{sec['historical_snippet']}\n```")
        else:
            user_content.append("\nNo continuous multi-line code spans were recorded (structural/token similarity only).")
    else:
        user_content.append("- **Matched Historical Reference**: None found in repository for this subject/language.")

    user_content.append(
        "\nPlease explain these findings clearly for faculty, explaining the contrast between the text score "
        "and AST score, analyzing why these specific blocks matched, identifying differences, and providing guidance "
        "without making an accusation."
    )

    return system_prompt, "\n".join(user_content)


def build_investigation_report_prompts(report_data: Dict[str, Any]) -> Tuple[str, str]:
    """Constructs system and user prompts for formal investigation report."""
    system_prompt = (
        "You are Grok, a senior academic integrity officer AI developed by xAI. "
        "You are generating a formal, structured ACADEMIC INTEGRITY INVESTIGATION REPORT "
        "for university faculty. This is an official document, not a chat message.\n\n"
        "STRICT RULES:\n"
        "1. Write in formal, professional language suitable for an official academic record.\n"
        "2. ONLY reference the exact numerical scores and evidence provided. NEVER invent or recalculate any metric.\n"
        "3. DO NOT make a final plagiarism determination or accusation. State that the final determination rests with the instructor.\n"
        "4. Follow the EXACT 7-section structure specified in the user prompt. Use the exact heading names.\n"
        "5. Each section must be substantive (3-6 sentences minimum). Section 4 must reference specific code block evidence.\n"
        "6. Use markdown formatting (## headings, **bold**, bullet lists, code blocks).\n"
        "7. Section 7 must include the mandatory disclaimer verbatim as instructed.\n"
        "Generate a thorough, evidence-grounded document that faculty can use as a formal case file."
    )

    ev = report_data
    hist_block = ""
    if ev.get("has_historical_match"):
        hist_block = (
            f"MATCHED HISTORICAL ARCHIVE:\n"
            f"  Academic Year      : {ev.get('historical_academic_year', 'N/A')}\n"
            f"  Assignment         : {ev.get('historical_assignment', 'N/A')}\n"
            f"  Historical File    : {ev.get('hist_filename', 'N/A')}\n"
            f"  Historical Scope   : {ev.get('historical_total_lines', 0)} lines\n"
            f"  Matched Lines      : ~{ev.get('matched_lines_count', 0)} lines across "
            f"{ev.get('matched_blocks_count', 0)} block(s)\n"
        )
    else:
        hist_block = "MATCHED HISTORICAL ARCHIVE:\n  No comparable historical record found in repository.\n"

    evidence_block = ""
    sections = ev.get("matched_sections", [])
    if sections:
        evidence_block = "MATCHED CODE EVIDENCE BLOCKS:\n"
        for i, sec in enumerate(sections, 1):
            evidence_block += (
                f"  [Block {i}] Student {sec['student_lines']} vs Historical {sec['historical_lines']}:\n"
                f"    Student code snippet:\n"
            )
            for ln in sec["student_snippet"].splitlines():
                evidence_block += f"      {ln}\n"
            if sec.get("historical_snippet"):
                evidence_block += f"    Historical archive snippet:\n"
                for ln in sec["historical_snippet"].splitlines():
                    evidence_block += f"      {ln}\n"
    else:
        evidence_block = "MATCHED CODE EVIDENCE BLOCKS: None recorded (structural/token similarity only).\n"

    prior_grok = ""
    if ev.get("grok_explanation"):
        prior_grok = (
            f"\nPRIOR GROK AI ANALYSIS (summary context, first 800 chars):\n"
            f"{ev['grok_explanation'][:800]}\n"
        )

    review_block = (
        f"FACULTY REVIEW STATUS      : {ev.get('review_status', 'Pending Review')}\n"
        f"FACULTY REVIEW NOTES       : {ev.get('review_notes', 'None recorded')}\n"
    )

    user_prompt = (
        f"Generate a formal Academic Integrity Investigation Report using EXACTLY this 7-section structure:\n\n"
        f"## ACADEMIC INTEGRITY INVESTIGATION REPORT\n"
        f"### Case Reference: SUB-{ev['submission_id']} | Generated: {ev['generated_at']}\n\n"
        f"## Section 1 — Executive Summary\n"
        f"## Section 2 — Submission Profile & Context\n"
        f"## Section 3 — Algorithmic Detection Findings\n"
        f"## Section 4 — Code Evidence Analysis\n"
        f"## Section 5 — Comparative Structural Analysis\n"
        f"## Section 6 — Recommended Faculty Actions\n"
        f"## Section 7 — Formal Disclaimer\n\n"
        f"---\n\n"
        f"CASE DATA:\n\n"
        f"CASE REFERENCE             : SUB-{ev['submission_id']}\n"
        f"REPORT GENERATED           : {ev['generated_at']}\n"
        f"REVIEWED BY                : {ev['faculty_name']} ({ev['faculty_username']})\n"
        f"INSTITUTION SYSTEM         : CodeGuard Academic Portal\n\n"
        f"SUBMISSION DETAILS:\n"
        f"  Assignment               : {ev['assignment_title']}\n"
        f"  Subject                  : {ev['subject']}\n"
        f"  Programming Language     : {ev['language'].upper()}\n"
        f"  Submitted                : {ev['submitted_at']}\n"
        f"  Source File              : {ev['source_filename']}\n"
        f"  Analysis Status          : {ev['analysis_status']}\n"
        f"  Submission Scope         : {ev['student_total_lines']} lines\n\n"
        f"PLAGIARISM DETECTION METRICS:\n"
        f"  Text Similarity Score    : {ev['text_score']}%  (40% weight)\n"
        f"  AST Structural Score     : {ev['ast_score']}%  (60% weight)\n"
        f"  Combined Score           : {ev['combined_score']}%  [{ev['similarity_label']}]\n"
        f"  Algorithm Summary        : {ev['analysis_summary']}\n\n"
        f"{hist_block}\n"
        f"{evidence_block}\n"
        f"{review_block}"
        f"{prior_grok}\n"
        f"---\n\n"
        f"Section 7 MUST end with this verbatim disclaimer:\n"
        f"> This report is generated by CodeGuard's automated plagiarism detection system "
        f"and interpreted by xAI Grok AI. It constitutes decision-support evidence only. "
        f"Similarity scores are algorithmic indicators and do not constitute proof of academic "
        f"misconduct. The final determination of academic integrity violation rests solely "
        f"with the instructor and institutional academic integrity process. No student should "
        f"be disciplined based on this report alone without independent review."
    )

    return system_prompt, user_prompt
