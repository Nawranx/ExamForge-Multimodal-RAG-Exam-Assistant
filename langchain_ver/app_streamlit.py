import os
import tempfile
import streamlit as st
import pdfplumber
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from multimodal_utils import convert_pdf_to_images, generate_exam_with_groq, create_pdf_report
import json

# Load .env
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("Groq API Key not found. Please set it in .env file.")
    st.stop()

# Streamlit UI
st.set_page_config(page_title="ExamForge - Multimodal RAG Exam Assistant", layout="wide")
st.title("🔥 ExamForge")
st.write("**Multimodal RAG Exam Assistant** - Upload a PDF, chat with it, and generate comprehensive exams using ultra-fast Groq AI")

# File Upload
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# If file uploaded
if uploaded_file is not None:
    with st.spinner("Reading and processing PDF..."):

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            pdf_path = tmp_file.name

        # Extract text 
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        # Chunking
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text)

        # Embeddings (Keep using free HuggingFace embeddings)
        embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = FAISS.from_texts(chunks, embedding_model)

        # LLM - Switch to Groq
        llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=groq_api_key)

        # QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=vectorstore.as_retriever()
        )

        st.success("PDF processed. You can now use the features below!")

        # Create Tabs
        tab1, tab2 = st.tabs(["💬 Chat with PDF", "📝 Exam Generator"])

        with tab1:
            st.header("Chat with your PDF")
            user_question = st.text_input("Ask a question about the PDF:")

            if user_question:
                with st.spinner("Thinking..."):
                    try:
                        answer = qa_chain.invoke(user_question)
                        st.markdown("### 📌 Answer:")
                        st.write(answer['result'])
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with tab2:
            st.header("Multimodal Exam Generator")
            st.info("This feature uses Groq Llama 4 Scout to analyze diagrams and text across the ENTIRE PDF.")
            
            if st.button("Generate Comprehensive Exam"):
                # Use a placeholder for dynamic status updates
                status_placeholder = st.empty()
                
                def update_status(msg):
                    status_placeholder.text(msg)
                
                with st.spinner("Analyzing PDF and generating questions..."):
                    try:
                        # 1. Convert ALL PDF pages to images
                        images_b64 = convert_pdf_to_images(pdf_path)
                        
                        # 2. Call Groq Utility with batch processing
                        exam_json = generate_exam_with_groq(images_b64, groq_api_key, status_callback=update_status)
                        
                        status_placeholder.empty()

                        if not exam_json or (not exam_json["mcq"] and not exam_json["short_answer"] and not exam_json["essay"]):
                            st.warning("No technical content was found to generate questions. The PDF might be mostly administrative or images might be too low resolution.")
                        else:
                            st.success(f"Exam Generated! Total Questions: {len(exam_json['mcq']) + len(exam_json['short_answer']) + len(exam_json['essay'])}")
                            
                            # MCQs
                            if exam_json["mcq"]:
                                st.subheader("Multiple Choice Questions")
                                for i, q in enumerate(exam_json["mcq"]):
                                    st.write(f"**{i+1}. {q['question']}**")
                                    for opt in q['options']:
                                        st.write(f"- {opt}")
                                    with st.expander(f"Show Answer {i+1}"):
                                        st.write(f"**Correct Answer:** {q.get('answer', 'Not provided')}")
                            
                            # Short Answer
                            if exam_json["short_answer"]:
                                st.subheader("Short Answer Questions")
                                for i, q in enumerate(exam_json["short_answer"]):
                                    st.write(f"**{i+1}. {q['question']}**")
                                    with st.expander(f"Show Answer {i+1}"):
                                        st.write(q.get('answer', 'Not provided'))

                            # Essay
                            if exam_json["essay"]:
                                st.subheader("Essay Questions")
                                for i, q in enumerate(exam_json["essay"]):
                                    st.write(f"**{i+1}. {q['question']}**")
                                    with st.expander(f"Show Key Points {i+1}"):
                                        st.write(q.get('key_points_to_cover', 'Not provided'))

                            # --- NEW: PDF Download Option ---
                            st.divider()
                            st.subheader("📥 Export Exam")
                            try:
                                pdf_content = create_pdf_report(exam_json)
                                st.download_button(
                                    label="Download Exam PDF",
                                    data=pdf_content,
                                    file_name="generated_exam.pdf",
                                    mime="application/pdf"
                                )
                            except Exception as pdf_err:
                                st.error(f"Error creating PDF: {pdf_err}")

                    except Exception as e:
                        st.error(f"An error occurred: {e}")