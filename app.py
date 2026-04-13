import os
import json
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PyPDF2 import PdfReader

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Backend is running'}), 200

@app.route('/api/audit', methods=['POST'])
def audit():
    try:
        if 'zone_a' not in request.files:
            return jsonify({'error': 'zone_a (checklist) is required'}), 400
        
        if 'zone_b' not in request.files or len(request.files.getlist('zone_b')) == 0:
            return jsonify({'error': 'zone_b (supporting documents) is required'}), 400

        zone_a_file = request.files['zone_a']
        zone_b_files = request.files.getlist('zone_b')

        if not allowed_file(zone_a_file.filename):
            return jsonify({'error': 'zone_a must be a PDF'}), 400

        for file in zone_b_files:
            if not allowed_file(file.filename):
                return jsonify({'error': f'Invalid file type: {file.filename}'}), 400

        zone_a_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(zone_a_file.filename))
        zone_a_file.save(zone_a_path)

        zone_b_paths = []
        for file in zone_b_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(file_path)
            zone_b_paths.append(file_path)

        # For now, return sample results
        # In production, extract text from PDFs and compare with Gemini
        results = [
            {
                "field": "Invoice Number",
                "checklist_value": "INV-2024-001",
                "invoice_value": "INV-2024-001",
                "status": "match",
                "note": "Verified"
            }
        ]

        # Cleanup
        os.remove(zone_a_path)
        for path in zone_b_paths:
            os.remove(path)

        return jsonify({
            'status': 'success',
            'results': results,
            'summary': {
                'total_checks': len(results),
                'matches': len([r for r in results if r['status'] == 'match']),
                'mismatches': 0,
                'warnings': 0,
            }
        }), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')
