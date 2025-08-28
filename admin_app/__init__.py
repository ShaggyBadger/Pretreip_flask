from flask import Blueprint, session, redirect, url_for, abort
from flask_app.models import Users
from flask_app.extensions import db

admin_bp = Blueprint(
    'admin', __name__,
    template_folder='templates',
    static_folder='static',
)

# ensure  that only people with requrired adminstrative level gain access to this
@admin_bp.before_request
def restrict_to_admins():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth_bp.login"))  # or abort(403)

    user = Users.query.get(user_id)
    user_admin_level = user.admin_level
    if not user or user_admin_level < 1:
        abort(403)  # Forbidden

from . import routes
