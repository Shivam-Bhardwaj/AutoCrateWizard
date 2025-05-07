# wizard_app/ui_modules/details.py
"""
Handles the display of detailed component tables.
"""
import streamlit as st
import pandas as pd

def display_details_tables(wall_results, floor_results, top_panel_results):
    """Displays the detail tables in expanders."""
    st.divider(); st.subheader("📋 Component Details")

    with st.expander("Wall Panel Cleat Details", expanded=False):
        if wall_results and wall_results.get("status") == "OK":
            wall_details_data = []
            side_panel_cleats = wall_results.get("side_panels", [{}])[0].get("cleats", [])
            # Changed from end_panel_cleats and "end_panels"
            back_panel_cleats = wall_results.get("back_panels", [{}])[0].get("cleats", [])

            for i, cleat in enumerate(side_panel_cleats):
                wall_details_data.append({
                    "Panel Type": "Side", "Cleat #": i + 1, "Cleat Type": cleat.get("type"),
                    "Length (in)": cleat.get("length"), "Width (in)": cleat.get("width"),
                    "Thickness (in)": cleat.get("thickness"),
                    "Center Pos X (rel)": cleat.get("position_x"),
                    "Center Pos Y (rel)": cleat.get("position_y")
                })
            for i, cleat in enumerate(back_panel_cleats): # Changed from end_panel_cleats
                wall_details_data.append({
                    "Panel Type": "Back", "Cleat #": i + 1, "Cleat Type": cleat.get("type"), # Changed from "End"
                    "Length (in)": cleat.get("length"), "Width (in)": cleat.get("width"),
                    "Thickness (in)": cleat.get("thickness"),
                    "Center Pos X (rel)": cleat.get("position_x"),
                    "Center Pos Y (rel)": cleat.get("position_y")
                })
            if wall_details_data:
                df_wall_details = pd.DataFrame(wall_details_data)
                st.dataframe(df_wall_details, use_container_width=True, hide_index=True,
                             column_config={
                                 "Length (in)": st.column_config.NumberColumn(format="%.2f"),
                                 "Width (in)": st.column_config.NumberColumn(format="%.2f"),
                                 "Thickness (in)": st.column_config.NumberColumn(format="%.2f"),
                                 "Center Pos X (rel)": st.column_config.NumberColumn(format="%.2f"),
                                 "Center Pos Y (rel)": st.column_config.NumberColumn(format="%.2f")
                             })
            else:
                st.caption("No wall cleat details to display.")
        elif wall_results: # If status is not OK
             st.caption(f"Wall panel details not available. Status: {wall_results.get('status', 'N/A')}")
        else: # wall_results is None
            st.caption("Wall panel calculation not run or module not available.")


    with st.expander("Floorboard Details", expanded=False):
        if floor_results and floor_results.get("status") in ["OK", "WARNING"] and floor_results.get("floorboards"):
            fb_boards_table = floor_results.get("floorboards", [])
            board_data_table = [
                {"Board #": i+1, "Nominal Size": b.get("nominal", "N/A"),
                 "Actual Width (in)": b.get("actual_width", 0.0),
                 "Position Start Y (in)": b.get("position", 0.0)}
                for i, b in enumerate(fb_boards_table)
            ]
            df_boards_table = pd.DataFrame(board_data_table)
            st.dataframe( df_boards_table, use_container_width=True, hide_index=True,
                         column_config={
                             "Actual Width (in)": st.column_config.NumberColumn(format="%.3f"),
                             "Position Start Y (in)": st.column_config.NumberColumn(format="%.3f")
                         })
        elif floor_results:
            st.caption(f"Floorboard details not available. Status: {floor_results.get('status', 'N/A')}")
        else:
            st.caption("Floorboard calculation not run or module not available.")

    with st.expander("Top Panel Cleat Details", expanded=False):
        if top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
            cap_details_data = []
            lc_data = top_panel_results.get("longitudinal_cleats",{})
            tc_data = top_panel_results.get("transverse_cleats",{})
            if lc_data.get("count",0)>0:
                for i,pos_x in enumerate(lc_data.get("positions",[])):
                    cap_details_data.append({
                        "Type":"Longitudinal","Cleat #":i+1,
                        "Length (in)":lc_data.get("cleat_length_each"),
                        "Width (in)":lc_data.get("cleat_width_each"),
                        "Thickness (in)":lc_data.get("cleat_thickness_each"),
                        "Center Pos X (rel)":pos_x,"Center Pos Y (rel)":"N/A" # Y is relative for this cleat
                    })
            if tc_data.get("count",0)>0:
                for i,pos_y in enumerate(tc_data.get("positions",[])):
                    cap_details_data.append({
                        "Type":"Transverse","Cleat #":i+1,
                        "Length (in)":tc_data.get("cleat_length_each"),
                        "Width (in)":tc_data.get("cleat_width_each"),
                        "Thickness (in)":tc_data.get("cleat_thickness_each"),
                        "Center Pos X (rel)":"N/A","Center Pos Y (rel)":pos_y # X is relative for this cleat
                    })
            if cap_details_data:
                df_cap_details = pd.DataFrame(cap_details_data)
                st.dataframe(df_cap_details,use_container_width=True,hide_index=True,
                             column_config={
                                 "Length (in)":st.column_config.NumberColumn(format="%.2f"),
                                 "Width (in)":st.column_config.NumberColumn(format="%.2f"),
                                 "Thickness (in)":st.column_config.NumberColumn(format="%.2f"),
                                 "Center Pos X (rel)":st.column_config.NumberColumn(format="%.2f"),
                                 "Center Pos Y (rel)":st.column_config.NumberColumn(format="%.2f")
                             })
            else:
                st.caption("No top panel cleat details to display.")
        elif top_panel_results:
            st.caption(f"Top panel cleat details not available. Status: {top_panel_results.get('status', 'N/A')}")
        else:
            st.caption("Top panel calculation not run or module not available.")