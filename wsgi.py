from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'pharmacy_secret_123'

# Create database
def get_db():
    conn = sqlite3.connect('pharmacy.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS medicines
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT,
                  box_number TEXT,
                  quantity INTEGER,
                  price REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  medicine_id INTEGER,
                  medicine_type TEXT,
                  quantity INTEGER,
                  price REAL,
                  total REAL,
                  sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['logged'] = True
            return redirect(url_for('dashboard'))
        else:
            return "Wrong username/password! Use admin/admin"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged'):
        return redirect(url_for('login'))
    search = request.args.get('search', '')
    conn = get_db()
    if search:
        meds = conn.execute("SELECT * FROM medicines WHERE type LIKE ?", ('%'+search+'%',)).fetchall()
    else:
        meds = conn.execute("SELECT * FROM medicines").fetchall()
    conn.close()
    return render_template('dashboard.html', medicines=meds, search=search)

@app.route('/add', methods=['GET','POST'])
def add():
    if request.method == 'POST':
        conn = get_db()
        conn.execute("INSERT INTO medicines (type, box_number, quantity, price) VALUES (?,?,?,?)",
                     (request.form['type'], request.form['box_number'], request.form['quantity'], request.form['price']))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('add.html')

@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    qty = int(request.form['quantity'])
    conn = get_db()
    med = conn.execute("SELECT * FROM medicines WHERE id=?", (id,)).fetchone()
    if med and med['quantity'] >= qty:
        total = qty * med['price']
        conn.execute("INSERT INTO sales (medicine_id, medicine_type, quantity, price, total) VALUES (?,?,?,?,?)",
                     (id, med['type'], qty, med['price'], total))
        conn.execute("UPDATE medicines SET quantity = quantity - ? WHERE id=?", (qty, id))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/sales')
def sales():
    conn = get_db()
    all_sales = conn.execute("SELECT * FROM sales ORDER BY sale_date DESC").fetchall()
    total_items = conn.execute("SELECT SUM(quantity) as s FROM sales").fetchone()['s'] or 0
    total_money = conn.execute("SELECT SUM(total) as s FROM sales").fetchone()['s'] or 0
    conn.close()
    return render_template('sales.html', sales=all_sales, total_items=total_items, total_money=total_money)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)