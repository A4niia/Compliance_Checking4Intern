# Thesis Agent System - Main Orchestrator
# Provides automated assistance for thesis research, implementation, and writing

"""
THESIS AGENT SYSTEM
==================

This system helps you with:
1. Research Tasks - Rule extraction, annotation, pattern analysis
2. Implementation - SHACL shapes, ontology, validation pipeline
3. Verification - SHACL2FOL testing, equivalence checking
4. Documentation - LaTeX report generation, figure creation

USAGE:
    python scripts/thesis_agent.py <command> [options]

COMMANDS:
    extract     - Extract rules from P&P documents
    annotate    - Annotate rules with linguistic features
    formalize   - Translate rules to FOL
    implement   - Generate SHACL shapes
    verify      - Run SHACL2FOL verification
    evaluate    - Run evaluation experiments
    report      - Generate LaTeX sections
"""

import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import json
import sys

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
RESEARCH_DIR = PROJECT_ROOT / "research"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
LATEX_DIR = PROJECT_ROOT / "latex"
TOOLS_DIR = PROJECT_ROOT / "tools"
PROTOTYPE_DIR = PROJECT_ROOT / "ait-policy-prototype"


class ThesisAgent:
    """Main thesis assistant agent."""
    
    def __init__(self):
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure all required directories exist."""
        for dir_path in [RESEARCH_DIR, LATEX_DIR, TOOLS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def status(self):
        """Show current thesis progress status."""
        print("\n" + "="*60)
        print("THESIS PROGRESS STATUS")
        print("="*60)
        
        # Check corpus
        corpus_file = RESEARCH_DIR / "policy_rules_corpus.xlsx"
        if corpus_file.exists():
            print(f"✅ Corpus spreadsheet: {corpus_file}")
        else:
            print(f"❌ Corpus spreadsheet not found")
        
        # Check codebook
        codebook_file = RESEARCH_DIR / "annotation_codebook.md"
        if codebook_file.exists():
            print(f"✅ Annotation codebook: {codebook_file}")
        else:
            print(f"❌ Annotation codebook not found")
        
        # Check SHACL shapes
        shacl_files = list(PROTOTYPE_DIR.glob("*.ttl"))
        print(f"📄 SHACL/Ontology files: {len(shacl_files)}")
        for f in shacl_files:
            print(f"   - {f.name}")
        
        # Check test cases
        test_cases = list(PROTOTYPE_DIR.glob("case*.ttl"))
        print(f"🧪 Test cases: {len(test_cases)}")
        
        print("\n" + "="*60)
    
    def extract_rules_help(self):
        """Show help for rule extraction."""
        help_text = """
RULE EXTRACTION WORKFLOW
========================

Step 1: Open AIT P&P PDFs
   - docs/AIT P&P/FB-6-1-1 Credit Policy AMT8Jun2022.pdf
   - docs/AIT P&P/FS-1-1-1 Campus Accommodation for Students AMT8Jun2022.pdf
   - docs/AIT P&P/AA-4-1-1 Academic Integrity in Research and Publication rev18Mar2022.pdf
   - docs/AIT P&P/PA-2-1-2 Ethical Behavior and Grievance Process AMT8Dec2021.pdf
   - docs/AIT P&P/Student-Handbook_August-2021.pdf

Step 2: Identify Rules
   Look for sentences containing:
   - Deontic markers: must, shall, may, should, is required, is prohibited
   - Conditional: if, when, unless, except
   - Quantifiers: all, every, no, any, students (implicit universal)

Step 3: Record in Spreadsheet
   Open: research/policy_rules_corpus.xlsx
   Fill in each column following annotation_codebook.md

Step 4: Initial Formalization Attempt
   For each rule, try to write FOL statement
   Record outcome: SUCCESS, PARTIAL, or FAILURE type

Step 5: Advisor Review
   Flag uncertain annotations for advisor sampling
   Schedule review session for FAILURE cases
"""
        print(help_text)
    
    def generate_latex_template(self):
        """Generate LaTeX thesis template."""
        
        main_tex = r"""\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{tikz}
\usetikzlibrary{shapes,arrows,positioning}

% Code listing style
\lstdefinestyle{turtle}{
  basicstyle=\small\ttfamily,
  breaklines=true,
  frame=single,
  numbers=left,
  numberstyle=\tiny,
  keywordstyle=\color{blue},
  commentstyle=\color{gray},
}

