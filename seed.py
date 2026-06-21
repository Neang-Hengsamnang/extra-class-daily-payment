from app import create_app
from extensions import db
from models import User, Course

app = create_app()

with app.app_context():
    db.create_all()

    # Seed admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')  # Change immediately after first login
        db.session.add(admin)

    # Seed staff user if not exists
    if not User.query.filter_by(username='staff').first():
        staff = User(username='staff', role='staff')
        staff.set_password('staff123')
        db.session.add(staff)

    # Seed default courses
    if not Course.query.first():
        db.session.add(Course(name='រៀនអង់គ្លេស', daily_fee=1000.0))
        db.session.add(Course(name='រៀនកុំព្យូទ័រ', daily_fee=1500.0))
        # Add more if needed

    db.session.commit()
    print("Database seeded successfully.")