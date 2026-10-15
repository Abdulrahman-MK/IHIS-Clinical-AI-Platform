from flask import Blueprint, request, jsonify
import os
import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer

rag_bp = Blueprint('rag', __name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    candidate_models = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-3.5-flash']
    llm_model = None
    for model_name in candidate_models:
        try:
            llm_model = genai.GenerativeModel(model_name)
            break
        except Exception as e:
            continue
    if not llm_model:
        print('Warning: Could not initialize any Gemini model variant.')
else:
    llm_model = None

# Initialize Embeddings and Chroma
try:
    print('Loading embedding model for RAG...')
    embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    chroma_client = chromadb.PersistentClient(path='./chroma_db')
    collection = chroma_client.get_collection(name='gahar_handbook')
except Exception as e:
    print('Warning: Failed to load embeddings or ChromaDB. Did you run ingest.py?', e)
    embedding_model = None
    collection = None

@rag_bp.route('/api/chat', methods=['POST'])
def chat():
    if not llm_model or not embedding_model or not collection:
        return jsonify({'error': 'Backend not fully initialized. Check embeddings, DB, or API keys.'}), 500

    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        query_embedding = embedding_model.encode([user_message]).tolist()
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=5
        )
        
        context_chunks = results['documents'][0]
        context_text = '\n\n'.join(context_chunks)
        
        prompt = f'''You are a helpful assistant for the IHIS web application. 
Use the following context from the GAHAR Hospital Accreditation Standards 2025 Edition to answer the user's question. 
If the answer is not contained in the context, say so. Answer in the same language as the user's question (English or Arabic).
Please format your response using Markdown. Use bold headers, bullet points, and nice spacing to make it easy to read.

Context:
{context_text}

User Question: {user_message}

Answer:'''

        response = llm_model.generate_content(prompt)
        
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
