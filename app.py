from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Create DB
with app.app_context():
    db.create_all()

# Dashboard + Charts
@app.route('/')
def dashboard():
    expenses = Expense.query.all()

    # Prepare data for charts
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    if not os.path.exists("static"):
        os.makedirs("static")

    if categories:
        # Pie chart
        plt.figure()
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
        plt.title("Category Distribution")
        plt.savefig("static/pie.png")
        plt.close()

        # Bar chart
        plt.figure()
        plt.bar(categories.keys(), categories.values())
        plt.title("Category-wise Expenses")
        plt.savefig("static/bar.png")
        plt.close()

    return render_template('dashboard.html', expenses=expenses)

# Add Expense
@app.route('/add', methods=['POST'])
def add_expense():
    category = request.form['category']
    amount = request.form['amount']

    new_expense = Expense(category=category, amount=amount)
    db.session.add(new_expense)
    db.session.commit()

    return redirect('/')

# Delete Expense
@app.route('/delete/<int:id>')
def delete(id):
    expense = Expense.query.get(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect('/')

# Edit Expense
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    expense = Expense.query.get(id)
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ---------------- MODELS ---------------- #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ---------------- #

@app.route('/')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    # Chart data
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    if not os.path.exists("static"):
        os.makedirs("static")

    if categories:
        plt.figure()
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
        plt.savefig("static/pie.png")
        plt.close()

        plt.figure()
        plt.bar(categories.keys(), categories.values())
        plt.savefig("static/bar.png")
        plt.close()

    return render_template('dashboard.html', expenses=expenses)

# ---------- AUTH ---------- #

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# ---------- EXPENSE ---------- #

@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    category = request.form['category']
    amount = request.form['amount']

    expense = Expense(category=category, amount=amount, user_id=current_user.id)
    db.session.add(expense)
    db.session.commit()

    return redirect('/')

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    expense = Expense.query.get(id)

    if expense.user_id == current_user.id:
        db.session.delete(expense)
        db.session.commit()

    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense = Expense.query.get(id)

    if expense.user_id != current_user.id:
        return redirect('/')

    if request.method == 'POST':
        expense.category = request.form['category']
        expense.amount = request.form['amount']
        db.session.commit()
        return redirect('/')

    return render_template('edit.html', expense=expense)

# ---------------- RUN ---------------- #

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)