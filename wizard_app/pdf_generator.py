# wizard_app/pdf_generator.py
"""
Utility functions for generating PDF reports for the AutoCrate Wizard.
Uses FPDF2 library for PDF creation and Kaleido for Plotly figure export.
"""
import io
import logging
from typing import Dict, List, Any

import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

log = logging.getLogger(__name__)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'AutoCrate Wizard - Crate Design Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def add_bom_table(self, bom_data: pd.DataFrame):
        if bom_data.empty:
            self.set_font('Arial', '', 10)
            self.cell(0, 10, "No Bill of Materials data available.", 0, 1)
            return

        self.set_font('Arial', 'B', 10)
        col_widths = {'Item No.': 20, 'Qty': 15, 'Part No.': 50, 'Description': 105} # Adjust as needed
        
        # Headers
        for col_name in bom_data.columns:
            self.cell(col_widths.get(col_name, 40), 7, col_name, 1, 0, 'C')
        self.ln()

        # Data
        self.set_font('Arial', '', 9)
        for index, row in bom_data.iterrows():
            for col_name in bom_data.columns:
                self.cell(col_widths.get(col_name, 40), 6, str(row[col_name]), 1, 0, 'L')
            self.ln()
            # TODO make this code more robust. The pdf is not being generated
    def add_plotly_figure_as_image(self, fig: go.Figure, title: str, fig_width_mm: int = 180):
        try:
            img_bytes = fig.to_image(format="png", engine="kaleido", width=800, height=600) # Adjust resolution as needed
            
            # Check page space, add new page if needed
            if self.get_y() + 70 > self.page_break_trigger: # Approximate height for image + title
                self.add_page()

            self.chapter_title(title)
            self.image(io.BytesIO(img_bytes), w=fig_width_mm) # Adjust width as needed
            self.ln(5)
        except Exception as e:
            log.error(f"Failed to add figure '{title}' to PDF: {e}", exc_info=True)
            self.set_font('Arial', 'I', 10)
            self.set_text_color(255, 0, 0) # Red color for error
            self.cell(0, 10, f"Error rendering figure: {title} ({e})", 0, 1)
            self.set_text_color(0, 0, 0) # Reset to black

def create_crate_report(bom_data: pd.DataFrame, figures: Dict[str, go.Figure], ui_inputs: Dict[str, Any]) -> bytes:
    """
    Generates a PDF report containing the BOM and crate component schematics.

    Args:
        bom_data: DataFrame containing the Bill of Materials.
        figures: Dictionary of Plotly figures, where keys are titles.
        ui_inputs: Dictionary of UI inputs for context.

    Returns:
        bytes: The generated PDF content.
    """
    pdf = PDF()
    pdf.alias_nb_pages() # Enable page numbering
    pdf.add_page()
    
    # Add some UI inputs for context (optional)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"Product Dimensions (WxLxH): {ui_inputs.get('product_width', 'N/A')}\" x {ui_inputs.get('product_length', 'N/A')}\" x {ui_inputs.get('product_height', 'N/A')}\"", 0, 1)
    pdf.cell(0, 6, f"Product Weight: {ui_inputs.get('product_weight', 'N/A')} lbs", 0, 1)
    pdf.ln(10)

    pdf.chapter_title("Bill of Materials (BOM)")
    pdf.add_bom_table(bom_data)

    for fig_title, fig_object in figures.items():
        if fig_object: # Ensure figure object exists
            pdf.add_page() # Add a new page for each figure for clarity, or manage flow better
            pdf.add_plotly_figure_as_image(fig_object, fig_title)

    return pdf.output(dest='S').encode('latin-1')