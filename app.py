from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import os
from typing import Optional

from src.helper import (
    State, 
    extract_hr_policy_from_pdf, 
    process_invoices, 
    get_summary
)
from src.store import process_employees_to_pinecone, answer_query_for_employee
from src.config import GOOGLE_API_KEY, PINECONE_API_KEY

app = FastAPI(title="Invoice Reimbursement Analysis API", version="1.0.0")

# Global state to store processed data
global_state = State(
    md_text="",
    employee_invoice_data={},
    extract_invoice_data={}
)

class QueryRequest(BaseModel):
    employee_name: str
    query: str

@app.post("/analyze_invoices")
async def analyze_invoices(
    hr_policy: UploadFile = File(...),
    invoices_zip: UploadFile = File(...)
):
    """
    Endpoint to analyze invoices against HR policy
    
    Args:
        hr_policy: PDF file containing HR reimbursement policy
        invoices_zip: ZIP file containing employee invoice PDFs
    
    Returns:
        JSON response with analysis results
    """
    try:
        # Reset global state
        global global_state
        global_state = State(
            md_text="",
            employee_invoice_data={},
            extract_invoice_data={}
        )
        
        # Validate file types
        if not hr_policy.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="HR policy must be a PDF file")
        
        if not invoices_zip.filename.lower().endswith('.zip'):
            raise HTTPException(status_code=400, detail="Invoices must be in ZIP format")
        
        # Save uploaded files temporarily
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as hr_temp:
            hr_temp.write(await hr_policy.read())
            hr_temp_path = hr_temp.name
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zip_temp:
            zip_temp.write(await invoices_zip.read())
            zip_temp_path = zip_temp.name
        
        try:
            # Step 1: Extract HR policy
            global_state = extract_hr_policy_from_pdf(global_state, hr_temp_path)
            
            # Step 2: Process invoices
            global_state = process_invoices(global_state, zip_temp_path)
            
            # Step 3: Generate summary
            summary = get_summary(global_state)
            global_state["extract_invoice_data"] = summary
            
            # Step 4: Store in Pinecone
            if summary:
                process_employees_to_pinecone(summary, PINECONE_API_KEY)
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Invoice analysis completed successfully",
                    "total_employees": len(summary),
                    "employees_processed": list(summary.keys()),
                    "analysis_summary": summary
                }
            )
            
        finally:
            # Clean up temporary files
            os.unlink(hr_temp_path)
            os.unlink(zip_temp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing invoices: {str(e)}")

@app.post("/query_employee")
async def query_employee(request: QueryRequest):
    """
    Endpoint to query specific employee data
    
    Args:
        request: QueryRequest containing employee_name and query
    
    Returns:
        JSON response with query answer
    """
    try:
        # Check if data has been processed
        if not global_state.get("extract_invoice_data"):
            raise HTTPException(
                status_code=400, 
                detail="No data available. Please analyze invoices first using /analyze_invoices endpoint"
            )
        
        # Query the employee data
        answer = answer_query_for_employee(
            employee_name=request.employee_name,
            query=request.query
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "employee_name": request.employee_name,
                "query": request.query,
                "answer": answer
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Invoice Analysis API is running"}

@app.get("/employees")
async def get_employees():
    """Get list of all processed employees"""
    try:
        if not global_state.get("extract_invoice_data"):
            return JSONResponse(
                status_code=200,
                content={
                    "message": "No employees processed yet",
                    "employees": []
                }
            )
        
        employees_list = []
        for employee_name, data in global_state["extract_invoice_data"].items():
            employees_list.append({
                "employee_name": employee_name,
                "invoice_count": data.get("invoice_count", 0),
                "invoice_mode": data.get("invoice_mode", "N/A"),
                "reimbursement_status": data.get("Reimbursement_Status", "N/A"),
                "description": data.get("description", "N/A")
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "total_employees": len(employees_list),
                "employees": employees_list
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving employees: {str(e)}")

@app.get("/employee/{employee_name}")
async def get_employee_details(employee_name: str):
    """Get detailed information for a specific employee"""
    try:
        if not global_state.get("extract_invoice_data"):
            raise HTTPException(
                status_code=400,
                detail="No data available. Please analyze invoices first using /analyze_invoices endpoint"
            )
        
        # Find employee (case-insensitive search)
        employee_data = None
        actual_name = None
        
        for name, data in global_state["extract_invoice_data"].items():
            if name.lower() == employee_name.lower():
                employee_data = data
                actual_name = name
                break
        
        if not employee_data:
            raise HTTPException(
                status_code=404,
                detail=f"Employee '{employee_name}' not found"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "employee_name": actual_name,
                "details": employee_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving employee details: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)