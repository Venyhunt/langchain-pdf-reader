
print("LangChain PDF Reader scaffold ready.")
from dotenv import load_dotenv
import os

# load environment variables from .env
load_dotenv()

# now OPENAI_API_KEY is availpython app.py
# now OPENAI_API_KEY is available via os.environ
print("OpenAI API key loaded:", bool(os.environ.get("OPENAI_API_KEY")))


from flask import Flask, request, render_template, jsonify,session
import os
from flask_session import Session
from PyPDF2 import PdfReader
import hashlib                # optional — used to create a stable id per pdf
from langchain_openai import OpenAIEmbeddings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA


app = Flask(__name__)

# session config (keeps the "current uploaded file" between requests in dev)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")  # change in prod
app.config["SESSION_TYPE"] = "filesystem"                             # store sessions on disk
# optional: custom dir for session files
app.config["SESSION_FILE_DIR"] = os.path.join(os.getcwd(), "flask_session")
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
Session(app)


# ensure samples folder exists
os.makedirs("samples", exist_ok=True)

def file_hash(path):
    """Return md5 hash of file bytes — used to create a stable collection name per file."""
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def index_file(pdf_path, chroma_dir="chroma_store/", use_hash_collection=True, max_chunks=None):
    """
    Index a PDF into Chroma.
    - pdf_path: path to PDF file on disk
    - chroma_dir: where Chroma persists data
    - use_hash_collection: if True, use md5(file) as a collection name (safer when many files)
    - max_chunks: if set, only index first N chunks (useful for testing + cost control)
    Returns: number of chunks processed (0 if skipped)
    """
    # ensure chroma dir exists
    os.makedirs(chroma_dir, exist_ok=True)

    # If using file-hash collections, skip if collection folder already exists
    if use_hash_collection:
        coll = file_hash(pdf_path)
        coll_path = os.path.join(chroma_dir, coll)
        if os.path.exists(coll_path) and os.listdir(coll_path):
            print(f"[index_file] collection {coll} already exists — skipping.")
            return 0

    # Load PDF into LangChain Documents (PyPDFLoader handles pages & metadata)
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # Split into chunks that embed nicely for LLMs/embedders
    splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    # optional: limit chunks during local testing to save OpenAI calls
    if max_chunks:
        chunks = chunks[:max_chunks]

    print(f"[index_file] {pdf_path} -> {len(chunks)} chunks (persist_dir={chroma_dir})")

    # Create embeddings and persist to Chroma
    embeddings = OpenAIEmbeddings()
    collection_name = file_hash(pdf_path) if use_hash_collection else None

    db = Chroma.from_documents(
        chunks,
        embeddings,
        persist_directory=chroma_dir,
        collection_name=collection_name
    )
    db.persist()
    return len(chunks)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "pdf" not in request.files:
        return "No file part", 400
    
    file = request.files["pdf"]
    if file.filename == "":
        return "No selected file", 400

     # ---- NEW: Check file type ----
    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files are allowed!", 400

    filepath = os.path.join("samples", file.filename)
    file.save(filepath)

    # Extract text
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

     # ---- NEW: Index PDF dynamically ----
    count = index_file(filepath, chroma_dir="chroma_store/", use_hash_collection=True, max_chunks=None)
    if count == 0:
        index_msg = "Already indexed (collection exists)."
    else:
        index_msg = f"Indexed {count} chunks, stored to chroma_store/"
    # after indexing finished

    collection_id = file_hash(filepath)

    # store the current uploaded collection in the server session
    session["current_collection"] = collection_id

    # render index.html with upload info + collection (so hidden input is filled)
    return render_template(
        "index.html",
        upload_success=True,
        filename=file.filename,
        index_msg=index_msg,
        collection=collection_id
    )

# --- CONFIG ---
CHROMA_DIR = os.path.join(os.getcwd(), "chroma_store")

# --- /ask route ---
@app.route("/ask", methods=["POST"])
def ask():
    
    """
    Accepts:
     - form field 'query' (from templates) OR JSON body {"query": "...", "collection": "..."}
    Returns:
     - If JSON request: JSON {answer, sources}
     - If form POST: render_template('index.html', answer=answer, sources=sources)
    """
       # get query from JSON or form
    if request.is_json:
        payload = request.get_json()
        query = payload.get("query", "").strip()
        collection_name = payload.get("collection")
 
    # FALLBACK: use last uploaded collection stored in session (if present)
    if not collection_name:
        collection_name = session.get("current_collection")


    if not query:
        return jsonify({"error": "Empty query"}), 400

    embeddings = OpenAIEmbeddings()

    try:
        vectordb = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
            collection_name=collection_name  # may be None if single-collection setup
        )
    except Exception as e:
        return jsonify({"error": f"Failed loading Chroma store: {e}"}), 500

    retriever = vectordb.as_retriever(search_kwargs={"k": 15})
    llm = OpenAI(temperature=0)

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    try:
        result = qa({"query": query})
    except Exception as e:
        return jsonify({"error": f"QA execution failed: {e}"}), 500

    answer = result.get("result") or result.get("answer") or "No answer."
    source_docs = result.get("source_documents", [])
    sources = [
        {
            "snippet": (getattr(doc, "page_content", "") or "")[:400],
            "metadata": getattr(doc, "metadata", {}) or {}
        }
        for doc in source_docs
    ]

    if request.is_json or request.headers.get("Accept") == "application/json":
        return jsonify({"answer": answer, "sources": sources})

    return render_template("index.html", answer=answer, sources=sources, collection=collection_name)



if __name__ == "__main__":
    app.run(debug=True)
