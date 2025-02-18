from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.user import User

main_bp = Blueprint('main_bp', __name__, template_folder='templates')

@main_bp.route('/')
def index():
    return render_template('main/index.html', title='Geodonis')

#=============================
# TEMPORARY Endpoints
#=============================

@main_bp.route('/login_check')
@login_required
def index_protected():
    # Dummy endpoint to text a logged in user, before we add any more pages
    current_user_looked_up = User.query.get(current_user.id)
    print(current_user_looked_up.username)
    return render_template('main/index.html', title='Geodonis')
