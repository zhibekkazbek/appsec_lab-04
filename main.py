from flask import Flask, request, jsonify
import pickle

app = Flask(__name__)

@app.route("/error")
def error():
    raise Exception("Database connection failed at 127.0.0.1 with user=admin password=supersecret")

SECRET_KEY = "HARDCODED_SECRET_123"

@app.route("/secret")
def secret():
    return f"The secret key is {SECRET_KEY}"

@app.route("/deserialize", methods=["POST"])
def deserialize():
    data = request.data
    obj = pickle.loads(data) 
    return jsonify({"status": "ok", "data": str(obj)})

if __name__ == "__main__":
    app.run(debug=True)
