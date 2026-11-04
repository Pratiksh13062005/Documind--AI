import streamlit as st
import io
import time
from pypdf import PdfReader
from google import genai


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="DocuGenius AI",
    page_icon="📚",
    layout="wide"
)


# ==========================================
# DESIGN
# ==========================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #f5f0ff, #fff0f6);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #5422a8, #a52a82);
}

[data-testid="stSidebar"] * {
    color: white;
}

.title {
    text-align: center;
    color: #7136b5;
    font-size: 42px;
    font-weight: 800;
}

.subtitle {
    text-align: center;
    color: #777;
    font-size: 18px;
}

.card {
    background: white;
    padding: 22px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(100, 50, 150, 0.12);
    margin-bottom: 15px;
}

.stButton > button {
    background: linear-gradient(90deg, #7136b5, #d63384);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# SESSION STATE
# ==========================================

defaults = {
    "document_text": "",
    "document_name": "",
    "page_count": 0,
    "chat_history": [],
    "summary": "",
    "document_id": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================
# GEMINI MODELS
# ==========================================

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite"
]


# ==========================================
# GEMINI API FUNCTION
# ==========================================

def call_gemini(prompt, api_key):

    if not api_key or not api_key.strip():
        raise Exception("Please enter your Gemini API Key.")

    client = genai.Client(
        api_key=api_key.strip()
    )

    errors = []

    for model in MODELS:

        for attempt in range(2):

            try:

                interaction = client.interactions.create(
                    model=model,
                    input=prompt
                )

                answer = interaction.output_text

                if answer and answer.strip():
                    return answer.strip()

                raise Exception("Gemini returned an empty response.")

            except Exception as error:

                error_message = str(error)
                errors.append(f"{model}: {error_message}")

                error_lower = error_message.lower()

                busy = any(word in error_lower for word in [
                    "503",
                    "unavailable",
                    "high demand",
                    "429",
                    "resource_exhausted",
                    "overloaded",
                    "temporarily"
                ])

                if busy:

                    if attempt == 0:
                        time.sleep(3)
                        continue

                    # Try the next model
                    break

                # Do not retry authentication or other permanent errors
                raise Exception(error_message)

    raise Exception(
        "All Gemini models are currently busy or unavailable.\n\n"
        + "\n\n".join(errors[-3:])
    )


# ==========================================
# PDF EXTRACTION
# ==========================================

def extract_pdf(uploaded_file):

    try:

        pdf_bytes = uploaded_file.getvalue()

        reader = PdfReader(
            io.BytesIO(pdf_bytes)
        )

        pages_text = []

        for number, page in enumerate(reader.pages, start=1):

            text = page.extract_text()

            if text:
                pages_text.append(
                    f"\nPAGE {number}\n{text}"
                )

        document_text = "\n".join(pages_text)

        if not document_text.strip():
            raise Exception(
                "No readable text found. This PDF may be scanned."
            )

        return document_text, len(reader.pages)

    except Exception as error:
        raise Exception(f"PDF Error: {error}")


# ==========================================
# QUESTION ANSWERING
# ==========================================

def ask_question(question, document_text, api_key):

    prompt = f"""
You are DocuGenius AI, an intelligent PDF assistant.

Answer the user's question using the document below.

Instructions:
1. Read the document carefully.
2. Answer the question directly.
3. Use simple English.
4. Give detailed explanations when necessary.
5. Use bullet points for important information.
6. Never invent facts.
7. If the answer is not in the document, say so clearly.

DOCUMENT:

{document_text[:30000]}

USER QUESTION:

{question}

Give the answer now.
"""

    return call_gemini(prompt, api_key)


# ==========================================
# SUMMARY
# ==========================================

def generate_summary(document_text, api_key):

    prompt = f"""
You are an expert PDF summarization assistant.

Create a clear and useful summary of this document.

Include:

1. Document Overview
2. Main Purpose
3. Important Topics
4. Key Points
5. Important Findings
6. Conclusion

Use simple English and headings.

DOCUMENT:

{document_text[:30000]}
"""

    return call_gemini(prompt, api_key)


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.markdown(
    "<h1 style='text-align:center;'>📚 DocuGenius AI</h1>",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

st.sidebar.subheader("🔐 Gemini API Key")

api_key = st.sidebar.text_input(
    "Enter Gemini API Key",
    type="password",
    placeholder="Paste your API key"
)

st.sidebar.markdown("---")

st.sidebar.subheader("📂 Upload PDF")

uploaded_file = st.sidebar.file_uploader(
    "Choose PDF",
    type=["pdf"]
)


# ==========================================
# PROCESS PDF
# ==========================================

if uploaded_file is not None:

    if st.session_state.document_id != uploaded_file.file_id:

        try:

            with st.spinner("Reading PDF document..."):

                text, pages = extract_pdf(uploaded_file)

                st.session_state.document_text = text
                st.session_state.document_name = uploaded_file.name
                st.session_state.page_count = pages
                st.session_state.document_id = uploaded_file.file_id

                st.session_state.chat_history = []
                st.session_state.summary = ""

            st.sidebar.success("PDF uploaded successfully!")

        except Exception as error:
            st.sidebar.error(str(error))


# ==========================================
# NAVIGATION
# ==========================================

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "💬 Document Q&A",
        "📝 Document Summary",
        "📖 Document Reader",
        "ℹ️ About Project"
    ]
)


# ==========================================
# DASHBOARD
# ==========================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="title">📚 DocuGenius AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Intelligent Document Question Answering System'
        '</div>',
        unsafe_allow_html=True
    )

    st.write("")

    st.markdown("## ✨ Welcome!")

    st.write(
        "Upload your PDF document and ask questions. "
        "Gemini AI will help you understand your document."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="card">
        <h3>📄 PDF Upload</h3>
        <p>Upload PDF documents and extract text.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
        <h3>🤖 AI Answers</h3>
        <p>Ask questions and receive AI answers.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="card">
        <h3>📝 Summary</h3>
        <p>Generate automatic document summaries.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    if st.session_state.document_text:

        st.success("PDF is ready!")

        col1, col2 = st.columns(2)

        col1.metric(
            "Total Pages",
            st.session_state.page_count
        )

        col2.metric(
            "Extracted Characters",
            f"{len(st.session_state.document_text):,}"
        )

        st.info(
            f"Document: {st.session_state.document_name}"
        )

    else:

        st.info("Upload a PDF from the sidebar to get started.")


# ==========================================
# DOCUMENT Q&A
# ==========================================

elif page == "💬 Document Q&A":

    st.title("💬 Ask Your Document")

    st.write("Ask any question about your uploaded PDF.")

    if not st.session_state.document_text:

        st.warning("Please upload a PDF first.")

    else:

        st.success(
            f"Loaded: {st.session_state.document_name}"
        )

        with st.form("question_form"):

            question = st.text_input(
                "Your Question",
                placeholder="What is the main purpose of this document?"
            )

            submit = st.form_submit_button("🚀 Ask AI")

        if submit:

            if not question.strip():

                st.warning("Please enter a question.")

            elif not api_key.strip():

                st.error("Please enter your Gemini API Key.")

            else:

                try:

                    with st.spinner(
                        "🤖 Gemini is generating your answer. Please wait..."
                    ):

                        answer = ask_question(
                            question,
                            st.session_state.document_text,
                            api_key
                        )

                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": answer
                    })

                except Exception as error:

                    st.error(str(error))

        st.markdown("---")

        st.subheader("💬 Answer History")

        for chat in reversed(st.session_state.chat_history):

            st.markdown(
                f"**🧑 Question:** {chat['question']}"
            )

            st.success(
                chat["answer"]
            )

            st.markdown("---")

        if st.button("🗑️ Clear History"):

            st.session_state.chat_history = []
            st.rerun()


