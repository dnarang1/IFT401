from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sys
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
import io
import base64
import random
from random import uniform
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://root:password@localhost/superstocks'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to the login page if not logged in

# Define the User model
class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    user_email = db.Column(db.String(128), primary_key=True)
    fname = db.Column(db.String(128), nullable=False)
    lname = db.Column(db.String(128), nullable=False)
    isadmin = db.Column(db.Boolean)
    islocked = db.Column(db.Boolean)
    cash = db.Column(db.DECIMAL(10,2), nullable=False)
    password = db.Column(db.String(512), nullable=False)

    def get_id(self):
        return self.user_email

# Define user stock
class User_Stock(db.Model):
    __tablename__ = 'user_stock'
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(128), db.ForeignKey('users.user_email'))
    stock_ticker = db.Column(db.CHAR(5), db.ForeignKey('market_stock.stock_ticker'))
    user_quantity = db.Column(db.Integer, nullable=False)
# Define user transactions
class User_Transactions(db.Model):
    __tablename__ = 'user_transactions'
    transaction_number = db.Column(db.Integer, primary_key=True, AUTO_INCREMENT=True) 
    stock_ticker = db.Column(db.CHAR(5), db.ForeignKey('market_stock.stock_ticker'))
    sell_buy = db.Column(db.Boolean)
    price_at_purchase = db.Column(db.DECIMAL(10,2), nullable=False)
    purchase_quantity = db.Column(db.Integer, nullable=False)
    user_email = db.Column(db.String(128), db.ForeignKey('users.user_email'))
