from flask import render_template
from tankGauge_app import tankGauge_bp

@tankGauge_bp.route('/')
def home():
    return render_template('tankGauge/home.html')