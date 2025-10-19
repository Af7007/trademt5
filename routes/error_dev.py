from flask import Blueprint, jsonify

error_bp = Blueprint('error', __name__)

@error_bp.app_errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found"
    }), 404

@error_bp.app_errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal error occurred"
    }), 500
