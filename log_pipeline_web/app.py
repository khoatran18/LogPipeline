from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
# import create_yaml_file
import docker_container
import subprocess
import os
import outline_yaml

vector_config_folder = "config/vector"

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route('/vector-action', methods=['POST'])
def handle_vector_action():
    data = request.get_json()
    print(data)
    outline_yaml.main_create_yaml_file(data, "config/vector")
    docker_container.run_container(data, vector_config_folder)
    return jsonify({"status": "success", "message": f"{data['action']} received"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