# ==========================================
# DOCUMENT SUMMARY
# ==========================================

elif page == "📝 Document Summary":

    st.title("📝 Document Summary")

    if not st.session_state.document_text:

        st.warning("Please upload a PDF first.")

    else:

        st.success(
            f"Document: {st.session_state.document_name}"
        )

        if st.button("✨ Generate Summary"):

            if not api_key.strip():

                st.error("Please enter your Gemini API Key.")

            else:

                try:

                    with st.spinner("Generating summary..."):

                        summary = generate_summary(
                            st.session_state.document_text,
                            api_key
                        )

                    st.session_state.summary = summary

                except Exception as error:

                    st.error(str(error))

        if st.session_state.summary:

            st.markdown("---")
            st.subheader("📌 AI Summary")
            st.markdown(st.session_state.summary)


# ==========================================
# DOCUMENT READER
# ==========================================

elif page == "📖 Document Reader":

    st.title("📖 Document Reader")

    if not st.session_state.document_text:

        st.warning("Please upload a PDF first.")

    else:

        st.success(
            f"Reading: {st.session_state.document_name}"
        )

        st.metric(
            "Total Pages",
            st.session_state.page_count
        )

        st.text_area(
            "Extracted Document Text",
            value=st.session_state.document_text,
            height=500
        )


# ==========================================
# ABOUT
# ==========================================

elif page == "ℹ️ About Project":

    st.title("ℹ️ About DocuGenius AI")

    st.markdown("""
    ## DocuGenius AI

    **Intelligent Document Question Answering System**

    DocuGenius AI is an AI-powered application
    that helps users understand PDF documents.

    ### Main Features

    - PDF Upload
    - PDF Text Extraction
    - AI Question Answering
    - Automatic PDF Summary
    - Document Reader
    - Chat History

    ### Technologies

    - Python
    - Streamlit
    - Google Gemini API
    - PyPDF

    ### AI Models

    - Gemini 3.8 Flash
    - Gemini 3.7 Flash
    - Gemini 3.5 Flash-Lite

    ### Project Category

    Generative Artificial Intelligence
    """)


# ==========================================
# FOOTER
# ==========================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "Made with ❤️ using Python and Gemini AI"
)
