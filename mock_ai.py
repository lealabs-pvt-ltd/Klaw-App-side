from flask import Flask, request, jsonify
import logging
from datetime import datetime
import socket

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename='mock_ai_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/api/user_request', methods=['POST'])
def user_request():
    """
    Mock AI API endpoint to simulate response to user queries.
    Expects form-data with user_id, course_code, user_question, previous_question_rating.
    Returns JSON with answer, input_tokens, and output_tokens.
    """
    try:
        # Extract form-data
        user_id = request.form.get('user_id')
        course_code = request.form.get('course_code')
        user_question = request.form.get('user_question')
        previous_question_rating = request.form.get('previous_question_rating')

        # Log request
        logger.info(
            f"Received request: user_id={user_id}, course_code={course_code}, "
            f"user_question={user_question}, previous_question_rating={previous_question_rating}"
        )

        # Validate required fields
        if not user_id or not course_code or not user_question:
            logger.error("Missing required fields in request")
            return jsonify({"error": "Missing required fields: user_id, course_code, and user_question are required"}), 400

        # Simulate AI response (hardcoded or simple logic)
        simulated_answer = f"Mock response to: {user_question}"
        if "binary tree" in user_question.lower():
            simulated_answer = (
                "A binary tree is a tree data structure in which each node has at most two children, "
                "referred to as the left child and the right child."
            )
        elif "python" in user_question.lower():
            simulated_answer = "Python is a high-level, interpreted programming language known for its readability and versatility."
        else:
            simulated_answer = f"This is a mock AI response to your question: {user_question}"

        # Calculate tokens (simple word count for simulation)
        input_tokens = len(user_question.split())
        output_tokens = len(simulated_answer.split())

        # Prepare response
        response_data = {
            "answer": simulated_answer,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

        logger.info(f"Returning response: {response_data}")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Get the local IP address
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"
    print(f"Server running on: http://{local_ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
