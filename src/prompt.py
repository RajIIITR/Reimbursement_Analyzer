def get_extraction_prompt(state):
    """Standard prompt for invoice data extraction"""
    md_text = state.get("md_text", "")
    
    return f"""Extract invoice information and identify the EMPLOYEE NAME.

EMPLOYEE NAME RULES:
- For MEAL invoices: Look for "Customer Name"
- For TRAVEL invoices: Look for "Passenger Details"
- For CAB invoices: Look for "Customer Name"
- If no customer/passenger name found: use "No information about employee"

REIMBURSEMENT STATUS ANALYSIS:
Based on the HR reimbursement policy below, analyze the invoice and determine status:

**HR REIMBURSEMENT POLICY:**
{md_text}

**Reimbursement Status Categories:**
- **Fully Reimbursed:** The entire invoice amount is reimbursable according to the HR policy
- **Partially Reimbursed:** Only a portion of the invoice amount is reimbursable according to the HR policy
- **Declined:** The invoice is not reimbursable according to the HR policy

FORMAT:
**EMPLOYEE NAME:** [exact name or "No information about employee"]

**REIMBURSEMENT STATUS:** [**Fully Reimbursed** OR **Partially Reimbursed** OR **Declined**]

**INVOICE DETAILS:**
- Invoice Type: [Meal/Travel/Cab/Accomodation/Other]
- Invoice Number: [if available]
- Date: [date]
- Total Amount: [amount with currency]
- Description: [brief description]
- Reason: What is the reason for this reimbursement?

Return clean markdown format."""

def get_query_response_prompt():
    """Prompt for answering employee queries"""
    return """
You are an HR assistant AI. Use the following employee information to answer the user's question.

Employee Data:
------------------
{context}

User Question:
------------------
{question}

Give a concise, helpful, and context-grounded answer.
"""