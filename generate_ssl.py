#!/usr/bin/env python3
"""
Generate self-signed SSL certificate for local network HTTPS
Works on Windows, Linux, macOS, Termux (Android), and other Unix-like systems
"""
import os
import socket
import subprocess
import sys
import platform
from pathlib import Path

def get_platform():
    """Detect the current platform"""
    system = platform.system().lower()
    
    # Termux detection (Android)
    if 'android' in system.lower() or 'termux' in os.environ.get('TERMUX_VERSION', '').lower():
        return 'termux'
    elif system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        return 'linux'
    else:
        return system

def find_openssl():
    """Find OpenSSL executable - works on all platforms including Termux"""
    
    platform_name = get_platform()
    
    # Common OpenSSL installation paths by platform
    paths = {
        'windows': [
            r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
            r"C:\Program Files\OpenSSL-Win32\bin\openssl.exe",
            r"C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe",
            r"C:\OpenSSL-Win64\bin\openssl.exe",
            r"C:\OpenSSL-Win32\bin\openssl.exe",
            r"C:\Program Files\Git\usr\bin\openssl.exe",
            r"C:\Program Files\Git\mingw64\bin\openssl.exe",
            r"C:\Program Files (x86)\Git\usr\bin\openssl.exe",
            r"C:\Strawberry\c\bin\openssl.exe",
        ],
        'termux': [
            '/data/data/com.termux/files/usr/bin/openssl',
            '/data/data/com.termux/files/usr/local/bin/openssl',
        ],
        'macos': [
            '/usr/bin/openssl',
            '/usr/local/bin/openssl',
            '/opt/homebrew/bin/openssl',  # Homebrew on Apple Silicon
            '/usr/local/opt/openssl/bin/openssl',
        ],
        'linux': [
            '/usr/bin/openssl',
            '/usr/local/bin/openssl',
            '/bin/openssl',
        ]
    }
    
    # Check platform-specific paths first
    if platform_name in paths:
        for path in paths[platform_name]:
            if os.path.exists(path):
                print(f"✓ Found OpenSSL at: {path}")
                return path
    
    # Try to find openssl in PATH
    try:
        # On Windows, we might need to use shell for PATH resolution
        if platform_name == 'windows':
            result = subprocess.run(
                ['openssl', 'version'], 
                capture_output=True, 
                text=True,
                shell=True
            )
        else:
            result = subprocess.run(
                ['openssl', 'version'], 
                capture_output=True, 
                text=True
            )
        
        if result.returncode == 0:
            print(f"✓ Found OpenSSL: {result.stdout.strip()}")
            return 'openssl'
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    return None

def install_openssl_guide():
    """Show installation guide for OpenSSL on different platforms"""
    platform_name = get_platform()
    
    print("\n" + "="*60)
    print("✗ OpenSSL NOT FOUND!")
    print("="*60)
    
    guides = {
        'windows': """
To install OpenSSL on Windows:

Option 1 (Recommended):
  Download from: https://slproweb.com/products/Win32OpenSSL.html
  Choose: 'Win64 OpenSSL v3.3.1' (or latest version)
  During installation, select 'Copy OpenSSL DLLs to Windows system directory'

Option 2 (If you have Git installed):
  Add Git's OpenSSL to PATH:
  C:\\Program Files\\Git\\mingw64\\bin
  or
  C:\\Program Files\\Git\\usr\\bin

Option 3 (Chocolatey):
  choco install openssl
""",
        'termux': """
To install OpenSSL on Termux:

  pkg update && pkg upgrade
  pkg install openssl

After installation, restart Termux and try again.
""",
        'macos': """
To install OpenSSL on macOS:

Option 1 (Homebrew):
  brew install openssl
  
  Then add to PATH:
  echo 'export PATH="/opt/homebrew/opt/openssl/bin:$PATH"' >> ~/.zshrc
  source ~/.zshrc

Option 2 (MacPorts):
  sudo port install openssl

Option 3 (From Apple):
  OpenSSL is usually pre-installed on macOS.
  Try: /usr/bin/openssl version
""",
        'linux': """
To install OpenSSL on Linux:

Debian/Ubuntu:
  sudo apt update
  sudo apt install openssl

Fedora/RHEL/CentOS:
  sudo dnf install openssl
  # or
  sudo yum install openssl

Arch Linux:
  sudo pacman -S openssl

Alpine Linux:
  apk add openssl

OpenWRT:
  opkg install openssl-util
"""
    }
    
    print(guides.get(platform_name, """
To install OpenSSL:

Please install OpenSSL using your system's package manager.
Visit: https://www.openssl.org/source/
"""))
    print("="*60)

def get_local_ip():
    """Get the local network IP address - works on all platforms"""
    try:
        # Try to connect to a public DNS server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (socket.error, OSError):
        # Fallback methods
        try:
            # Try using hostname
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip and not ip.startswith('127.'):
                return ip
        except:
            pass
        
        # Try getting all interfaces
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if ip and not ip.startswith('127.'):
                            return ip
        except ImportError:
            pass
        
        # Default fallback
        return "192.168.1.100"

