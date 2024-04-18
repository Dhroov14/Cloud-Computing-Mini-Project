from flask import Flask, request, jsonify
from hdfs import InsecureClient
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

# Initialize HDFS client
client = InsecureClient("http://<hdfs-host>:<hdfs-port>", user="<hdfs-username>")

# Generate a random encryption key
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

def divide_file(file_path, block_size=1024):
    """
    Divide a file into segments or blocks.
    """
    segments = []
    with open(file_path, 'rb') as f:
        while True:
            block = f.read(block_size)
            if not block:
                break
            segments.append(block)
    return segments

def encrypt_segment(segment):
    """
    Encrypt a file segment.
    """
    return cipher.encrypt(segment)

def decrypt_segment(encrypted_segment):
    """
    Decrypt an encrypted file segment.
    """
    return cipher.decrypt(encrypted_segment)

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
        segments = divide_file(file_path=file.stream)
        encrypted_segments = [encrypt_segment(segment) for segment in segments]
        
        # Upload encrypted segments to HDFS
        for i, segment in enumerate(encrypted_segments):
            with client.write(os.path.join(destination, f"segment_{i}.enc"), overwrite=True) as writer:
                writer.write(segment)

        return jsonify({"message": "File uploaded successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download_file", methods=["GET"])
def download_file():
    """
    Endpoint to download a file from HDFS.
    """
    file_name = request.args.get("file_name")
    if not file_name:
        return jsonify({"error": "No file name provided"}), 400

    destination = request.args.get("destination", os.getcwd())

    try:
        segments = []
        # Download encrypted segments from HDFS
        for i, _ in enumerate(client.list("/")):
            with client.read(os.path.join("/", f"segment_{i}.enc")) as reader:
                encrypted_segment = reader.read()
                segments.append(encrypted_segment)

        decrypted_segments = [decrypt_segment(segment) for segment in segments]

        # Concatenate decrypted segments and save the file
        with open(os.path.join(destination, file_name), 'wb') as f:
            for segment in decrypted_segments:
                f.write(segment)

        return jsonify({"message": "File downloaded successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
