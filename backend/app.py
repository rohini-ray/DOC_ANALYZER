from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

import os
from dotenv import load_dotenv

import google.generativeai as genai

from utils.pdf_reader import extract_pdf_text
from utils.docx_reader import extract_docx_text
from utils.chunking import chunk_text
from utils.embeddings import (
    create_embeddings,
    create_query_embedding
)
from utils.rag import (
    store_embeddings,
    search_similar_chunks
)

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Load Gemini model
model = genai.GenerativeModel(
    "gemini-1.5-flash"
)

# Flask app
app = Flask(__name__)
CORS(app)

# Upload folder
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables
document_chunks = []
faiss_index = None


@app.route("/")
def home():

    return jsonify({
        "message": "Document Analyser Backend Running"
    })


@app.route("/upload", methods=["POST"])
def upload_document():

    global document_chunks
    global faiss_index

    if "document" not in request.files:

        return jsonify({
            "error": "No file uploaded"
        })

    file = request.files["document"]

    if file.filename == "":

        return jsonify({
            "error": "No selected file"
        })

    # Save uploaded file
    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    text = ""

    # Extract text from file
    if file.filename.endswith(".pdf"):

        text = extract_pdf_text(filepath)

    elif file.filename.endswith(".docx"):

        text = extract_docx_text(filepath)

    elif file.filename.endswith(".txt"):

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read()

    else:

        return jsonify({
            "error": "Unsupported file format"
        })

    # Check extracted text
    if text.strip() == "":

        return jsonify({
            "error": "No text found in document"
        })

    # Chunk text
    document_chunks = chunk_text(text)

    # Create embeddings
    embeddings = create_embeddings(
        document_chunks
    )

    # Store embeddings in FAISS
    faiss_index = store_embeddings(
        embeddings
    )

    return jsonify({
        "message": "Document uploaded successfully",
        "chunks_created": len(document_chunks)
    })


@app.route("/ask", methods=["POST"])
def ask_question():

    global document_chunks
    global faiss_index

    question = request.form.get("question")

    if not question:

        return jsonify({
            "error": "Question is required"
        })

    if faiss_index is None:

        return jsonify({
            "error": "Please upload a document first"
        })

    # Create query embedding
    query_embedding = create_query_embedding(
        question
    )

    # Retrieve relevant chunks
    retrieved_chunks = search_similar_chunks(
        faiss_index,
        query_embedding,
        document_chunks
    )

    # Create context
    context = "\n".join(
        retrieved_chunks
    )

    # Prompt for Gemini
    prompt = f"""
    You are an AI document assistant.

    Answer the user's question
    ONLY using the document context below.

    DOCUMENT CONTEXT:
    {context}

    QUESTION:
    {question}
    """

    try:

        # Generate Gemini response
        response = model.generate_content(
            prompt
        )

        answer = response.text

        return jsonify({
            "answer": answer
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )