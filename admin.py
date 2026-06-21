import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Student, Course, Payment, PaymentCourse, User
from datetime import date, datetime, timedelta
import qrcode
from io import BytesIO
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

# ---- Student Management ----
@admin_bp.route('/students')
@admin_required
def students():
    all_students = Student.query.order_by(Student.id).all()
    courses = Course.query.all()
    return render_template('admin/students.html', students=all_students, courses=courses)

@admin_bp.route('/student/add', methods=['POST'])
@admin_required
def add_student():
    full_name = request.form.get('full_name')
    default_course_id = request.form.get('default_course_id')
    if not full_name or not default_course_id:
        flash('ឈ្មោះពេញលេញ និងវគ្គសិក្សាលំនាំដែលត្រូវការ។', 'danger')
        return redirect(url_for('admin.students'))

    # Generate new student ID
    last = Student.query.order_by(Student.id.desc()).first()
    if last:
        num = int(last.id[1:]) + 1
    else:
        num = 1
    student_id = f"S{num:04d}"

    # Generate QR code
    qr = qrcode.make(student_id)
    qr_dir = os.path.join(current_app.static_folder, 'qrcodes')
    
    # Handle case where qrcodes exists as a file instead of directory
    if os.path.isfile(qr_dir):
        os.remove(qr_dir)
    
    os.makedirs(qr_dir, exist_ok=True)
    filename = f"{student_id}.png"
    qr.save(os.path.join(qr_dir, filename))

    gender = request.form.get('gender')
    grade_level = request.form.get('grade_level')
    student = Student(
        id=student_id,
        full_name=full_name,
        gender=gender,
        grade_level=grade_level,
        default_course_id=int(default_course_id),
        qr_code_filename=filename,
        registration_date=date.today()
    )
    db.session.add(student)
    db.session.commit()
    flash(f'រៀងរាល់សិស្ស {full_name} បានបន្ថែមដោយ ID {student_id}.', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/edit/<string:id>', methods=['POST'])
@admin_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    student.full_name = request.form.get('full_name', student.full_name)
    student.gender = request.form.get('gender', student.gender)
    student.grade_level = request.form.get('grade_level', student.grade_level)
    student.default_course_id = int(request.form.get('default_course_id', student.default_course_id))
    # Fix: Check if checkbox is in form (means it was checked)
    student.is_active = 'is_active' in request.form and request.form.get('is_active') == 'true'
    db.session.commit()
    flash('សិស្សបានធ្វើបច្ចុប្បន្នភាព។', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/deactivate/<string:id>')
@admin_required
def deactivate_student(id):
    student = Student.query.get_or_404(id)
    student.is_active = False
    db.session.commit()
    flash(f'សិស្ស {student.full_name} បានបិទ។', 'info')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/activate/<string:id>')
@admin_required
def activate_student(id):
    student = Student.query.get_or_404(id)
    student.is_active = True
    db.session.commit()
    flash(f'សិស្ស {student.full_name} បានធ្វើឱ្យសកម្ម។', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/delete/<string:id>')
@admin_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    student_name = student.full_name
    db.session.delete(student)
    db.session.commit()
    flash(f'សិស្ស {student_name} បានលុប។', 'success')
    return redirect(url_for('admin.students'))

# ---- Course Management ----
@admin_bp.route('/courses')
@admin_required
def courses():
    all_courses = Course.query.all()
    return render_template('admin/courses.html', courses=all_courses)

@admin_bp.route('/course/add', methods=['POST'])
@admin_required
def add_course():
    name = request.form.get('name')
    fee = request.form.get('daily_fee')
    if not name or fee is None:
        flash('ឈ្មោះវគ្គសិក្សា និងតម្លៃ ត្រូវតែមាន!', 'danger')
        return redirect(url_for('admin.courses'))
    course = Course(name=name, daily_fee=float(fee))
    db.session.add(course)
    db.session.commit()
    flash('វគ្គសិក្សាបានបន្ថែម។', 'success')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/course/edit/<int:id>', methods=['POST'])
@admin_required
def edit_course(id):
    course = Course.query.get_or_404(id)
    course.name = request.form.get('name', course.name)
    course.daily_fee = float(request.form.get('daily_fee', course.daily_fee))
    db.session.commit()
    flash('វគ្គសិក្សាបានធ្វើបច្ចុប្បន្នភាព។', 'success')
    return redirect(url_for('admin.courses'))

@admin_bp.route('/course/delete/<int:id>')
@admin_required
def delete_course(id):
    course = Course.query.get_or_404(id)
    course_name = course.name
    db.session.delete(course)
    db.session.commit()
    flash(f'វគ្គសិក្សា {course_name} បានលុប។', 'success')
    return redirect(url_for('admin.courses'))

# ---- Daily Report ----
@admin_bp.route('/daily_report', methods=['GET', 'POST'])
@admin_required
def daily_report():
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
            amount = f"៛{payment.total_amount:.0f} {'(Paid)' if payment.is_paid else '(Tabs)'}"
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

# ---- Monthly Report ----
@admin_bp.route('/monthly_report', methods=['GET'])
@admin_required
def monthly_report():
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', date.today().month, type=int)

    # All active students at the time of report (simplified)
    active_count = Student.query.filter_by(is_active=True).count()

    # Query all payments in that month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    payments = Payment.query.filter(Payment.date >= start_date, Payment.date < end_date).all()

    # Daily revenue
    daily_revenue = {}
    daily_present = {}
    for p in payments:
        d = p.date
        daily_revenue[d] = daily_revenue.get(d, 0) + p.total_amount
        daily_present[d] = daily_present.get(d, 0) + 1

    # Build complete day series
    import calendar
    days_in_month = calendar.monthrange(year, month)[1]
    labels = [f"{year}-{month:02d}-{d:02d}" for d in range(1, days_in_month+1)]
    revenue_series = []
    present_series = []
    absent_series = []
    for d in range(1, days_in_month+1):
        dt = date(year, month, d)
        rev = daily_revenue.get(dt, 0)
        pres = daily_present.get(dt, 0)
        revenue_series.append(round(rev, 2))
        present_series.append(pres)
        absent_series.append(active_count - pres)

    # Revenue by course
    course_revenue = {}
    for p in payments:
        for pc in p.courses:
            cname = pc.course.name
            course_revenue[cname] = course_revenue.get(cname, 0) + pc.course.daily_fee

    # Paid vs Tabs pie
    total_paid = sum(p.total_amount for p in payments if p.is_paid)
    total_tabs = sum(p.total_amount for p in payments if not p.is_paid)

    # Summary stats
    total_revenue = total_paid + total_tabs
    average_attendance = round(sum(present_series) / days_in_month, 1) if days_in_month else 0

    return render_template('admin/monthly_report.html',
                           year=year, month=month,
                           labels=labels,
                           revenue_series=revenue_series,
                           present_series=present_series,
                           absent_series=absent_series,
                           course_revenue_keys=list(course_revenue.keys()),
                           course_revenue_values=list(course_revenue.values()),
                           total_paid=total_paid,
                           total_tabs=total_tabs,
                           total_revenue=total_revenue,
                           average_attendance=average_attendance)

# ---- User Management (Admin can add staff) ----
@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/user/add', methods=['POST'])
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    if not username or not password or role not in ('admin', 'staff'):
        flash('All fields required.', 'danger')
        return redirect(url_for('admin.users'))
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin.users'))
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash('User added.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/user/edit/<int:id>', methods=['POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if not username or role not in ('admin', 'staff'):
        flash('All fields required.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Check if new username already exists (and it's not the same user)
    if username != user.username and User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.username = username
    user.role = role
    
    # Update password only if provided
    if password:
        user.set_password(password)
    
    db.session.commit()
    flash('User updated successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/user/delete/<int:id>')
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # Prevent deleting the current user
    if user.id == current_user.id:
        flash('Cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} deleted.', 'success')
    return redirect(url_for('admin.users'))