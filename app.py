from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages

# In-memory storage
tables = []        # [{'number': '1'}]
menu_items = []    # [{'name': 'Pizza', 'price': 250.0, 'quantity': 10}]
orders = []        # [{'table': '1', 'item': 'Pizza', 'quantity': 2, 'total': 500.0}]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/tables', methods=['GET', 'POST'])
def manage_tables():
    if request.method == 'POST':
        table_number = request.form.get('table_number')
        if table_number and not any(t['number'] == table_number for t in tables):
            tables.append({'number': table_number})
            flash(f"Table {table_number} added successfully!", 'success')
        else:
            flash("Table already exists or invalid!", 'warning')
        return redirect(url_for('manage_tables'))
    return render_template('tables.html', tables=tables)


@app.route('/delete_table/<number>')
def delete_table(number):
    global tables
    tables = [t for t in tables if t['number'] != number]
    flash(f"Table {number} deleted!", 'info')
    return redirect(url_for('manage_tables'))


@app.route('/menu', methods=['GET', 'POST'])
def manage_menu():
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        quantity = int(request.form.get('quantity'))
        if name and price >= 0 and quantity >= 0:
            menu_items.append({'name': name, 'price': price, 'quantity': quantity})
            flash(f"Menu item '{name}' added!", 'success')
        else:
            flash("Invalid input!", 'danger')
        return redirect(url_for('manage_menu'))
    return render_template('menu.html', menu=menu_items)


@app.route('/delete_menu/<path:name>')
def delete_menu(name):
    global menu_items
    menu_items = [m for m in menu_items if m['name'] != name]
    flash(f"Menu item '{name}' deleted!", 'info')
    return redirect(url_for('manage_menu'))


@app.route('/orders', methods=['GET', 'POST'])
def manage_orders():
    if request.method == 'POST':
        table = request.form.get('table')
        item_name = request.form.get('item')
        quantity = int(request.form.get('quantity'))

        item = next((i for i in menu_items if i['name'] == item_name), None)
        if item and item['quantity'] >= quantity:
            total = item['price'] * quantity
            item['quantity'] -= quantity
            orders.append({'table': table, 'item': item_name, 'quantity': quantity, 'total': total})
            flash(f"Order placed for {item_name} (x{quantity}) on Table {table}!", 'success')
        else:
            flash(f"Insufficient stock for '{item_name}'!", 'danger')

        return redirect(url_for('manage_orders'))

    bill_summary = {}
    for order in orders:
        bill_summary.setdefault(order['table'], 0)
        bill_summary[order['table']] += order['total']

    return render_template('orders.html', orders=orders, tables=tables, menu=menu_items, bill_summary=bill_summary)


@app.route('/delete_order/<int:index>')
def delete_order(index):
    if 0 <= index < len(orders):
        deleted = orders.pop(index)
        flash(f"Deleted order: {deleted['item']} from Table {deleted['table']}", 'info')
    else:
        flash("Invalid order index", 'danger')
    return redirect(url_for('manage_orders'))


@app.route('/inventory')
def inventory():
    return render_template('inventory.html', menu=menu_items)


if __name__ == '__main__':
    app.run(debug=True)
