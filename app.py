import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

def sanitize_script_name(instruction):
    """
    Ensures the script name has a .py extension and strips directory 
    paths to prevent directory traversal attacks (e.g., ../../script.py).
    """
    if not instruction.endswith('.py'):
        instruction += '.py'
    return os.path.basename(instruction)

@app.route('/run-script', methods=['POST'])
def execute_script():
    # 1. Attempt to get the instruction from the request header
    instruction = request.headers.get('X-Instruction')
    
    # 2. If not found in headers, check the JSON body
    if not instruction:
        if request.is_json:
            instruction = request.get_json().get('instruction')
            
    # 3. Validate an instruction was actually provided
    if not instruction:
        return jsonify({
            "error": "Missing instruction. Provide it via 'X-Instruction' header or JSON body key 'instruction'."
        }), 400
        
    script_name = sanitize_script_name(instruction)
    
    # 4. Verify the script exists in the current directory
    if not os.path.isfile(script_name):
        return jsonify({"error": f"Script '{script_name}' not found in the current directory."}), 404
        
    # 5. Execute the script
    try:
        # Run the script, capture output, and set a timeout so it doesn't hang the server
        result = subprocess.run(
            ['python', script_name], # Use 'python3' if required by your environment
            capture_output=True, 
            text=True, 
            timeout=30 
        )
        
        return jsonify({
            "status": "success" if result.returncode == 0 else "error",
            "script": script_name,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "exit_code": result.returncode
        }), 200 if result.returncode == 0 else 500
        
    except subprocess.TimeoutExpired:
        return jsonify({"error": f"Script '{script_name}' timed out after 30 seconds."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Runs the Flask dev server continuously
    # host='0.0.0.0' exposes it to your local network; port 5000 is standard
    app.run(host='0.0.0.0', port=5000)
