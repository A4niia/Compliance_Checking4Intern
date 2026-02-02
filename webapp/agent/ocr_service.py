"""
OCR Service for Document Processing
PyMuPDF-based text extraction for reproducibility
"""

import os
import fitz  # PyMuPDF
from typing import List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OCRResult:
    """Result from OCR processing"""
    success: bool
    text: str
    pages: int
    words: int
    method: str  # Always "pymupdf"
    confidence: float
    tables: List[dict] = None
    error: str = None
    
    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "text_preview": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "pages": self.pages,
            "words": self.words,
            "method": self.method,
            "confidence": self.confidence,
            "tables_count": len(self.tables) if self.tables else 0,
            "error": self.error
        }


class OCRService:
    """
    OCR Service using PyMuPDF for reproducible text extraction
    
    Rationale for PyMuPDF-only approach:
    - Reproducibility: Deterministic output, no API dependencies
    - Sufficiency: ~85% accuracy adequate for manually-verified gold standard
    - Simplicity: Single extraction method, easier maintenance
    - Research focus: LLM classification, not OCR optimization
    """
    
    def __init__(self):
        """Initialize OCR service with PyMuPDF"""
        pass
    
    def extract_text(self, pdf_path: str) -> OCRResult:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            OCRResult with extracted text and metadata
        """
        return self._extract_with_pymupdf(pdf_path)
    
    def _extract_with_pymupdf(self, pdf_path: str) -> OCRResult:
        """Extract text using PyMuPDF (fitz)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            tables = []
            
            for page_num, page in enumerate(doc):
                # Extract text
                page_text = page.get_text()
                text += page_text + "\n"
                
                # Detect tables (simple heuristic)
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        lines = block.get("lines", [])
                        if len(lines) >= 3:
                            # Potential table if multiple aligned lines
                            spans_per_line = [len(line.get("spans", [])) for line in lines]
                            if all(s > 2 for s in spans_per_line):
                                tables.append({
                                    "page": page_num + 1,
                                    "type": "detected_table",
                                    "rows": len(lines)
                                })
            
            pages = len(doc)
            doc.close()
            
            return OCRResult(
                success=True,
                text=text,
                pages=pages,
                words=len(text.split()),
                method="pymupdf",
                confidence=0.85,  # Estimated accuracy
                tables=tables
            )
        except Exception as e:
            return OCRResult(
                success=False,
                text="",
                pages=0,
                words=0,
                method="pymupdf",
                confidence=0,
                error=str(e)
            )


# Global OCR service instance
ocr_service = OCRService()
