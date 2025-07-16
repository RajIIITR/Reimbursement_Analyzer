import time
import re
from typing import Dict, List, Optional
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.prompt import get_query_response_prompt

INDEX_NAME = "employee-database"

def process_employees_to_pinecone(employee_invoice_data: Dict[str, Dict[str, str]], pinecone_api_key: str):
    """
    Process employee data and add to Pinecone.
    """
    # Initialize embeddings and Pinecone
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    pc = Pinecone(api_key=pinecone_api_key)

    # Create index if it doesn't exist
    existing_indexes = [index.name for index in pc.list_indexes()]

    if INDEX_NAME in existing_indexes:
        pc.delete_index(INDEX_NAME)
        
        # Wait for deletion to complete
        while INDEX_NAME in [index.name for index in pc.list_indexes()]:
            time.sleep(1)

    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

    # Wait for index to be ready
    while not pc.Index(INDEX_NAME).describe_index_stats():
        time.sleep(1)

    # Initialize vector store
    vector_store = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings
    )

    # Process each employee
    all_chunks = []

    for employee_name, employee_data in employee_invoice_data.items():
        # Create text content
        text = f"""
        Employee Name: {employee_name}
        Invoice Count: {employee_data.get('invoice_count', 0)}
        Invoice Mode: {employee_data.get('invoice_mode', 'N/A')}
        Reimbursement Status: {employee_data.get('Reimbursement_Status', 'N/A')}
        Description: {employee_data.get('description', 'N/A')}
        """

        # Extract date from description
        extracted_date = extract_date_from_description(employee_data.get('description', ''))

        # Create document
        doc = Document(
            page_content=text.strip(),
            metadata={
                "employee_name": employee_name,
                "date": extracted_date,
                "document_type": "employee_record",
                "text": text.strip()
            }
        )

        all_chunks.append(doc)

    # Add all documents to Pinecone
    vector_store.add_documents(all_chunks)
    time.sleep(1)
    
    return all_chunks

def extract_date_from_description(description: str) -> Optional[str]:
    """Extract date from description using regex."""
    if not description:
        return None

    # Simple regex for DD/MM/YYYY format
    date_pattern = r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'
    match = re.search(date_pattern, description)

    if match:
        day, month, year = match.groups()
        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"

    return None

def search_by_employee_name(employee_name: str, top_k: int = 10):
    """
    Search for documents by employee name using metadata filtering
    """
    # Initialize embeddings (same as used during indexing)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Initialize vector store
    vector_store = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings
    )

    # Create metadata filter for employee name
    metadata_filter = {"employee_name": employee_name}

    # Perform search with metadata filter
    results = vector_store.similarity_search_with_score(
        query="employee record",
        k=top_k,
        filter=metadata_filter
    )

    return results

def answer_query_for_employee(employee_name: str, query: str, top_k: int = 5):
    """
    Answer a user query for a specific employee using Pinecone context and Gemini LLM.
    """
    # Initialize Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    # Step 1: Get relevant documents for the employee
    results = search_by_employee_name(employee_name, top_k=top_k)

    if not results:
        return f"No data found for employee: {employee_name}"

    # Step 2: Concatenate all context from Pinecone
    context = "\n\n".join([doc.page_content for doc, _ in results])

    # Step 3: Define a prompt template
    prompt_template = PromptTemplate(
        template=get_query_response_prompt(),
        input_variables=["context", "question"]
    )

    # Step 4: Create LLM Chain
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Step 5: Run the chain
    response = chain.run({
        "context": context,
        "question": query
    })

    return response