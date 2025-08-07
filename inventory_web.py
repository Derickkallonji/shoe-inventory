# inventory_web.py
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key')
bcrypt = Bcrypt(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

class Shoe:
    def __init__(self, country, code, product, cost, quantity):
        self.country = country
        self.code = code
        self.product = product
        self.cost = float(cost)
        self.quantity = int(quantity)

    def __str__(self):
        return f"{self.country},{self.code},{self.product},{self.cost},{self.quantity}"

    def to_dict(self):
        return {
            "country": self.country,
            "code": self.code,
            "product": self.product,
            "cost": self.cost,
            "quantity": self.quantity
        }

shoe_list = []

def get_db_connection():
    return psycopg2.connect(os.environ.get('POSTGRES_URL'), cursor_factory=RealDictCursor)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shoes (
            country TEXT,
            code TEXT PRIMARY KEY,
            product TEXT,
            cost REAL,
            quantity INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def read_shoes_data():
    shoe_list.clear()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM shoes")
        for row in cursor.fetchall():
            shoe_list.append(Shoe(
                row["country"], row["code"], row["product"],
                row["cost"], row["quantity"]
            ))
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error reading data: {e}")

def save_shoes_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM shoes")
        for shoe in shoe_list:
            cursor.execute(
                "INSERT INTO shoes (country, code, product, cost, quantity) VALUES (%s, %s, %s, %s, %s)",
                (shoe.country, shoe.code, shoe.product, shoe.cost, shoe.quantity)
            )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving data: {e}")

init_db()

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user and bcrypt.check_password_hash(user['password'], password):
                login_user(User(user['id']))
                return redirect(url_for('home'))
            flash("Invalid username or password", "danger")
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id", 
                          (username, hashed_password))
            user_id = cursor.fetchone()['id']
            conn.commit()
            cursor.close()
            conn.close()
            login_user(User(user_id))
            flash("Registration successful!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"Error: {e}", "danger")
    return render_template('register.html')

@app.route('/view_all')
@login_required
def view_all():
    read_shoes_data()
    return render_template('view_all.html', shoes=shoe_list)

@app.route('/add_shoe', methods=['GET', 'POST'])
@login_required
def add_shoe():
    if request.method == 'POST':
        country = request.form['country'].strip()
        code = request.form['code'].strip()
        product = request.form['product'].strip()
        try:
            cost = float(request.form['cost'])
            quantity = int(request.form['quantity'])
            if not all([country, code, product]) or cost < 0 or quantity < 0:
                return render_template('add_shoe.html', error="Invalid input! All fields required and cost/quantity must be non-negative.")
            read_shoes_data()
            new_shoe = Shoe(country, code, product, cost, quantity)
            shoe_list.append(new_shoe)
            save_shoes_data()
            flash("Shoe added successfully!", "success")
            return redirect(url_for('view_all'))
        except ValueError:
            return render_template('add_shoe.html', error="Invalid cost or quantity!")
        except psycopg2.IntegrityError:
            return render_template('add_shoe.html', error="Shoe code already exists!")
    return render_template('add_shoe.html')

@app.route('/re_stock', methods=['GET', 'POST'])
@login_required
def re_stock():
    read_shoes_data()
    if not shoe_list:
        return render_template('re_stock.html', error="No shoes in inventory!")
    
    min_shoe = min(shoe_list, key=lambda x: x.quantity)
    if request.method == 'POST':
        try:
            additional = int(request.form['quantity'])
            if additional < 0:
                return render_template('re_stock.html', shoe=min_shoe, error="Quantity cannot be negative!")
            for shoe in shoe_list:
                if shoe.code == min_shoe.code:
                    shoe.quantity += additional
                    break
            save_shoes_data()
            flash("Shoe restocked successfully!", "success")
            return redirect(url_for('view_all'))
        except ValueError:
            return render_template('re_stock.html', shoe=min_shoe, error="Invalid quantity!")
    return render_template('re_stock.html', shoe=min_shoe)

@app.route('/search_shoe', methods=['GET', 'POST'])
@login_required
def search_shoe():
    if request.method == 'POST':
        code = request.form['code'].strip()
        if not code:
            return render_template('search_shoe.html', error="Code cannot be empty!")
        read_shoes_data()
        for shoe in shoe_list:
            if shoe.code == code:
                return render_template('search_shoe.html', shoe=shoe)
        return render_template('search_shoe.html', error="Shoe not found!")
    return render_template('search_shoe.html')

@app.route('/value_per_item')
@login_required
def value_per_item():
    read_shoes_data()
    if not shoe_list:
        return render_template('value_per_item.html', error="No shoes in inventory!")
    values = [(shoe.product, shoe.cost * shoe.quantity) for shoe in shoe_list]
    return render_template('value_per_item.html', values=values)

@app.route('/highest_qty')
@login_required
def highest_qty():
    read_shoes_data()
    if not shoe_list:
        return render_template('highest_qty.html', error="No shoes in inventory!")
    max_shoe = max(shoe_list, key=lambda x: x.quantity)
    return render_template('highest_qty.html', shoe=max_shoe)

if __name__ == '__main__':
    read_shoes_data()
    app.run(debug=True)