# Define market stock
class Market_Stock(db.Model):
    __tablename__ = 'market_stock'
    stock_ticker = db.Column(db.CHAR(5), primary_key=True)
    stock_name = db.Column(db.String(128), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    stock_price = db.Column(db.DECIMAL(10,2), nullable=False)
    market_high = db.Column(db.DECIMAL(10,2), nullable=False)
    market_low = db.Column(db.DECIMAL(10,2), nullable=False)
# Define market
class Market(db.Model):
    __tablename__ = 'market'
    DOY = db.Column(db.Integer, primary_key=True)
    isOpen = db.Column(db.Boolean)
    openHour = db.Column(db.Integer, nullable=False)
    closeHour = db.Column(db.Integer, nullable=False)

# Load user callback
@login_manager.user_loader
def load_user(user_email):
    return Users.query.get(user_email)

# Database init
@app.route('/createdb')
def creDB():
    db.create_all()
    return "Created product database"
# Homepage
@app.route('/')
def home():
    current_year = datetime.now().year
    return render_template('home.html', current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Grab email and password from webpage
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Login logic. Finds user then checks password against hashed password in the database
        user = Users.query.filter_by(user_email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)  # Log the user in
            print('Successful Login')
            flash('Login successful', 'success')
            if not user.isadmin:
                return redirect(url_for('dashboard_view'))
            else:
                return redirect(url_for('admin_page'))
        else:
            print('Login failed')
            flash('Login failed. Check your email or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        EnteredPassword = request.form['password']
        HashedPassword = generate_password_hash(EnteredPassword)
        userObj = Users(
            user_email=username,
            password=HashedPassword,
            fname="dne",
            lname="dne",
            isadmin=False,
            cash=0,
            islocked=False
        )
        # attempt to add to database
        try:
            db.session.add(userObj)
            print('User added successfully') # Debug message
            db.session.commit()
            flash(f'Registration successful for {username}', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            print(f'Error adding user: {e}') # Debug message
            flash('Registration failed. Please try again.', 'danger')
    return render_template('register.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/dashboard')
@login_required
def dashboard_view():
    username = current_user.user_email  # Use the logged-in user's email
    user = db.session.query(Users).filter(Users.user_email == username).first()
    cash = user.cash

    AllMarketStocks = db.session.query(Market_Stock).all()

    #randomize stock prices
    for item in AllMarketStocks:
        rando = Decimal(uniform(0.75,1.25))
        oldPrice = item.stock_price
        newPrice = rando * oldPrice
        setattr(item, 'stock_price', item.stock_price * rando)
    db.session.commit()

    AllMarketStocks = db.session.query(Market_Stock).all()

    userStocks = db.session.query(User_Stock).filter(User_Stock.user_email == username).all()
    listOfUserStock = []
    stockData = []
    for item in userStocks:
        listOfUserStock.append(item.stock_ticker)
        stockData.append(item.user_quantity)

    return render_template('dashboard.html', username=username, cash=cash, allstocks=AllMarketStocks, ownedStocklables=listOfUserStock, data=stockData)

@app.route('/buy_stocks', methods=['GET', 'POST'])
@login_required
def buy_stocks():
    if request.method == 'GET':
        #print(request.args.get('stock'))
        enteredStock = request.args.get('stock')
        #print("selected Stock: ",enteredStock)
        availableMarket = db.session.query(Market_Stock).filter(Market_Stock.stock_ticker == enteredStock).first()
        count = availableMarket.stock_quantity
        value = availableMarket.stock_price * count
        #get user obj to show max number of stocks that could be bought
        userObj = db.session.query(Users).filter(Users.user_email==current_user.user_email).first()
        cash = userObj.cash
        TotalUserCanBuy = cash // availableMarket.stock_price
        print("user has: ",cash, "cash. Total Stock Value: ",value)
        if(TotalUserCanBuy > count):
            buyableCount = count
            
        else:
            buyableCount = TotalUserCanBuy
        value = buyableCount * availableMarket.stock_price

        #return "list available stocks"
        return render_template('buy_stocks.html', stockToAction=enteredStock,ownedCount=buyableCount,summedValue=value)

    #if post
    if request.method == 'POST':
        #return "to be implemented"
        stock = request.form.get('stock_ticker')
        num_stocks = request.form.get('num_stocks')
        userEmail = current_user.user_email
        user_inventoryObj = db.session.query(User_Stock).filter(User_Stock.user_email == userEmail, User_Stock.stock_ticker == stock).first()
        Market_stockObj = db. session.query(Market_Stock).filter(Market_Stock.stock_ticker == stock).first()
        UserObj = db.session.query(Users).filter(Users.user_email == userEmail).first()
        if (user_inventoryObj == None):
            #user does not have any existing stock

            ##new Transaction!!!
            newTransaction = User_Transactions(
                stock_ticker = stock,
                sell_buy = True,
                price_at_purchase = Market_stockObj.stock_price,
                purchase_quantity = num_stocks,
                user_email = userEmail
            )
            db.session.add(newTransaction)
            db.session.commit()
            #decrease available stocks in market
            setattr(Market_stockObj, 'stock_quantity', Market_stockObj.stock_quantity - int(num_stocks))
            db.session.commit()
            #decrease cash
            cashValue = Market_stockObj.stock_price * int(num_stocks)
            setattr(UserObj, 'cash', UserObj.cash - cashValue)
            db.session.commit()
            #new user_stock obj
            NewStockInventory = User_Stock (
                user_email = userEmail,
                stock_ticker = stock,
                user_quantity = num_stocks
            )
            db.session.add(NewStockInventory)
            db.session.commit()

            return redirect(url_for('dashboard_view'))
        else:
            ##user already has stock, bump count

            #new transaction
            newTransaction = User_Transactions(
                stock_ticker = stock,
                sell_buy = True,
                price_at_purchase = Market_stockObj.stock_price,
                purchase_quantity = num_stocks,
                user_email = userEmail
            )
            db.session.add(newTransaction)
            db.session.commit()
            #decrease availble stocks in market
            setattr(Market_stockObj, 'stock_quantity', Market_stockObj.stock_quantity - int(num_stocks))
            db.session.commit()
            #decrease cash
            cashValue = Market_stockObj.stock_price * int(num_stocks)
            setattr(UserObj, 'cash', UserObj.cash - cashValue)
            db.session.commit()
            #update inventory
            setattr(user_inventoryObj, 'user_quantity', user_inventoryObj.user_quantity + int(num_stocks))
            db.session.commit()

            return redirect(url_for('dashboard_view'))
    return "Buy Stocks page (To be implemented)"

@app.route('/add_cash', methods=['GET', 'POST'])
@login_required
def add_cash():
    username = current_user.user_email  # Use the logged-in user's email
    userObj = db.session.query(Users).filter(Users.user_email == username).first()
    current_cash = userObj.cash
    if request.method == 'POST':
        amount = float(request.form['amount'])
        success_rate = random.choice([True, False])

        if success_rate:
            new_cash = Decimal(current_cash) + Decimal(amount)
            flash(f'Success! ${amount} has been added to your account. Your new balance is ${new_cash:.2f}.', 'success')
            setattr(userObj, 'cash',new_cash)
            db.session.commit()
            return redirect(url_for('dashboard_view'))
        else:
            flash('Error: Failed to add cash. Please try again.', 'danger')
            return redirect(url_for('add_cash'))
    if request.method == 'GET':
        #get current cash

        
        return render_template('add_cash.html',username=username, current_cash=current_cash)
    
@app.route('/withdraw_cash', methods=['GET','POST'])
@login_required
def withdraw_cash():
    username = current_user.user_email  # Use the logged-in user's email
    userObj = db.session.query(Users).filter(Users.user_email == username).first()
    current_cash = userObj.cash
    if request.method == 'GET':
        return render_template('withdraw_cash.html',totalCash=current_cash,username=username)
    if request.method == 'POST':
        amount = float(request.form['amount'])
        new_cash = Decimal(current_cash) - Decimal(amount)
        setattr(userObj, 'cash',new_cash)
        db.session.commit()
        return redirect(url_for('dashboard_view'))

    return "it broke"

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
@login_required
def sell_stocks():
    if request.method == 'POST':
        #get info from user
        stock = request.form.get('stock_ticker')
        print("selected stock: ",stock)
        num_stocks = request.form.get('num_stocks')
        print(num_stocks)
        userEmail = current_user.user_email

        #get row from db
        user_inventoryObj = db.session.query(User_Stock).filter(User_Stock.stock_ticker == stock, User_Stock.user_email == current_user.user_email).first()
        print(user_inventoryObj)
        oldStockCount = user_inventoryObj.user_quantity
        newStockCount = oldStockCount - int(num_stocks)
        print("new stock count:", newStockCount)
        setattr(user_inventoryObj, 'user_quantity', newStockCount)
        db.session.commit()
        print("sold stock from user")
        print(db.session.query(User_Stock).filter(User_Stock.stock_ticker == stock, User_Stock.user_email == current_user.user_email).first())
        #add cash to user
        user_obj = db.session.query(Users).filter(Users.user_email == userEmail).first()
        market_stockObj = db.session.query(Market_Stock).filter(Market_Stock.stock_ticker == stock).first()
        cashValue = market_stockObj.stock_price * int(num_stocks)
        setattr(user_obj, 'cash', user_obj.cash + cashValue)
        db.session.commit()
        print("added cash to user profile")
        num_stocks = int(num_stocks)
        total_stocks = 50  # Replace with actual stock quantity logic
        newTransaction = User_Transactions(
            stock_ticker = stock,
            sell_buy = False,
            price_at_purchase = market_stockObj.stock_price,
            purchase_quantity = num_stocks,
            user_email = userEmail
        )
        db.session.add(newTransaction)
        db.session.commit()
        print("added transaction log")

        return redirect(url_for('dashboard_view'))

    if request.method == 'GET':
        enteredStock = request.args.get('stock')
        print(enteredStock)
        userStockObj = db.session.query(User_Stock).filter(User_Stock.stock_ticker == enteredStock, User_Stock.user_email == current_user.user_email).first()
        stockObj = db.session.query(Market_Stock).filter(Market_Stock.stock_ticker == enteredStock).first()
        print(stockObj.stock_price)
        count = userStockObj.user_quantity
        print(count)
        value = stockObj.stock_price * count
        print(value)
        return render_template('sell_stocks.html', error=False, stockToAction=enteredStock,ownedCount=count,summedValue = value)


    return render_template('sell_stocks.html', error=False)

@app.route('/not_enough_stocks')
@login_required
def not_enough_stocks():
    return render_template('not_enough_stocks.html')



# User settings
@app.route('/user_settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    if request.method == 'POST':
        new_email = request.form['email']
        new_password = request.form['password']
        flash('User settings updated successfully', 'success')
        return redirect(url_for('dashboard_view'))
    return render_template('user_settings.html')
# Admin page
@app.route('/admin_page')
@login_required
def admin_page():
    if not current_user.isadmin:
        return "ADMIN ACCESS ONLY", 403
    return render_template('admin_page.html')
# Add stock
@app.route('/admin/addstock', methods=['GET', 'POST'])
@login_required
def admin_add_stock():
    # Grab info from webpage
    if request.method == 'POST':
        stockName = request.form['stockName']
        stockTicker = request.form['stockTicker']
        stockPrice = request.form['stockPrice']
        stockCount = request.form['stockCount']
        stockObj = Market_Stock(
            stock_ticker=stockTicker,
            stock_name=stockName,
            stock_price=stockPrice,
            stock_quantity=stockCount,
            market_high=stockPrice,
            market_low=stockPrice,
        )
        # Add info to database
        db.session.add(stockObj)
        db.session.commit()
        flash('Stock added successfully!', 'success')
        return redirect(url_for('admin_page'))
    return render_template('admin_add_stock.html')



@app.route('/admin/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith("user_email_"):
                user_email = request.form[key]  # Extract original email
                new_email = request.form.get(f"email_{user_email}", user_email)
                new_fname = request.form.get(f"fname_{user_email}", "")  # Get new first name
                new_lname = request.form.get(f"lname_{user_email}", "")  # Get new last name
                new_cash = request.form.get(f"cash_{user_email}", "0")  # Get new cash value
                is_admin = f"isadmin_{user_email}" in request.form
                is_locked = f"islocked_{user_email}" in request.form

                # Update the user details
                update_user_details(user_email, new_email, new_fname, new_lname, new_cash)
                update_user_status(user_email, is_admin, is_locked)

        flash('User details updated successfully!', 'success')
        return redirect(url_for('manage_users'))

    users = get_all_users()  # Fetch all users from the database
    return render_template('manage_users.html', users=users)

def update_user_details(old_email, new_email, new_fname, new_lname, new_cash):
    user = Users.query.filter_by(user_email=old_email).first()
    if user:
        user.user_email = new_email
        user.fname = new_fname
        user.lname = new_lname
        user.cash = float(new_cash)  # Ensure cash is stored as a numeric value
        db.session.commit()  # Commit changes to the database
    else:
        print(f"User with email {old_email} not found.")

def update_user_status(email, is_admin, is_locked):
    user = Users.query.filter_by(user_email=email).first()
    if user:
        user.isadmin = is_admin
        user.islocked = is_locked
        db.session.commit()  # Commit the change to the database
    else:
        print(f"User with email {email} not found.")

def get_all_users():
    return Users.query.all()  # Fetch all users from the Users table


@app.route('/admin/manage_stocks', methods=['GET', 'POST'])
@login_required
def manage_stocks():
    if not current_user.isadmin:
        return "ADMIN ACCESS ONLY", 403

    # Add logic to handle stock management
    return render_template('manage_stocks.html')

@app.route('/admin/manage_users/review_transactions')
@login_required
def review_transactions():
    if not current_user.isadmin:
       return "ADMIN ACCESS ONLY", 403
    
    return render_template('review_transactions.html')
@app.route('/admin/manage_users/generate_reports')
@login_required
def generate_reports():
    if not current_user.isadmin:
        return "ADMIN ACCESS ONLY", 403
    
    return render_template('generate_reports.html')
@app.route('/admin/site_settings')
@login_required
def site_settings():
    if not current_user.isadmin:
        return "ADMIN ACCESS ONLY", 403
    return render_template('site_settings.html')

@app.route('/admin/site_settings/save_holiday_settings', methods=['POST'])
@login_required
def save_holiday_settings():
    if not current_user.isadmin:
        return "ADMIN ACCESS ONLY", 403
    try:
        holiday_date = request.form['holiday_date']
        is_closed = 'market_closed' in request.form  # Checkbox checked if present in form data

        # Convert date to DOY (Day of Year)
        doy = datetime.strptime(holiday_date, '%Y-%m-%d').timetuple().tm_yday

        # Find or create the market day entry
        market_day = Market.query.get(doy) or Market(DOY=doy)

        if is_closed:
            # Set as closed for the day
            market_day.isOpen = False
            market_day.openHour = None  # Null for closed day
            market_day.closeHour = None
        else:
            # Set open hours for the holiday if the market is not closed
            open_hour = int(request.form['holiday_start_time'].split(':')[0])
            close_hour = int(request.form['holiday_end_time'].split(':')[0])
            market_day.isOpen = True
            market_day.openHour = open_hour
            market_day.closeHour = close_hour

        db.session.add(market_day)
        db.session.commit()
        return redirect(url_for('site_settings'))  # Redirect to the settings page
    except Exception as e:
        return f"Error saving holiday settings: {e}", 500


@app.route('/admin/site_settings/save_market_hours', methods=['POST'])
@login_required
def save_market_hours():
    try:
        market_start_time = request.form['market_start_time']
        market_end_time = request.form['market_end_time']

        open_hour = int(market_start_time.split(':')[0])
        close_hour = int(market_end_time.split(':')[0])

        # Update market hours for each day in the year
        for doy in range(1, 366):  # Loop through all DOY (1-365 or 1-366 in a leap year)
            market_day = Market.query.get(doy) or Market(DOY=doy)
            market_day.isOpen = True  # General market days are open by default
            market_day.openHour = open_hour
            market_day.closeHour = close_hour
            db.session.add(market_day)

        db.session.commit()
        return redirect(url_for('site_settings'))  # Redirect to the settings page
    except Exception as e:
        return f"Error saving market hours: {e}", 500



if __name__ == '__main__':
    app.run(debug=True)