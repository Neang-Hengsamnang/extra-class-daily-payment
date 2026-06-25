import os
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Student, Course, Payment, PaymentCourse
from datetime import date
from export_google_sheets import create_monthly_payment_sheet
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_bp = Blueprint('api', __name__)


@api_bp.route('/students')
@login_required
def get_student_list():
    """Return all active students for the Select Student dropdown."""
    students = Student.query.filter_by(is_active=True).order_by(Student.full_name).all()
    return jsonify({
        'students': [
            {'id': s.id, 'name': s.full_name}
            for s in students
        ]
    })


@api_bp.route('/student/<string:student_id>')
@login_required
def get_student_info(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    if not student.is_active:
        return jsonify({'error': 'Student is not active'}), 400

    all_courses = Course.query.all()
    courses_data = []
    for c in all_courses:
        courses_data.append({
            'id': c.id,
            'name': c.name,
            'fee': c.daily_fee,
            'is_default': c.id == student.default_course_id
        })

    return jsonify({
        'student': {
            'id': student.id,
            'name': student.full_name,
            'gender': student.gender,
            'grade_level': student.grade_level,
            'default_course_id': student.default_course_id,
            'courses': courses_data
        }
    })


@api_bp.route('/today-record/<string:student_id>')
@login_required
def get_today_record(student_id):
    """Check if student has a record for today and return it for modification."""
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    today_record = Payment.query.filter_by(
        student_id=student_id,
        date=date.today()
    ).first()

    if not today_record:
        return jsonify({'has_record': False})

    courses_list = [
        {
            'id': pc.course_id,
            'name': pc.course.name,
            'fee': pc.course.daily_fee
        }
        for pc in today_record.courses
    ]

    return jsonify({
        'has_record': True,
        'record': {
            'id': today_record.id,
            'student_id': today_record.student_id,
            'date': today_record.date.isoformat(),
            'is_paid': today_record.is_paid,
            'total_amount': today_record.total_amount,
            'courses': courses_list,
            'recorded_by': today_record.recorded_by_user.username if today_record.recorded_by_user else 'Unknown'
        }
    })


@api_bp.route('/unpaid-tabs')
@login_required
def get_unpaid_tabs():
    """Return all unpaid payment tabs (outstanding payments)."""
    unpaid_payments = Payment.query.filter_by(is_paid=False).all()
    
    tabs_data = []
    for p in unpaid_payments:
        courses_list = [pc.course.name for pc in p.courses]
        tabs_data.append({
            'id': p.id,
            'student_id': p.student.id,
            'student_name': p.student.full_name,
            'date': p.date.isoformat(),
            'courses': courses_list,
            'total_amount': p.total_amount,
            'recorded_by': p.recorded_by_user.username if p.recorded_by_user else 'Unknown'
        })
    
    return jsonify({
        'total_tabs': len(tabs_data),
        'total_outstanding': sum(p.total_amount for p in unpaid_payments),
        'tabs': tabs_data
    })


@api_bp.route('/record_payment', methods=['POST'])
@login_required
def record_payment():
    data = request.get_json()
    student_id = data.get('student_id')
    course_ids = data.get('course_ids', [])
    is_paid = not data.get('tabs', False)

    if not student_id or not course_ids:
        return jsonify({'error': 'Missing data'}), 400

    student = Student.query.get(student_id)
    if not student or not student.is_active:
        return jsonify({'error': 'Invalid student'}), 400

    courses = Course.query.filter(Course.id.in_(course_ids)).all()
    if len(courses) != len(course_ids):
        return jsonify({'error': 'Invalid course selection'}), 400

    total = sum(c.daily_fee for c in courses)

    payment = Payment(
        student_id=student.id,
        date=date.today(),
        is_paid=is_paid,
        total_amount=total,
        recorded_by=current_user.id
    )
    db.session.add(payment)
    db.session.flush()

    for c in courses:
        pc = PaymentCourse(payment_id=payment.id, course_id=c.id)
        db.session.add(pc)

    db.session.commit()
    return jsonify({
        'success': True,
        'payment_id': payment.id,
        'total': total,
        'is_paid': is_paid
    })


@api_bp.route('/update_payment/<int:payment_id>', methods=['POST'])
@login_required
def update_payment(payment_id):
    """Update an existing payment record."""
    data = request.get_json()
    course_ids = data.get('course_ids', [])
    is_paid = not data.get('tabs', False)

    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Payment record not found'}), 404

    if payment.date != date.today():
        return jsonify({'error': 'Can only modify today\'s records'}), 400

    if not course_ids:
        return jsonify({'error': 'Must select at least one course'}), 400

    courses = Course.query.filter(Course.id.in_(course_ids)).all()
    if len(courses) != len(course_ids):
        return jsonify({'error': 'Invalid course selection'}), 400

    total = sum(c.daily_fee for c in courses)

    # Delete old course associations
    PaymentCourse.query.filter_by(payment_id=payment_id).delete()

    # Update payment
    payment.is_paid = is_paid
    payment.total_amount = total

    # Add new course associations
    for c in courses:
        pc = PaymentCourse(payment_id=payment_id, course_id=c.id)
        db.session.add(pc)

    db.session.commit()
    return jsonify({
        'success': True,
        'payment_id': payment.id,
        'total': total,
        'is_paid': is_paid
    })


@api_bp.route('/export-monthly-report', methods=['POST'])
@login_required
def export_monthly_report():
    """
    Export monthly payment report to Google Sheets.
    
    Request JSON:
    {
        'year': 2024,
        'month': 6,
        'spreadsheet_id': 'YourSpreadSheetID'
    }
    
    Returns:
        JSON with spreadsheet_id, spreadsheet_url, and status
    """
    data = request.get_json()
    year = data.get('year')
    month = data.get('month')
    custom_sheet_name = data.get('custom_sheet_name')
    spreadsheet_id =  os.getenv('SPREADSHEET_ID')
    
    if not year or not month:
        return jsonify({'error': 'Year and month are required'}), 400
    
    if not (1 <= month <= 12):
        return jsonify({'error': 'Month must be between 1 and 12'}), 400
    
    try:
        result = create_monthly_payment_sheet(year, month, custom_sheet_name, spreadsheet_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500