#!/usr/bin/env python3
"""
Generate self-signed SSL certificate for local network HTTPS
Works on Windows, Linux, and macOS
"""
import os
import socket
import subprocess
import sys
from pathlib import Path

def find_openssl():
    """Find OpenSSL executable - especially important on Windows"""
    
    # Common OpenSSL installation paths on Windows
    windows_paths = [
        r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
        r"C:\Program Files\OpenSSL-Win32\bin\openssl.exe",
        r"C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe",
        r"C:\OpenSSL-Win64\bin\openssl.exe",
        r"C:\OpenSSL-Win32\bin\openssl.exe",
        # Common Git paths (Git includes OpenSSL)
        r"C:\Program Files\Git\usr\bin\openssl.exe",
        r"C:\Program Files\Git\mingw64\bin\openssl.exe",
        r"C:\Program Files (x86)\Git\usr\bin\openssl.exe",
        r"C:\Program Files\Git\mingw64\bin\openssl.exe",
        # Strawberry Perl (includes OpenSSL)
        r"C:\Strawberry\c\bin\openssl.exe",
    ]
    
    # On Windows, check specific paths first
    if sys.platform == 'win32':
        for path in windows_paths:
            if os.path.exists(path):
                print(f"✓ Found OpenSSL at: {path}")
                return path
    
    # Try to find openssl in PATH
    try:
        result = subprocess.run(
            ['openssl', 'version'], 
            capture_output=True, 
            text=True,
            shell=(sys.platform == 'win32')  # Use shell on Windows
        )
        if result.returncode == 0:
            print(f"✓ Found OpenSSL: {result.stdout.strip()}")
            return 'openssl'
    except:
        pass
    
    return None

def get_local_ip():
    """Get the local network IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "192.168.1.100"

def generate_self_signed_cert():
    """Generate self-signed SSL certificate"""
    
    # Find OpenSSL first
    openssl_path = find_openssl()
    
    if not openssl_path:
        print("\n" + "="*60)
        print("✗ OpenSSL NOT FOUND!")
        print("="*60)
        print("\nTo install OpenSSL on Windows:")
        print("\nOption 1 (Recommended):")
        print("  Download from: https://slproweb.com/products/Win32OpenSSL.html")
        print("  Choose: 'Win64 OpenSSL v3.3.1' (or latest version)")
        print("  During installation, select 'Copy OpenSSL DLLs to Windows system directory'")
        print("\nOption 2 (If you have Git installed):")
        print("  Add Git's OpenSSL to PATH:")
        print("  C:\\Program Files\\Git\\mingw64\\bin")
        print("  or")
        print("  C:\\Program Files\\Git\\usr\\bin")
        print("\nOption 3 (Chocolatey):")
        print("  choco install openssl")
        print("="*60)
        return
    
    # Get the directory where this script is located
    base_dir = Path(__file__).parent
    ssl_dir = base_dir / 'ssl'
    ssl_dir.mkdir(exist_ok=True)
    
    cert_file = ssl_dir / 'cert.pem'
    key_file = ssl_dir / 'key.pem'
    
    # Check if certificates already exist
    if cert_file.exists() and key_file.exists():
        response = input("SSL certificates already exist. Overwrite? (y/n): ").lower()
        if response != 'y':
            print("Keeping existing certificates.")
            return
    
    # Get IP and hostname
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("Generate Self-Signed SSL Certificate for HTTPS")
    print("="*60)
    print(f"\nDetected local IP: {local_ip}")
    
    hostname = input(f"Enter hostname or IP (press Enter for {local_ip}): ").strip()
    if not hostname:
        hostname = local_ip
    
    print(f"\nGenerating certificate for: {hostname}")
    print("This will be valid for 10 years.")
    
    # Create OpenSSL config
    config_file = ssl_dir / 'openssl.cnf'
    with open(config_file, 'w') as f:
        f.write(f"""
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = School
OU = IT
CN = {hostname}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = {hostname}
DNS.2 = raspberrypi.local
DNS.3 = localhost
IP.1 = {local_ip}
IP.2 = 127.0.0.1
""")
    
    try:
        # Generate private key
        print("\nGenerating private key...")
        if sys.platform == 'win32' and openssl_path != 'openssl':
            # Use full path on Windows
            subprocess.run([openssl_path, 'genrsa', '-out', str(key_file), '2048'], 
                         check=True, capture_output=True)
        else:
            subprocess.run(['openssl', 'genrsa', '-out', str(key_file), '2048'], 
                         check=True, capture_output=True, shell=(sys.platform == 'win32'))
        
        # Generate certificate
        print("Generating certificate...")
        if sys.platform == 'win32' and openssl_path != 'openssl':
            subprocess.run([openssl_path, 'req', '-new', '-x509', '-key', str(key_file), 
                          '-out', str(cert_file), '-days', '3650', '-config', str(config_file),
                          '-extensions', 'v3_req'], check=True, capture_output=True)
        else:
            subprocess.run(['openssl', 'req', '-new', '-x509', '-key', str(key_file), 
                          '-out', str(cert_file), '-days', '3650', '-config', str(config_file),
                          '-extensions', 'v3_req'], check=True, capture_output=True, 
                          shell=(sys.platform == 'win32'))
        
        # Set proper permissions (Unix only)
        if sys.platform != 'win32':
            os.chmod(key_file, 0o600)
            os.chmod(cert_file, 0o644)
        
        print("\n" + "="*60)
        print("✓ SSL Certificate Generated Successfully!")
        print("="*60)
        print(f"\nCertificate: {cert_file}")
        print(f"Private Key:  {key_file}")
        print(f"\nYour app will be accessible at:")
        print(f"  https://localhost:5000")
        print(f"  https://{local_ip}:5000")
        print(f"\nIMPORTANT: Accept the certificate warning on your phone:")
        print(f"  1. Open https://{local_ip}:5000 on your phone")
        print(f"  2. Tap 'Advanced' or 'Show Details'")
        print(f"  3. Tap 'Proceed anyway' or 'Visit This Website'")
        print("="*60)
        
        # Clean up config file
        os.remove(config_file)
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating certificate: {e}")
        print(f"STDERR: {e.stderr.decode() if e.stderr else 'No error output'}")
        sys.exit(1)

if __name__ == '__main__':
    generate_self_signed_cert()