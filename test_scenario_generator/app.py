import argparse
import requests
import json
from flask import Flask, request, jsonify
from facade import TestScenarioGeneratorFacade

# Define constants
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.2
DEFAULT_GROQ_API_KEY = "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"

app = Flask(__name__)

@app.route('/generate-test-scenarios', methods=['POST'])
def generate_test_scenarios():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    uploaded_file = request.files['file']
    
    if uploaded_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the uploaded file as a plain text file
    saved_path = "uploaded_requirements.txt"
    uploaded_file.save(saved_path)

    # Create the test scenario generator instance
    generator = TestScenarioGeneratorFacade(
        api_key=DEFAULT_GROQ_API_KEY,
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE
    )

    # Generate test scenarios from the uploaded text file
    test_scenarios = generator.generate_test_scenarios(saved_path)

    return jsonify(test_scenarios)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
