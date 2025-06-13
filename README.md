# Customer Management System

A web-based customer management and payment collection dashboard designed primarily for cable operators, built with Flask (Python) and Bootstrap (HTML/CSS). This application streamlines the management of customers, tracks payments, generates reports, and provides actionable business insights.

#preview <img src="https://github.com/Gokul-dev-creator/Cable-pro/blob/main/static/images/preview.PNG">

## Features

- **Dashboard Overview**
  - Visual summary of total customers, active customers, outstanding payments, and collections for the day.
  - Quick actions for adding customers, recording payments, and accessing reports.

- **Customer Management**
  - Add, edit, and delete customer records.
  - Store customer details: name, phone number, address, plan details, monthly charge, set-top box number, connection date, and status (Active, Inactive, Suspended).
  - Each customer is uniquely associated with a set-top box number.

- **Payment Recording**
  - Record payments with details like amount, method (Cash/Online), billing period, and transaction reference.
  - Associate each payment to a customer and track who received it.

- **Payments Log**
  - Searchable and paginated log of all payments.
  - Filter by customer name.
  - Displays customer, set-top box number, date, amount paid, payment method, billing period, transaction reference, and received by.

- **Reports**
  - Outstanding Payments Report for a selected billing period (by month and year).
  - Collections Report for a selected date range, summarizing cash/online totals and listing individual payments.
  - Exportable and printable views for business accounting.

- **Modern UI**
  - Responsive Bootstrap interface with icons, navigation bar, and alert messages.
  - Uses Select2 for enhanced dropdowns.

## Installation

1. **Clone the repository**
   ```
   git clone https://github.com/Gokul-dev-creator/customer-management.git
   cd customer-management
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Set up the database**
   - The app uses Flask-SQLAlchemy and `psycopg2-binary` for PostgreSQL.
   - See `app.py` for database creation CLI commands.

4. **Run the application**
   ```
   flask run
   ```
   Or use gunicorn for production:
   ```
   gunicorn app:app
   ```

## Technologies Used

- Python (Flask, Flask-SQLAlchemy)
- HTML/CSS (Bootstrap, FontAwesome)
- JavaScript (jQuery, Select2)
- PostgreSQL (via psycopg2)

## Contributing

Feel free to fork and submit pull requests!

## License

MIT License
