import re
import html as html_module

def md_to_html(md: str) -> str:
    """Converts a subset of Markdown to clean, self-contained HTML."""
    h = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Fenced code blocks
    h = re.sub(r"```[a-zA-Z0-9_-]*\n([\s\S]*?)```",
               lambda m: f"<pre><code>{m.group(1).rstrip()}</code></pre>", h)
    # Inline code
    h = re.sub(r"`([^`]+)`", r"<code>\1</code>", h)
    # Blockquote (> text)
    h = re.sub(r"^&gt; (.+)$", r"<blockquote>\1</blockquote>", h, flags=re.MULTILINE)
    # Headings
    h = re.sub(r"^### (.+)$", r"<h3>\1</h3>", h, flags=re.MULTILINE)
    h = re.sub(r"^## (.+)$", r"<h2>\1</h2>", h, flags=re.MULTILINE)
    h = re.sub(r"^# (.+)$", r"<h2>\1</h2>", h, flags=re.MULTILINE)
    # Horizontal rules
    h = re.sub(r"^---$", "<hr>", h, flags=re.MULTILINE)
    # Bold & italic
    h = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", h)
    h = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", h)
    # Bullet list items
    h = re.sub(r"^\s*[-*] (.+)$", r"<li>\1</li>", h, flags=re.MULTILINE)
    h = re.sub(r"(<li>.*?</li>)", r"<ul>\1</ul>", h, flags=re.DOTALL)
    h = re.sub(r"</ul>\s*<ul>", "", h)
    # Paragraph breaks
    blocks = [b.strip() for b in re.split(r"\n{2,}", h)]
    out = []
    for b in blocks:
        if not b:
            continue
        if re.match(r"<(h[2-3]|hr|pre|ul|blockquote)", b):
            out.append(b)
        else:
            out.append(f"<p>{b.replace(chr(10), '<br>')}</p>")
    return "\n".join(out)


def render_html_investigation_report(sub_id: int, result: dict) -> str:
    """Builds a polished, standalone HTML document for the Academic Integrity Investigation Report."""
    report_md = result.get("report", "")
    generated_at = result.get("generated_at", "")
    sub_id_str = f"SUB-{sub_id}"
    faculty_name = result.get("faculty_name", "Faculty Member")
    combined_score = result.get("combined_score", 0.0)
    similarity_label = result.get("similarity_label", "N/A")
    model_name = result.get("model", "grok-2-latest")

    if similarity_label == "High Similarity":
        badge_bg, badge_color = "#fee2e2", "#991b1b"
    elif similarity_label == "Medium Similarity":
        badge_bg, badge_color = "#fef3c7", "#92400e"
    else:
        badge_bg, badge_color = "#d1fae5", "#065f46"

    body_html = md_to_html(report_md)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Investigation Report — {sub_id_str}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13.5px;
    color: #1e293b;
    background: #f8fafc;
    padding: 0;
  }}
  .page-wrap {{ max-width: 820px; margin: 32px auto; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; box-shadow: 0 4px 24px rgba(0,0,0,.08); overflow: hidden; }}
  .report-header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    color: #fff;
    padding: 32px 36px 24px;
  }}
  .report-header .institution {{ font-size: 11px; text-transform: uppercase; letter-spacing: .12em; color: #93c5fd; margin-bottom: 8px; }}
  .report-header h1 {{ font-size: 20px; font-weight: 700; line-height: 1.3; margin-bottom: 10px; }}
  .report-header .meta-row {{ display: flex; flex-wrap: wrap; gap: 18px; font-size: 12px; color: #cbd5e1; margin-top: 12px; }}
  .report-header .meta-item strong {{ color: #fff; }}
  .score-banner {{
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    background: #f1f5f9; border-bottom: 1px solid #e2e8f0;
    padding: 14px 36px;
  }}
  .score-banner .score-chip {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 16px; border-radius: 9999px;
    font-size: 13px; font-weight: 700;
    background: {badge_bg}; color: {badge_color};
    border: 1px solid {badge_color}33;
  }}
  .score-banner .score-chip .score-val {{ font-size: 18px; }}
  .score-banner .meta {{ font-size: 11.5px; color: #64748b; }}
  .report-body {{ padding: 30px 36px; }}
  .report-body h2 {{
    font-size: 14.5px; font-weight: 700; color: #0f172a;
    border-bottom: 2px solid #3b82f6; padding-bottom: 5px;
    margin: 28px 0 10px;
  }}
  .report-body h3 {{ font-size: 13px; font-weight: 600; color: #1e40af; margin: 16px 0 6px; }}
  .report-body p {{ line-height: 1.7; margin-bottom: 10px; color: #334155; }}
  .report-body ul {{ margin: 8px 0 10px 22px; }}
  .report-body li {{ margin-bottom: 4px; line-height: 1.6; color: #334155; }}
  .report-body pre {{
    background: #0f172a; color: #e2e8f0;
    padding: 14px 16px; border-radius: 6px;
    font-size: 12px; overflow-x: auto; margin: 10px 0 14px;
  }}
  .report-body code {{
    background: #f1f5f9; color: #0f172a;
    padding: 2px 5px; border-radius: 4px; font-size: 12px;
  }}
  .report-body pre code {{ background: none; color: inherit; padding: 0; }}
  .report-body blockquote {{
    border-left: 4px solid #f59e0b;
    background: #fffbeb; color: #78350f;
    padding: 10px 16px; margin: 12px 0;
    border-radius: 0 6px 6px 0; font-size: 12.5px;
  }}
  .report-body hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }}
  .report-body strong {{ color: #0f172a; }}
  .report-footer {{
    background: #f8fafc; border-top: 1px solid #e2e8f0;
    padding: 14px 36px; font-size: 11px; color: #94a3b8;
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  }}
  @media print {{
    body {{ background: #fff; }}
    .page-wrap {{ box-shadow: none; border: none; margin: 0; }}
    .report-header {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
  }}
</style>
</head>
<body>
<div class="page-wrap">
  <div class="report-header">
    <div class="institution">CodeGuard Academic Integrity Portal — Official Report</div>
    <h1>Academic Integrity Investigation Report</h1>
    <div class="meta-row">
      <div class="meta-item"><strong>Case Ref:</strong> {sub_id_str}</div>
      <div class="meta-item"><strong>Generated:</strong> {html_module.escape(generated_at)}</div>
      <div class="meta-item"><strong>Reviewed By:</strong> {html_module.escape(faculty_name)}</div>
      <div class="meta-item"><strong>AI Engine:</strong> xAI Grok ({html_module.escape(model_name)})</div>
    </div>
  </div>
  <div class="score-banner">
    <div class="score-chip">
      <span class="score-val">{combined_score}%</span>
      <span>{html_module.escape(similarity_label)}</span>
    </div>
    <div class="meta">Combined Plagiarism Score (40% Text + 60% AST Structural Similarity)</div>
  </div>
  <div class="report-body">
    {body_html}
  </div>
  <div class="report-footer">
    <span>CodeGuard Academic Integrity Portal &bull; Faculty Confidential Document</span>
    <span>Generated {html_module.escape(generated_at)}</span>
  </div>
</div>
</body>
</html>"""

