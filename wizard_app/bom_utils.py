# wizard_app/bom_utils.py
"""
Utility functions for compiling Bill of Materials data and generating PDF reports.
Refactored to align BOM structure and columns with provided PDF examples.
"""
import pandas as pd
from collections import defaultdict
import io
import logging
import math

# Attempt to import config relative to package structure
try:
    from . import config
except ImportError:
    try:
        import config
    except ImportError:
        class ConfigFallback:
            STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS = 1.5
            SKID_LENGTH_ASSUMPTION = "crate_overall_length"
        config = ConfigFallback()
        logging.warning("BOM Utils: Could not import config, using minimal fallbacks.")

# Attempt to import FPDF
try:
    from fpdf import FPDF
except ImportError:
    logging.error("FPDF2 library not found. Please install it: pip install fpdf2")
    FPDF = None # Set FPDF to None if not found

log = logging.getLogger(__name__)

def compile_bom_data(skid_results, floor_results, wall_results, top_panel_results, overall_dims):
    """
    Aggregates data into a BOM structure resembling the provided PDF examples,
    focusing on assemblies and major components.

    Returns:
        pd.DataFrame: DataFrame with columns: 'Item No.', 'Qty', 'Part No.', 'Description'.
                      Returns an empty DataFrame if no components are found.
    """
    bom_list = []
    item_counter = 1
    log.debug("Starting BOM data compilation (Assembly Focus).")

    def add_bom_item(qty, part_no_placeholder, description):
        nonlocal item_counter
        if qty is not None and qty > 0:
            bom_list.append({
                "Item No.": item_counter,
                "Qty": int(qty),
                "Part No.": part_no_placeholder, # Use placeholder for now
                "Description": description
            })
            log.debug(f"Added BOM Item {item_counter}: Qty={qty}, Desc={description}")
            item_counter += 1
        else:
             log.warning(f"Skipped adding BOM item due to zero/invalid quantity: {description}")

    # --- Skids ---
    if skid_results and skid_results.get("status") == "OK":
        skid_count = skid_results.get('skid_count', 0)
        skid_len = overall_dims.get('length')
        skid_w = skid_results.get('skid_width')
        skid_h = skid_results.get('skid_height')
        skid_type = skid_results.get('skid_type', '') # e.g., '4x4'

        if skid_len and skid_w and skid_h:
            # Format like: SKID, LUMBER, 4x4, 96.00 x 3.50 x 3.50
            desc = f"SKID, LUMBER, {skid_type}, {skid_len:.2f} x {skid_w:.2f} x {skid_h:.2f}"
            add_bom_item(skid_count, "TBD_SKID_PN", desc)
        else:
            log.warning("Missing dimensions for Skids, cannot add to BOM.")

    # --- Floorboards ---
    if floor_results and floor_results.get("status") in ["OK", "WARNING"]:
        boards = floor_results.get("floorboards", [])
        board_len = floor_results.get("floorboard_length_across_skids")
        board_thickness = config.STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS

        board_groups = defaultdict(int)
        # Group by nominal size AND actual width to handle custom correctly
        for board in boards:
            key = (board.get("nominal"), round(board.get("actual_width", 0), 3))
            board_groups[key] += 1

        if board_len and board_thickness:
            for (nominal, actual_width), quantity in board_groups.items():
                # Format like: FLOORBOARD, LUMBER, 2x8, 94.00 x 7.25 x 1.50
                # Or: FLOORBOARD, LUMBER, Custom 3.75" W, 94.00 x 3.75 x 1.50
                spec = nominal if nominal != "Custom" else f"Custom {actual_width:.2f}\" W"
                desc = f"FLOORBOARD, LUMBER, {spec}, {board_len:.2f} x {actual_width:.2f} x {board_thickness:.3f}"
                add_bom_item(quantity, "TBD_FLOOR_PN", desc)
        else:
             log.warning("Missing dimensions for Floorboards, cannot add to BOM.")

    # --- Wall Panel Assemblies ---
    # List assemblies, not individual components
    if wall_results and wall_results.get("status") == "OK":
        ply_thick = wall_results.get("panel_plywood_thickness_used")
        ply_spec = f"{ply_thick:.3f}\" PLYWOOD" if ply_thick else "PLYWOOD"
        # Placeholder for cleating standard reference
        cleat_ref = "CLEATED PER 0251-70054" # Reference standard if applicable

        if wall_results.get("side_panels"):
            side_panel_data = wall_results["side_panels"][0]
            side_w, side_h = side_panel_data.get("panel_width"), side_panel_data.get("panel_height")
            if side_w and side_h:
                desc = f"SIDE PANEL ASSY, {ply_spec}, {cleat_ref} ({side_w:.2f} x {side_h:.2f})"
                add_bom_item(2, "TBD_SIDE_PN", desc) # Quantity 2
            else:
                log.warning("Missing dimensions for Side Panel Assy.")

        if wall_results.get("back_panels"):
            back_panel_data = wall_results["back_panels"][0]
            back_w, back_h = back_panel_data.get("panel_width"), back_panel_data.get("panel_height")
            if back_w and back_h:
                desc = f"BACK PANEL ASSY, {ply_spec}, {cleat_ref} ({back_w:.2f} x {back_h:.2f})"
                add_bom_item(2, "TBD_BACK_PN", desc) # Quantity 2
            else:
                log.warning("Missing dimensions for Back Panel Assy.")

    # --- Top Panel Assembly ---
    if top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
        cap_w = top_panel_results.get("cap_panel_width")
        cap_l = top_panel_results.get("cap_panel_length")
        cap_ply_thick = top_panel_results.get("cap_panel_thickness")
        ply_spec = f"{cap_ply_thick:.3f}\" PLYWOOD" if cap_ply_thick else "PLYWOOD"
        cleat_ref = "CLEATED PER 0251-70054" # Reference standard if applicable

        if cap_w and cap_l:
             desc = f"TOP PANEL ASSY, {ply_spec}, {cleat_ref} ({cap_l:.2f} x {cap_w:.2f})"
             add_bom_item(1, "TBD_TOP_PN", desc) # Quantity 1
        else:
             log.warning("Missing dimensions for Top Panel Assy.")


    log.info(f"BOM data compilation finished. Found {item_counter-1} items.")
    # Ensure columns exist even if list is empty, matching PDF standard
    final_columns = ["Item No.", "Qty", "Part No.", "Description"]
    bom_df = pd.DataFrame(bom_list, columns=final_columns)
    # Fill NaN potentially introduced if list was empty but columns forced
    bom_df.fillna({"Item No.":0, "Qty":0, "Part No.":"-", "Description":"-"}, inplace=True)
    # Ensure integer types where appropriate
    bom_df["Item No."] = bom_df["Item No."].astype(int)
    bom_df["Qty"] = bom_df["Qty"].astype(int)

    return bom_df


