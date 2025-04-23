from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'jenny'
app.config['MYSQL_DB'] = 'restaurant_db'

mysql = MySQL(app)

@app.route('/')
def index():
    if 'admin' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/tables', methods=['GET', 'POST'])
def manage_tables():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        table_number = request.form.get('table_number')
        cur.execute("SELECT * FROM tables WHERE number = %s", (table_number,))
        existing = cur.fetchone()
        if not existing:
            cur.execute("INSERT INTO tables (number) VALUES (%s)", (table_number,))
            mysql.connection.commit()
            flash(f"Table {table_number} added!", "success")
        else:
            flash("Table already exists!", "warning")
        return redirect(url_for('manage_tables'))

    cur.execute("SELECT * FROM tables")
    tables_data = cur.fetchall()
    tables = [{'id': row[0], 'number': row[1]} for row in tables_data]
    return render_template('tables.html', tables=tables)

@app.route('/delete_table/<int:id>')
def delete_table(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM tables WHERE id = %s", (id,))
    mysql.connection.commit()
    flash(f"Table deleted!", 'info')
    return redirect(url_for('manage_tables'))

@app.route('/menu', methods=['GET', 'POST'])
def manage_menu():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        quantity = int(request.form.get('quantity'))
        cur.execute("INSERT INTO menu_items (name, price, quantity) VALUES (%s, %s, %s)", (name, price, quantity))
        mysql.connection.commit()
        flash(f"Menu item '{name}' added!", 'success')
        return redirect(url_for('manage_menu'))

    cur.execute("SELECT * FROM menu_items")
    menu = [{'id': row[0], 'name': row[1], 'price': row[2], 'quantity': row[3]} for row in cur.fetchall()]
    return render_template('menu.html', menu=menu)

@app.route('/delete_menu/<int:id>')
def delete_menu(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM menu_items WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Menu item deleted!", 'info')
    return redirect(url_for('manage_menu'))
@app.route('/orders', methods=['GET', 'POST'])
def manage_orders():
    cur = mysql.connection.cursor()

    # Get tables and menu items from DB
    cur.execute("SELECT * FROM tables")
    tables_data = cur.fetchall()
    tables = [{'id': row[0], 'number': row[1]} for row in tables_data]

    cur.execute("SELECT * FROM menu_items")
    menu_data = cur.fetchall()
    menu_items = [{'id': row[0], 'name': row[1], 'price': row[2], 'quantity': row[3]} for row in menu_data]

    if request.method == 'POST':
        table_number = request.form.get('table')
        item_name = request.form.get('item')
        quantity = int(request.form.get('quantity'))

        # Fetch table_id and item details
        table = next((t for t in tables if t['number'] == table_number), None)
        item = next((m for m in menu_items if m['name'] == item_name), None)

        if table and item and item['quantity'] >= quantity:
            total = item['price'] * quantity
            cur.execute("INSERT INTO orders (table_id, item_id, quantity, total) VALUES (%s, %s, %s, %s)",
                        (table['id'], item['id'], quantity, total))
            # Update inventory
            cur.execute("UPDATE menu_items SET quantity = quantity - %s WHERE id = %s", (quantity, item['id']))
            mysql.connection.commit()
            flash(f"Order placed for {item_name} (x{quantity}) on Table {table_number}!", 'success')
        else:
            flash("Invalid order or insufficient stock.", "danger")

        return redirect(url_for('manage_orders'))

    # Fetch all orders with join to get table number and item name
    cur.execute("""
        SELECT o.id, t.number, m.name, o.quantity, o.total
        FROM orders o
        JOIN tables t ON o.table_id = t.id
        JOIN menu_items m ON o.item_id = m.id
    """)
    order_data = cur.fetchall()
    orders = [{'table': row[1], 'item': row[2], 'quantity': row[3], 'total': row[4]} for row in order_data]

    # Generate bill summary
    bill_summary = {}
    for order in orders:
        bill_summary.setdefault(order['table'], 0)
        bill_summary[order['table']] += order['total']

    return render_template('orders.html', orders=orders, tables=tables, menu=menu_items, bill_summary=bill_summary)




@app.route('/delete_order/<int:id>')
def delete_order(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM orders WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Order deleted!", 'info')
    return redirect(url_for('manage_orders'))

@app.route('/inventory')
def inventory():
    cur = mysql.connection.cursor()
    cur.execute("SELECT name, quantity FROM menu_items")
    menu = [{'name': row[0], 'quantity': row[1]} for row in cur.fetchall()]
    return render_template('inventory.html', menu=menu)

@app.route('/test_mysql')
def test_mysql():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT VERSION()")
        version = cur.fetchone()
        return f"MySQL Connection Successful! Version: {version[0]}"
    except Exception as e:
        return f"MySQL Connection Failed: {str(e)}"
    
from flask import Flask, render_template, request, redirect, url_for, flash, session

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Replace with actual admin check logic or DB auth if needed
        if username == 'admin' and password == 'joice':
            session.permanent = True
            session['admin'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
