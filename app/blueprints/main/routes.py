from flask import Blueprint, render_template

main_bp = Blueprint('main_bp', __name__, template_folder='templates')

@main_bp.route('/')
def index():
    return render_template('main/index.html', title='Geodonis')

