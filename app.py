import streamlit as st

from llm import answer_question


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Insurance Policy Assistant",
    page_icon="🛡️",
    layout="wide"
)


# --------------------------------------------------
# Custom styling
# --------------------------------------------------

st.markdown(
    """
    <style>

    .stApp {
        background-color: #212121;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    h1, h2, h3, p, span, label {
        color: #ececec;
    }

    [data-testid="stChatMessage"] {
        background-color: transparent;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    [data-testid="stChatInput"] {
        background-color: #2f2f2f;
        border-radius: 24px;
    }

    [data-testid="stChatInput"] textarea {
        color: #ececec;
    }

    [data-testid="stExpander"] {
        border: 1px solid #3a3a3a;
        border-radius: 8px;
        background-color: #262626;
    }

    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your **Insurance Policy Assistant**. "
                "Ask me anything about the home insurance policy."
            ),
            "sources": []
        }
    ]


# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown(
    '<div style="text-align:center; margin-bottom:30px;">'
    '<h2 style="margin-bottom:5px; color:#ececec;">'
    '🛡️ Insurance Policy Assistant'
    '</h2>'
    '<p style="color:#9b9b9b; font-size:14px;">'
    'Ask questions about your home insurance policy'
    '</p>'
    '</div>',
    unsafe_allow_html=True
)


# --------------------------------------------------
# Display chat history
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


        if (
            message["role"] == "assistant"
            and message.get("sources")
        ):

            with st.expander("Sources"):

                for source in message["sources"]:

                    if source["type"] == "cross-reference":

                        st.markdown(
                            f"**Section {source['section']} — "
                            f"{source['title']}**  \n"
                            f"↳ Followed from a cross-reference"
                        )

                    else:

                        st.markdown(
                            f"**Section {source['section']} — "
                            f"{source['title']}**"
                        )


# --------------------------------------------------
# Chat input
# --------------------------------------------------

question = st.chat_input(
    "Ask about the insurance policy..."
)


# --------------------------------------------------
# Handle new question
# --------------------------------------------------

if question:

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
            "sources": []
        }
    )


    # Display user message
    with st.chat_message("user"):

        st.markdown(question)


    # Generate assistant response
    with st.chat_message("assistant"):

        with st.spinner("Searching the policy..."):

            answer, sources = answer_question(question)


        st.markdown(answer)


        if sources:

            with st.expander("Sources"):

                for source in sources:

                    if source["type"] == "cross-reference":

                        st.markdown(
                            f"**Section {source['section']} — "
                            f"{source['title']}**  \n"
                            f"↳ Followed from a cross-reference"
                        )

                    else:

                        st.markdown(
                            f"**Section {source['section']} — "
                            f"{source['title']}**"
                        )


    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources
        }
    )