def check_openssl_compatibility(openssl_path):
    """Check if OpenSSL supports required features"""
    try:
        if openssl_path == 'openssl':
            cmd = ['openssl', 'version']
        else:
            cmd = [openssl_path, 'version']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ OpenSSL version: {version}")
            
            # Check if it supports req command with -extensions
            test_cmd = ['openssl', 'req', '-help'] if openssl_path == 'openssl' else [openssl_path, 'req', '-help']
            test_result = subprocess.run(test_cmd, capture_output=True, text=True)
            if '-extensions' in test_result.stderr or '-extensions' in test_result.stdout:
                return True
            else:
                print("⚠ Warning: OpenSSL might not support extensions. Certificate may work but with limited features.")
                return True
        return False
    except:
        return False

def generate_self_signed_cert():
    """Generate self-signed SSL certificate - cross-platform"""
    
    # Find OpenSSL first
    openssl_path = find_openssl()
    
    if not openssl_path:
        install_openssl_guide()
        return
    
    # Check OpenSSL compatibility
    if not check_openssl_compatibility(openssl_path):
        print("\n⚠ Warning: OpenSSL may not be fully functional.")
        proceed = input("Continue anyway? (y/n): ").lower()
        if proceed != 'y':
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
    print(f"\nDetected platform: {get_platform().title()}")
    print(f"Detected local IP: {local_ip}")
    
    hostname = input(f"Enter hostname or IP (press Enter for {local_ip}): ").strip()
    if not hostname:
        hostname = local_ip
    
    # Additional SAN entries for common local names
    san_entries = []
    san_entries.append(f"DNS.1 = {hostname}")
    
    # Add common local names if they differ from hostname
    common_names = ['localhost', 'raspberrypi.local', 'homeassistant.local']
    counter = 2
    for name in common_names:
        if name != hostname:
            san_entries.append(f"DNS.{counter} = {name}")
            counter += 1
    
    # Add IP addresses
    san_entries.append(f"IP.1 = {local_ip}")
    san_entries.append("IP.2 = 127.0.0.1")
    
    # Add additional IPs if the user entered an IP
    if hostname != local_ip and hostname.replace('.', '').isdigit():
        san_entries.append(f"IP.{counter} = {hostname}")
    
    print(f"\nGenerating certificate for: {hostname}")
    print("This will be valid for 10 years.")
    
    # Create OpenSSL config
    config_file = ssl_dir / 'openssl.cnf'
    config_content = f"""
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no
default_bits = 2048

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
{chr(10).join(san_entries)}
"""
    
    # Write config file
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
    except IOError as e:
        print(f"\n✗ Error creating config file: {e}")
        sys.exit(1)
    
    try:
        platform_name = get_platform()
        use_shell = (platform_name == 'windows')
        
        # Determine command prefix
        if openssl_path != 'openssl':
            cmd_prefix = [openssl_path]
        else:
            cmd_prefix = ['openssl']
        
        # Generate private key
        print("\nGenerating private key...")
        gen_key_cmd = cmd_prefix + ['genrsa', '-out', str(key_file), '2048']
        subprocess.run(gen_key_cmd, check=True, capture_output=True, text=True, shell=use_shell)
        
        # Generate certificate
        print("Generating certificate...")
        gen_cert_cmd = cmd_prefix + [
            'req', '-new', '-x509', '-key', str(key_file), 
            '-out', str(cert_file), '-days', '3650', 
            '-config', str(config_file), '-extensions', 'v3_req'
        ]
        subprocess.run(gen_cert_cmd, check=True, capture_output=True, text=True, shell=use_shell)
        
        # Set proper permissions (Unix only)
        if platform_name in ['linux', 'macos', 'termux']:
            os.chmod(key_file, 0o600)
            os.chmod(cert_file, 0o644)
        
        # On Termux, show special instructions
        if platform_name == 'termux':
            print("\n" + "="*60)
            print("✓ SSL Certificate Generated Successfully on Termux!")
            print("="*60)
            print(f"\nCertificate: {cert_file}")
            print(f"Private Key:  {key_file}")
            print(f"\nYour app will be accessible at:")
            print(f"  https://localhost:5000")
            print(f"  https://{local_ip}:5000")
            print(f"\nIMPORTANT for Termux:")
            print(f"  - Make sure your phone is on the same network")
            print(f"  - You may need to run: termux-wifi-connectioninfo")
            print(f"  - If using hotspot, use: {local_ip}")
            print("="*60)
        else:
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
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating certificate: {e}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        
        # Provide platform-specific troubleshooting
        platform_name = get_platform()
        if platform_name == 'termux':
            print("\nTroubleshooting for Termux:")
            print("  1. Make sure OpenSSL is installed: pkg install openssl")
            print("  2. Check permissions: chmod 755 ~/storage")
            print("  3. Try running: termux-fix-shebang")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Clean up config file
        if config_file.exists():
            try:
                os.remove(config_file)
            except OSError:
                pass  # Ignore cleanup errors

def main():
    """Main entry point with platform information"""
    platform_name = get_platform()
    print(f"🖥️  Running on: {platform_name.title()}")
    
    # Check for Termux specific environment
    if platform_name == 'termux':
        try:
            import pkg_resources
            print("📱 Termux environment detected")
        except:
            pass
    
    generate_self_signed_cert()

if __name__ == '__main__':
    main()