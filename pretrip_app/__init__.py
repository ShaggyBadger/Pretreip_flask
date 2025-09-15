from flask import Blueprint, session, redirect, url_for, abort, request, jsonify

pretrip_bp = Blueprint(
    'pretrip', 
    __name__,
    template_folder='templates',
    static_folder='static'
    )

@pretrip_bp.before_request
def require_login():
    """
    Block non-authenticated access to this blueprint.
    - Browser requests -> redirect to login page
    - AJAX/JSON requests -> return JSON 401/403 so frontend can handle it
    """
    user_id = session.get("user_id")
    if user_id:
        return None  # OK -> proceed with request

    # Not logged in. Decide behavior based on request type.
    wants_json = request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json'
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'  # traditional AJAX header

    if wants_json or is_xhr or request.is_json:
        # For API/AJAX requests, return a JSON error (401 Unauthorized or 403 Forbidden).
        # 401 is appropriate if they are not authenticated (not logged in).
        return jsonify({"error": "authentication_required", "message": "You must be logged in"}), 401

    # Otherwise (likely a browser navigation/form post), redirect to login page.
    return redirect(url_for('auth_bp.login', _external=False))

from . import routes