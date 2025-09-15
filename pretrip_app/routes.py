from flask import render_template, request, redirect, url_for, session, current_app, flash
from . import pretrip_bp

@pretrip_bp.route('/')
def home():
    return render_template('pretrip/index.html')