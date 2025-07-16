import os
import re
import zipfile
import tempfile
import pymupdf4llm
import fitz
import base64
from typing import Dict, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from src.prompt import get_extraction_prompt

class State(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        md_text: contains HR Reimbursement Policy
        employee_invoice_data: contains employee invoice data
        extract_invoice_data: contains processed invoice summary
    """
    md_text: str
    employee_invoice_data: Dict[str, Dict[str, str]]
    extract_invoice_data: Dict[str, Dict[str, str]]

def extract_hr_policy_from_pdf(state: State, pdf_path: str) -> State:
    """
    Extract HR reimbursement policy from PDF.

    Args:
        state: LangGraph state to update
        pdf_path: Path to the PDF file

    Returns:
        Updated state with md_text containing extracted policy
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    try:
        # First try to extract directly from PDF
        md_text = pymupdf4llm.to_markdown(pdf_path)

        # If no text extracted, convert PDF to images and feed to gemini
        if not md_text or md_text.strip() == "":
            pdf_document = fitz.open(pdf_path)
            all_extracted_text = []

            for page_num in range(len(pdf_document)):
                # Convert page to PNG image
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                img_base64 = base64.b64encode(img_data).decode()

                # Create message with image and prompt
                message = HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": "Extract the HR Reimbursement policy from this image. Return the text in markdown format."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                )

                # Get extracted text from vision model
                response = llm.invoke([message])
                all_extracted_text.append(response.content)

            pdf_document.close()
            md_text = "\n\n".join(all_extracted_text)

        # Update state with extracted text
        state["md_text"] = md_text
        
    except Exception as e:
        state["md_text"] = ""

    return state

def process_invoices(state: State, zip_path: str) -> State:
    """Main function: Extract ZIP → Process PDFs → Store in state"""
    
    # Initialize state
    if "employee_invoice_data" not in state:
        state["employee_invoice_data"] = {}

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Extract ZIP and find all PDFs
            pdf_files = extract_zip_and_find_pdfs(zip_path, temp_dir)

            # Step 2: Process each PDF
            for pdf_path in pdf_files:
                invoice_data = extract_invoice_data(pdf_path, state)

                if invoice_data:
                    employee_name = get_employee_name(invoice_data)

                    # Step 3: Store in state
                    if employee_name in state["employee_invoice_data"]:
                        state["employee_invoice_data"][employee_name] += "\n\n---\n\n" + invoice_data
                    else:
                        state["employee_invoice_data"][employee_name] = invoice_data

    except Exception as e:
        state["employee_invoice_data"]["Error"] = str(e)

    return state

def extract_zip_and_find_pdfs(zip_path: str, extract_to: str) -> list:
    """Extract ZIP file and return list of PDF file paths"""
    pdf_files = []

    # Extract ZIP
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    # Find all PDFs (including nested ZIPs)
    for root, dirs, files in os.walk(extract_to):
        for file in files:
            file_path = os.path.join(root, file)

            if file.lower().endswith('.pdf'):
                pdf_files.append(file_path)

            elif file.lower().endswith('.zip'):
                # Handle nested ZIP
                nested_dir = os.path.join(root, f"nested_{file[:-4]}")
                os.makedirs(nested_dir, exist_ok=True)
                nested_pdfs = extract_zip_and_find_pdfs(file_path, nested_dir)
                pdf_files.extend(nested_pdfs)

    return pdf_files

def extract_invoice_data(pdf_path: str, state: State) -> str:
    """Extract invoice data from PDF using text extraction or vision model"""
    try:
        # Try text extraction first
        text = pymupdf4llm.to_markdown(pdf_path)

        if not text or text.strip() == "":
            # Use vision model if text extraction fails
            text = extract_with_vision(pdf_path, state)
        else:
            # Process extracted text with LLM
            text = process_with_llm(text, state)

        return text

    except Exception as e:
        return ""

def extract_with_vision(pdf_path: str, state: State) -> str:
    """Use vision model to extract data from PDF images"""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    doc = fitz.open(pdf_path)
    all_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = pix.tobytes("png")
        img_base64 = base64.b64encode(img_data).decode()

        # Get the image content first, then process with full prompt
        message = HumanMessage(content=[
            {"type": "text", "text": "Extract all text and details from this invoice image:"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
        ])

        response = llm.invoke([message])
        extracted_text = response.content

        # Now process with full prompt including status prediction
        full_prompt = get_extraction_prompt(state)
        final_message = HumanMessage(content=f"{full_prompt}\n\nExtracted text:\n\n{extracted_text}")
        final_response = llm.invoke([final_message])

        all_text.append(final_response.content)

    doc.close()
    return "\n\n".join(all_text)

def process_with_llm(text: str, state: State) -> str:
    """Process text-extracted content with LLM for better structure"""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    prompt = get_extraction_prompt(state)
    message = HumanMessage(content=f"{prompt}\n\nExtracted text:\n\n{text}")
    response = llm.invoke([message])

    return response.content

def get_employee_name(invoice_text: str) -> str:
    """Extract employee name from processed invoice text"""
    try:
        lines = invoice_text.split('\n')

        for line in lines:
            if '**EMPLOYEE NAME:**' in line:
                name = line.split(':', 1)[1].strip()
                name = name.replace('**', '').replace('*', '').strip()

                if name and name != "No information about employee":
                    return name

        # Fallback: search for customer patterns
        patterns = [
            r'Customer Name[:\s]+([A-Za-z\s]+)',
            r'Passenger[:\s]+([A-Za-z\s]+)',
            r'Name[:\s]+([A-Za-z\s]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, invoice_text, re.IGNORECASE)
            if matches:
                name = matches[0].strip()
                if name and len(name) > 1:
                    return name

        return "No information about employee"

    except Exception as e:
        return "No information about employee"

def get_reimbursement_status(invoice_text: str) -> str:
    """Extract reimbursement status from processed invoice text"""
    try:
        lines = invoice_text.split('\n')

        for line in lines:
            if '**REIMBURSEMENT STATUS:**' in line:
                status = line.split(':', 1)[1].strip()
                status = status.replace('**', '').replace('*', '').strip()

                if status:
                    return status

        # Fallback: search for status patterns
        patterns = [
            r'Status[:\s]+([A-Za-z\s*]+)',
            r'Reimbursement[:\s]+([A-Za-z\s*]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, invoice_text, re.IGNORECASE)
            if matches:
                status = matches[0].strip()
                if status and len(status) > 1:
                    return status

        return "**Pending Review**"

    except Exception as e:
        return "**Pending Review**"

def get_invoice_category_and_description(invoice_data: str) -> tuple:
    """Extract invoice category and generate detailed description"""
    try:
        # Get category from invoice type
        category_match = re.search(r'Invoice Type[:\s]+([A-Za-z/]+)', invoice_data, re.IGNORECASE)
        category = category_match.group(1).lower() if category_match else "other"

        # Normalize category
        if 'meal' in category or 'food' in category:
            category = 'meal'
        elif 'travel' in category or 'ticket' in category or 'flight' in category or 'train' in category:
            category = 'travel'
        elif 'cab' in category or 'taxi' in category or 'uber' in category or 'ola' in category:
            category = 'cab'
        elif 'hotel' in category or 'house' in category or 'pg' in category or 'hostel' in category:
            category = 'accomodation'
        else:
            category = 'other'

        # Generate description using LLM
        description = generate_description_with_llm(invoice_data, category)

        return category, description

    except Exception as e:
        return "other", "Unable to generate description"

def generate_description_with_llm(invoice_data: str, category: str) -> str:
    """Use LLM to generate category-specific description"""
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

        if category == 'travel':
            prompt = """Based on the following invoice data, provide a SHORT travel description (max 2 lines):

Include: Mode of travel, total cost, from which location to where, Date (should strictly match DD/MM/YYYY format), reason of given reimbursement
Format: "Flight from Delhi to Mumbai, total cost ₹5,000, Date is 12/02/22, reason of partially reimbursement is that for traveling cost as per HR Policy we can reimburse only ₹2000 as per 5.2 Travel Expenses" or "Train journey from Chennai to Bangalore, total cost ₹800, Date is 12/3/23, since it is within limit as mentioned in HR Reimbursement Policy hence it is fully reimburse as per 5.2 Travel Expenses."

Invoice data:
"""
        elif category == 'meal':
            prompt = """Based on the following invoice data, provide a SHORT meal description (max 2 lines):

Include: Cuisine/food name, total cost, restaurant name, Date (should strictly match DD/MM/YYYY format), reason of given reimbursement
Format: "North Indian cuisine at Punjabi Dhaba, total cost ₹450, Date is 4/2/25, within HR Policy Budget as per 5.1 Food and Beverages." or "Pizza and beverages at Domino's, total cost ₹600, Date is 23/5/24, it's not with HR Reimbursement policy as given budget by HR is ₹500 but your total cost is ₹600 hence it is partially reimburse as per 5.1 Food and Beverages."

Include: If Cuisine/food include any wine/vodka/cigarette
Format: "Decline!!! as wine doesn't comes under reimbursement Policy as per 5.1 Food and Beverages."

Invoice data:
"""
        elif category == 'cab':
            prompt = """Based on the following invoice data, provide a SHORT cab description (max 2 lines):

Include: Total cost, pickup and drop location if available, Date (should strictly match DD/MM/YYYY format), reason of given reimbursement
Format: "Cab ride from Airport to Hotel, total cost ₹350, Date of travel is 23/2/21, it's more than HR Reimbursement Policy as per 5.2 Travel Expenses hence partially reimburse" or "Uber ride within city, total cost ₹120, Date of travel is 3/01/2002, its within the limit as per 5.2 Travel Expenses hence fully reimburse."

Invoice data:
"""
        elif category == 'accomodation':
            prompt = """Based on the following invoice data, provide a SHORT accommodation description (max 2 lines):

Include: Total cost, hotel name if available, Date (should strictly match DD/MM/YYYY format), reason of given reimbursement
Format: "You stayed in hotel for 2 days, total cost ₹350, Date of travel is 23/2/21, it's more than HR Reimbursement Policy as per 5.3 Accommodation hence partially reimburse" or "You stayed in PG, total cost ₹120, Date of travel is 3/01/2002, its within the limit as per 5.3 Accommodation hence fully reimburse."

Invoice data:
"""
        else:
            prompt = """Based on the following invoice data, provide a SHORT description (max 2 lines):

Include: Service type, total cost, Date (should strictly match DD/MM/YYYY format), brief details
Format: "Service description with cost"

Invoice data:
"""

        message = HumanMessage(content=prompt + invoice_data)
        response = llm.invoke([message])

        # Clean up the response
        description = response.content.strip()
        # Remove quotes if present
        if description.startswith('"') and description.endswith('"'):
            description = description[1:-1]

        return description

    except Exception as e:
        return f"Invoice total with basic details (Error: {str(e)})"

def get_summary(state: State) -> dict:
    """Get summary of all employees and their invoices with category and description"""
    if "employee_invoice_data" not in state:
        return {}

    summary = {}
    for employee_name, invoice_data in state["employee_invoice_data"].items():
        invoice_count = invoice_data.count("**INVOICE DETAILS:**")
        amounts = re.findall(r'Total Amount[:\s]+[₹$]\s*([0-9,]+\.?\d*)', invoice_data)
        total_amount = sum(float(amt.replace(',', '')) for amt in amounts if amt)

        # Get invoice category and description
        category, description = get_invoice_category_and_description(invoice_data)
        status = get_reimbursement_status(invoice_data)
        summary[employee_name] = {
            'invoice_count': invoice_count,
            'invoice_mode': category,
            'Reimbursement_Status': status,
            'description': description
        }

    return summary

def extract_date_from_description(description: str) -> str:
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