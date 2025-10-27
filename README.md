# LangChain PDF Reader
LangChain PDF Reader : a simple Flask app that lets students upload textbooks or notes and chat with their content using LangChain, OpenAI, and ChromaDB. Designed to help learners ask natural questions about study material and get instant, contextual answers. Built around RAG (Retrieval-Augmented Generation),combining document retrieval with LLM 

##  Overview

This project allows students, researchers, and curious learners to **query textbooks, notes, or academic PDFs** directly.  
It extracts text from your PDFs, splits it into chunks, stores embeddings locally using **ChromaDB**, and uses **LangChain** to provide accurate, context-based answers through OpenAI’s language model.

---

##  Features

-  Chat with your PDFs using natural language.  
-  Ideal for students asking questions about their study materials.  
-  Uses **RAG** for accurate, contextual responses.  
-  Persistent vector storage with **ChromaDB** (keeps memory between runs).  
-  Simple and minimal Flask backend — easy to understand and extend.  
-  Includes example PDFs to test instantly.

---

##  Tech Stack

- **Python 3.12+**
- **Flask**
- **LangChain**
- **OpenAI API**
- **ChromaDB**
- **PyPDF / pdfminer / tiktoken**

---

##  Getting Started

###  Clone the repository
```bash
git clone https://github.com/Venyhunt/langchian-pdf-reader.git
cd langchian-pdf-reader
