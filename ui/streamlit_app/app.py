"""TeleOps - Entry point that redirects to Incident Generator."""

import streamlit as st

st.set_page_config(page_title="TeleOps", layout="wide")

# Redirect to main page
st.switch_page("pages/1_Incident_Generator.py")
