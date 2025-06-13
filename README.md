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

Installation
Clone the repository
git clone https://github.com/Gokul-dev-creator/customer-management.git
cd customer-management
Use code with caution.
Bash
Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Use code with caution.
Bash
Install dependencies
pip install -r requirements.txt
Use code with caution.
Bash
Configure the database connection
This application requires a DATABASE_URL environment variable to connect to your PostgreSQL database. You can set this in your shell or use a .env file.
Create a file named .env in the project root and add the following line, replacing the values with your actual database credentials:
DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DATABASE_NAME"
Use code with caution.
Example: DATABASE_URL="postgresql://postgres:mysecretpassword@localhost:5432/customers_db"
Set up the database schema
The application includes a Flask CLI command to initialize the database tables. Run the following command:
flask init-db
Use code with caution.
Bash
(Note: Check app.py if a different custom command is used for database creation.)
Running the Application
You can run the app using the built-in Flask development server or a production-ready server like Gunicorn.
For Development:
flask run
Use code with caution.
Bash
The application will be available at http://127.0.0.1:5000.
For Production (with Gunicorn):
gunicorn --workers 3 app:app
Use code with caution.
Bash
Contributing
Contributions are welcome! Please feel free to open an issue or submit a pull request.
License
This project is licensed under the MIT License - see the LICENSE file for details.
31.2s
Start typing a prompt


## Technologies Used

- Python (Flask, Flask-SQLAlchemy)
- HTML/CSS (Bootstrap, FontAwesome)
- JavaScript (jQuery, Select2)
- PostgreSQL (via psycopg2)

## Contributing

Feel free to fork and submit pull requests!

## License

MIT License


https://chatgpt.com/share/684b96aa-0574-8000-a20a-975b896b36bf
