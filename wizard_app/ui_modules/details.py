# wizard_app/ui_modules/details.py
"""
Handles the display of detailed component tables.
Ensures numeric columns use None for missing data for Arrow compatibility.
Uses st.column_config for display formatting.
"""
import streamlit as st
import pandas as pd
import math # Needed for isnan

def display_details_tables(wall_results, floor_results, top_panel_results):
    """Displays the detail tables in expanders."""
    st.divider(); st.subheader("📋 Component Details")

    # --- Wall Panel Cleat Details ---
    with st.expander("Wall Panel Cleat Details", expanded=False):
        if wall_results and wall_results.get("status") == "OK":
            wall_details_list = []
            # Process Side Panels
            side_panel_cleats = wall_results.get("side_panels", [{}])[0].get("cleats", [])
            for i, cleat in enumerate(side_panel_cleats):
                 # Ensure positions are float or None
                 pos_x = cleat.get("position_x"); pos_x = float(pos_x) if isinstance(pos_x, (int, float)) else None
                 pos_y = cleat.get("position_y"); pos_y = float(pos_y) if isinstance(pos_y, (int, float)) else None
                 wall_details_list.append({
                     "Panel Type": "Side", "Cleat #": i + 1, "Cleat Type": cleat.get("type", "-"),
                     "Length (in)": float(cleat.get("length")) if isinstance(cleat.get("length"), (int, float)) else None,
                     "Width (in)": float(cleat.get("width")) if isinstance(cleat.get("width"), (int, float)) else None,
                     "Thickness (in)": float(cleat.get("thickness")) if isinstance(cleat.get("thickness"), (int, float)) else None,
                     "Center Pos X (rel)": pos_x,
                     "Center Pos Y (rel)": pos_y
                 })
            # Process Back Panels
            back_panel_cleats = wall_results.get("back_panels", [{}])[0].get("cleats", [])
            for i, cleat in enumerate(back_panel_cleats):
                 pos_x = cleat.get("position_x"); pos_x = float(pos_x) if isinstance(pos_x, (int, float)) else None
                 pos_y = cleat.get("position_y"); pos_y = float(pos_y) if isinstance(pos_y, (int, float)) else None
                 wall_details_list.append({
                     "Panel Type": "Back", "Cleat #": i + 1, "Cleat Type": cleat.get("type", "-"),
                     "Length (in)": float(cleat.get("length")) if isinstance(cleat.get("length"), (int, float)) else None,
                     "Width (in)": float(cleat.get("width")) if isinstance(cleat.get("width"), (int, float)) else None,
                     "Thickness (in)": float(cleat.get("thickness")) if isinstance(cleat.get("thickness"), (int, float)) else None,
                     "Center Pos X (rel)": pos_x,
                     "Center Pos Y (rel)": pos_y
                 })

            if wall_details_list:
                df_wall_details = pd.DataFrame(wall_details_list)
                # Use column_config for formatting in Streamlit display
                st.dataframe(
                    df_wall_details,
                    use_container_width=True, hide_index=True,
                    column_config={ # Format how numbers are DISPLAYED, handles None correctly
                         "Length (in)": st.column_config.NumberColumn(format="%.2f"),
                         "Width (in)": st.column_config.NumberColumn(format="%.2f"),
                         "Thickness (in)": st.column_config.NumberColumn(format="%.3f"),
                         "Center Pos X (rel)": st.column_config.NumberColumn(format="%.2f"),
                         "Center Pos Y (rel)": st.column_config.NumberColumn(format="%.2f"),
                    }
                )
            else: st.caption("No wall cleat details generated.")
        elif wall_results: st.caption(f"Wall panel details not available. Status: {wall_results.get('status', 'N/A')}")
        else: st.caption("Wall panel calculation not run or module not available.")


    # --- Floorboard Details ---
    with st.expander("Floorboard Details", expanded=False):
        # [ Keep the corrected floorboard details logic from the previous response - ensuring None not 'N/A' ]
        if floor_results and floor_results.get("status") in ["OK", "WARNING"] and floor_results.get("floorboards"):
            fb_boards_table = floor_results.get("floorboards", []);
            board_data_table = [ {
                "Board #": i+1, "Nominal Size": b.get("nominal", "N/A"),
                "Actual Width (in)": float(b.get("actual_width")) if isinstance(b.get("actual_width"), (int,float)) else None,
                "Position Start Y (in)": float(b.get("position")) if isinstance(b.get("position"), (int,float)) else None
            } for i, b in enumerate(fb_boards_table) ]
            df_boards_table = pd.DataFrame(board_data_table);
            st.dataframe( df_boards_table, use_container_width=True, hide_index=True,
                column_config={
                    "Actual Width (in)": st.column_config.NumberColumn(format="%.3f"),
                    "Position Start Y (in)": st.column_config.NumberColumn(format="%.3f")
                 })
        elif floor_results: st.caption(f"Floorboard details not available. Status: {floor_results.get('status', 'N/A')}")
        else: st.caption("Floorboard calculation not run or module not available.")

    # --- Top Panel Cleat Details ---
    with st.expander("Top Panel Cleat Details", expanded=False):
        # [ Keep the corrected top panel cleat details logic from the previous response - ensuring None not 'N/A' ]
        if top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
            cap_details_list = []; lc_data = top_panel_results.get("longitudinal_cleats",{}); tc_data = top_panel_results.get("transverse_cleats",{})
            if lc_data.get("count",0)>0:
                for i,pos_x in enumerate(lc_data.get("positions",[])):
                     cap_details_list.append({"Type":"Longitudinal","Cleat #":i+1,"Length (in)": float(lc_data.get("cleat_length_each")) if isinstance(lc_data.get("cleat_length_each"), (int,float)) else None,"Width (in)": float(lc_data.get("cleat_width_each")) if isinstance(lc_data.get("cleat_width_each"), (int,float)) else None,"Thickness (in)": float(lc_data.get("cleat_thickness_each")) if isinstance(lc_data.get("cleat_thickness_each"), (int,float)) else None,"Center Pos X (rel)": float(pos_x) if isinstance(pos_x, (int,float)) else None, "Center Pos Y (rel)": None})
            if tc_data.get("count",0)>0:
                for i,pos_y in enumerate(tc_data.get("positions",[])):
                     cap_details_list.append({"Type":"Transverse","Cleat #":i+1,"Length (in)": float(tc_data.get("cleat_length_each")) if isinstance(tc_data.get("cleat_length_each"), (int,float)) else None,"Width (in)": float(tc_data.get("cleat_width_each")) if isinstance(tc_data.get("cleat_width_each"), (int,float)) else None,"Thickness (in)": float(tc_data.get("cleat_thickness_each")) if isinstance(tc_data.get("cleat_thickness_each"), (int,float)) else None,"Center Pos X (rel)": None,"Center Pos Y (rel)": float(pos_y) if isinstance(pos_y, (int,float)) else None})
            if cap_details_list:
                df_cap_details = pd.DataFrame(cap_details_list);
                st.dataframe( df_cap_details,use_container_width=True,hide_index=True,
                    column_config={
                         "Length (in)":st.column_config.NumberColumn(format="%.2f"), "Width (in)":st.column_config.NumberColumn(format="%.2f"), "Thickness (in)":st.column_config.NumberColumn(format="%.3f"),
                         "Center Pos X (rel)":st.column_config.NumberColumn(format="%.2f"), "Center Pos Y (rel)":st.column_config.NumberColumn(format="%.2f")
                    })
            else: st.caption("No top panel cleat details generated.")
        elif top_panel_results: st.caption(f"Top panel cleat details not available. Status: {top_panel_results.get('status', 'N/A')}")
        else: st.caption("Top panel calculation not run or module not available.")