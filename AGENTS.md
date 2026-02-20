# UAE Annual Leave Management System - Agent Guide

## Project Overview

This is a **Streamlit-based web application** for managing employee annual leave with compliance to **UAE Federal Decree Law No. 33 of 2021** on Employment Relationships. The system provides a complete leave management solution with role-based access control, multi-level approval workflows, and intelligent conflict detection.

**Key Capabilities:**
- Employee leave request submission and tracking
- Two-level approval workflow (Admin/HR → Manager)
- Automatic conflict detection when 2+ employees have overlapping leave
- UAE Labour Law compliance validation
- Leave calendar visualization
- Reports and analytics

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| Web Framework | Streamlit (>=1.28.0) |
| Data Processing | pandas (>=2.0.0) |
| Data Storage | JSON files (local filesystem) |
| Authentication | SHA-256 with salt |
| UI Styling | Inline CSS with Streamlit markdown |

---

## Project Structure

```
.
├── annual_leave_system.py    # Main application (~2500 lines, monolithic)
├── requirements.txt          # Python dependencies
├── README.md                 # User documentation
├── AGENTS.md                 # This file - agent documentation
├── employees.json            # Employee records (auto-generated)
├── leave_data.json           # Leave requests (auto-generated)
└── users.json                # User accounts with hashed passwords (auto-generated)
```

### Data Files

| File | Purpose | Schema |
|------|---------|--------|
| `employees.json` | Employee master data | Dict of `Employee` objects keyed by `id` |
| `leave_data.json` | Leave requests history | Dict of `LeaveRequest` objects keyed by `id` |
| `users.json` | Authentication accounts | Dict of `User` objects keyed by `username` |

---

## Application Architecture

### Core Classes

```python
# Data Models (dataclasses)
Employee          # Employee information and leave balance
User              # Authentication credentials with SHA-256 hashing
LeaveRequest      # Leave application with approval workflow tracking

# Manager Classes
DataManager       # CRUD operations for all data entities, JSON persistence
AuthManager       # Password hashing, verification, and validation
LeaveCalculator   # Date calculations, conflict detection
```

### User Roles & Permissions

| Role | Permissions |
|------|-------------|
| `employee` | Submit leave requests, view own dashboard and history |
| `admin` | Full employee management, user management, Level 1 approvals, reports |
| `manager` | Level 2 (final) approvals, view-only employee access, reports |

### Approval Workflow

```
Pending → Admin_Approved → Manager_Approved
   ↓
Rejected (can happen at any level)
```

- **Admin/HR** performs first-level review
- **Manager** performs final approval
- Managers can approve directly if admin hasn't acted

---

## Leave Types (UAE Law Compliant)

| Leave Type | Duration | Payment | Calendar Days |
|------------|----------|---------|---------------|
| Annual Leave | 30 days/year | Full pay | Calendar |
| Sick Leave | Up to 90 days/year | 15 full + 30 half + 45 unpaid | Calendar |
| Maternity Leave | 60 days | 45 full + 15 half | Calendar |
| Parental Leave | 5 days | Full pay | **Working** |
| Bereavement Leave | 3-5 days | Full pay | Calendar |
| Hajj Leave | 30 days (once) | Unpaid | Calendar |
| Study Leave | 10 days/year | Full pay | **Working** |
| Emergency Leave | 1-2 days | Full pay | Calendar |
| Unpaid Leave | As agreed | No pay | Calendar |

**UAE Weekend Consideration:** Saturday and Sunday are excluded when calculating working days.

---

## Running the Application

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or manually
pip install streamlit>=1.28.0 pandas>=2.0.0
```

### Start the Application

```bash
streamlit run annual_leave_system.py
```

The application will be available at `http://localhost:8501`

### Default Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Manager | `manager` | `manager123` |
| Employee | `ahmed.hassan` | `employee123` |
| Employee | `fatima.zahra` | `employee123` |
| Employee | `mohammed.ali` | `employee123` |

---

## Code Organization

The application is structured as follows within `annual_leave_system.py`:

### Section 1: Configuration & Constants (Lines 19-174)
- Data file paths
- User role definitions
- UAE Labour Law constants (`UAE_LEAVE_ENTITLEMENTS`)
- Leave type definitions with metadata (`LEAVE_TYPES`)

### Section 2: Data Classes (Lines 177-343)
- `@dataclass Employee` - Employee entity
- `@dataclass User` - User account with password hash and salt
- `class AuthManager` - Authentication utilities
- `@dataclass LeaveRequest` - Leave application entity

### Section 3: Data Management (Lines 346-493)
- `class DataManager` - JSON persistence, CRUD operations
- Auto-creates sample data on first run

### Section 4: Leave Calculator (Lines 496-608)
- `class LeaveCalculator` - Date arithmetic, conflict detection
- UAE weekend handling (Saturday/Sunday)

### Section 5: UI Rendering Functions (Lines 611-2417)
| Function | Purpose |
|----------|---------|
| `render_login()` | Authentication page |
| `render_dashboard()` | Admin/Manager dashboard with metrics |
| `render_employee_management()` | CRUD for employees |
| `render_leave_request()` | Submit leave (admin view) |
| `render_leave_approvals()` | Legacy approval view |
| `render_two_level_approvals()` | Two-level approval workflow |
| `render_approval_list()` | Render requests with action buttons |
| `render_leave_calendar()` | Monthly calendar view |
| `render_leave_entitlements()` | UAE law reference guide |
| `render_reports()` | Analytics and statistics |
| `render_user_management()` | User account management (admin only) |
| `render_employee_dashboard()` | Employee self-service portal |
| `render_employee_leave_request()` | Employee leave submission |
| `render_employee_history()` | Personal leave history |

