# 🏢 UAE Annual Leave Management System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive **Streamlit-based web application** for managing employee annual leave with full compliance to **UAE Federal Decree Law No. 33 of 2021** on Employment Relationships.

![App Screenshot](screenshot.png)

---

## ✨ Features

### 👥 Employee Management
- Complete employee database with profiles
- Leave balance tracking
- Department organization
- Employee status management (Active/On Leave/Inactive)

### 📝 Leave Management
- **9 Leave Types**: Annual, Sick, Maternity, Parental, Bereavement, Hajj, Study, Emergency, Unpaid
- Two-level approval workflow (Admin/HR → Manager)
- Automatic conflict detection for overlapping leaves
- Calendar vs Working days calculation (UAE weekends: Sat/Sun)
- Negative balance prevention

### 📊 Reports & Analytics
- Leave Summary Report
- Department Analysis
- Employee Leave Report
- **Leave Calendar Report** - View all employees on leave between specific dates
- Export to CSV

### 🔐 Security & Authentication
- SHA-256 password hashing with salt
- Role-based access control (Admin, Manager, Employee)
- Session management

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/uae-leave-management.git
cd uae-leave-management
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
# On Windows (double-click)
run_app_with_browser.bat

# Or via command line
streamlit run annual_leave_system.py
```

4. **Access the app**
Open your browser and navigate to: `http://localhost:8501`

---

## 🔐 Security First

After first login, **immediately change default passwords** using the "🔐 Change Password" menu option.

| Role | Default Username | Default Password | Action Required |
|------|------------------|------------------|-----------------|
| Admin | `admin` | `admin123` | ⚠️ Change after first login |
| Manager | `manager` | `manager123` | ⚠️ Change after first login |
| Employee | (auto-generated) | (auto-generated) | Change via User Management |

---

## 📁 Project Structure

```
.
├── annual_leave_system.py    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── LICENSE                   # MIT License
├── .gitignore               # Git ignore rules
├── run_app.bat              # Run script (headless)
├── run_app_with_browser.bat # Run script (with browser)
├── employees.json           # Employee data (auto-generated)
├── leave_data.json          # Leave records (auto-generated)
├── users.json               # User accounts (auto-generated)
└── employee_credentials.txt # Login credentials (auto-generated)
```

---

## 📋 Leave Types (UAE Law Compliant)

| Leave Type | Duration | Payment | Calendar Days |
|------------|----------|---------|---------------|
| Annual Leave | 30 days/year | Full pay | ✅ Calendar |
| Sick Leave | Up to 90 days/year | 15 full + 30 half + 45 unpaid | ✅ Calendar |
| Maternity Leave | 60 days | 45 full + 15 half | ✅ Calendar |
| Parental Leave | 5 days | Full pay | ❌ **Working** |
| Bereavement Leave | 3-5 days | Full pay | ✅ Calendar |
| Hajj Leave | 30 days (once) | Unpaid | ✅ Calendar |
| Study Leave | 10 days/year | Full pay | ❌ **Working** |
| Emergency Leave | 1-2 days | Full pay | ✅ Calendar |
| Unpaid Leave | As agreed | No pay | ✅ Calendar |

---

## 🏢 User Roles & Permissions

### Admin
- ✅ Full employee management (CRUD)
- ✅ User management
- ✅ Level 1 leave approvals
- ✅ View all reports
- ✅ System configuration

### Manager
- ✅ Level 2 (final) leave approvals
- ✅ View-only employee access
- ✅ View all reports
- ❌ Cannot modify employees

### Employee
- ✅ Submit leave requests
- ✅ View personal dashboard
- ✅ View leave history
- ✅ Cancel pending requests
- ❌ Cannot view other employees' data

---

## ⚙️ Configuration

### Data Storage
All data is stored locally in JSON files:
- `employees.json` - Employee master data
- `leave_data.json` - Leave request history
- `users.json` - User authentication data

### Port Configuration
If port 8501 is in use:
```bash
streamlit run annual_leave_system.py --server.port 8502
```

---

## 🔧 Customization

### Adding New Departments
Edit the `dept_options` list in `annual_leave_system.py`:
```python
dept_options = ["Administration", "Finance", "HR", "IT", ...]
```

### Modifying Leave Types
Edit the `LEAVE_TYPES` dictionary in the configuration section.

### Changing Your Password
1. Log in to the system
2. Click on "🔐 Change Password" in the navigation menu (Admin & Manager)
3. Enter current password and new password
4. Click "Change Password"

### Bulk Importing Employees
1. Go to "👥 Employee Management"
2. Click on "📥 Bulk Import" tab
3. Select import format (JSON or Excel/CSV)
4. Upload your file
5. Configure options (skip existing, create user accounts)
6. Click "Import Employees"

**Supported File Formats:**
- **JSON**: `employees.json` format with employee objects
- **Excel/CSV**: Columns: `id`, `name`, `email`, `department`, `position`, `join_date`

After import, you'll receive a CSV file with auto-generated login credentials.

---

## 🛡️ Security Notes

- Passwords are hashed using **SHA-256 with random salt**
- All data is stored locally (no cloud services)
- No data encryption at rest (filesystem security only)
- Regular backups of JSON files recommended

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "streamlit not recognized" | Run `pip install streamlit pandas` |
| Port already in use | Change port with `--server.port 8502` |
| Cannot access from other devices | Use `--server.address 0.0.0.0` |
| Data files corrupted | Restore from backup |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- UAE Ministry of Human Resources & Emiratisation for labour law guidelines
- Streamlit team for the amazing framework
- All contributors and testers

---

## 📞 Support

For support, email: your-email@example.com

Or open an issue on [GitHub Issues](https://github.com/yourusername/uae-leave-management/issues)

---

Made with ❤️ in UAE 🇦🇪
