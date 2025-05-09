# wizard_app/ui_modules/status.py
# REV: R9
"""
Handles the display of calculation status messages.
Reverted to plain text and simple markdown for stability.
"""
import streamlit as st

def display_status(skid_results, floor_results, wall_results, top_panel_results):
    """Displays the status of each calculation module using simple markdown."""
    
    results_map = {
        "STATUS_Skid_Assy": skid_results,
        "STATUS_Floor_Assy": floor_results,
        "STATUS_Wall_Panels": wall_results,
        "STATUS_Cap_Assy": top_panel_results
    }
    
    active_results_map = {name_key: data for name_key, data in results_map.items() if data is not None}
    
    if not active_results_map:
        st.caption("No calculation results available to display status.")
        return

    num_cols = len(active_results_map)
    if num_cols == 0: return
    
    cols = st.columns(num_cols) 
    
    col_idx = 0
    for name_key, results_data in active_results_map.items():
        if col_idx < len(cols):
            current_col = cols[col_idx]
            with current_col:
                status_text_display = f"**{name_key}**: " # Bold NX variable name
                
                message = "Calculation details not available or module did not run." 
                if results_data: 
                    status_val = results_data.get("status", "PENDING")
                    message = results_data.get("message", "No specific message.") 
                    
                    if status_val == "OK":
                        status_text_display += "✅ OK"
                    elif status_val == "WARNING":
                        status_text_display += f"⚠️ {status_val}"
                    elif status_val in ["ERROR", "OVER", "CRITICAL ERROR", "INPUT ERROR", "NOT FOUND", "SKIPPED"]:
                        status_text_display += f"❌ {status_val}"
                    elif status_val == "PENDING": 
                        status_text_display += "⚪️ Pending"
                    else: 
                        status_text_display += f"ℹ️ {status_val}"
                else: 
                    status_text_display += "⚪️ Not Run" 

                st.markdown(status_text_display, help=message) # unsafe_allow_html=False is default
        col_idx += 1