# wizard_app/ui_modules/status.py
"""
Handles the display of calculation status messages.
"""
import streamlit as st

def display_status(skid_results, floor_results, wall_results, top_panel_results):
    """Displays the status of each calculation module."""
    st.subheader("📊 Calculation Status")
    status_cols = st.columns(4)

    # Skid Status
    with status_cols[0]:
        st.markdown("**Base/Skid Status**")
        skid_status = skid_results.get("status", "UNKNOWN")
        skid_message = skid_results.get("message", "N/A")
        if skid_status == "OK": st.success(f"✅ OK: {skid_message}")
        elif skid_status in ["ERROR", "OVER", "CRITICAL ERROR"]: st.error(f"❌ {skid_status}: {skid_message}")
        else: st.info(f"⚪️ {skid_status}: {skid_message}")

    # Floorboard Status
    with status_cols[1]:
        st.markdown("**Floorboard Status**")
        if floor_results:
            fb_status = floor_results.get("status", "UNKNOWN"); fb_message = floor_results.get("message", "N/A")
            if fb_status == "OK": st.success(f"✅ OK: {fb_message}")
            elif fb_status == "WARNING": st.warning(f"⚠️ WARNING: {fb_message}")
            elif fb_status in ["ERROR", "INPUT ERROR", "NOT FOUND", "CRITICAL ERROR", "SKIPPED"]: st.error(f"❌ {fb_status}: {fb_message}")
            else: st.info(f"⚪️ {fb_status}: {fb_message}")
        else: st.info("⚪️ Calculation pending...")

    # Wall Panel Status
    with status_cols[2]:
        st.markdown("**Wall Panel Status**")
        if wall_results:
            wp_status = wall_results.get("status", "UNKNOWN"); wp_message = wall_results.get("message", "N/A")
            if wp_status == "OK": st.success(f"✅ OK: {wp_message}")
            elif wp_status == "WARNING": st.warning(f"⚠️ WARNING: {wp_message}")
            elif wp_status in ["ERROR", "NOT FOUND", "CRITICAL ERROR", "SKIPPED"]: st.error(f"❌ {wp_status}: {wp_message}")
            else: st.info(f"⚪️ {wp_status}: {wp_message}")
        else: st.info("⚪️ Calculation pending...")

    # Top Panel Status
    with status_cols[3]:
        st.markdown("**Top Panel Status**")
        if top_panel_results:
            tp_status_val = top_panel_results.get("status", "UNKNOWN"); tp_message_val = top_panel_results.get("message", "N/A")
            if tp_status_val == "OK": st.success(f"✅ OK: {tp_message_val}")
            elif tp_status_val == "WARNING": st.warning(f"⚠️ WARNING: {tp_message_val}")
            elif tp_status_val in ["ERROR", "NOT FOUND", "CRITICAL ERROR", "SKIPPED"]: st.error(f"❌ {tp_status_val}: {tp_message_val}")
            else: st.info(f"⚪️ {tp_status_val}: {tp_message_val}")
        else: st.info("⚪️ Calculation pending...")

