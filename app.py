```python
import os
import json
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import google.generativeai as genai
from pdf_processor import extract_pdf_text
from document_comparator import compare_documents

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not set. Some features will not work.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'CustomsVerify Backend is running'}), 200

@app.route('/api/audit', methods=['POST'])
def audit():
    """
    Main audit endpoint
    Expects:
    - zone_a: Target checklist PDF
    - zone_b: Supporting documents (multiple files)
    """
    try:
        # Validate files
        if 'zone_a' not in request.files:
            return jsonify({'error': 'zone_a (checklist) is required'}), 400
        
        if 'zone_b' not in request.files or len(request.files.getlist('zone_b')) == 0:
            return jsonify({'error': 'zone_b (supporting documents) is required'}), 400

        zone_a_file = request.files['zone_a']
        zone_b_files = request.files.getlist('zone_b')

        # Validate filenames
        if not allowed_file(zone_a_file.filename):
            return jsonify({'error': 'zone_a must be a PDF'}), 400

        for file in zone_b_files:
            if not allowed_file(file.filename):
                return jsonify({'error': f'Invalid file type: {file.filename}'}), 400

        # Save files temporarily
        zone_a_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(zone_a_file.filename))
        zone_a_file.save(zone_a_path)

        zone_b_paths = []
        for file in zone_b_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(file_path)
            zone_b_paths.append(file_path)

        # Extract text from documents
        print("Extracting text from zone_a...")
        checklist_text = extract_pdf_text(zone_a_path)

        print("Extracting text from zone_b files...")
        invoice_texts = {}
        for idx, path in enumerate(zone_b_paths):
            invoice_texts[f'document_{idx}'] = extract_pdf_text(path)

        # Compare documents using Gemini AI
        print("Comparing documents with Gemini AI...")
        audit_results = compare_documents(
            checklist_text,
            invoice_texts,
            api_key=GEMINI_API_KEY
        )

        # Cleanup
        os.remove(zone_a_path)
        for path in zone_b_paths:
            os.remove(path)

        return jsonify({
            'status': 'success',
            'results': audit_results,
            'summary': {
                'total_checks': len(audit_results),
                'matches': len([r for r in audit_results if r['status'] == 'match']),
                'mismatches': len([r for r in audit_results if r['status'] == 'mismatch']),
                'warnings': len([r for r in audit_results if r['status'] == 'warning']),
            }
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
```
