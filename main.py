import streamlit as st
from streamlit_chat import message
import requests
from dataai import display_data_ai_session

# API endpoints
UPLOAD_URL = 'http://ec2-15-207-95-73.ap-south-1.compute.amazonaws.com/Docgeniee/v1/doc/upload'
CONVERSATION_URL = 'http://ec2-15-207-95-73.ap-south-1.compute.amazonaws.com/Docgeniee/v1/doc/conversation'
CHAT_URL = 'http://ec2-15-207-95-73.ap-south-1.compute.amazonaws.com/Docgeniee/v1/doc/chat'

def api_post_request(url, json_data=None, files=None):
    """ Helper function for POST requests. """
    try:
        response = requests.post(url, json=json_data, files=files)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    return None

def upload_file(file):
    """ Handle file uploads. """
    files = {'file': (file.name, file, 'application/octet-stream')}
    return api_post_request(UPLOAD_URL, files=files)

def general_chat(query):
    """ Handle general chat. """
    response = requests.post(CHAT_URL, json={'query': query})
    return response.json()

def conversation_with_document(unique_id, query):
    """ Handle conversation with a document. """
    return api_post_request(CONVERSATION_URL, json_data={'id': unique_id, 'query': query})

def display_chat_ui(user_input_function, chat_function):
    """ Generic function to display chat UI. """
    reply_container = st.container()
    container = st.container()

    with container:
        with st.form(key='chat_form', clear_on_submit=True):
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                # Check if there's a last_message to pre-populate, else default placeholder
                last_message = st.session_state.get('last_message', "")
                user_input = st.text_area("Message:", value=last_message, placeholder="Type your message here", key='chat_input', height=100)
            with col2:
                regenerate_button = st.form_submit_button(label='🔄')

            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            with st.spinner('Generating response...'):
                response = user_input_function(user_input)
                if response:
                    chat_function(user_input, response)
            # Clear the last_message after submitting
            st.session_state['last_message'] = ""

        if regenerate_button:
            # If there's a past message to regenerate, do not clear the input but trigger the response generation
            if 'past' in st.session_state and st.session_state['past']:
                # Get the last user message
                last_message = st.session_state['past'][-1]
                # Set last_message to regenerate the form with it
                st.session_state['last_message'] = last_message
                # Optionally, you can call the function directly here if you want to process it immediately
                response = user_input_function(last_message)
                if response:
                    chat_function(last_message, response)

    if 'generated' in st.session_state and st.session_state['generated']:
        with reply_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="thumbs")
                message(st.session_state["generated"][i], key=str(i), avatar_style="fun-emoji")

def update_chat_history(user_input, api_response):
    """ Update chat history with the response from the API. """
    # Check if the 'response' key is in the API response and update the session state accordingly
    if 'response' in api_response:
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(api_response['response'])
    else:
        st.error("Received an unexpected response format from the API.")


def display_chat_with_documents():
    """ Display chat interface for document-based conversations. """
    uploaded_files = st.sidebar.file_uploader("Upload files", accept_multiple_files=True, type=['pdf', 'docx', 'txt'])  # Specified file types for upload
    documents = []

    if uploaded_files:
        for uploaded_file in uploaded_files:
            upload_response = upload_file(uploaded_file)
            print(upload_response)
            if upload_response:
                documents.append({'name': uploaded_file.name, 'unique_id': upload_response['unique_id']})

    document_names = [doc['name'] for doc in documents]
    document_options = ["All Documents"] + document_names  # Add 'All Documents' option

    selected_option = st.selectbox("Select Document", document_options, index=0)  # Make 'All Documents' the default selection

    if documents:
        selected_ids = [doc['unique_id'] for doc in documents] if selected_option == "All Documents" else [next(doc['unique_id'] for doc in documents if doc['name'] == selected_option)]

        
        # Container for chat messages
        reply_container = st.container()
        container = st.container()

        with container:
            with st.form(key='chat_form', clear_on_submit=True):
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    # Check if there's a last_message to pre-populate, else default placeholder
                    last_message = st.session_state.get('last_message', "")
                    user_input = st.text_area("Message:", value=last_message, placeholder="Type your message here", key='chat_input', height=100)
                with col2:
                    regenerate_button = st.form_submit_button(label='🔄')

                submit_button = st.form_submit_button(label='Send')

                if submit_button and user_input:
                    with st.spinner('Generating response...'):
                        # Call the function to handle the conversation, passing the selected document ID and the user query
                        output = conversation_with_document(selected_ids, user_input)
                        if output:
                            # Extract the actual response from the output if necessary
                            response_message = output.get('answer') or output
                            # Update session state with the new messages
                            update_chat_history(user_input, response_message)

                if regenerate_button:
                    # If there's a past message to regenerate, trigger the response generation again
                    if 'past' in st.session_state and st.session_state['past']:
                        # Get the last user message
                        last_message = st.session_state['past'][-1]
                        # Optionally, you can trigger response generation directly here
                        output = conversation_with_document(selected_ids, last_message)
                        if output:
                            response_message = output.get('answer') or output
                            update_chat_history(last_message, response_message)

        # Display chat history using session state
        if 'generated' in st.session_state and st.session_state['generated']:
            with reply_container:
                for i in range(len(st.session_state['generated'])):
                    message(st.session_state["past"][i], is_user=True, key=str(i) + '_user', avatar_style="thumbs")
                    message(st.session_state["generated"][i], key=str(i), avatar_style="fun-emoji")
    else:
        st.write("No documents uploaded yet.")


def initialize_session_state():
    """ Initialize session state. """
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["Welcome to Geniee!"]
    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hello!"]

def main():
    initialize_session_state()
    st.title("Geniee🫡")
    chat_mode = st.radio("Choose your interaction mode:", ['General Chat', 'Chat with Documents', 'Data-AI'])

    if chat_mode == 'General Chat':
        display_chat_ui(general_chat, update_chat_history)
    elif chat_mode == 'Chat with Documents':
        display_chat_with_documents()
    elif chat_mode == 'Data-AI':
        display_data_ai_session()

if __name__ == "__main__":
    main()
