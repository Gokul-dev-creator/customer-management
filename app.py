import os
from datetime import datetime, date
import calendar
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func # Removed 'and_' and 'extract' as not directly used yet

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_key_for_dev') # Important for sessions/flashing
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cable_app.db') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Constants ---
BILLING_MONTHS = [{'value': i, 'name': calendar.month_name[i]} for i in range(1, 13)]
CURRENT_YEAR = datetime.now().year
BILLING_YEARS = list(range(CURRENT_YEAR - 5, CURRENT_YEAR + 5)) 

# --- Helper Functions ---
def get_month_name(month_number):
    try:
        return calendar.month_name[int(month_number)]
    except (IndexError, ValueError, TypeError):
        return "Invalid Month"

def get_current_billing_period():
    now = datetime.now()
    return now.month, now.year

def get_current_billing_period_display():
    month, year = get_current_billing_period()
    return f"{get_month_name(month)} {year}"

# --- Models ---
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=False)
    plan_details = db.Column(db.String(100), nullable=True)
    monthly_charge = db.Column(db.Float, nullable=False)
    set_top_box_number = db.Column(db.String(50), unique=True, nullable=False)
    connection_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Active', nullable=False) # Active, Inactive, Suspended
    notes = db.Column(db.Text, nullable=True)
    
    payments = db.relationship('Payment', backref='customer', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Customer {self.name} ({self.set_top_box_number})>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today) # Use date.today for default
    amount_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False) # Cash, Online
    transaction_reference = db.Column(db.String(100), nullable=True)
    billing_period_month = db.Column(db.Integer, nullable=False)
    billing_period_year = db.Column(db.Integer, nullable=False)
    received_by = db.Column(db.String(100), nullable=True)

    @property
    def billing_period_display(self):
        return f"{get_month_name(self.billing_period_month)} {self.billing_period_year}"

    def __repr__(self):
        return f'<Payment {self.id} for Customer {self.customer_id}>'

# --- Routes ---

@app.route('/')
def index():
    search_term_home = request.args.get('search_home', '').strip()
    
    total_customers_count = Customer.query.count()
    active_customers_count = Customer.query.filter_by(status='Active').count()
    
    current_month, current_year = get_current_billing_period()
    
    active_customer_ids = [c.id for c in Customer.query.filter_by(status='Active').with_entities(Customer.id).all()]
    
    paid_this_month_ids = [
        p.customer_id for p in Payment.query.filter(
            Payment.customer_id.in_(active_customer_ids),
            Payment.billing_period_month == current_month,
            Payment.billing_period_year == current_year
        ).with_entities(Payment.customer_id).distinct().all()
    ]
    outstanding_payments_count = len(active_customer_ids) - len(paid_this_month_ids)
            
    collections_today_val = db.session.query(func.sum(Payment.amount_paid)).filter(
        Payment.payment_date == date.today()
    ).scalar() or 0.0

    customers_query = Customer.query.order_by(Customer.name)
    if search_term_home:
        search_like = f"%{search_term_home}%"
        customers_query = customers_query.filter(
            or_(
                Customer.name.ilike(search_like),
                Customer.set_top_box_number.ilike(search_like)
            )
        )
    
    customers_on_home_db = customers_query.all()
    customers_list_on_home = []
    for cust in customers_on_home_db:
        paid_current_month = cust.id in paid_this_month_ids
        customers_list_on_home.append({
            'id': cust.id,
            'name': cust.name,
            'set_top_box_number': cust.set_top_box_number,
            'monthly_charge': cust.monthly_charge,
            'status': cust.status,
            'paid_current_month': paid_current_month
        })
        
    return render_template('index.html',
                           total_customers_count=total_customers_count,
                           active_customers_count=active_customers_count,
                           outstanding_payments_count=outstanding_payments_count,
                           collections_today=collections_today_val,
                           current_billing_period_display=get_current_billing_period_display(),
                           customers_list_on_home=customers_list_on_home,
                           search_term_home=search_term_home)

@app.route('/customers')
def customers_list():
    search_query = request.args.get('search_customers', '').strip()
    query = Customer.query
    if search_query:
        search_like = f"%{search_query}%"
        query = query.filter(
            or_(
                Customer.name.ilike(search_like),
                Customer.set_top_box_number.ilike(search_like),
                Customer.address.ilike(search_like),
                Customer.phone_number.ilike(search_like)
            )
        )
    customers = query.order_by(Customer.name).all()
    return render_template('customers.html', customers=customers, search_query_customers=search_query)