# --- PDF Generation Class and Function ---
if FPDF:
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 12)
            title = 'Bill of Materials - AutoCrate Wizard'
            title_w = self.get_string_width(title) + 6
            doc_w = self.w
            self.set_x((doc_w - title_w) / 2)
            self.cell(title_w, 10, title, border=0, ln=1, align='C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

        def chapter_title(self, title):
            # Remove default chapter title - header is sufficient
            pass

        def chapter_body(self, df):
            if df.empty or df['Qty'].sum() == 0 : # Check if genuinely empty
                self.set_font('Helvetica', 'I', 10)
                self.cell(0, 10, "No Bill of Materials data available.", ln=1)
                return

            self.set_font('Helvetica', '', 9)
            self.set_draw_color(50, 50, 50)
            self.set_line_width(0.3)

            # Define column widths for ["Item No.", "Qty", "Part No.", "Description"]
            # Landscape A4 approx 277mm available (297 - 2*10margin)
            page_width = self.w - 2 * self.l_margin
            col_widths = {
                "Item No.": 15,   # Width for Item No.
                "Qty": 15,        # Width for Qty
                "Part No.": 50,   # Width for Part No.
                "Description": 197 # Remaining width for Description
            }
            # Adjust last column to take remaining space precisely
            desc_width = page_width - col_widths["Item No."] - col_widths["Qty"] - col_widths["Part No."]
            col_widths["Description"] = desc_width


            # Header
            self.set_font('Helvetica', 'B', 9)
            self.set_fill_color(230, 230, 230)
            self.set_text_color(0)
            for col_name in ["Item No.", "Qty", "Part No.", "Description"]: # Use defined order
                self.cell(col_widths[col_name], 7, col_name, border=1, fill=True, align='C')
            self.ln()

            # Body
            self.set_font('Helvetica', '', 8)
            self.set_fill_color(255, 255, 255)
            self.set_text_color(0)
            fill = False
            for index, row in df.iterrows():
                if row['Qty'] == 0: continue # Skip rows added just for column structure

                if self.get_y() > (self.h - self.b_margin - 12): # Check page break
                    self.add_page(orientation=self.cur_orientation)
                    # Redraw header
                    self.set_font('Helvetica', 'B', 9)
                    self.set_fill_color(230, 230, 230)
                    for col_name in ["Item No.", "Qty", "Part No.", "Description"]: self.cell(col_widths[col_name], 7, col_name, border=1, fill=True, align='C')
                    self.ln()
                    self.set_font('Helvetica', '', 8)
                    fill = False

                # Draw row - handle potential text overflow for Description
                current_x = self.get_x()
                current_y = self.get_y()
                max_line_height = 0

                # Draw fixed columns first
                self.cell(col_widths["Item No."], 6, str(row["Item No."]), border='LR', fill=fill, align='C')
                self.cell(col_widths["Qty"], 6, str(row["Qty"]), border='LR', fill=fill, align='C')
                self.cell(col_widths["Part No."], 6, str(row["Part No."]), border='LR', fill=fill, align='L')

                # Handle Description with MultiCell for wrapping
                desc_text = str(row["Description"])
                self.multi_cell(col_widths["Description"], 6, desc_text, border='LR', fill=fill, align='L', max_line_height=6) # Adjust height as needed

                # Reset Y position after multi_cell potentially moved it
                # We actually want all cells in the row to have the same height, determined by the tallest cell (Description)
                # This requires pre-calculating height or using a simpler approach
                # Simpler: Set fixed height and let text truncate or use smaller font
                # For now, sticking with fixed height 6 - long descriptions might be cut off
                self.set_xy(current_x + col_widths["Item No."] + col_widths["Qty"] + col_widths["Part No."] + col_widths["Description"], current_y)
                self.ln(6) # Move down by cell height

                fill = not fill
            # Closing bottom border
            self.cell(sum(col_widths.values()), 0, '', 'T')


        def print_df(self, df, title=""):
            self.add_page(orientation='L')
            self.alias_nb_pages()
            # Title is handled by header now
            # if title: self.chapter_title(title)
            self.chapter_body(df)


    def generate_bom_pdf_bytes(bom_df):
        """Generates the BOM PDF (assembly focus) and returns it as bytes."""
        if not FPDF:
            log.error("FPDF2 library not loaded. Cannot generate PDF.")
            return None
        if bom_df is None:
            log.error("BOM DataFrame is None. Cannot generate PDF.")
            return None
        # Check if DataFrame is effectively empty (might have dummy row)
        if bom_df.empty or bom_df['Qty'].sum() == 0:
            log.warning("BOM DataFrame is empty. Generating PDF indicating no data.")
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "I", 12)
            pdf.cell(0, 10, "No Bill of Materials data available to generate.", ln=1, align='C')
            pdf_output = pdf.output(dest='S')
            if isinstance(pdf_output, str): return pdf_output.encode('latin-1')
            else: return bytes(pdf_output)

        try:
            pdf = PDF()
            pdf.print_df(bom_df)
            pdf_output = pdf.output(dest='S')
            log.info(f"FPDF output type: {type(pdf_output)}")
            if isinstance(pdf_output, str):
                log.warning("FPDF output was string, encoding to latin-1.")
                pdf_bytes = pdf_output.encode('latin-1')
            elif isinstance(pdf_output, (bytes, bytearray)):
                 pdf_bytes = bytes(pdf_output)
            else:
                log.error(f"Unexpected output type from FPDF: {type(pdf_output)}")
                return None
            log.info("Successfully generated BOM PDF bytes.")
            return pdf_bytes
        except Exception as e:
            log.error(f"Error generating BOM PDF: {e}", exc_info=True)
            return None
else:
    log.warning("FPDF2 library not available. BOM PDF generation disabled.")
    def generate_bom_pdf_bytes(bom_df): return None