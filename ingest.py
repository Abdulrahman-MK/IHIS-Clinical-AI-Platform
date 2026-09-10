import os
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

def ingest_pdf(pdf_path, persist_directory='./chroma_db', collection_name='gahar_handbook'):
    print(f'Loading {pdf_path}...')
    reader = PdfReader(pdf_path)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'

    print('Splitting text...')
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)
    print(f'Created {len(chunks)} chunks.')

    print('Initializing embedding model...')
    # Using the specified multilingual model
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    
    print('Generating embeddings...')
    embeddings = model.encode(chunks, show_progress_bar=True)

    print('Initializing ChromaDB...')
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    
    # Create or get collection
    collection = chroma_client.get_or_create_collection(name=collection_name)
    
    # Add to ChromaDB
    print('Adding chunks to ChromaDB...')
    ids = [f'chunk_{i}' for i in range(len(chunks))]
    collection.add(
        documents=chunks,
        embeddings=embeddings.tolist(),
        ids=ids
    )
    
    print('Ingestion complete! Database saved to', persist_directory)

if __name__ == '__main__':
    pdf_filename = 'gahar-handbook-for-hospitals-accreditation-standards-final.pdf'
    if not os.path.exists(pdf_filename):
        print(f'Error: {pdf_filename} not found.')
    else:
        ingest_pdf(pdf_filename)
