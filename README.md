# 🇦🇪 UAE Annual Leave Management System

A comprehensive Streamlit application for managing staff annual leave with UAE Labour Law compliance and intelligent conflict detection.

## ✨ Features

### Core Features
- **👥 Employee Management** - Add, edit, delete, and manage employee records
- **📝 Leave Application** - Submit various types of leave requests
- **✅ Approval Workflow** - Review and approve/reject leave requests
- **⚠️ Conflict Detection** - Automatic alerts when 2+ employees have overlapping leave
- **📅 Calendar View** - Visual overview of all leaves by month
- **📊 Reports & Analytics** - Comprehensive leave statistics and trends

### UAE Labour Law Compliance
This system is fully compliant with **UAE Federal Decree Law No. 33 of 2021** on Employment Relationships:

| Leave Type | Duration | Payment | Notes |
|------------|----------|---------|-------|
| **Annual Leave** | 30 calendar days/year | Full pay | After 1 year; 2 days/month after 6 months |
| **Maternity Leave** | 60 calendar days | 45 full + 15 half | For female employees |
| **Parental Leave** | 5 working days | Full pay | Within first 6 months (either parent) |
| **Sick Leave** | Up to 90 days/year | 15 full + 30 half + 45 unpaid | Medical certificate required |
| **Bereavement Leave** | 3-5 days | Full pay | Spouse (5d), close relatives (3d) |
| **Hajj Leave** | Up to 30 days | Unpaid | Once during employment |
| **Study Leave** | 10 working days/year | Full pay | UAE-accredited institutions |

### Conflict Detection Features
- ⚠️ **Multi-employee Conflict Alert** - Warns when 2+ employees have overlapping leave dates
- 🏢 **Department Conflict Tracking** - Highlights same-department conflicts for business continuity
- 🚦 **Visual Indicators** - Color-coded warnings (red for 2+ conflicts, info for 1)
- 📋 **Conflict Details** - Lists all conflicting employees with their leave dates

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install streamlit pandas
```

### Step 2: Run the Application
```bash
streamlit run annual_leave_system.py
```

The application will open in your default web browser at `http://localhost:8501`

## 📖 Usage Guide

### 1. Dashboard
- Overview of total employees, pending requests, and approvals
- "Who's On Leave Today" section
- Upcoming leaves (next 30 days)
- Conflict alerts for same-department overlaps

### 2. Employee Management
- **View Employees**: Complete employee directory with filters
- **Add Employee**: Register new employees with department and leave balance
- **Edit/Delete**: Modify employee details or remove records

### 3. Apply for Leave
1. Select employee from dropdown
2. Choose leave type
3. Select start and end dates
4. View automatic day calculations
5. Check for conflicts before submitting
6. Provide reason and submit

**Conflict Detection**: The system will warn you if:
- 2 or more employees have overlapping dates (⚠️ Warning)
- Someone in the same department is on leave (ℹ️ Note)

### 4. Leave Approvals
- **Pending Requests**: Review and approve/reject with one click
- **Approved Leaves**: View all approved leaves with cancel option
- **All Requests**: Filterable view with CSV export

### 5. Leave Calendar
- Month-by-month view of all approved leaves
- Department filtering
- Color-coded leave types

### 6. UAE Entitlements Guide
Built-in reference for:
- Annual leave calculations
- Special leave types
- Key legal provisions
- Calculation examples

### 7. Reports
- Leave summary by type
- Monthly trends
- Department analysis
- Individual employee reports

## 🗄️ Data Storage

The application uses JSON files for data persistence:
- `employees.json` - Employee records
- `leave_data.json` - Leave requests and approvals

Data is automatically saved after each operation.

## 🏢 Default Sample Data

The system comes with 10 sample employees across various departments:
- Engineering (3 employees)
- HR (2 employees)
- Finance (2 employees)
- Marketing (2 employees)
- Operations (1 employee)

## ⚙️ Configuration

### Modifying Leave Types
Edit the `LEAVE_TYPES` dictionary in the code to customize leave types, descriptions, and colors.

### UAE Labour Law Constants
The `UAE_LEAVE_ENTITLEMENTS` dictionary contains all UAE-specific leave entitlements. Modify with caution to maintain compliance.

## 📋 UAE Labour Law Highlights

### Annual Leave Provisions
1. **Full Year**: 30 calendar days after completing 1 year
2. **Partial Year**: 2 days per month after 6 months but less than 1 year
3. **Part-time**: Proportional to working hours

### Important Rules
- Employer must give 1 month notice for leave dates
- Cannot prevent employee from using leave for more than 2 consecutive years
- Public holidays within leave count as leave days
- Unused leave upon termination must be paid

### Leave Carry Forward
- Allowed with employer consent
- Employee entitled to payment for unused days carried forward
- Based on basic salary calculation

## 🔒 Security & Best Practices

- All data is stored locally in JSON files
- No external API calls or data sharing
- Suitable for on-premise deployment
- Regular backups recommended

## 🛠️ Troubleshooting

### Common Issues

**Port already in use:**
```bash
streamlit run annual_leave_system.py --server.port 8502
```

**Data not saving:**
- Check write permissions in the application directory
- Ensure `employees.json` and `leave_data.json` are not open in other programs

**Import errors:**
```bash
pip install --upgrade streamlit pandas
```

## 📞 Support

For questions or issues:
1. Check the UAE Entitlements section in the app
2. Review the code comments for implementation details
3. Ensure all dependencies are properly installed

## 📜 License

This project is provided as-is for HR departments to manage leave in compliance with UAE Labour Law.

---

**Disclaimer**: While this system implements UAE Labour Law provisions, always consult with legal professionals for specific employment matters. Labour laws may change; keep your system updated accordingly.
