from flask import Blueprint, jsonify
from src.db.connection import get_db_connection

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    try:
        conn = get_db_connection()
        conn.close()

        return jsonify({
            "status": "ok",
            "database": "connected"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }), 500
