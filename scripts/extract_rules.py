# Rule Extraction Script for AIT P&P Documents
# Extracts policy rules from PDF documents for thesis corpus

"""
This script helps extract policy rules from AIT P&P PDF documents.
It uses pdfplumber for text extraction and provides structured output.

USAGE:
    python scripts/extract_rules.py <pdf_path>
    
OPTIONS:
    --all     Extract from all P&P documents
    --output  Specify output file (default: extracted_rules.json)
"""

import re
import json
from pathlib import Path
from datetime import datetime
import sys

try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "pdfplumber", "-q"])
    import pdfplumber

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs" / "AIT P&P"
RESEARCH_DIR = PROJECT_ROOT / "research"

# Deontic markers that indicate policy rules
DEONTIC_MARKERS = [
    r'\bmust\b', r'\bshall\b', r'\bmay\b', r'\bshould\b',
    r'\bis required\b', r'\bare required\b',
    r'\bis prohibited\b', r'\bare prohibited\b',
    r'\bnot allowed\b', r'\bnot permitted\b',
    r'\bhas to\b', r'\bhave to\b',
    r'\bwill be\b.*\b(suspended|terminated|dismissed|fined)\b',
    r'\bcannot\b', r'\bmust not\b', r'\bshall not\b',
]

# Compile regex pattern
RULE_PATTERN = re.compile('|'.join(DEONTIC_MARKERS), re.IGNORECASE)


def extract_text_from_pdf(pdf_path: Path) -> dict:
    """Extract text from PDF with page numbers."""
    result = {
        "file": str(pdf_path.name),
        "pages": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            result["pages"].append({
                "page_number": i,
                "text": text
            })
    
    return result


def identify_potential_rules(text: str, page_num: int, source: str) -> list:
    """Identify sentences that might be policy rules."""
    rules = []
    
    # Split into sentences (rough approximation)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:  # Skip very short fragments
            continue
            
        # Check if sentence contains deontic markers
        if RULE_PATTERN.search(sentence):
            rules.append({
                "text": sentence,
                "page": page_num,
                "source": source,
                "markers_found": [m.group() for m in RULE_PATTERN.finditer(sentence)]
            })
    
    return rules


def extract_rules_from_document(pdf_path: Path) -> list:
    """Extract all potential rules from a PDF document."""
    print(f"\n📄 Processing: {pdf_path.name}")
    
    all_rules = []
    doc_data = extract_text_from_pdf(pdf_path)
    
    for page in doc_data["pages"]:
        rules = identify_potential_rules(
            page["text"], 
            page["page_number"],
            pdf_path.name
        )
        all_rules.extend(rules)
    
    print(f"   Found {len(all_rules)} potential rules")
    return all_rules


def generate_rule_id(source: str, index: int) -> str:
    """Generate a rule ID based on source document."""
    # Extract document code from filename
    # e.g., "FB-6-1-1 Credit Policy..." -> "FB-6-1-1"
    match = re.match(r'^([A-Z]{2}-\d+-\d+-\d+)', source)
    if match:
        doc_code = match.group(1)
    else:
        doc_code = "DOC"
    
    return f"{doc_code}-R{index:03d}"


def format_rules_for_corpus(rules: list) -> list:
    """Format extracted rules for the corpus spreadsheet."""
    formatted = []
    
    # Group by source document
    by_source = {}
    for rule in rules:
        source = rule["source"]
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(rule)
    
    # Generate IDs and format
    for source, source_rules in by_source.items():
        for i, rule in enumerate(source_rules, 1):
            formatted.append({
                "rule_id": generate_rule_id(source, i),
                "source_document": source,
                "page_number": rule["page"],
                "section": "",  # To be filled manually
                "original_text": rule["text"],
                "simplified_text": "",  # To be filled manually
                "deontic_markers": ", ".join(rule["markers_found"]),
                
                # Annotation placeholders
                "ann_syntactic_structure": "",
                "ann_clause_count": "",
                "ann_nesting_depth": "",
                "ann_deontic_marker": rule["markers_found"][0] if rule["markers_found"] else "",
                "ann_deontic_type": "",
                "ann_quantification": "",
                "ann_conditional_structure": "",
                "ann_has_exception": "",
                "ann_temporal_elements": "",
                "ann_entity_types": "",
                "ann_ambiguity_indicators": "",
                
                # Formalization placeholders
                "form_outcome": "",
                "form_fol_statement": "",
                "form_confidence": "",
                
                # Metadata
                "extraction_date": datetime.now().isoformat(),
                "needs_review": True,
            })
    
    return formatted


def save_rules_json(rules: list, output_path: Path):
    """Save extracted rules to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved {len(rules)} rules to: {output_path}")


def save_rules_markdown(rules: list, output_path: Path):
    """Save extracted rules to Markdown for review."""
    
    content = f"""# Extracted Policy Rules
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Total Rules Found: {len(rules)}

---

"""
    
    # Group by source
    by_source = {}
    for rule in rules:
        source = rule["source_document"]
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(rule)
    
    for source, source_rules in by_source.items():
        content += f"\n## {source}\n\n"
        content += f"Rules found: {len(source_rules)}\n\n"
        
        for rule in source_rules:
            content += f"""### {rule['rule_id']} (Page {rule['page_number']})

**Original Text:**
> {rule['original_text']}

**Deontic Markers:** {rule['deontic_markers']}

**Needs Review:** ✅

---

"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"📝 Saved markdown review file to: {output_path}")


def main():
    """Main extraction workflow."""
    print("=" * 60)
    print("AIT P&P POLICY RULE EXTRACTOR")
    print("=" * 60)
    
    # Check for PDF files
    if not DOCS_DIR.exists():
        print(f"❌ P&P documents directory not found: {DOCS_DIR}")
        return
    
    pdf_files = list(DOCS_DIR.glob("*.pdf"))
    print(f"\n📁 Found {len(pdf_files)} PDF documents:")
    for f in pdf_files:
        print(f"   - {f.name}")
    
    # Extract from all documents
    all_rules = []
    for pdf_path in pdf_files:
        rules = extract_rules_from_document(pdf_path)
        all_rules.extend(rules)
    
    print(f"\n{'='*60}")
    print(f"TOTAL POTENTIAL RULES FOUND: {len(all_rules)}")
    print(f"{'='*60}")
    
    # Format for corpus
    formatted_rules = format_rules_for_corpus(all_rules)
    
    # Save outputs
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    
    # JSON for programmatic use
    save_rules_json(formatted_rules, RESEARCH_DIR / "extracted_rules.json")
    
    # Markdown for human review
    save_rules_markdown(formatted_rules, RESEARCH_DIR / "extracted_rules_review.md")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("""
1. Review the extracted rules in:
   - research/extracted_rules_review.md (human readable)
   - research/extracted_rules.json (structured data)

2. For each rule, determine if it's actually a policy rule:
   - Mark FALSE POSITIVES for removal
   - Identify MISSING rules not caught by extraction

3. Transfer validated rules to:
   - research/policy_rules_corpus.xlsx

4. Complete annotation for each rule following:
   - research/annotation_codebook.md
""")


if __name__ == "__main__":
    main()