@app.route('/customer/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        stb_number = request.form.get('set_top_box_number', '').strip()
        if not stb_number:
            flash('Set-Top Box number is required.', 'danger')
        else:
            existing_stb = Customer.query.filter_by(set_top_box_number=stb_number).first()
            if existing_stb:
                flash(f'Set-Top Box number "{stb_number}" already exists.', 'danger')

        if not request.form.get('name', '').strip():
            flash('Name is required.', 'danger')
        if not request.form.get('address', '').strip():
            flash('Address is required.', 'danger')
        if not request.form.get('monthly_charge', '').strip():
            flash('Monthly charge is required.', 'danger')


        if '_flashes' in session: # Check if any error message was flashed
            # Repopulate form with submitted data
            conn_date_str_on_error = request.form.get('connection_date')
            parsed_conn_date_on_error = None
            if conn_date_str_on_error:
                try:
                    parsed_conn_date_on_error = datetime.strptime(conn_date_str_on_error, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid connection date format. It was ignored.', 'warning')
            
            customer_data_for_template = {
                'name': request.form.get('name'),
                'phone_number': request.form.get('phone_number'),
                'address': request.form.get('address'),
                'plan_details': request.form.get('plan_details'),
                'monthly_charge': request.form.get('monthly_charge'), # Keep as string
                'set_top_box_number': stb_number,
                'connection_date': parsed_conn_date_on_error, # Date object or None
                'status': request.form.get('status', 'Active'),
                'notes': request.form.get('notes')
            }
            return render_template('add_customer.html', is_edit=False, customer=customer_data_for_template, today_date=date.today().isoformat())

        try:
            monthly_charge = float(request.form.get('monthly_charge'))
        except (ValueError, TypeError):
            flash('Monthly charge must be a valid number.', 'danger')
            # Re-render with data (similar to above, simplified here)
            return redirect(url_for('add_customer')) # Or full re-render logic

        connection_date_str = request.form.get('connection_date')
        conn_date = None
        if connection_date_str:
            try:
                conn_date = datetime.strptime(connection_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid connection date format. Saved without connection date.', 'warning')

        new_customer = Customer(
            name=request.form.get('name'),
            phone_number=request.form.get('phone_number'),
            address=request.form.get('address'),
            plan_details=request.form.get('plan_details'),
            monthly_charge=monthly_charge,
            set_top_box_number=stb_number,
            connection_date=conn_date,
            status=request.form.get('status', 'Active'),
            notes=request.form.get('notes')
        )
        db.session.add(new_customer)
        try:
            db.session.commit()
            flash('Customer added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'danger')
        return redirect(url_for('customers_list'))
    
    return render_template('add_customer.html', is_edit=False, customer=None, today_date=date.today().isoformat())

@app.route('/customer/edit/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        # STB number is readonly, not expecting change.
        if not request.form.get('name', '').strip():
            flash('Name is required.', 'danger')
        if not request.form.get('address', '').strip():
            flash('Address is required.', 'danger')
        if not request.form.get('monthly_charge', '').strip():
            flash('Monthly charge is required.', 'danger')

        if '_flashes' in session:
             # If errors, re-render with current (potentially unsaved) customer data
            return render_template('add_customer.html', is_edit=True, customer=customer, today_date=date.today().isoformat())

        try:
            monthly_charge = float(request.form.get('monthly_charge'))
        except (ValueError, TypeError):
            flash('Monthly charge must be a valid number.', 'danger')
            return render_template('add_customer.html', is_edit=True, customer=customer, today_date=date.today().isoformat())

        connection_date_str = request.form.get('connection_date')
        conn_date = customer.connection_date 
        if connection_date_str:
            try:
                conn_date = datetime.strptime(connection_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid connection date format. Kept existing date.', 'warning')
        else: # If field is submitted empty, set to None
            conn_date = None


        customer.name = request.form.get('name')
        customer.phone_number = request.form.get('phone_number')
        customer.address = request.form.get('address')
        customer.plan_details = request.form.get('plan_details')
        customer.monthly_charge = monthly_charge
        customer.connection_date = conn_date
        customer.status = request.form.get('status')
        customer.notes = request.form.get('notes')
        
        try:
            db.session.commit()
            flash('Customer updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating customer: {str(e)}', 'danger')
        return redirect(url_for('customers_list'))
    
    return render_template('add_customer.html', is_edit=True, customer=customer, today_date=date.today().isoformat())


@app.route('/customer/delete/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    try:
        db.session.delete(customer)
        db.session.commit()
        flash(f'Customer "{customer.name}" and their payments deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting customer: {str(e)}', 'danger')
    return redirect(url_for('customers_list'))


@app.route('/payment/record', methods=['GET', 'POST'])
def record_payment():
    customer_id_prefill_str = request.args.get('customer_id_prefill')
    customer_id_prefill = None
    if customer_id_prefill_str:
        try:
            customer_id_prefill = int(customer_id_prefill_str)
        except ValueError:
            flash("Invalid customer ID for prefill.", "warning")

    default_amount = None
    if customer_id_prefill:
        customer_for_default = Customer.query.get(customer_id_prefill)
        if customer_for_default:
            default_amount = customer_for_default.monthly_charge

    if request.method == 'POST':
        customer_id = request.form.get('customer_id', type=int)
        payment_date_str = request.form.get('payment_date')
        amount_paid_str = request.form.get('amount_paid')
        payment_method = request.form.get('payment_method')
        transaction_reference = request.form.get('transaction_reference')
        billing_period_month = request.form.get('billing_period_month', type=int)
        billing_period_year = request.form.get('billing_period_year', type=int)
        received_by = request.form.get('received_by')

        if not customer_id:
            flash('Customer is required.', 'danger')
        if not payment_date_str:
            flash('Payment date is required.', 'danger')
        if not billing_period_month:
            flash('Billing period month is required.', 'danger')
        if not billing_period_year:
            flash('Billing period year is required.', 'danger')

        customer = None
        if customer_id:
            customer = Customer.query.get(customer_id)
            if not customer:
                flash('Selected customer not found.', 'danger')
        
        pay_date = None
        if payment_date_str:
            try:
                pay_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                flash('Invalid payment date format.', 'danger')

        amount_paid_val = None
        if amount_paid_str and amount_paid_str.strip():
            try:
                amount_paid_val = float(amount_paid_str)
                if amount_paid_val <= 0:
                     flash('Amount paid must be a positive number.', 'danger')
                     amount_paid_val = None # invalidate
            except ValueError:
                flash('Invalid amount paid. Must be a number.', 'danger')
        elif customer: # If blank, use customer's monthly charge
            amount_paid_val = customer.monthly_charge
        else: # Amount blank and no customer selected (or invalid)
            flash('Amount paid is required or customer must be selected for default.', 'danger')


        if '_flashes' in session:
            # If any errors, re-render. Get all customers for the dropdown.
            all_customers_for_form = Customer.query.order_by(Customer.name).all()
            now = datetime.now()
            return render_template('record_payment.html',
                                   customers=all_customers_for_form,
                                   customer_id_prefill=customer_id, # Use submitted customer_id
                                   today_date=date.today().isoformat(),
                                   default_amount=amount_paid_str, # Pass back what was typed or default
                                   billing_months=BILLING_MONTHS,
                                   current_month=billing_period_month or now.month,
                                   billing_years=BILLING_YEARS,
                                   current_year=billing_period_year or now.year,
                                   # Pass other form values too if needed for repopulation
                                   form_values=request.form 
                                   )

        # Check for duplicate payment for the same billing period (optional based on business logic)
        existing_payment = Payment.query.filter_by(
            customer_id=customer_id,
            billing_period_month=billing_period_month,
            billing_period_year=billing_period_year
        ).first()

        if existing_payment:
            flash(f'Warning: A payment for {customer.name} for {get_month_name(billing_period_month)} {billing_period_year} already exists. Proceeding to add new payment.', 'warning')
            # If strictly one payment per period, this should be an error and redirect.
            # For this example, we'll allow it with a warning.

        new_payment = Payment(
            customer_id=customer_id,
            payment_date=pay_date,
            amount_paid=amount_paid_val,
            payment_method=payment_method,
            transaction_reference=transaction_reference if payment_method == 'Online' else None,
            billing_period_month=billing_period_month,
            billing_period_year=billing_period_year,
            received_by=received_by
        )
        db.session.add(new_payment)
        try:
            db.session.commit()
            flash('Payment recorded successfully!', 'success')
            return redirect(url_for('payments_log')) 
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording payment: {str(e)}', 'danger')
            # Fall through to re-render form
        
    all_customers = Customer.query.order_by(Customer.name).all()
    now = datetime.now()
    return render_template('record_payment.html',
                           customers=all_customers,
                           customer_id_prefill=customer_id_prefill,
                           today_date=date.today().isoformat(),
                           default_amount=default_amount,
                           billing_months=BILLING_MONTHS,
                           current_month=now.month,
                           billing_years=BILLING_YEARS,
                           current_year=now.year,
                           form_values=request.form if request.method == 'POST' else None)


@app.route('/payments_log')
def payments_log():
    page = request.args.get('page', 1, type=int)
    search_customer_name = request.args.get('customer_name', '').strip()
    
    query = Payment.query.join(Customer).order_by(Payment.payment_date.desc(), Payment.id.desc())
    
    if search_customer_name:
        search_like = f"%{search_customer_name}%"
        query = query.filter(Customer.name.ilike(search_like))
        
    payments_pagination = query.paginate(page=page, per_page=15) 
    
    return render_template('payments_log.html',
                           payments=payments_pagination,
                           search_customer_name=search_customer_name)

@app.route('/reports')
def reports_page():
    return render_template('reports.html', report_type=None, today_date=date.today().isoformat())

@app.route('/reports/outstanding_payments', methods=['GET'])
def outstanding_payments_report():
    now = datetime.now()
    report_month_str = request.args.get('month')
    report_year_str = request.args.get('year')

    report_month = now.month
    if report_month_str:
        try: report_month = int(report_month_str)
        except ValueError: flash("Invalid month selected, defaulting to current.", "warning")
    
    report_year = now.year
    if report_year_str:
        try: report_year = int(report_year_str)
        except ValueError: flash("Invalid year selected, defaulting to current.", "warning")


    selected_month_name = get_month_name(report_month)

    paid_customer_ids_subquery = db.session.query(Payment.customer_id).filter(
        Payment.billing_period_month == report_month,
        Payment.billing_period_year == report_year
    ).distinct().subquery() # .distinct() is important

    outstanding_customers_query = Customer.query.filter(
        Customer.status == 'Active',
        Customer.id.notin_(paid_customer_ids_subquery)
    )
    
    # Handle the case where form is just loaded vs. submitted
    # If month and year are explicitly passed (form submitted), then query.
    # Otherwise, show empty or default. The template shows a form first.
    outstanding_customers = []
    if request.args.get('month') and request.args.get('year'): # Check if form was submitted
        outstanding_customers = outstanding_customers_query.order_by(Customer.name).all()
    
    return render_template('reports.html',
                           report_type='outstanding',
                           selected_month_name=selected_month_name,
                           report_year=report_year,
                           billing_months=BILLING_MONTHS,
                           report_month=report_month, 
                           billing_years=BILLING_YEARS,
                           outstanding_customers=outstanding_customers,
                           today_date=date.today().isoformat())


@app.route('/reports/collections', methods=['GET'])
def collections_report():
    today_str = date.today().isoformat()
    start_date_str = request.args.get('start_date') 
    end_date_str = request.args.get('end_date')

    collections_data = []
    total_cash = 0
    total_online = 0
    grand_total = 0
    
    s_date, e_date = None, None
    
    # Only process if the form was submitted (i.e., dates are present in args)
    form_submitted = bool(start_date_str and end_date_str)

    if form_submitted:
        try:
            s_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError): # Added TypeError for None
            flash('Invalid start date format.', 'warning')
            form_submitted = False # Invalidate submission
        try:
            e_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError): # Added TypeError for None
            flash('Invalid end date format.', 'warning')
            form_submitted = False # Invalidate submission
    
        if form_submitted and s_date and e_date:
            if s_date > e_date:
                flash('Start date cannot be after end date.', 'warning')
            else:
                query = Payment.query.filter(
                    Payment.payment_date >= s_date,
                    Payment.payment_date <= e_date
                ).order_by(Payment.payment_date.asc(), Payment.id.asc())
                
                collections_data = query.all()

                for p in collections_data:
                    if p.payment_method == 'Cash':
                        total_cash += p.amount_paid
                    elif p.payment_method == 'Online':
                        total_online += p.amount_paid
                grand_total = total_cash + total_online
    
    return render_template('reports.html',
                           report_type='collections',
                           start_date=start_date_str, 
                           end_date=end_date_str,    
                           today_date=today_str,     
                           collections=collections_data,
                           total_cash=total_cash,
                           total_online=total_online,
                           grand_total=grand_total,
                           # For template conditional: {% if start_date and end_date %}
                           # Ensure these are only non-None if form was successfully processed
                           _form_submitted_and_valid=form_submitted and s_date and e_date 
                           )


# --- CLI command to create DB ---
@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    db.create_all()
    print('Initialized the database.')

# --- Flask Session Access (Needed for _flashes check) ---
from flask import session

# --- Main Execution ---
if __name__ == '__main__':
    db_path = os.path.join(BASE_DIR, "cable_app.db")
    if not os.path.exists(db_path):
        with app.app_context():
            print(f"Database not found at {db_path}. Creating tables...")
            db.create_all()
            print("Database tables created.")
    app.run(debug=True)
