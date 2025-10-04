print("LangChain PDF Reader scaffold ready.")
from flask import Flask, request, render_template
import os
from PyPDF2 import PdfReader

app = Flask(__name__)

# ensure samples folder exists
os.makedirs("samples", exist_ok=True)

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

    filepath = os.path.join("samples", file.filename)
    file.save(filepath)

    # Extract text
    reader = PdfReader(filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    
    return f"Uploaded {file.filename} ✅<br> Pages: {len(reader.pages)}<br> Characters: {len(text)}"

if __name__ == "__main__":
    app.run(debug=True)