\lstdefinestyle{fol}{
  basicstyle=\small\ttfamily,
  breaklines=true,
  frame=single,
  mathescape=true,
}

% Title info
\title{A Methodology for Transforming Natural Language Academic Policies into Formal Knowledge for Automated Reasoning}
\author{Ponkrit Kaewsawee (ST124960)}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
This thesis presents a systematic methodology for transforming natural language academic policies into machine-executable formal knowledge using First-Order Logic (FOL) and SHACL (Shapes Constraint Language). The research addresses the challenge of automated policy compliance checking by: (1) discovering linguistic patterns that determine the formalizability of policy rules, (2) developing a verified transformation pipeline from natural language to SHACL constraints, and (3) evaluating the accuracy and coverage of the proposed approach using real policies from the Asian Institute of Technology.

\textbf{Keywords:} Policy Formalization, SHACL, First-Order Logic, Semantic Web, Compliance Checking
\end{abstract}

\tableofcontents

% Include chapters
\include{chapters/01_introduction}
\include{chapters/02_literature_review}
\include{chapters/03_methodology}
\include{chapters/04_implementation}
\include{chapters/05_evaluation}
\include{chapters/06_conclusion}

% Appendices
\appendix
\include{appendices/A_corpus}
\include{appendices/B_fol_statements}
\include{appendices/C_shacl_shapes}

\bibliographystyle{plain}
\bibliography{references}

\end{document}
"""
        
        # Create LaTeX directory structure
        (LATEX_DIR / "chapters").mkdir(parents=True, exist_ok=True)
        (LATEX_DIR / "appendices").mkdir(parents=True, exist_ok=True)
        (LATEX_DIR / "figures").mkdir(parents=True, exist_ok=True)
        
        # Write main.tex
        with open(LATEX_DIR / "main.tex", 'w', encoding='utf-8') as f:
            f.write(main_tex)
        
        # Create chapter stubs
        chapters = {
            "01_introduction": self._get_intro_template(),
            "02_literature_review": self._get_literature_template(),
            "03_methodology": self._get_methodology_template(),
            "04_implementation": self._get_implementation_template(),
            "05_evaluation": self._get_evaluation_template(),
            "06_conclusion": self._get_conclusion_template(),
        }
        
        for name, content in chapters.items():
            with open(LATEX_DIR / "chapters" / f"{name}.tex", 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Create references.bib
        bib_content = self._get_references_template()
        with open(LATEX_DIR / "references.bib", 'w', encoding='utf-8') as f:
            f.write(bib_content)
        
        print(f"✅ LaTeX thesis template created in: {LATEX_DIR}")
        print("   - main.tex")
        print("   - chapters/01_introduction.tex through 06_conclusion.tex")
        print("   - references.bib")
    
    def _get_intro_template(self):
        return r"""\chapter{Introduction}

\section{Background and Motivation}
% TODO: Write about:
% - The challenge of policy compliance in organizations
% - Gap between natural language policies and automated systems
% - Need for formal representation

\section{Problem Statement}
% TODO: Define the specific problem your research addresses

\section{Research Questions}
\begin{enumerate}
    \item \textbf{RQ1:} What linguistic and structural patterns in AIT academic policies can be formally represented in First-Order Logic and SHACL, and what patterns exceed the expressiveness of these formalisms?
    
    \item \textbf{RQ2:} How can we systematically verify that SHACL shapes correctly implement the intended policy semantics using automated equivalence checking?
    
    \item \textbf{RQ3:} What is the overall formalization coverage, validation accuracy, and detection precision of the proposed methodology when applied to AIT policies?
\end{enumerate}

\section{Research Objectives}
% TODO: List 3-5 specific objectives

\section{Scope and Limitations}
% TODO: Define boundaries

\section{Thesis Organization}
% TODO: Brief description of each chapter
"""

    def _get_literature_template(self):
        return r"""\chapter{Literature Review}

\section{Policy Formalization}
% TODO: Review existing work on formalizing regulations/policies

\section{Semantic Web Technologies}
\subsection{Ontology and RDF}
\subsection{SHACL - Shapes Constraint Language}

\section{First-Order Logic in Compliance Checking}
% TODO: Review FOL applications

\section{SHACL2FOL and Formal Verification}
% TODO: Review Pareti's work

\section{Assumption-Based Argumentation}
% TODO: Review ABA for handling ambiguity

\section{Related Work Comparison}
% TODO: Table comparing your approach with existing work
"""

    def _get_methodology_template(self):
        return r"""\chapter{Methodology}

