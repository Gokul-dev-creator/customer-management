import os
from datetime import datetime, date
from calendar import month_name
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# Using Werkzeug for stable password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# --- App and DB Configuration ---
app = Flask(__name__)
# IMPORTANT: Change this secret key!
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 
login_manager.login_message_category = 'danger' 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Database Models ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    # Increased hash length for Werkzeug
    password_hash = db.Column(db.String(128), nullable=False) 
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    payments = db.relationship('Payment', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}')"

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone_number = db.Column(db.String(15))
    plan_details = db.Column(db.String(100))
    monthly_charge = db.Column(db.Float, nullable=False)
    set_top_box_number = db.Column(db.String(50), unique=True, nullable=False)
    connection_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='Active')
    notes = db.Column(db.Text)
    payments = db.relationship('Payment', backref='customer', lazy=True, cascade="all, delete-orphan")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    payment_date = db.Column(db.Date, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    billing_period_month = db.Column(db.Integer, nullable=False)
    billing_period_year = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False, default='Cash')
    transaction_reference = db.Column(db.String(100))
    received_by = db.Column(db.String(100)) 

    @property
    def billing_period_display(self):
        return f"{month_name[self.billing_period_month]} {self.billing_period_year}"

# --- Utility Functions & Decorators ---
def get_billing_periods():
    current_year = datetime.now().year
    billing_months = [{'value': i, 'name': month_name[i]} for i in range(1, 13)]
    billing_years = list(range(current_year - 5, current_year + 2))
    return billing_months, billing_years

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('This page is accessible by administrators only.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Routes ---

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Login successful. Welcome, {user.username}!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, is_admin=False)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash(f'Account created for {username}! You are now logged in.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route("/users")
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.username).all()
    return render_template('manage_users.html', users=users)

