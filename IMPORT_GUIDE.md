# 📥 Bulk Import Guide

This guide explains how to import employee and leave data in bulk.

---

## 👤 Importing Employee Data

### Option 1: JSON Format

**File:** `employees.json`

```json
{
  "EMP001": {
    "id": "EMP001",
    "name": "Ahmed Hassan",
    "email": "ahmed@company.com",
    "department": "IT",
    "position": "Senior Developer",
    "join_date": "2020-03-15",
    "employment_type": "Full-time",
    "annual_leave_balance": 30.0,
    "status": "Active",
    "nationality": "UAE",
    "gender": "Male"
  },
  "EMP002": {
    "id": "EMP002",
    "name": "Fatima Al Zahra",
    "email": "fatima@company.com",
    "department": "HR",
    "position": "HR Manager",
    "join_date": "2021-06-01",
    "employment_type": "Full-time",
    "annual_leave_balance": 25.0,
    "status": "Active",
    "nationality": "UAE",
    "gender": "Female"
  }
}
```

### Option 2: Excel/CSV Format

**Required Columns:**
| Column | Description | Example |
|--------|-------------|---------|
| `id` | Employee ID | EMP001 |
| `name` | Full Name | Ahmed Hassan |
| `email` | Email Address | ahmed@company.com |
| `department` | Department | IT |
| `position` | Job Position | Senior Developer |
| `join_date` | Join Date (YYYY-MM-DD) | 2020-03-15 |

**Optional Columns:**
| Column | Default | Description |
|--------|---------|-------------|
| `employment_type` | Full-time | Employment type |
| `annual_leave_balance` | 30.0 | Leave balance in days |
| `status` | Active | Active/Inactive |
| `nationality` | (empty) | Nationality |
| `gender` | Unknown | Male/Female/Unknown |

---

## 📅 Importing Leave Data

### Option 1: JSON Format

**File:** `leave_data.json`

```json
{
  "LEAVE001": {
    "id": "LEAVE001",
    "employee_id": "EMP001",
    "leave_type": "Annual Leave",
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "days_requested": 5,
    "reason": "Family vacation",
    "status": "Manager_Approved",
    "submitted_date": "2024-02-15 10:30:00",
    "approved_by": "manager",
    "approved_date": "2024-02-16",
    "comments": "Approved as requested"
  }
}
```

### Option 2: Excel/CSV Format

**Required Columns:**
| Column | Description | Example |
|--------|-------------|---------|
| `id` | Leave Request ID | LEAVE001 |
| `employee_id` | Employee ID | EMP001 |
| `leave_type` | Type of Leave | Annual Leave |
| `start_date` | Start Date | 2024-03-01 |
| `end_date` | End Date | 2024-03-05 |
| `days_requested` | Number of Days | 5 |

**Optional Columns:**
| Column | Default | Description |
|--------|---------|-------------|
| `reason` | (empty) | Reason for leave |
| `status` | Pending | Pending/Admin_Approved/Manager_Approved/Rejected/Cancelled |
| `submitted_date` | Current time | When request was submitted |
| `approved_by` | (empty) | Username who approved |
| `approved_date` | (empty) | Approval date |
| `comments` | (empty) | Additional comments |

### Leave Type Options

- `Annual Leave`
- `Sick Leave`
- `Maternity Leave`
- `Parental Leave`
- `Bereavement Leave`
- `Hajj Leave`
- `Study Leave`
- `Emergency Leave`
- `Unpaid Leave`

### Status Options

| Status | Description |
|--------|-------------|
| `Pending` | Waiting for approval |
| `Admin_Approved` | Approved by Admin/HR (Level 1) |
| `Manager_Approved` | Fully approved (Final) |
| `Rejected` | Rejected |
| `Cancelled` | Cancelled |

---

## 🔄 Import Process

1. **Go to:** `👥 Employee Management` → `📥 Bulk Import` tab
2. **Select Import Type:**
   - 👤 Employee Data (JSON)
   - 👤 Employee Data (Excel/CSV)
   - 📅 Leave Data (JSON)
   - 📅 Leave Data (Excel/CSV)
3. **Upload your file**
4. **Review the preview**
5. **Configure options:**
   - Skip existing records
   - Create user accounts (for employees)
   - Update leave balance (for approved leaves)
6. **Click Import**
7. **Download credentials** (if employee accounts were created)

---

## ⚠️ Important Notes

### Employee Import
- Employee IDs must be unique
- If employee already exists, it will be skipped (if option selected)
- User accounts are auto-generated from email (username = part before @)
- Temporary passwords are generated automatically

### Leave Data Import
- Employee ID must exist in the system (or enable skip option)
- Dates should be in YYYY-MM-DD format
- The app will try to auto-detect various date formats
- Leave balance update is optional (use with caution)

### General Tips
- Always backup your data before bulk import (`⚙️ Settings` → `💾 Data Backup`)
- Test with a small file first
- Check the preview before confirming import
- Download and save credentials immediately after employee import

---

## 📁 Sample Files

See these files in the repository:
- `sample_employees.json` - Example employee data
- `sample_leave_data.json` - Example leave data

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid date format" | Use YYYY-MM-DD format (e.g., 2024-03-15) |
| "Employee not found" | Import employees first, then leave data |
| "Duplicate ID" | Check that all IDs are unique |
| "File too large" | Split into smaller files (max 1000 records at a time) |

---

Need help? Contact your system administrator.
