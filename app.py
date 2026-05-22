from flask import Flask, render_template, request, jsonify
import os

from utils.pdf_reader import extract_pdf_text
from utils.docx_reader import extract_docx_text
from utils.chunking import chunk_text
from utils.embeddings import create_embeddings, create_query_embedding
from utils.rag import (
    store_embeddings,
    search_similar_chunks
)

import requests

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Global storage
document_chunks = []
faiss_index = None

# Create uploads folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_document():

    global document_chunks
    global faiss_index

    if "document" not in request.files:
        return "No file uploaded"

    file = request.files["document"]

    if file.filename == "":
        return "No selected file"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    text = ""

    # Extract text
    if file.filename.endswith(".pdf"):
        text = extract_pdf_text(filepath)

    elif file.filename.endswith(".docx"):
        text = extract_docx_text(filepath)

    elif file.filename.endswith(".txt"):
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

    else:
        return "Unsupported file format"

    # Chunking
    document_chunks = chunk_text(text)

    # Embeddings
    embeddings = create_embeddings(document_chunks)

    # Store in FAISS
    faiss_index = store_embeddings(embeddings)

    return render_template(
        "index.html",
        upload_success=True
    )


@app.route("/ask", methods=["POST"])
def ask_question():

    global document_chunks
    global faiss_index

    question = request.form["question"]

    if faiss_index is None:
        return jsonify({
            "answer": "Please upload a document first."
        })

    # Create query embedding
    query_embedding = create_query_embedding(question)

    # Retrieve relevant chunks
    retrieved_chunks = search_similar_chunks(
        faiss_index,
        query_embedding,
        document_chunks
    )

    context = "\n".join(retrieved_chunks)

    prompt = f"""
    Answer the question based only on the context below.

    Context:
    {context}

    Question:
    {question}
    """

    # Ollama API
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    answer = response.json()["response"]

    return jsonify({
        "answer": answer
    })


if __name__ == "__main__":
    app.run(debug=True)