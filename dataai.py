from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
from pandasai import SmartDataframe, SmartDatalake  # Assuming SmartDatalake is part of pandasai
from pandasai.llm import OpenAI

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

def load_sheet_data(selected_sheets_info):
    """Load data for selected sheets."""
    loaded_data = {}
    for key, (file, sheet_name) in selected_sheets_info.items():
        # Load data from the sheet
        data = pd.read_excel(file, sheet_name=sheet_name)
        loaded_data[key] = data
    return loaded_data

def display_data_ai_session():
    """Display UI for Data-AI session."""
    st.subheader("Data-AI Session")
    data_files = st.sidebar.file_uploader("Upload your data file", type=['csv', 'xlsx'], accept_multiple_files=True)
    
    if data_files:
        sheet_options = {}
        for data_file in data_files:
            if data_file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                xls = pd.ExcelFile(data_file)
                for sheet_name in xls.sheet_names:
                    # Unique key for each sheet across all files
                    key = f"{data_file.name} - {sheet_name}"
                    sheet_options[key] = (data_file, sheet_name)

        selected_sheets = st.multiselect("Select sheets to load", options=list(sheet_options.keys()))

        if selected_sheets:
            selected_sheets_info = {key: sheet_options[key] for key in selected_sheets}
            loaded_data = load_sheet_data(selected_sheets_info)

            if len(loaded_data) > 1:
                # Use SmartDatalake for multiple sheets
                sdl = SmartDatalake(list(loaded_data.values()), config={"llm": OpenAI(api_token=api_key)})
                # Example of using sdl
                st.write("Loaded data into SmartDatalake")
            else:
                # Use SmartDataframe for a single sheet
                sdf = SmartDataframe(next(iter(loaded_data.values())), config={"llm": OpenAI(api_token=api_key)})
                # Example of using sdf
                st.write("Loaded data into SmartDataframe")

            # Display data preview for selected sheets
            for key, data in loaded_data.items():
                st.write(f"Data Preview for {key}:", data.head())
            user_query = st.text_input("Ask a question about your data")
            # Assuming user queries are to be made per sheet

            if user_query:
                if len(loaded_data) > 1:
                    response = sdl.chat(user_query)
                else:
                    response = sdf.chat(user_query)
                st.write("Response:", response)
                # Handle response images similarly
                response_images = []
                for img in response_images:
                    st.image(img, caption="Analysis")
    else:
        st.info("Upload one or more files.")

