from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from flask_mail import Mail, Message
import json


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

class CheckoutOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    items = db.Column(db.Text, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('checkout_orders', lazy=True))

@app.before_request
def setup_app():
    db.create_all()
    if 'cart' not in session:
        session['cart'] = []

    admin_email = 'admin@example.com'
    if not User.query.filter_by(email=admin_email).first():
        admin = User(email=admin_email, name='Admin')
        admin.set_password('adminpass123')
        admin.is_admin = True  # ✅ sets admin privileges
        db.session.add(admin)
        db.session.commit()

@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(user_name=user.name if user else None, is_admin=session.get('is_admin'))
    return dict(user_name=None, is_admin=False)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to view this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def block_admins(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('is_admin'):
            flash('Admins are restricted to the dashboard.', 'warning')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("Admin access required.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    total = sum(item['price'] for item in cart)

    # Enforce minimum order total (e.g. $50)
    MIN_ORDER_TOTAL = 50.00
    if total < MIN_ORDER_TOTAL:
        flash(f'Minimum order is ${MIN_ORDER_TOTAL:.2f}. Please add more items to your cart.', 'warning')
        return redirect(url_for('view_cart'))

    if request.method == 'POST':
        guest_email = request.form.get('guestEmail')  # From form, if guest

        user = User.query.filter_by(name=session.get('user')).first()
        order = CheckoutOrder(
            user_id=user.id if user else None,
            items=json.dumps(cart),
            total_price=total
        )
        db.session.add(order)
        db.session.commit()

        # Email sending logic
        if user or guest_email:
            try:
                recipient_email = user.email if user else guest_email
                recipient_name = user.name if user else "Guest"

                msg = Message(
                    subject="Sydney Flowers Express - Order Confirmation",
                    recipients=[recipient_email]
                )
                msg.body = f"""Hi {recipient_name},

Thank you for your order at Sydney Flowers Express!

Order Summary:
{chr(10).join(f"- {item['name']} (${item['price']:.2f})" for item in cart)}

Total: ${total:.2f}

We’ll begin preparing your flowers and contact you once it's ready for delivery.

Warm regards,
Sydney Flowers Express Team
"""
                mail.send(msg)
            except Exception as e:
                print(f"Email failed: {e}")
                flash("Order placed, but we couldn’t send a confirmation email.", "warning")

        session['cart'] = []  # Clear cart
        session.modified = True

        flash("Order placed successfully!", "success")
        return render_template('checkout_confirmation.html', order=order, cart=cart)

    return render_template('checkout.html', cart=cart, total=total)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'  # Use app password, not regular one
mail = Mail(app)

class SavedBouquet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('saved_bouquets', lazy=True))

# ---------------------- ROUTES ----------------------

@app.route('/')
@block_admins
def home():
    return render_template('home.html')

@app.route('/catalogue')
@block_admins
def catalogue():
    flower_name = request.args.get('flower')

    flower_data = {
        "Alstroemerias": {
            "name": "Alstroemerias",
            "latin_name": "Alstroemeria aurantiaca",
            "description": "Alstroemerias (Peruvian Lilies) are tough, rounded stems that produce beautiful orchid-like flowers carried in clusters on top of the stems. These flowers have very diverse patterns of colours and symbolise friendship and devotion.",
            "category": "Cut Flowers",
            "genus": "Alstroemeria aurantiaca",
            "common_name": "Lily of the Incas, Peruvian Lily",
            "longevity": "7–12 days, depending on care and handling",
            "stem_length": "Approx. 50cm – 70cm",
            "availability": "All Year Round",
            "variants": [
                {'name': 'Alstroemeria - Red', 'price': 16.00, 'image': 'alstroemeria_red.jpg'},
                {'name': 'Alstroemeria - Pink', 'price': 16.00, 'image': 'alstroemeria_pink.jpg'},
                {'name': 'Alstroemeria - White', 'price': 16.00, 'image': 'alstroemeria_white.jpg'}
            ]
        },
        "Bell Flowers": {
            "name": "Bell Flowers",
            "latin_name": "Campanula",
            "description": "Bell Flowers are charming blooms known for their bell-shaped blossoms and vibrant colours.",
            "category": "Cut Flowers",
            "genus": "Campanula",
            "common_name": "Bell Flower",
            "longevity": "5–10 days, depending on care",
            "stem_length": "Approx. 40cm – 60cm",
            "availability": "Seasonal",
            "variants": [
                {'name': 'Bell Flower - Blue', 'price': 25.00, 'image': 'bell_blue.jpg'},
                {'name': 'Bell Flower - Pink', 'price': 25.00, 'image': 'bell_pink.jpg'},
                {'name': 'Bell Flower - White', 'price': 25.00, 'image': 'bell_white.jpg'}
            ]
        },
        "Calla Lilies": {
            "name": "Calla Lilies",
            "latin_name": "Zantedeschia Areceae",
            "description": "Calla lilies are a beautiful type of flower that have been enjoyed for centuries. They are widely used in weddings, bouquets, and cut flower arrangements. Calla Lilies are bride favourites and symbolise magnificent beauty.",
            "category": "Cut Flowers",
            "genus": "Zantedeschia Areceae",
            "common_name": "Calla Lilies",
            "longevity": "7–10 days, depending on care and handling",
            "stem_length": "Approx. 30–45cm",
            "availability": "All Year Round",
            "variants": [
                {'name': 'Calla Lily - Chocolate', 'price': 25.00, 'image': 'calla_chocolate.jpg'},
                {'name': 'Calla Lily - Pink', 'price': 25.00, 'image': 'calla_pink.jpg'},
                {'name': 'Calla Lily - White', 'price': 25.00, 'image': 'calla_white.jpg'},
                {'name': 'Calla Lily - Yellow', 'price': 25.00, 'image': 'calla_yellow.jpg'}
            ]
        }
    }

    flower = flower_data.get(flower_name)
    if flower:
        return render_template('catalogue.html', flower=flower)
    else:
        return render_template('catalogue.html', flower=None)

@app.route('/customise', methods=['GET', 'POST'])
@block_admins
def customise():
    flower_options = [
        {"name": "Roses", "price": 20},
        {"name": "Alstroemerias", "price": 16},
        {"name": "Calla Lilies", "price": 25},
        {"name": "Sunflowers", "price": 18},
        {"name": "Tulips", "price": 22}
    ]
    size_prices = {"Small": 40, "Medium": 60, "Large": 80}

    confirmation = False

    if request.method == 'POST':
        flower_type = request.form.get('flowerType')
        colour = request.form.get('colourScheme')
        message = request.form.get('message')
        size = request.form.get('size')
        action = request.form.get('action')

        bouquet_description = f"{flower_type} | Colour: {colour}"
        if message:
            bouquet_description += f" | Message: {message}"

        price = size_prices.get(size, 0)

        custom_bouquet = {
            "name": f"Custom Bouquet ({bouquet_description}, Size: {size})",
            "price": price
        }

        if action == "place_order_now":
            session.setdefault('cart', []).append(custom_bouquet)
            session.modified = True
            # Render the confirmation page with bouquet details
            return render_template(
                'customise_confirmation.html',
                flower_type=flower_type,
                colour=colour,
                message=message,
                size=size
            )
        elif action == "add_to_cart":
            session.setdefault('cart', []).append(custom_bouquet)
            session.modified = True
            flash("Custom bouquet added to cart!", "success")
            return redirect(url_for('view_cart'))

    return render_template('customise.html', flower_options=flower_options, user_name=session.get('user'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    checkout_orders = CheckoutOrder.query.all()

    total_users = len(users)
    total_orders = len(checkout_orders)
    total_revenue = sum(order.total_price for order in checkout_orders)

    from collections import Counter
    import json

    flower_counter = Counter()
    for order in checkout_orders:
        try:
            items = json.loads(order.items)
            for item in items:
                flower_counter[item['name']] += 1
        except:
            continue

    top_selling = flower_counter.most_common(5)

    return render_template(
        'admin_dashboard.html',
        user_name=session.get('user'),
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=total_revenue,
        top_selling=top_selling
    )


@app.route('/register', methods=['GET', 'POST'])
@block_admins
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

        session['user_id'] = new_user.id
        session['is_admin'] = new_user.is_admin
        flash('Registration successful! You are now logged in.', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@block_admins
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user'] = user.name
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin

            flash('Login successful!', 'success')
            
            # 👇 Redirect to admin dashboard if user is admin
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
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
@block_admins
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

@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    product = get_product_by_id(product_id)  # You can create this helper function
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('catalogue'))

    item = {
        'id': product_id,
        'name': product['name'],
        'price': float(product['price'])
    }

    session.setdefault('cart', []).append(item)
    session.modified = True
    flash(f"{item['name']} added to cart.", "success")
    return redirect(url_for('view_cart'))

@app.route('/add_variant_to_cart', methods=['POST'])
@block_admins
def add_variant_to_cart():
    variant_name = request.form.get('variant_name')
    try:
        variant_price = float(request.form.get('variant_price'))
    except (TypeError, ValueError):
        flash("Invalid price.", "danger")
        return redirect(url_for('catalogue'))
    try:
        quantity = int(request.form.get('quantity'))
        if quantity < 1:
            raise ValueError
    except (TypeError, ValueError):
        flash("Invalid quantity.", "danger")
        return redirect(url_for('catalogue'))

    if quantity > 250:
        flash("For bulk orders over 250, please contact us directly.", "warning")
        return redirect(url_for('catalogue'))

    item = {
        'name': variant_name,
        'price': variant_price * quantity,
        'quantity': quantity,
        'unit_price': variant_price
    }
    session.setdefault('cart', []).append(item)
    session.modified = True
    flash(f"Added {quantity} x {variant_name} to cart.", "success")
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

@app.route('/orders')
@login_required
def orders():
    user = User.query.filter_by(name=session.get('user')).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    orders = BouquetOrder.query.filter_by(user_id=user.id).order_by(BouquetOrder.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/saved-bouquets')
@block_admins
@login_required
def saved_bouquets():
    user = User.query.filter_by(name=session.get('user')).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    bouquets = SavedBouquet.query.filter_by(user_id=user.id).order_by(SavedBouquet.created_at.desc()).all()
    return render_template('saved_bouquets.html', bouquets=bouquets)

@app.route('/reorder/<int:bouquet_id>')
@login_required
def reorder(bouquet_id):
    bouquet = SavedBouquet.query.get_or_404(bouquet_id)
    session.setdefault('cart', []).append({
        "name": f"Custom Bouquet (Reordered: {bouquet.description})",
        "price": bouquet.total_price
    })
    session.modified = True
    flash("Bouquet added to cart again!", "success")
    return redirect(url_for('view_cart'))

if __name__ == '__main__':
    app.run(debug=True)
