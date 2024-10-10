from flask import Flask, render_template, redirect, url_for, request, flash
from datetime import datetime  # Import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://root:password@localhost/superstocks'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#define tables
class Users(db.Model):
    __tablename__ = 'users'
    user_email = db.Column(db.String(128), primary_key=True)
    fname = db.Column(db.String(128), nullable=False)
    lname = db.Column(db.String(128), nullable=False)
    isadmin = db.Column(db.Boolean)
    cash = db.Column(db.DECIMAL(10,2), nullable=False)
    password = db.Column(db.String(128), nullable=False)

class User_Stock(db.Model):
    __tablename__ = 'user_stock'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(128), db.ForeignKey('users.user_email'))
    stock_ticker = db.Column(db.CHAR(5), db.ForeignKey('market_stock.stock_ticker'))
    user_quantity = db.Column(db.Integer, nullable=False)

class User_Transactions(db.Model):
    __tablename__ = 'user_transactions'
    transaction_number = db.Column(db.Integer, primary_key=True)
    stock_ticker = db.Column(db.CHAR(5), db.ForeignKey('market_stock.stock_ticker'))
    sell_buy = db.Column(db.Boolean)
    price_at_purchase = db.Column(db.DECIMAL(10,2), nullable=False)
    purchase_quantity = db.Column(db.Integer, nullable=False)
    user_email = db.Column(db.String(128), db.ForeignKey('users.user_email'))

class Market_Stock(db.Model):
    __tablename__ = 'market_stock'
    stock_ticker = db.Column(db.CHAR(5), primary_key=True)
    stock_name = db.Column(db.String(128), nullable=False)
    stock_quantity= db.Column(db.Integer, nullable=False)
    stock_price = db.Column(db.DECIMAL(10,2), nullable=False)

class Market(db.Model):
    __tablename__ = 'market'
    DOY = db.Column(db.Integer, primary_key=True)
    isOpen = db.Column(db.Boolean)
    openHour = db.Column(db.Integer, nullable=False)
    closeHour = db.Column(db.Integer, nullable=False)


@app.route('/createdb')
def creDB():
    db.create_all()
    return "Createed product databa"

@app.route('/')
def home():
    current_year = datetime.now().year  # Get the current year
    return render_template('home.html', current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Placeholder login logic
        if email == "test@example.com" and password == "password123":
            flash('Login successful', 'success')
            return redirect(url_for('dashboard_view', username="Test User"))
        else:
            flash('Login failed. Check your email or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        flash(f'Registration successful for {username}', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/dashboard')
def dashboard_view():
    username = "Test User"
    cash = 1000  # Placeholder for current cash
    return render_template('dashboard.html', username=username, cash=cash)

@app.route('/buy_stocks')
def buy_stocks():
    return "Buy Stocks page (To be implemented)"

@app.route('/add_cash', methods=['GET', 'POST'])
def add_cash():
    username = "Test User"
    current_cash = 1000.00

    if request.method == 'POST':
        amount = float(request.form['amount'])
        import random
        success_rate = random.choice([True, False])

        if success_rate:
            new_cash = current_cash + amount
            flash(f'Success! ${amount} has been added to your account. Your new balance is ${new_cash:.2f}.', 'success')
            return redirect(url_for('dashboard', username=username))
        else:
            flash('Error: Failed to add cash. Please try again.', 'danger')
            return redirect(url_for('add_cash'))

    return render_template('add_cash.html', username=username, current_cash=current_cash)

@app.route('/logout')
def logout():
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        flash(f'A password reset link has been sent to {email}', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/sell_stocks', methods=['GET', 'POST'])
def sell_stocks():
    if request.method == 'POST':
        stock = request.form.get('stock')
        num_stocks = request.form.get('num_stocks')

        if not num_stocks or not num_stocks.isdigit():
            flash("Please enter a valid number of stocks.", "danger")
            return render_template('sell_stocks.html', error=False)

        num_stocks = int(num_stocks)
        total_stocks = 50

        if num_stocks > total_stocks:
            flash(f"Not enough stocks available to sell. You have {total_stocks} stocks.", "danger")
            return redirect(url_for('not_enough_stocks'))
        else:
            sell_value = num_stocks * 500
            flash(f'Successfully sold {num_stocks} stocks for ${sell_value}.', 'success')
            return redirect(url_for('dashboard'))

    return render_template('sell_stocks.html', error=False)

@app.route('/not_enough_stocks')
def not_enough_stocks():
    return render_template('not_enough_stocks.html')

@app.route('/user_settings', methods=['GET', 'POST'])
def user_settings():
    if request.method == 'POST':
        # Get new email and password from the form
        new_email = request.form['email']
        new_password = request.form['password']
        # Add logic to update user's email and password in the database
        flash('User settings updated successfully', 'success')
        return redirect(url_for('dashboard_view'))
    return render_template('user_settings.html')

@app.route('/admin_page')
def admin_page():
    return render_template('admin_page.html')

if __name__ == '__main__':
    app.run(debug=True)

