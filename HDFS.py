from flask import Flask, request, jsonify
from hdfs import InsecureClient

app = Flask(__name__)

# Initialize HDFS client
client = InsecureClient("http://<hdfs-host>:<hdfs-port>", user="<hdfs-username>")

@app.route("/list_files", methods=["GET"])
def list_files():
    """
    Endpoint to list files in a directory in HDFS.
    """
    directory = request.args.get("directory", "/")

    try:
        files = client.list(directory)
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload_file", methods=["POST"])
def upload_file():
    """
    Endpoint to upload a file to HDFS.
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    destination = request.form.get("destination", "/")

    try:
        client.upload(destination, file)
        return jsonify({"message": "File uploaded successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
