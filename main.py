import os
import logging
from typing import Any, Dict, Mapping

from dotenv import load_dotenv
from flask import Flask, request, jsonify

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.warning("SECRET_KEY is not set in environment. Using ephemeral fallback (not for prod).")
    SECRET_KEY = os.urandom(24).hex()

app.config["SECRET_KEY"] = SECRET_KEY
app.config["PROPAGATE_EXCEPTIONS"] = False  

@app.route("/")
def index():
    return jsonify({"status": "ok", "msg": "safe Flask demo"}), 200

@app.route("/error")
def simulated_error():
    logger.warning("Simulated error endpoint called: /error")
    return jsonify({"error": "internal_error"}), 500


@app.route("/secret")
def secret_status():
    return jsonify({"secret_configured": bool(app.config.get("SECRET_KEY"))}), 200


@app.route("/deserialize", methods=["POST"])
def safe_deserialize():
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception as exc:
        logger.debug("Invalid JSON received on /deserialize: %s", exc)
        return jsonify({"error": "invalid_json"}), 400

    if not payload or not isinstance(payload, Mapping):
        return jsonify({"error": "invalid_payload"}), 400

    allowed_schema: Dict[str, Any] = {
        "name": str,
        "count": int,
    }

    sanitized: Dict[str, Any] = {}
    for key, value in payload.items():
        expected_type = allowed_schema.get(key)
        if expected_type is None:
            logger.debug("Field not allowed in payload: %s", key)
            return jsonify({"error": f"invalid_field:{key}"}), 400
        if not isinstance(value, expected_type):
            logger.debug("Field %s has wrong type: expected %s, got %s", key, expected_type, type(value))
            return jsonify({"error": f"invalid_type:{key}"}), 400
        sanitized[key] = value
    return jsonify({"status": "ok", "data": sanitized}), 200

@app.errorhandler(400)
def handle_400(err):
    return jsonify({"error": "bad_request"}), 400


@app.errorhandler(404)
def handle_404(err):
    return jsonify({"error": "not_found"}), 404


@app.errorhandler(500)
def handle_500(err):
    logger.exception("Internal server error occurred")
    return jsonify({"error": "internal_error"}), 500

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    if debug_mode:
        logger.warning("Starting Flask in DEBUG mode (FLASK_DEBUG=1) - not for production.")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=debug_mode)
