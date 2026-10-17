from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = '12345'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pharmacy'

mysql = MySQL(app)

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['loggedin'] = True
            return redirect('/dashboard')
        else:
            return "Wrong! Use admin / admin <a href='/login'>Back</a>"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'loggedin' not in session:
        return redirect('/login')
    cur = mysql.connection.cursor()
    search = request.args.get('search')
    if search:
        cur.execute("SELECT * FROM medicines WHERE type LIKE %s", ('%' + search + '%',))
    else:
        cur.execute("SELECT * FROM medicines")
    medicines = cur.fetchall()
    cur.close()
    return render_template('dashboard.html', medicines=medicines)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'loggedin' not in session:
        return redirect('/login')
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO medicines (type, box_number, quantity, price) VALUES (%s, %s, %s, %s)",
                    (request.form['type'], request.form['box_number'], request.form['quantity'], request.form['price']))
        mysql.connection.commit()
        cur.close()
        return redirect('/dashboard')
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'loggedin' not in session:
        return redirect('/login')
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        cur.execute("UPDATE medicines SET type=%s, box_number=%s, quantity=%s, price=%s WHERE id=%s",
                    (request.form['type'], request.form['box_number'], request.form['quantity'], request.form['price'], id))
        mysql.connection.commit()
        cur.close()
        return redirect('/dashboard')
    cur.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    medicine = cur.fetchone()
    cur.close()
    return render_template('edit.html', medicine=medicine)

@app.route('/sell/<int:id>', methods=['POST'])
def sell(id):
    if 'loggedin' not in session:
        return redirect('/login')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM medicines WHERE id=%s", (id,))
    medicine = cur.fetchone()
    if not medicine:
        cur.close()
        return redirect('/dashboard')

    sell_qty = int(request.form['sell_qty'])
    current_qty = int(medicine[3])
    price = float(medicine[4])

    if sell_qty > current_qty:
        cur.close()
        return f"Not enough stock! Only {current_qty} left. <a href='/dashboard'>Back</a>"

    new_qty = current_qty - sell_qty
    total_sale = sell_qty * price

    # Deduct stock
    cur.execute("UPDATE medicines SET quantity=%s WHERE id=%s", (new_qty, id))
    # Save to sales history
    cur.execute("INSERT INTO sales (medicine_id, medicine_type, quantity, price, total) VALUES (%s, %s, %s, %s, %s)",
                (id, medicine[1], sell_qty, price, total_sale))
    mysql.connection.commit()
    cur.close()
    return redirect('/dashboard')

@app.route('/sales')
def sales_history():
    if 'loggedin' not in session:
        return redirect('/login')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM sales ORDER BY sale_date DESC")
    sales = cur.fetchall()
    cur.execute("SELECT SUM(total), SUM(quantity) FROM sales")
    result = cur.fetchone()
    total_amount = result[0] if result[0] else 0
    total_qty = result[1] if result[1] else 0
    cur.close()
    return render_template('sales.html', sales=sales, total_amount=total_amount, total_qty=total_qty)

@app.route('/clear_sales')
def clear_sales():
    if 'loggedin' not in session:
        return redirect('/login')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM sales")
    mysql.connection.commit()
    cur.close()
    return redirect('/sales')

@app.route('/delete/<int:id>')
def delete(id):
    if 'loggedin' not in session:
        return redirect('/login')
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM medicines WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)