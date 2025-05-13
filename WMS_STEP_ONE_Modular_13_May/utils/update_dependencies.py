#!/usr/bin/env python3
"""
Dependency Management Script

This script helps manage dependencies for the WMS API project.
It provides commands to check for outdated packages, security vulnerabilities,
and update dependencies safely.

Usage:
    python update_dependencies.py check      # Check for outdated packages
    python update_dependencies.py audit      # Check for security vulnerabilities
    python update_dependencies.py update     # Update dependencies with confirmation
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def check_outdated_packages():
    """Check for outdated packages using pip-tools"""
    print("\n📦 Checking for outdated packages...")
    result = subprocess.run(
        ["pip-compile", "--upgrade", "--dry-run", "requirements.txt"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Error checking outdated packages: {result.stderr}")
        return False
    
    print(result.stdout)
    return True

def audit_security():
    """Check for security vulnerabilities using pip-audit"""
    print("\n🔒 Checking for security vulnerabilities...")
    
    # Run pip-audit with JSON output for parsing
    result = subprocess.run(
        ["pip-audit", "--format=json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0 and not result.stdout:
        print(f"❌ Error running security audit: {result.stderr}")
        return False
    
    try:
        audit_results = json.loads(result.stdout)
        
        # Check if there are vulnerabilities
        if not audit_results.get("vulnerabilities"):
            print("✅ No security vulnerabilities found!")
            return True
        
        # Print vulnerability information
        print(f"⚠️ Found {len(audit_results['vulnerabilities'])} vulnerabilities:")
        
        for vuln in audit_results["vulnerabilities"]:
            package = vuln.get("name", "Unknown")
            version = vuln.get("version", "Unknown")
            fixed_in = vuln.get("fix_versions", ["No fix available"])[0] if vuln.get("fix_versions") else "No fix available"
            
            print(f"\n- Package: {package} {version}")
            print(f"  Vulnerability ID: {vuln.get('id', 'Unknown')}")
            print(f"  Fixed in version: {fixed_in}")
            print(f"  Description: {vuln.get('description', 'No description available')}")
        
        return False
    
    except json.JSONDecodeError:
        print("✅ No security vulnerabilities found!")
        return True

def update_dependencies():
    """Update dependencies after confirmation"""
    print("\n🔄 Preparing to update dependencies...")
    
    # First check outdated packages to show what will be updated
    if not check_outdated_packages():
        return False
    
    # Ask for confirmation
    confirmation = input("\n⚠️ Do you want to proceed with updating these dependencies? (y/N): ")
    
    if confirmation.lower() not in ["y", "yes"]:
        print("Update cancelled.")
        return False
    
    print("\n🔄 Updating dependencies...")
    
    # Create a backup of the current requirements file
    backup_file = f"requirements.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    try:
        with open("requirements.txt", "r") as src:
            with open(backup_file, "w") as dst:
                dst.write(src.read())
        print(f"📄 Created backup: {backup_file}")
    except Exception as e:
        print(f"❌ Failed to create backup: {str(e)}")
        return False
    
    # Update the requirements file using pip-compile
    result = subprocess.run(
        ["pip-compile", "--upgrade", "--output-file=requirements.txt", "requirements.txt"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Error updating dependencies: {result.stderr}")
        return False
    
    print("✅ Dependencies updated successfully!")
    print("\n🔄 Running security audit on updated dependencies...")
    audit_security()
    
    return True

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ["check", "audit", "update"]:
        print(__doc__)
        return
    
    command = sys.argv[1]
    
    if command == "check":
        check_outdated_packages()
    elif command == "audit":
        audit_security()
    elif command == "update":
        update_dependencies()

if __name__ == "__main__":
    main() 