\section{Research Design Overview}
% TODO: High-level methodology diagram

\section{Phase 1: Corpus Construction and Pattern Discovery}
\subsection{Data Collection}
\subsection{Annotation Scheme}
\subsection{Formalization Protocol}
\subsection{Pattern Analysis}

\section{Phase 2: Transformation Pipeline}
\subsection{Policy to FOL Translation}
\subsection{FOL to SHACL Conversion}
\subsection{Ontology Design}

\section{Phase 3: Formal Verification}
\subsection{SHACL2FOL Integration}
\subsection{Equivalence Checking}
\subsection{Counterexample Generation}

\section{Phase 4: Evaluation}
\subsection{Metrics}
\subsection{Experiment Design}
"""

    def _get_implementation_template(self):
        # Note: Using regular string with escaped backslashes to avoid issues with $this
        return """\\chapter{Implementation}

\\section{System Architecture}
% TODO: Architecture diagram

\\section{Complete Worked Example}
% TODO: Step-by-step from policy to validation

\\subsection{Original Policy Statement}
\\begin{quote}
``Self-support students who have not paid tuition fees within two weeks of the fee due date are not eligible for course registration.''
-- AIT Financial Policies FB-6-1-1, Section III.1.(2)
\\end{quote}

\\subsection{First-Order Logic Representation}
% See FOL statements in Appendix B

\\subsection{SHACL Shape}
% See SHACL shapes in Appendix C and ait-policy-prototype/ait-shacl-rules.ttl

\\subsection{Validation Result}
% TODO: Show validation output

\\section{Tool Chain}
% TODO: Describe tools used
"""

    def _get_evaluation_template(self):
        return r"""\chapter{Evaluation}

\section{Experiment Setup}
% TODO: Describe experimental configuration

\section{Results}

\subsection{Pattern Discovery Results (RQ1)}
% TODO: Pattern taxonomy table

\subsection{Verification Results (RQ2)}
% TODO: Equivalence checking results

\subsection{Overall Evaluation (RQ3)}
\begin{table}[h]
\centering
\caption{Formalization and Validation Results}
\begin{tabular}{lrrrr}
\toprule
Rule Pattern & Count & Formalized & Accuracy & Precision \\
\midrule
Simple Prohibition & -- & --\% & --\% & --\% \\
Conditional (1-2 cond.) & -- & --\% & --\% & --\% \\
Temporal Constraints & -- & --\% & --\% & --\% \\
\textbf{TOTAL} & \textbf{--} & \textbf{--\%} & -- & -- \\
\bottomrule
\end{tabular}
\end{table}

\section{Discussion}
\subsection{Findings}
\subsection{Limitations}
\subsection{Threats to Validity}
"""

    def _get_conclusion_template(self):
        return r"""\chapter{Conclusion}

\section{Summary of Contributions}
% TODO: List main contributions

\section{Research Questions Revisited}
% TODO: Answer each RQ

\section{Limitations}
% TODO: Honest limitations

\section{Future Work}
% TODO: Extensions and improvements
"""

    def _get_references_template(self):
        return r"""@article{pareti2024shacl2fol,
  title={Formal Semantics for SHACL},
  author={Pareti, Paolo},
  journal={arXiv preprint},
  year={2024}
}

@book{toni2014tutorial,
  title={A Tutorial on Assumption-Based Argumentation},
  author={Toni, Francesca},
  journal={Argument \& Computation},
  volume={5},
  number={1},
  pages={89--117},
  year={2014}
}

@standard{w3c2017shacl,
  title={Shapes Constraint Language (SHACL)},
  author={{W3C}},
  year={2017},
  url={https://www.w3.org/TR/shacl/}
}

% TODO: Add more references as needed
"""


def main():
    parser = argparse.ArgumentParser(description="Thesis Agent System")
    parser.add_argument('command', nargs='?', default='status',
                        choices=['status', 'extract', 'latex', 'verify', 'help'],
                        help='Command to execute')
    
    args = parser.parse_args()
    
    agent = ThesisAgent()
    
    if args.command == 'status':
        agent.status()
    elif args.command == 'extract':
        agent.extract_rules_help()
    elif args.command == 'latex':
        agent.generate_latex_template()
    elif args.command == 'verify':
        # Run SHACL2FOL test
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "shacl2fol_test.py")])
    elif args.command == 'help':
        print(__doc__)


if __name__ == "__main__":
    main()
