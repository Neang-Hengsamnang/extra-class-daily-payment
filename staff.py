from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Payment, Student, Course
from datetime import date, datetime
from functools import wraps

staff_bp = Blueprint('staff', __name__)

def staff_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'staff' and current_user.role != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@staff_bp.route('/scan')
@staff_required
def scan():
    return render_template('staff/scan.html')

@staff_bp.route('/today')
@staff_required
def today_payments():
    today = date.today()
    payments = db.session.query(Payment).join(Student, Payment.student_id == Student.id).\
        filter(Payment.date == today).order_by(Student.grade_level.asc(), Payment.id.desc()).all()
    return render_template('staff/today_payments.html', payments=payments)

@staff_bp.route('/unpaid-tabs')
@staff_required
def unpaid_tabs():
    """View all outstanding payment tabs."""
    unpaid_payments = Payment.query.filter_by(is_paid=False).order_by(Payment.date.desc()).all()
    total_outstanding = sum(p.total_amount for p in unpaid_payments)
    return render_template('staff/unpaid_tabs.html', payments=unpaid_payments, total_outstanding=total_outstanding)

@staff_bp.route('/payment/<int:payment_id>/pay-off', methods=['POST'])
@staff_required
def pay_off_tab(payment_id):
    """Mark a payment tab as paid."""
    payment = Payment.query.get_or_404(payment_id)
    if payment.is_paid:
        flash(f'កំណត់ត្រាលេខ {payment_id} បានកត់ត្រាបង់ប្រាក់រួចកាលពីមុនហើយ។', 'warning')
    else:
        payment.is_paid = True
        db.session.commit()
        flash(f'ការបង់ប្រាក់ចំនួន ៛{payment.total_amount:,.0f} របស់ {payment.student.full_name} បានកត់ត្រាជោគជ័យ', 'success')
    return redirect(url_for('staff.unpaid_tabs'))

@staff_bp.route('/payment/<int:payment_id>/delete', methods=['POST'])
@staff_required
def delete_payment(payment_id):
    """Delete a duplicate or mistaken payment record."""
    payment = Payment.query.get_or_404(payment_id)
    student_name = payment.student.full_name
    amount = payment.total_amount
    db.session.delete(payment)
    db.session.commit()
    flash(f'ការបង់ប្រាក់ ៛{amount:,.0f}៛ របស់សិស្ស {student_name} ត្រូវបានលុបដោយជោគជ័យ។', 'success')
    return redirect(url_for('staff.today_payments'))

@staff_bp.route('/daily_report', methods=['GET', 'POST'])
@staff_required
def daily_report():
    """Display daily report for staff and admins."""
    selected_date = date.today()
    if request.method == 'POST':
        date_str = request.form.get('report_date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    active_students = Student.query.filter_by(is_active=True).all()
    payments_today = Payment.query.filter_by(date=selected_date).all()
    paid_dict = {p.student_id: p for p in payments_today}

    present_count = len(payments_today)
    total_active = len(active_students)
    absent_count = total_active - present_count

    revenue_collected = sum(p.total_amount for p in payments_today if p.is_paid)
    tabs_outstanding = sum(p.total_amount for p in payments_today if not p.is_paid)

    report_rows = []
    for s in active_students:
        payment = paid_dict.get(s.id)
        if payment:
            courses_taken = ', '.join([pc.course.name for pc in payment.courses])
            amount = f"៛{payment.total_amount:,.0f} {'(Paid)' if payment.is_paid else '(Tabs)'}"
            status = 'Present'
        else:
            courses_taken = '-'
            amount = '-'
            status = 'Absent'
        report_rows.append({
            'student': s,
            'status': status,
            'courses_taken': courses_taken,
            'amount': amount
        })

    return render_template('admin/daily_report.html',
                           report_rows=report_rows,
                           selected_date=selected_date,
                           total_active=total_active,
                           present_count=present_count,
                           absent_count=absent_count,
                           revenue_collected=revenue_collected,
                           tabs_outstanding=tabs_outstanding)