### Section 6: Main Entry Point (Lines 2419-2537)
- `main()` - Application entry, routing, session initialization

---

## Security Considerations

### Authentication
- Passwords are hashed using **SHA-256 with random salt**
- Salt is stored alongside the hash in `users.json`
- Session state tracks `authenticated`, `current_user`, `user_role`, `employee_id`

### Data Security
- All data stored locally in JSON files
- No external API calls or cloud services
- No data encryption at rest (filesystem security only)

### Password Generation
```python
# From AuthManager.generate_temporary_password()
# Generates 12-character password with:
# - Upper and lowercase letters
# - Numbers
# - Symbols: !@#$%^&*
```

---

## Key Implementation Details

### Conflict Detection Logic
```python
# Located in LeaveCalculator.check_conflicts()
# Returns: (has_conflict, warning_message, conflicting_leaves)
# - 2+ overlapping employees → Warning (red)
# - 1 overlapping employee → Info note
# - Same department conflicts highlighted separately
```

### Date Calculations
```python
# Working days: Excludes Saturday (5) and Sunday (6)
# Calendar days: Includes all days
# Leave deduction: Calendar days for most types, Working days for Parental/Study leave
```

### Leave Balance Management
- Balance deducted on **admin approval** for annual leave
- Balance restored when leave is **cancelled**
- Balance check prevents submitting requests exceeding available days

---

## Development Guidelines

### Adding New Leave Types

1. Add entry to `LEAVE_TYPES` dictionary (line ~53):
```python
"New Leave": {
    "description": "Brief description",
    "uae_law": "Legal reference",
    "entitlement": "Detailed entitlement",
    "payment": "Payment terms",
    "requirements": "Requirements",
    "carry_forward": "Carry forward rules",
    "color": "#HEXCODE",
    "paid": True/False,
    "max_days": N,
    "calendar_days": True/False,
}
```

2. If using working days instead of calendar days, update the deduction logic in:
   - `render_leave_request()` (line ~1087)
   - `render_employee_leave_request()` (line ~2147)

### Modifying Approval Workflow

The approval states are defined in `APPROVAL_WORKFLOW` (line ~31):
```python
APPROVAL_WORKFLOW = {
    "Pending": "Submitted by Employee",
    "Admin_Approved": "Approved by Admin/HR (Level 1)",
    "Manager_Approved": "Approved by Manager (Final)",
    "Rejected": "Rejected",
    "Cancelled": "Cancelled",
}
```

Status checks throughout the code filter on these values.

### Styling Conventions

The application uses a dark blue theme (`#1e3a5f`) with:
- Border accent: `#4a90d9`
- Leave type colors defined in `LEAVE_TYPES`
- Inline CSS via `st.markdown(..., unsafe_allow_html=True)`

---

## Testing

### Manual Testing Checklist

1. **Authentication**
   - Login with each role type
   - Verify role-based menu restrictions
   - Test password reset functionality

2. **Leave Request Flow**
   - Submit leave request as employee
   - Approve as admin (Level 1)
   - Approve as manager (Level 2)
   - Verify balance deduction
   - Test cancellation and balance restoration

3. **Conflict Detection**
   - Create overlapping leave requests
   - Verify warning displays
   - Check same-department conflict highlighting

4. **Data Persistence**
   - Verify JSON files update after operations
   - Test data reload on application restart

---

## Deployment Notes

### Local Deployment
- Single Python file execution
- No database server required
- JSON files must be writable by the application process

### Port Configuration
```bash
# If port 8501 is in use
streamlit run annual_leave_system.py --server.port 8502
```

### Data Backup
- Regular backups of `employees.json`, `leave_data.json`, and `users.json` recommended
- Files are human-readable JSON for easy inspection

---

## Limitations & Known Issues

1. **Single File Architecture** - The entire application is in one ~2500 line file
2. **No Concurrent Access Control** - JSON file writes are not atomic; concurrent modifications may cause data loss
3. **No Audit Log** - No history of who changed what and when
4. **Fixed UAE Weekend** - Saturday/Sunday hardcoded; not configurable for other regions
5. **No Email Notifications** - No automated email alerts for approvals
6. **No Database** - JSON storage not suitable for large datasets

---

## File Modification Guidelines

When modifying code:

1. **Preserve dataclass schemas** - Changes to `Employee`, `User`, or `LeaveRequest` fields require migration logic in `from_dict()` methods
2. **Maintain backward compatibility** - The `LeaveRequest.from_dict()` includes backward compatibility handling for legacy field names
3. **Update both admin and employee views** - Many features exist in both `render_leave_request()` and `render_employee_leave_request()`
4. **Test authentication flow** - Changes to session state can break the login system
5. **Validate JSON persistence** - Ensure `to_dict()` methods serialize all new fields

---

*Last updated: 2026-02-20*
*Project Language: English (all documentation and code comments)*
