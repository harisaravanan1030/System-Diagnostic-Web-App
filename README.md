# SysDiag Pro

## Overview

SysDiag Pro is a Flask-based System Diagnostic Web Application that monitors system performance and provides real-time insights into CPU, RAM, Disk, Network, and Security metrics. The application includes interactive dashboards, internet speed testing, email report generation, and admin management features.

## Features

* User Registration and Login
* Real-Time System Diagnostics
* CPU, RAM, Disk, and Network Monitoring
* Interactive Charts and Visualizations
* Security Score Analysis
* Internet Speed Testing
* Email Report Generation
* Historical Performance Tracking
* Admin Dashboard and User Management
* SQLite Database Integration

## Tech Stack

### Backend

* Python
* Flask

### Database

* SQLite

### Frontend

* HTML
* CSS
* JavaScript
* Chart.js
* Font Awesome

### Libraries

* psutil
* GPUtil
* screeninfo
* speedtest-cli

## Installation

```bash
git clone https://github.com/harisaravanan1030/System-Diagnostic-Web-App.git
cd System-Diagnostic-Web-App

pip install -r requirements.txt

python app.py
```

## Project Structure

```text
sysdiag-pro/
├── app.py
├── scanner.py
├── database.py
├── email_sender.py
├── speed_test.py
├── templates/
├── static/
├── data/
└── requirements.txt
```

## Usage

1. Register a new account or log in.
2. Run a system diagnostic scan.
3. View system performance metrics and security analysis.
4. Run internet speed tests.
5. Generate and receive email reports.
6. Access admin features for user and report management.

## Future Enhancements

* Cloud-based monitoring support
* Advanced security auditing
* Multi-device monitoring
* Export reports in PDF format
* AI-powered performance recommendations

## Author

Hari Saravanan

GitHub: harisaravanan1030
