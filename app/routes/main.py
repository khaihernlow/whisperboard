"""
Main application routes
"""
from flask import Blueprint, render_template, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@main_bp.route('/welcome')
def welcome():
    """Welcome endpoint"""
    return jsonify({"message": "Welcome to the Attendee API!"}), 200