@app.route("/users/toggle_admin/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user_to_modify = User.query.get_or_404(user_id)
    if user_to_modify.id == current_user.id:
        flash("You cannot change your own admin status.", "danger")
        return redirect(url_for('manage_users'))
    user_to_modify.is_admin = not user_to_modify.is_admin
    db.session.commit()
    new_status = "Admin" if user_to_modify.is_admin else "Operator"
    flash(f"User '{user_to_modify.username}' has been updated to {new_status}.", "success")
    return redirect(url_for('manage_users'))

@app.route("/users/delete/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.id == current_user.id:
        flash("You cannot delete your own account.", 'danger')
        return redirect(url_for('manage_users'))
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"User '{user_to_delete.username}' has been deleted.", 'success')
    return redirect(url_for('manage_users'))

# --- Main Application Routes ---

@app.route("/")
@app.route("/index")
@login_required
def index():
    total_customers_count = Customer.query.count()
    active_customers_count = Customer.query.filter_by(status='Active').count()
    collections_today = db.session.query(db.func.sum(Payment.amount_paid)).filter(Payment.payment_date == date.today()).scalar() or 0.0
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_billing_period_display = f"{month_name[current_month]} {current_year}"
    paid_customer_ids = [p.customer_id for p in Payment.query.filter_by(billing_period_month=current_month, billing_period_year=current_year).all()]
    outstanding_payments_count = Customer.query.filter(Customer.status == 'Active', Customer.id.notin_(paid_customer_ids)).count()
    search_term_home = request.args.get('search_home', '')
    query = Customer.query
    if search_term_home:
        search_pattern = f"%{search_term_home}%"
        query = query.filter(or_(Customer.name.ilike(search_pattern), Customer.set_top_box_number.ilike(search_pattern)))
    all_customers_on_home = query.order_by(Customer.name).all()
    customers_list_on_home = []
    for customer in all_customers_on_home:
        customers_list_on_home.append({
            'id': customer.id, 'name': customer.name, 'set_top_box_number': customer.set_top_box_number,
            'monthly_charge': customer.monthly_charge, 'status': customer.status,
            'paid_current_month': customer.id in paid_customer_ids
        })
    return render_template('index.html', total_customers_count=total_customers_count, active_customers_count=active_customers_count,
                           outstanding_payments_count=outstanding_payments_count, collections_today=collections_today,
                           current_billing_period_display=current_billing_period_display,
                           customers_list_on_home=customers_list_on_home, search_term_home=search_term_home)

@app.route('/customers')
@login_required
def customers_list():
    search_query_customers = request.args.get('search_customers', '')
    query = Customer.query
    if search_query_customers:
        search_pattern = f"%{search_query_customers}%"
        query = query.filter(or_(
            Customer.name.ilike(search_pattern), Customer.set_top_box_number.ilike(search_pattern),
            Customer.address.ilike(search_pattern), Customer.phone_number.ilike(search_pattern)
        ))
    customers = query.order_by(Customer.name).all()
    return render_template('customers.html', customers=customers, search_query_customers=search_query_customers)


@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        stb_exists = Customer.query.filter_by(set_top_box_number=request.form['set_top_box_number']).first()
        if stb_exists:
            flash('A customer with this Set-Top Box number already exists.', 'danger')
            return render_template('add_customer.html', is_edit=False, customer=request.form, today_date=date.today().isoformat())
        new_customer = Customer(
            name=request.form['name'], address=request.form['address'], phone_number=request.form.get('phone_number'),
            plan_details=request.form.get('plan_details'), monthly_charge=float(request.form['monthly_charge']),
            set_top_box_number=request.form['set_top_box_number'],
            connection_date=datetime.strptime(request.form['connection_date'], '%Y-%m-%d').date() if request.form.get('connection_date') else None,
            status=request.form['status'], notes=request.form.get('notes')
        )
        db.session.add(new_customer)
        db.session.commit()
        flash(f'Customer {new_customer.name} added successfully!', 'success')
        return redirect(url_for('customers_list'))
    return render_template('add_customer.html', is_edit=False, customer=None, today_date=date.today().isoformat())


@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form['name']; customer.address = request.form['address']
        customer.phone_number = request.form.get('phone_number'); customer.plan_details = request.form.get('plan_details')
        customer.monthly_charge = float(request.form['monthly_charge'])
        customer.connection_date = datetime.strptime(request.form['connection_date'], '%Y-%m-%d').date() if request.form.get('connection_date') else None
        customer.status = request.form['status']; customer.notes = request.form.get('notes')
        db.session.commit()
        flash(f'Customer {customer.name} updated successfully!', 'success')
        return redirect(url_for('customers_list'))
    return render_template('add_customer.html', is_edit=True, customer=customer, today_date=date.today().isoformat())


@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash(f'Customer {customer.name} and all their payments have been deleted.', 'success')
    return redirect(url_for('customers_list'))


@app.route('/payments/record', methods=['GET', 'POST'])
@login_required
def record_payment():
    billing_months, billing_years = get_billing_periods()
    customers = Customer.query.filter_by(status='Active').order_by(Customer.name).all()
    customer_id_prefill = request.args.get('customer_id_prefill', type=int)
    default_amount = None
    if customer_id_prefill:
        prefill_customer = Customer.query.get(customer_id_prefill)
        if prefill_customer: default_amount = prefill_customer.monthly_charge
    if request.method == 'POST':
        customer_id = request.form.get('customer_id'); customer = Customer.query.get(customer_id)
        if not customer:
            flash('Invalid customer selected.', 'danger')
            return render_template('record_payment.html', form_values=request.form, today_date=date.today().isoformat(), customers=customers, 
                                   billing_months=billing_months, billing_years=billing_years, current_month=datetime.now().month, current_year=datetime.now().year)
        amount_paid_str = request.form.get('amount_paid'); amount_paid = float(amount_paid_str) if amount_paid_str else customer.monthly_charge
        new_payment = Payment(
            customer_id=customer_id, user_id=current_user.id, payment_date=datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date(),
            amount_paid=amount_paid, billing_period_month=int(request.form['billing_period_month']),
            billing_period_year=int(request.form['billing_period_year']), payment_method=request.form['payment_method'],
            transaction_reference=request.form.get('transaction_reference'), received_by=current_user.username 
        )
        db.session.add(new_payment); db.session.commit()
        flash(f'Payment for {customer.name} recorded successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('record_payment.html', customers=customers, today_date=date.today().isoformat(),
                           billing_months=billing_months, billing_years=billing_years, current_month=datetime.now().month,
                           current_year=datetime.now().year, customer_id_prefill=customer_id_prefill,
                           default_amount=default_amount, form_values=None)

@app.route('/payments/log')
@login_required
def payments_log():
    page = request.args.get('page', 1, type=int)
    search_customer_name = request.args.get('customer_name', '')
    query = Payment.query.join(Customer).order_by(Payment.payment_date.desc(), Payment.id.desc())
    if search_customer_name:
        search_pattern = f"%{search_customer_name}%"
        query = query.filter(Customer.name.ilike(search_pattern))
    payments = query.paginate(page=page, per_page=15)
    return render_template('payments_log.html', payments=payments, search_customer_name=search_customer_name)


@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html', report_type=None)


@app.route('/reports/outstanding')
@login_required
def outstanding_payments_report():
    billing_months, billing_years = get_billing_periods()
    report_month = request.args.get('month', type=int)
    report_year = request.args.get('year', type=int)
    outstanding_customers = []
    selected_month_name = ''
    if report_month and report_year:
        selected_month_name = month_name[report_month]
        paid_customer_ids = [p.customer_id for p in Payment.query.filter_by(billing_period_month=report_month, billing_period_year=report_year).all()]
        outstanding_customers = Customer.query.filter(Customer.status == 'Active', Customer.id.notin_(paid_customer_ids)).order_by(Customer.name).all()
    return render_template('reports.html', report_type='outstanding', outstanding_customers=outstanding_customers,
                           billing_months=billing_months, billing_years=billing_years, report_month=report_month or datetime.now().month, 
                           report_year=report_year or datetime.now().year, selected_month_name=selected_month_name)


@app.route('/reports/collections')
@login_required
def collections_report():
    start_date_str = request.args.get('start_date'); end_date_str = request.args.get('end_date')
    _form_submitted_and_valid = False
    collections, total_cash, total_online, grand_total = [], 0, 0, 0
    if start_date_str and end_date_str:
        _form_submitted_and_valid = True
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        collections = Payment.query.filter(Payment.payment_date.between(start_date, end_date)).order_by(Payment.payment_date.desc()).all()
        total_cash = db.session.query(db.func.sum(Payment.amount_paid)).filter(Payment.payment_date.between(start_date, end_date), Payment.payment_method == 'Cash').scalar() or 0.0
        total_online = db.session.query(db.func.sum(Payment.amount_paid)).filter(Payment.payment_date.between(start_date, end_date), Payment.payment_method == 'Online').scalar() or 0.0
        grand_total = total_cash + total_online
    return render_template('reports.html', report_type='collections', collections=collections, total_cash=total_cash, 
                           total_online=total_online, grand_total=grand_total, start_date=start_date_str, end_date=end_date_str,
                           today_date=date.today().isoformat(), _form_submitted_and_valid=_form_submitted_and_valid)


if __name__ == '__main__':
    app.run(debug=True)