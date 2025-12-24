# blueprints/brokers.py

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from database.broker_db import add_broker, get_all_brokers, delete_broker
from utils.session import check_session_validity
from utils.logging import get_logger

logger = get_logger(__name__)
brokers_bp = Blueprint('brokers', __name__, url_prefix='/brokers')

@brokers_bp.route('/', methods=['GET'])
@check_session_validity
def manage_brokers():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    brokers = get_all_brokers(user_id)
    return render_template('broker_management.html', brokers=brokers)

@brokers_bp.route('/add', methods=['POST'])
@check_session_validity
def add_broker_route():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    broker_name = request.form.get('broker_name')
    api_key = request.form.get('api_key')
    api_secret = request.form.get('api_secret')

    if not all([broker_name, api_key, api_secret]):
        flash('All fields are required.', 'error')
        return redirect(url_for('brokers.manage_brokers'))

    add_broker(user_id, broker_name, api_key, api_secret)
    flash('Broker added successfully.', 'success')
    return redirect(url_for('brokers.manage_brokers'))

@brokers_bp.route('/delete/<int:broker_id>', methods=['POST'])
@check_session_validity
def delete_broker_route(broker_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    broker = get_broker(user_id, broker_id) # Assuming get_broker can fetch by id
    if broker and broker['user_id'] == user_id:
        delete_broker(broker_id)
        flash('Broker deleted successfully.', 'success')
    else:
        flash('You are not authorized to delete this broker.', 'error')
    return redirect(url_for('brokers.manage_brokers'))
