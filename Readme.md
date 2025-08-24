# Invoice Reimbursement Analysis System

An intelligent, automated system for analyzing employee invoices against HR reimbursement policies using AI-powered document processing and natural language querying.

## Project Overview

The Invoice Reimbursement Analysis System automates the traditionally manual process of reviewing employee expense claims. The system:

- **Extracts and analyzes** HR reimbursement policies from PDF documents
- **Processes multiple invoices** simultaneously using batch processing
- **Determines reimbursement status** (Fully Reimbursed, Partially Reimbursed, or Declined) based on policy rules
- **Stores processed data** in a vector database for efficient retrieval
- **Provides natural language interface** for employees to query their reimbursement status

### Key Capabilities

**Multi-format Support**: Handles PDFs with text extraction using PyPDF4llm and OCR vision models (In our case it is Google Gemini 2.5 but we can use Pytesseract I preferred Gemini model due to it's latency) <br> 
**AI-Powered Analysis**: Google Gemini LLM for intelligent document understanding  
**Vector Search**: Pinecone integration for efficient data retrieval  
**Employee Chatbot**: Natural language queries about reimbursement status  
**Web Interface**: Simple Streamlit frontend for testing and demonstration  


### Data Flow

1. **Upload**: HR Policy PDF + Employee Invoices ZIP
2. **Extract**: Policy rules and invoice details using OCR/Vision
3. **Analyze**: Compare invoices against policy using Gemini LLM
4. **Store**: Processed data in Pinecone vector database
5. **Query**: Natural language search for employee-specific information



### Project Structure

```
invoice-reimbursement-system/
├── src/
│   ├── __init__.py
│   ├── helper.py          # Core processing functions
│   ├── prompt.py          # LLM prompts
│   ├── store.py           # Pinecone operations
│   └── config.py          # Configuration
├── app.py                 # FastAPI application
├── frontend.py            # Streamlit frontend
├── main.py                # Standalone processing
├── run_app.py             # Run both services
├── requirements.txt       # Dependencies
└── README.md
```


### **API Docs**: 
  - http://localhost:8000/docs  (We can check our swagger UI here)

**Parameters:**
- `hr_policy`: PDF file (multipart/form-data)
- `invoices_zip`: ZIP file containing invoice PDFs



**(The Entire flow of data in our code base)**
```json  
{
  "message": "Invoice analysis completed successfully",
  "total_employees": 3,
  "employees_processed": ["John Doe", "Jane Smith", "Bob Johnson"],
  "analysis_summary": {
    "John Doe": {
      "invoice_count": 1,
      "invoice_mode": "meal",
      "Reimbursement_Status": "Fully Reimbursed",
      "description": "Lunch at restaurant, total cost ₹450, Date is 15/01/2024..."
    }
  }
}
```


**Sample Output & User Question**
```json
{
  "employee_name": "John Doe",
  "query": "What are my reimbursement details?",
  "answer": "Based on your invoice data, you have 1 invoices processed..."
}
```

### Libraries and Dependencies

**Core Framework:**
- **FastAPI**: Modern, fast web framework for building APIs
- **Streamlit**: Web app framework for the frontend interface
- **Uvicorn**: ASGI server for FastAPI

**AI and ML:**
- **LangChain**: Framework for LLM applications and chains
- **Google Generative AI**: Integration with Gemini LLM
- **Sentence Transformers**: Text embeddings for vector storage in HuggingFace

**Document Processing:**
- **PyMuPDF (fitz)**: PDF text extraction and processing
- **pymupdf4llm**: LLM-optimized PDF to markdown conversion (Extension of PyMuPDF)
- **Pillow**: Image processing for OCR (Google Gemini 2.5)

**Vector Storage:**
- **Pinecone**: Cloud-based vector database
- **langchain-pinecone**: LangChain integration for Pinecone

### LLM and Embedding Model Choices (Giving Answer to Why?)

**Large Language Model: Google Gemini 2.5 Flash**
- **Reasoning**: Multimodal capabilities (text + vision) for processing invoice images
- **Cost-effective**: Currently free API key for high-volume processing
- **Vision support**: Can process PDFs as images when text extraction fails

**Embedding Model: sentence-transformers/all-MiniLM-L6-v2**
- **Reasoning**: Lightweight, fast, and effective for semantic similarity
- **Dimension**: 384 dimensions (efficient storage and retrieval)
- **Performance**: Good balance between speed and accuracy
- **Multilingual**: Supports multiple languages for global use


**Search Strategy:**
- **Metadata filtering**: Filter by employee name for precise results
- **Semantic search**: Use embeddings for contextual understanding
- **Hybrid approach**: Combine exact matching with semantic similarity


### Test Data Requirements

**HR Policy PDF:**
- Clear reimbursement rules and limits
- Structured format with sections (meals, travel, accommodation)
- Readable text or high-quality images

**Invoice ZIP File:**
- Mixed formats (text-based and image-based PDFs)
- Various invoice types (meals, travel, cabs, accommodation)
- Different employees and amounts

**If You love Do like the Repository.**
