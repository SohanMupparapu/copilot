from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import sys
import pdfkit
from dotenv import load_dotenv

# Add the parent directory to sys.path to import consistency_chker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from consistency_chker import RequirementsConsistencyChecker

load_dotenv()

app = Flask(__name__)

# Configure CORS to allow requests from port 8080
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Get API key from environment variable (optional now since we're using mock responses)
api_key = os.environ.get("HF_API_KEY")

@app.route('/api/check-consistency', methods=['POST', 'OPTIONS'])
def check_consistency():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
        
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    # Save the uploaded file to a temporary location
    temp_dir = tempfile.mkdtemp()
    input_file_path = os.path.join(temp_dir, "requirements_document.txt")
    file.save(input_file_path)
    
    # Initialize the checker with mock mode enabled
    checker = RequirementsConsistencyChecker(api_key, model_name="gpt2")
    checker.use_mock = True  # Ensure mock mode is enabled
    
    try:
        # Process the document
        results = checker.process_large_document(input_file_path)
        
        # Generate markdown report
        md_report_path = os.path.join(temp_dir, "report.md")
        report_content = checker.generate_report(results)
        
        with open(md_report_path, 'w') as f:
            f.write(report_content)
        
        # Convert markdown to PDF
        pdf_report_path = os.path.join(temp_dir, "requirements_analysis_report.pdf")
        # print(report_content)
        try:
            pdfkit.from_file(md_report_path, pdf_report_path)
        except Exception as pdf_error:
            # If PDF generation fails, return the markdown as text
            print(f"PDF generation failed: {str(pdf_error)}")
            with open(md_report_path, 'r') as f:
                return jsonify({
                    "report": f.read(),
                    "error": "PDF generation failed, returning markdown instead"
                })
        
        # Return the PDF file with CORS headers
        response = send_file(
            pdf_report_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='requirements_analysis_report.pdf'
        )
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)  # Bind to all interfaces
