# Customer Management System

A web-based customer management and payment collection dashboard designed primarily for cable operators, built with Flask (Python) and Bootstrap (HTML/CSS). This application streamlines the management of customers, tracks payments, generates reports, and provides actionable business insights.

# Preview 

<img src="https://github.com/Gokul-dev-creator/Cable-pro/blob/main/static/images/preview.PNG">

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

🛠️ Installation Guide ✅
Follow the steps below to install and run the Cable-pro web application on your local machine.
1. Clone the Repository
git clone https://github.com/Gokul-dev-creator/Cable-pro.git
cd Cable-pro

2. Create and Activate a Virtual Environment (Recommended)
# Create virtual environment
python -m venv venv

# Activate the virtual environment
# For Windows:
venv\Scripts\activate

# For macOS/Linux:
source venv/bin/activate

3.Install Python Dependencies
# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

4.Set Environment Variables for Flask
# On Windows
set FLASK_APP=app.py
set FLASK_ENV=development

# On macOS/Linux
export FLASK_APP=app.py
export FLASK_ENV=development

5.Initialize the Database
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()

6.Run the Flask Application
```bash
 flask run
```or
```bash
python app.py
```




7. Access the Web App
   Open your browser and go to:
http://127.0.0.1:5000



## Technologies Used

- Python (Flask, Flask-SQLAlchemy)
- HTML/CSS (Bootstrap, FontAwesome)
- JavaScript (jQuery, Select2)
- PostgreSQL (via psycopg2)



