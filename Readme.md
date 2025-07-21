# Invoice Reimbursement Analysis System

An intelligent, automated system for analyzing employee invoices against HR reimbursement policies using AI-powered document processing and natural language querying.

## 📋 Project Overview

The Invoice Reimbursement Analysis System automates the traditionally manual process of reviewing employee expense claims. The system:

- **Extracts and analyzes** HR reimbursement policies from PDF documents
- **Processes multiple invoices** simultaneously using batch processing
- **Determines reimbursement status** (Fully Reimbursed, Partially Reimbursed, or Declined) based on policy rules
- **Stores processed data** in a vector database for efficient retrieval
- **Provides natural language interface** for employees to query their reimbursement status

### Key Capabilities

✅ **Multi-format Support**: Handles PDFs with text extraction and OCR vision models (In our case it is Google Gemini 2.5 but we can use Pytesseract I preferred Gemini model due to it's latency) 
✅ **Batch Processing**: Concurrent processing of multiple invoices using ThreadPoolExecutor  
✅ **AI-Powered Analysis**: Google Gemini LLM for intelligent document understanding  
✅ **Vector Search**: Pinecone integration for efficient data retrieval  
✅ **Employee Chatbot**: Natural language queries about reimbursement status  
✅ **Web Interface**: Simple Streamlit frontend for testing and demonstration  

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │    Pinecone     │
│   Frontend      │───▶│    Backend      │───▶│  Vector Store   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Google Gemini  │
                    │      LLM        │
                    └─────────────────┘
```

### Data Flow

1. **Upload**: HR Policy PDF + Employee Invoices ZIP
2. **Extract**: Policy rules and invoice details using OCR/Vision
3. **Analyze**: Compare invoices against policy using Gemini LLM
4. **Store**: Processed data in Pinecone vector database
5. **Query**: Natural language search for employee-specific information

## 🛠️ Installation Instructions

### Prerequisites

- Python 3.10
- Google Cloud API key (for Gemini LLM)
- Pinecone API key (for vector storage)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/RajIIITR/Reimbursement_Analyzer
cd invoice-reimbursement-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Create a `.env` file in the root directory:

```bash
# .env file
GOOGLE_API_KEY=your_google_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
```

### Step 3: Get API Keys

**Google Gemini API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gemini API
3. Create an API key
4. Copy the key to your `.env` file

**Pinecone API Key:**
1. Sign up at [Pinecone](https://pinecone.io)
2. Create a new project
3. Go to API Keys section
4. Copy the API key to your `.env` file

### Step 4: Project Structure

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

## 🚀 Usage Guide

### Method 1: Complete Web Interface

```bash
# Start both FastAPI backend and Streamlit frontend
python run_app.py
```

Access the application:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Method 2: API Only

```bash
# Start FastAPI backend only
python app.py
```

### Method 3: Standalone Processing

```bash
# Edit file paths in main.py, then run
python main.py
```

## 📚 API Endpoints

### 1. Analyze Invoices
**POST** `/analyze_invoices`

Processes HR policy and employee invoices with batch processing.

**Parameters:**
- `hr_policy`: PDF file (multipart/form-data)
- `invoices_zip`: ZIP file containing invoice PDFs

**Example:**
```bash
curl -X POST "http://localhost:8000/analyze_invoices" \
  -F "hr_policy=@hr_policy.pdf" \
  -F "invoices_zip=@invoices.zip" \
```

**Response:**
```json
{
  "message": "Invoice analysis completed successfully using 4 concurrent workers",
  "total_employees": 3,
  "employees_processed": ["John Doe", "Jane Smith", "Bob Johnson"],
  },
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

### 2. Query Employee Data
**POST** `/query_employee`

Natural language queries about employee reimbursement data.

**Request Body:**
```json
{
  "employee_name": "John Doe",
  "query": "What are my reimbursement details?"
}
```

**Response:**
```json
{
  "employee_name": "John Doe",
  "query": "What are my reimbursement details?",
  "answer": "Based on your invoice data, you have 1 invoices processed..."
}
```

### 3. Additional Endpoints

- **GET** `/health` - Health check
- **GET** `/employees` - List all processed employees
- **GET** `/employee/{name}` - Get specific employee details

## 🔧 Technical Details

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
- **Pillow**: Image processing for OCR

**Vector Storage:**
- **Pinecone**: Cloud-based vector database
- **langchain-pinecone**: LangChain integration for Pinecone

### LLM and Embedding Model Choices

**Large Language Model: Google Gemini 2.5 Flash**
- **Reasoning**: Multimodal capabilities (text + vision) for processing invoice images
- **Speed**: Fast inference suitable for batch processing
- **Cost-effective**: Currently free API key for high-volume processing
- **Vision support**: Can process PDFs as images when text extraction fails

**Embedding Model: sentence-transformers/all-MiniLM-L6-v2**
- **Reasoning**: Lightweight, fast, and effective for semantic similarity
- **Dimension**: 384 dimensions (efficient storage and retrieval)
- **Performance**: Good balance between speed and accuracy
- **Multilingual**: Supports multiple languages for global use

### Vector Store Integration Approach

**Pinecone Configuration:**
```python
# Index creation
pc.create_index(
    name="employee-database",
    dimension=384,  # Matches embedding model
    metric="cosine",  # Semantic similarity
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

**Data Structure:**
```python
# Document format stored in Pinecone
{
    "page_content": "Employee: John Doe\nInvoice Count: 1\n...",
    "metadata": {
        "employee_name": "John Doe",
        "date": "15/01/2024",
        "document_type": "employee_record"
    }
}
```

**Search Strategy:**
- **Metadata filtering**: Filter by employee name for precise results
- **Semantic search**: Use embeddings for contextual understanding
- **Hybrid approach**: Combine exact matching with semantic similarity

## 📝 Prompt Design

### Invoice Analysis Prompt

**Design Philosophy:**
- **Structured output**: Enforces consistent format for parsing
- **Context-aware**: Includes HR policy for decision-making
- **Comprehensive**: Covers all invoice types and scenarios

**Template Structure:**
```python
def get_extraction_prompt(state):
    return f"""
    Extract invoice information and identify the EMPLOYEE NAME.
    
    EMPLOYEE NAME RULES:
    - For MEAL invoices: Look for "Customer Name"
    - For TRAVEL invoices: Look for "Passenger Details"
    - For CAB invoices: Look for "Customer Name"
    
    REIMBURSEMENT STATUS ANALYSIS:
    Based on the HR reimbursement policy below:
    {state.get('md_text', '')}
    
    **Reimbursement Status Categories:**
    - **Fully Reimbursed**: Entire amount reimbursable
    - **Partially Reimbursed**: Only portion reimbursable  
    - **Declined**: Not reimbursable per policy
    
    FORMAT:
    **EMPLOYEE NAME:** [exact name]
    **REIMBURSEMENT STATUS:** [status]
    **INVOICE DETAILS:**
    - Invoice Type: [type]
    - Date: [date]
    - Total Amount: [amount]
    - Reason: [explanation]
    """
```

**Key Design Elements:**
1. **Clear Instructions**: Specific rules for different invoice types
2. **Policy Integration**: Dynamic inclusion of HR policy context
3. **Structured Output**: Consistent format for easy parsing
4. **Reasoning Required**: Asks for explanation of decisions

### Chatbot Interaction Prompt

**Design Philosophy:**
- **Context-grounded**: Uses retrieved employee data
- **Conversational**: Natural, helpful responses
- **Concise**: Direct answers without unnecessary verbosity

**Template:**
```python
def get_query_response_prompt():
    return """
    You are an HR assistant AI. Use the following employee information 
    to answer the user's question.
    
    Employee Data:
    {context}
    
    User Question:
    {question}
    
    Give a concise, helpful, and context-grounded answer.
    """
```

**Prompt Engineering Techniques:**
1. **Role Definition**: Clear AI assistant role
2. **Context Injection**: Relevant employee data included
3. **Response Guidelines**: Specific instruction for answer quality
4. **Grounding**: Emphasizes using provided context

### Vision Model Prompts

**For Policy Extraction:**
```python
"Extract the HR Reimbursement policy from this image. 
Return the text in markdown format."
```

**For Invoice Processing:**
```python
"Extract all text and details from this invoice image:"
```

**Design Rationale:**
- **Simple and clear**: Avoid complex instructions that confuse vision models
- **Format specification**: Markdown for consistent structure
- **Focused task**: Single, well-defined objective per prompt

## 🧪 Testing and Validation

### Test Data Requirements

**HR Policy PDF:**
- Clear reimbursement rules and limits
- Structured format with sections (meals, travel, accommodation)
- Readable text or high-quality images

**Invoice ZIP File:**
- Mixed formats (text-based and image-based PDFs)
- Various invoice types (meals, travel, cabs, accommodation)
- Different employees and amounts

## 🚀 Deployment Options

### Local Development
```bash
python run_app.py
```

### Cloud Deployment

**Backend (Render/Railway/Heroku):**
```bash
# Procfile
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

**Frontend (Streamlit Cloud):**
- Push to GitHub
- Deploy on https://share.streamlit.io
- Set main file as `frontend.py`


## 🔒 Security Considerations

### Data Protection
- **File validation**: Strict PDF/ZIP format checking
- **Temporary files**: Automatic cleanup after processing
- **API keys**: Environment variable storage
- **Input sanitization**: Prevents injection attacks

### Best Practices
- Use HTTPS in production
- Implement rate limiting
- Add authentication for sensitive data
- Regular security updates
- May Add Batch Processing to reduce latency

## 🐛 Troubleshooting

### Common Issues

**1. API Connection Errors**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check environment variables
echo $GOOGLE_API_KEY
echo $PINECONE_API_KEY
```

**2. File Processing Errors**
- Verify PDF is not corrupted
- Check file size limits
- Ensure ZIP contains valid PDFs

**3. Performance Issues**
- Reduce `max_workers` for limited resources
- Check system memory usage
- Optimize PDF file sizes

#
```

### Code Structure
- Keep functions focused and single-purpose
- Add type hints for better code clarity
- Include docstrings for all functions
- Handle errors gracefully



---

**If You love Do like the Repository.**