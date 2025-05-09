# wizard_app/ui_modules/details.py
# REV: R2
"""
Handles the display of detailed component tables with NX-style column headers.
Ensures unsafe_allow_html=True for expander labels.
"""
import streamlit as st
import pandas as pd
import math 

# Define NX style for labels, consistent with app.py
NX_LABEL_STYLE = "color:green; font-weight:bold; font-family: 'Courier New', Courier, monospace;"
NX_LABEL_STYLE_HTML_OPEN = f"<span style='{NX_LABEL_STYLE}'>"
NX_LABEL_STYLE_HTML_CLOSE = "</span>"

def display_details_tables(wall_results, floor_results, top_panel_results):
    """Displays the detail tables in expanders with NX-style headers."""
    st.divider()
    st.subheader("Component Details (NX Variables)") 

    # --- Wall Panel Cleat Details ---
    expander_label_wall = f"{NX_LABEL_STYLE_HTML_OPEN}LIST_Wall_Panel_Cleats{NX_LABEL_STYLE_HTML_CLOSE}"
    with st.expander(expander_label_wall, expanded=False):
        # No need to repeat st.markdown for expander label if st.expander supports it.
        # However, if it doesn't, the line below is a good fallback.
        # st.markdown(expander_label_wall, unsafe_allow_html=True) 
        if wall_results and wall_results.get("status") == "OK":
            wall_details_list = []
            
            panel_types_data = {
                "Side": wall_results.get("side_panels", [{}])[0].get("cleats", []),
                "Back": wall_results.get("back_panels", [{}])[0].get("cleats", []) 
            }

            for panel_label, panel_cleats_data in panel_types_data.items():
                for i, cleat in enumerate(panel_cleats_data):
                    pos_x = cleat.get("position_x"); pos_x = float(pos_x) if isinstance(pos_x, (int, float)) and not (isinstance(pos_x, float) and math.isnan(pos_x)) else None
                    pos_y = cleat.get("position_y"); pos_y = float(pos_y) if isinstance(pos_y, (int, float)) and not (isinstance(pos_y, float) and math.isnan(pos_y)) else None
                    
                    wall_details_list.append({
                        "ATTR_Panel_Type": panel_label, 
                        "ATTR_Cleat_Index": i + 1, 
                        "ATTR_Cleat_Logi_Type": cleat.get("type", "-"), 
                        "DIM_Cleat_Length": float(cleat.get("length")) if isinstance(cleat.get("length"), (int, float)) else None,
                        "DIM_Cleat_Width_Actual": float(cleat.get("width")) if isinstance(cleat.get("width"), (int, float)) else None, 
                        "DIM_Cleat_Thickness_Actual": float(cleat.get("thickness")) if isinstance(cleat.get("thickness"), (int, float)) else None, 
                        "POS_Cleat_Center_X_Rel": pos_x, 
                        "POS_Cleat_Center_Y_Rel": pos_y  
                    })
            
            if wall_details_list:
                df_wall_details = pd.DataFrame(wall_details_list)
                st.dataframe(
                    df_wall_details,
                    use_container_width=True, hide_index=True,
                    column_config={ 
                         "DIM_Cleat_Length": st.column_config.NumberColumn(format="%.2f in"),
                         "DIM_Cleat_Width_Actual": st.column_config.NumberColumn(format="%.2f in"),
                         "DIM_Cleat_Thickness_Actual": st.column_config.NumberColumn(format="%.3f in"),
                         "POS_Cleat_Center_X_Rel": st.column_config.NumberColumn(format="%.2f in"),
                         "POS_Cleat_Center_Y_Rel": st.column_config.NumberColumn(format="%.2f in"),
                    }
                )
            else: st.caption("No wall cleat details generated.")
        elif wall_results: st.caption(f"Wall panel details not available. Status: {wall_results.get('status', 'N/A')}")
        else: st.caption("Wall panel calculation not run or module not available.")


    # --- Floorboard Details ---
    expander_label_floor = f"{NX_LABEL_STYLE_HTML_OPEN}LIST_Floorboards{NX_LABEL_STYLE_HTML_CLOSE}"
    with st.expander(expander_label_floor, expanded=False):
        if floor_results and floor_results.get("status") in ["OK", "WARNING"] and floor_results.get("floorboards"):
            fb_boards_table = floor_results.get("floorboards", [])
            board_data_table = []
            for i, b in enumerate(fb_boards_table):
                board_data_table.append({
                    "ATTR_Board_Index": i+1, 
                    "ATTR_Board_Nominal_Size": b.get("nominal", "N/A"),
                    "DIM_Board_Actual_Width": float(b.get("actual_width")) if isinstance(b.get("actual_width"), (int,float)) else None,
                    "POS_Board_Start_Y_Abs": float(b.get("position")) if isinstance(b.get("position"), (int,float)) else None 
                })
            df_boards_table = pd.DataFrame(board_data_table)
            st.dataframe( df_boards_table, use_container_width=True, hide_index=True,
                column_config={
                    "DIM_Board_Actual_Width": st.column_config.NumberColumn(format="%.3f in"),
                    "POS_Board_Start_Y_Abs": st.column_config.NumberColumn(format="%.3f in")
                 })
        elif floor_results: st.caption(f"Floorboard details not available. Status: {floor_results.get('status', 'N/A')}")
        else: st.caption("Floorboard calculation not run or module not available.")

    # --- Top Panel Cleat Details ---
    expander_label_top = f"{NX_LABEL_STYLE_HTML_OPEN}LIST_Cap_Cleats{NX_LABEL_STYLE_HTML_CLOSE}"
    with st.expander(expander_label_top, expanded=False):
        if top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
            cap_details_list = []
            lc_data = top_panel_results.get("longitudinal_cleats",{})
            tc_data = top_panel_results.get("transverse_cleats",{})
            
            if lc_data.get("count",0)>0:
                for i,pos_x in enumerate(lc_data.get("positions",[])):
                     cap_details_list.append({
                         "ATTR_Cleat_Type": "Longitudinal",
                         "ATTR_Cleat_Index": i+1,
                         "DIM_Cleat_Length": float(lc_data.get("cleat_length_each")) if isinstance(lc_data.get("cleat_length_each"), (int,float)) else None,
                         "DIM_Cleat_Width_Actual": float(lc_data.get("cleat_width_each")) if isinstance(lc_data.get("cleat_width_each"), (int,float)) else None,
                         "DIM_Cleat_Thickness_Actual": float(lc_data.get("cleat_thickness_each")) if isinstance(lc_data.get("cleat_thickness_each"), (int,float)) else None,
                         "POS_Cleat_Center_X_Rel": float(pos_x) if isinstance(pos_x, (int,float)) else None, 
                         "POS_Cleat_Center_Y_Rel": None 
                    })
            if tc_data.get("count",0)>0:
                for i,pos_y in enumerate(tc_data.get("positions",[])):
                     cap_details_list.append({
                         "ATTR_Cleat_Type": "Transverse",
                         "ATTR_Cleat_Index": i+1,
                         "DIM_Cleat_Length": float(tc_data.get("cleat_length_each")) if isinstance(tc_data.get("cleat_length_each"), (int,float)) else None,
                         "DIM_Cleat_Width_Actual": float(tc_data.get("cleat_width_each")) if isinstance(tc_data.get("cleat_width_each"), (int,float)) else None,
                         "DIM_Cleat_Thickness_Actual": float(tc_data.get("cleat_thickness_each")) if isinstance(tc_data.get("cleat_thickness_each"), (int,float)) else None,
                         "POS_Cleat_Center_X_Rel": None,
                         "POS_Cleat_Center_Y_Rel": float(pos_y) if isinstance(pos_y, (int,float)) else None
                    })
            
            if cap_details_list:
                df_cap_details = pd.DataFrame(cap_details_list)
                st.dataframe( df_cap_details,use_container_width=True,hide_index=True,
                    column_config={
                         "DIM_Cleat_Length":st.column_config.NumberColumn(format="%.2f in"), 
                         "DIM_Cleat_Width_Actual":st.column_config.NumberColumn(format="%.2f in"), 
                         "DIM_Cleat_Thickness_Actual":st.column_config.NumberColumn(format="%.3f in"),
                         "POS_Cleat_Center_X_Rel":st.column_config.NumberColumn(format="%.2f in"), 
                         "POS_Cleat_Center_Y_Rel":st.column_config.NumberColumn(format="%.2f in")
                    })
            else: st.caption("No top panel cleat details generated.")
        elif top_panel_results: st.caption(f"Top panel cleat details not available. Status: {top_panel_results.get('status', 'N/A')}")
        else: st.caption("Top panel calculation not run or module not available.")
