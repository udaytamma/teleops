"""TeleOps entry point - immediately redirects to Incident Generator."""

import streamlit as st

# Hide this page from sidebar by not setting any page config with a title
# and immediately redirecting
st.switch_page("pages/1_Incident_Generator.py")
