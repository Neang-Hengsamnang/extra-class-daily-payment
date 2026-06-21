import os
import ssl
from flask import Flask
from extensions import db, login_manager, csrf

def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-to-a-random-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'checkin.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REMEMBER_COOKIE_DURATION'] = 365 * 24 * 60 * 60  # 1 year

    # HTTPS/SSL Configuration (only if SSL certificates exist)
    ssl_dir = os.path.join(basedir, 'ssl')
    ssl_cert = os.path.join(ssl_dir, 'cert.pem')
    ssl_key = os.path.join(ssl_dir, 'key.pem')
    
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PREFERRED_URL_SCHEME'] = 'https'
        print("✓ SSL certificates found - HTTPS mode enabled")
    else:
        app.config['PREFERRED_URL_SCHEME'] = 'http'
        print("ℹ SSL certificates not found - running in HTTP mode")
        print("  Run 'python generate_ssl.py' to create certificates for HTTPS")

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)

    # Import models and set up user loader
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from staff import staff_bp
    app.register_blueprint(staff_bp, url_prefix='/staff')

    from api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    csrf.exempt(api_bp)  # API handles CSRF via X-CSRFToken header

    # Root route - redirect to login or dashboard based on auth status
    from flask import redirect, url_for
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('staff.scan'))
        return redirect(url_for('auth.login'))

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        # HSTS only if using HTTPS
        if app.config['PREFERRED_URL_SCHEME'] == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Allow camera access for QR scanning
        response.headers['Permissions-Policy'] = 'camera=(self), microphone=()'
        response.headers['Feature-Policy'] = "camera 'self'"
        
        return response

    # Create tables inside app context
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Check if SSL certificates exist
    ssl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl')
    ssl_cert = os.path.join(ssl_dir, 'cert.pem')
    ssl_key = os.path.join(ssl_dir, 'key.pem')
    
    if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        # Run with HTTPS
        print("\n" + "="*60)
        print("Starting server with HTTPS")
        print("="*60)
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(ssl_cert, ssl_key)
        
        # Use port 443 for HTTPS (requires root/sudo on Linux)
        # Use port 5000 for development/testing
        import platform
        if platform.system() == 'Windows':
            # Windows doesn't need special permissions for high ports
            port = 443
        else:
            # On Linux/Raspberry Pi, check if running as root
            import getpass
            if getpass.getuser() == 'root':
                port = 443
            else:
                port = 5000
                print("ℹ Not running as root - using port 5000 for HTTPS")
                print("  Run with sudo to use port 443")
        
        print(f"Server: https://0.0.0.0:{port}")
        
        # Get local IP
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"Local:  https://{local_ip}:{port}")
            print(f"Mobile: https://{local_ip}:{port}")
        except:
            pass
        
        print("="*60 + "\n")
        
        app.run(host='0.0.0.0', port=port, ssl_context=context, debug=False)
    else:
        # Run without HTTPS
        print("\n" + "="*60)
        print("Starting server without HTTPS (HTTP mode)")
        print("="*60)
        print("WARNING: Camera access requires HTTPS!")
        print("Run 'python generate_ssl.py' to create SSL certificates")
        print("="*60 + "\n")
        
        app.run(host='0.0.0.0', port=5000, debug=False)