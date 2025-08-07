# inventory_web.py
from flask import Flask, request, render_template, redirect, url_for
import os
import json
import vercel_storage.blob as vercel_blob

app = Flask(__name__)

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

def read_shoes_data():
    """Read shoe data from Vercel Blob or local inventory.txt."""
    shoe_list.clear()
    try:
        # Try to read from Vercel Blob
        blob = vercel_blob.get("inventory.json")
        if blob:
            data = json.loads(blob.decode('utf-8'))
            for item in data:
                shoe_list.append(Shoe(
                    item["country"], item["code"], item["product"],
                    item["cost"], item["quantity"]
                ))
        else:
            # Fallback to local inventory.txt for initial setup
            if os.path.exists('inventory.txt'):
                with open('inventory.txt', 'r') as file:
                    lines = file.readlines()
                    if len(lines) > 1:  # Skip header
                        for line in lines[1:]:
                            data = line.strip().split(',')
                            if len(data) != 5:
                                continue
                            try:
                                country, code, product, cost, quantity = data
                                float(cost)
                                int(quantity)
                                shoe_list.append(Shoe(country, code, product, cost, quantity))
                            except ValueError:
                                continue
    except Exception as e:
        print(f"Error reading data: {e}")

def save_shoes_data():
    """Save shoe data to Vercel Blob."""
    try:
        data = [shoe.to_dict() for shoe in shoe_list]
        vercel_blob.put("inventory.json", json.dumps(data).encode('utf-8'))
    except Exception as e:
        print(f"Error saving data: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view_all')
def view_all():
    read_shoes_data()
    return render_template('view_all.html', shoes=shoe_list)

@app.route('/add_shoe', methods=['GET', 'POST'])
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
            return redirect(url_for('view_all'))
        except ValueError:
            return render_template('add_shoe.html', error="Invalid cost or quantity!")
    return render_template('add_shoe.html')

@app.route('/re_stock', methods=['GET', 'POST'])
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
            return redirect(url_for('view_all'))
        except ValueError:
            return render_template('re_stock.html', shoe=min_shoe, error="Invalid quantity!")
    return render_template('re_stock.html', shoe=min_shoe)

@app.route('/search_shoe', methods=['GET', 'POST'])
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
def value_per_item():
    read_shoes_data()
    if not shoe_list:
        return render_template('value_per_item.html', error="No shoes in inventory!")
    values = [(shoe.product, shoe.cost * shoe.quantity) for shoe in shoe_list]
    return render_template('value_per_item.html', values=values)

@app.route('/highest_qty')
def highest_qty():
    read_shoes_data()
    if not shoe_list:
        return render_template('highest_qty.html', error="No shoes in inventory!")
    max_shoe = max(shoe_list, key=lambda x: x.quantity)
    return render_template('highest_qty.html', shoe=max_shoe)

if __name__ == '__main__':
    read_shoes_data()
    app.run(debug=True)