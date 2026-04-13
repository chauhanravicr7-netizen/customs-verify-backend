import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Backend is running'}), 200

@app.route('/api/audit', methods=['POST'])
def audit():
    try:
        if 'zone_a' not in request.files or 'zone_b' not in request.files:
            return jsonify({'error': 'Both zone_a and zone_b required'}), 400
        
        # Sample response
        results = [
            {"field": "Invoice Number", "checklist_value": "INV-001", "invoice_value": "INV-001", "status": "match", "note": "Verified"},
            {"field": "Total Amount", "checklist_value": "10000", "invoice_value": "10000", "status": "match", "note": "Verified"}
        ]
        
        return jsonify({
            'status': 'success',
            'results': results,
            'summary': {'total_checks': 2, 'matches': 2, 'mismatches': 0, 'warnings': 0}
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
