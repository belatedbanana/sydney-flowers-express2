from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure SQLite DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------------- MODELS ----------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BouquetOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    flower_type = db.Column(db.String(100), nullable=False)
    colour = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=True)
    size = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('bouquet_orders', lazy=True))

# ---------------------- UTILITY ----------------------

@app.before_request
def setup_app():
    db.create_all()
    if 'cart' not in session:
        session['cart'] = []

    # Admin creation
    admin_email = 'admin@example.com'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, name='Admin')
        admin.set_password('adminpass123')
        db.session.add(admin)
        db.session.commit()

@app.context_processor
def inject_user():
    return dict(user_name=session.get('user'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('You must be logged in to view this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') != 'Admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------- ROUTES ----------------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/catalogue')
def catalogue():
    flower = request.args.get('flower')
    variants = []

    if flower == "Alstroemerias":
        variants = [
            {'name': 'Alstroemeria - Red', 'price': 16.00, 'image': 'alstroemeria_red.jpg'},
            {'name': 'Alstroemeria - Pink', 'price': 16.00, 'image': 'alstroemeria_pink.jpg'},
            {'name': 'Alstroemeria - White', 'price': 16.00, 'image': 'alstroemeria_white.jpg'},
            {'name': 'Alstroemeria - Yellow', 'price': 16.00, 'image': 'alstroemeria_yellow.jpg'}
        ]
    elif flower == "Bell Flowers":
        variants = [
            {'name': 'Bell Flower - Blue', 'price': 25.00, 'image': 'bell_blue.jpg'},
            {'name': 'Bell Flower - Pink', 'price': 25.00, 'image': 'bell_pink.jpg'},
            {'name': 'Bell Flower - White', 'price': 25.00, 'image': 'bell_white.jpg'}
        ]
    elif flower == "Calla Lilies":
        variants = [
            {'name': 'Calla Lily - Chocolate', 'price': 25.00, 'image': 'calla_chocolate.jpg'},
            {'name': 'Calla Lily - Pink', 'price': 25.00, 'image': 'calla_pink.jpg'},
            {'name': 'Calla Lily - White', 'price': 25.00, 'image': 'calla_white.jpg'},
            {'name': 'Calla Lily - Yellow', 'price': 25.00, 'image': 'calla_yellow.jpg'}
        ]

    return render_template('catalogue.html', flower=flower, variants=variants)

@app.route('/customise', methods=['GET', 'POST'])
@login_required
def customise():
    if request.method == 'POST':
        flower_type = request.form['flowerType']
        colour = request.form['colourScheme']
        message = request.form['message']
        size = request.form['size']

        user = User.query.filter_by(name=session.get('user')).first()
        if not user:
            flash("You must be logged in to place a custom order.", "danger")
            return redirect(url_for('login'))

        bouquet_order = BouquetOrder(
            user_id=user.id,
            flower_type=flower_type,
            colour=colour,
            message=message,
            size=size
        )
        db.session.add(bouquet_order)
        db.session.commit()

        flash("Your custom bouquet order has been placed!", "success")
        return render_template('customise_confirmation.html',
                               flower_type=flower_type,
                               colour=colour,
                               message=message,
                               size=size)

    return render_template('customise.html')

@app.route('/admin')
@login_required
def admin():
    user = User.query.filter_by(name=session.get('user')).first()
    if not user or not user.is_admin:
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('home'))
    return render_template('admin.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    user_count = User.query.count()
    return render_template('admin_dashboard.html', user_count=user_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].lower()
        name = request.form['name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return redirect(url_for('register'))

        new_user = User(email=email, name=name)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['user'] = name
        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user'] = user.name
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ---------------------- CART ROUTES ----------------------

@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])
    total = sum(item['price'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/remove_from_cart/<int:index>')
def remove_from_cart(index):
    if 'cart' in session and 0 <= index < len(session['cart']):
        session['cart'].pop(index)
        session.modified = True
    return redirect(url_for('view_cart'))

# ---------------------- STATIC & CACHE ----------------------

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(debug=True)
