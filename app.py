import mysql
from flask import Flask, render_template, request, redirect, session, send_file
import random
import string
from captcha_generator import generate_captcha
import io

from db_config import get_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        captcha_input = request.form.get('captcha_input')

        if (username == 'admin' and password == 'admin123' and
                captcha_input == session.get('captcha_text')):
            return redirect('/dashboard')
        else:
            error = "Invalid credentials or captcha"
            session['captcha_text'] = generate_captcha()
            return render_template('login.html', captcha=session['captcha_text'], error=error)

    session['captcha_text'] = generate_captcha()
    return render_template('login.html', captcha=session['captcha_text'])

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/department', methods=['GET', 'POST'])
def department():
    if request.method == 'POST':
        dept = request.form.get('department')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        client_code = request.form.get('client_code')
        txt_content = f"Department: {dept}\nFrom: {from_date}\nTo: {to_date}\nClient Code: {client_code}"
        return send_file(io.BytesIO(txt_content.encode()), mimetype='text/plain', as_attachment=True, download_name='department_data.txt')
    return render_template('department.html')

@app.route('/bank', methods=['GET', 'POST'])
def bank():
    if request.method == 'POST':
        bank = request.form.get('bank')
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        client_code = request.form.get('client_code')
        xml_content = f"<BankData><Bank>{bank}</Bank><From>{from_date}</From><To>{to_date}</To><ClientCode>{MPST98}</ClientCode></BankData>"
        return send_file(io.BytesIO(xml_content.encode()), mimetype='application/xml', as_attachment=True, download_name='bank_data.xml')
    return render_template('bank.html')

@app.route('/txn_enquiry', methods=['GET', 'POST'])
def txn_enquiry():
    result = None
    if request.method == 'POST':
        txn_type = request.form.get('txn_type')
        txn_id = request.form.get('txn_id')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Query by transaction ID
        if txn_type == "SabPaisa":
            cursor.execute("SELECT * FROM treasury_transactions WHERE sabpaisa_txn_id = %s", (txn_id,))
        elif txn_type == "Client":
            cursor.execute("SELECT * FROM treasury_transactions WHERE treasury_txn_id  = %s", (txn_id,))
        result = cursor.fetchone()
        print(result)

        cursor.close()
        conn.close()

    return render_template('txn_enquiry.html', result=result)


@app.route('/grn_enquiry', methods=['GET', 'POST'])
def grn_enquiry():
    result = None
    if request.method == 'POST':
        grn = request.form.get('grn_number')   # ✅ match form input
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM treasury_transactions WHERE merchant_reference_number = %s", (grn,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

    return render_template('grn_enquiry.html', result=result)

@app.route('/txn_history', methods=['GET', 'POST'])
def txn_history():
    result = None
    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        client_code = request.form.get('client_code')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # ✅ SQL Query
        query = """
            SELECT sabpaisa_txn_id, treasury_txn_id, merchant_reference_number, 
                   treasury_account_type, total_amount, payment_status, 
                   payment_mode, trans_complete_date
            FROM treasury_transactions
            WHERE client_code = %s
              AND DATE(trans_complete_date) BETWEEN %s AND %s
        """
        cursor.execute(query, (client_code, from_date, to_date))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

    return render_template('txn_history.html', result=result)



@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        client_code = request.form.get('client_code')
        excel_content = f"Date From: {from_date}\nDate To: {to_date}\nClient Code: {client_code}"
        return send_file(io.BytesIO(excel_content.encode()), mimetype='application/vnd.ms-excel', as_attachment=True, download_name='report.xls')
    return render_template('report.html')

@app.route('/refund_report', methods=['GET', 'POST'])
def refund_report():
    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
        client_code = request.form.get('client_code')

        # Sample content for Excel
        excel_content = (
            f"Refund Report\n"
            f"From Date: {from_date}\n"
            f"To Date: {to_date}\n"
            f"Client Code: {client_code}\n"
        )

        return send_file(
            io.BytesIO(excel_content.encode()),
            mimetype='application/vnd.ms-excel',
            as_attachment=True,
            download_name='refund_report.xls'
        )
    return render_template('refund_report.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
