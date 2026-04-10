```python
import google.generativeai as genai
import json
import re

COMPARISON_PROMPT = """
You are an expert customs and shipping document verifier. Analyze the provided documents and create a detailed audit report.

TARGET CHECKLIST (Zone A):
{checklist_text}

SUPPORTING DOCUMENTS (Zone B):
{invoice_texts}

Your task:
1. Extract all key fields from the TARGET CHECKLIST (Zone A)
2. Find corresponding values in SUPPORTING DOCUMENTS (Zone B)
3. Compare each field for accuracy and compliance
4. Check for regulatory compliance issues

For each field, provide a comparison with:
- Field name
- Expected value (from checklist)
- Actual value (from invoices/documents)
- Status: 'match', 'mismatch', or 'warning'
- Any notes about compliance

Return ONLY a valid JSON array with this exact structure. No markdown, no preamble:
[
  {{
    "field": "Invoice Number",
    "checklist_value": "INV-2024-001",
    "invoice_value": "INV-2024-001",
    "status": "match",
    "note": "Invoice number verified"
  }},
  {{
    "field": "HS Code",
    "checklist_value": "4407.10",
    "invoice_value": "4407.99",
    "status": "mismatch",
    "note": "HS Code mismatch detected. Checklist shows 4407.10 (Sawn wood) but invoice shows 4407.99 (Other). Verify with customs authority."
  }},
  {{
    "field": "Total Weight (kg)",
    "checklist_value": "3737.414",
    "invoice_value": "3737.414",
    "status": "match",
    "note": "Weight verified - matches exactly"
  }}
]

Important:
- Check ALL critical fields from the checklist
- Look for date format consistency
- Verify numerical values match exactly
- Flag any regulatory red flags
- Be thorough but concise in notes
- Return ONLY JSON, no other text
"""

def compare_documents(checklist_text, invoice_texts, api_key):
    """
    Use Gemini AI to compare documents and generate audit results.
    
    Args:
        checklist_text: Extracted text from Zone A (target checklist)
        invoice_texts: Dict of extracted texts from Zone B (supporting documents)
        api_key: Gemini API key
    
    Returns:
        List of audit results
    """
    
    # Format invoice texts for the prompt
    invoice_formatted = ""
    for doc_name, text in invoice_texts.items():
        invoice_formatted += f"\n\n{doc_name}:\n{text}\n"
    
    # Build the prompt
    prompt = COMPARISON_PROMPT.format(
        checklist_text=checklist_text[:2000],  # Limit to 2000 chars for API efficiency
        invoice_texts=invoice_formatted[:3000]  # Limit to 3000 chars
    )
    
    try:
        # Call Gemini API
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Parse response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        response_text = response_text.strip()
        
        # Parse JSON
        results = json.loads(response_text)
        
        return results
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response: {response_text}")
        # Fallback: return error result
        return [{
            "field": "Error",
            "checklist_value": "N/A",
            "invoice_value": "N/A",
            "status": "warning",
            "note": "Failed to parse audit results. Please check document format."
        }]
    
    except Exception as e:
        print(f"Gemini API error: {e}")
        return [{
            "field": "System Error",
            "checklist_value": "N/A",
            "invoice_value": "N/A",
            "status": "warning",
            "note": f"API Error: {str(e)}"
        }]
```
