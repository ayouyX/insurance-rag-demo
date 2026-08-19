import streamlit as st

from llm import answer_question


st.set_page_config(
    page_title="Insurance Policy Assistant",
    page_icon="📄"
)


st.title("📄 Insurance Policy Assistant")

st.write(
    "Ask a question about the home insurance policy."
)


question = st.text_input(
    "Your question",
    placeholder="What is the deductible for water damage?"
)


if st.button("Ask"):

    if question.strip():

        with st.spinner("Searching the policy..."):

            answer, sources = answer_question(question)


        st.subheader("Answer")

        st.write(answer)


        if sources:

            st.subheader("Sources")

            for source in sources:

                st.write(
                    f"Section {source['section']} — "
                    f"{source['title']}"
                )

    else:

        st.warning("Please enter a question.")