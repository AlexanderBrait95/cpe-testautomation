"""PDF report generator — optional WeasyPrint dependency."""
from __future__ import annotations


def generate_pdf_report(html_content: str, output_path: str) -> bool:
    """Generate a PDF from *html_content* using WeasyPrint.

    Returns
    -------
    bool
        ``True`` when the PDF was written successfully.
        ``False`` when WeasyPrint is not installed.
    """
    try:
        from weasyprint import HTML  # type: ignore[import]

        HTML(string=html_content).write_pdf(output_path)
        return True
    except ImportError:
        return False
