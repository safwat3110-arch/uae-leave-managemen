"""
UAE Annual Leave Management System
A Streamlit application for managing staff annual leave with conflict detection.
Compliant with UAE Federal Decree Law No. 33 of 2021 on Employment Relationships.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import json
import os
from collections import defaultdict
import hashlib
import secrets
import re
import time

# ============== CONFIGURATION ==============
DATA_FILE = "leave_data.json"
EMPLOYEES_FILE = "employees.json"
USERS_FILE = "users.json"

# ============== AUTHENTICATION & USER ROLES ==============
USER_ROLES = {
    "employee": "Employee - Can submit leave requests and view own data",
    "admin": "Admin/HR - First level approval, user management, reports",
    "manager": "Manager - Final approval authority, department oversight",
}

APPROVAL_WORKFLOW = {
    "Pending": "Submitted by Employee",
    "Admin_Approved": "Approved by Admin/HR (Level 1)",
    "Manager_Approved": "Approved by Manager (Final)",
    "Rejected": "Rejected",
    "Cancelled": "Cancelled",
}

# UAE Labour Law Constants (Federal Decree Law No. 33 of 2021)
UAE_LEAVE_ENTITLEMENTS = {
    "annual_leave_full": 30,  # Days after 1 year of service
    "annual_leave_partial": 2,  # Days per month after 6 months but < 1 year
    "maternity_leave": 60,  # 45 full pay + 15 half pay
    "parental_leave": 5,  # Working days within first 6 months
    "bereavement_leave": 3,  # Days for close relative death
    "hajj_leave": 30,  # Once during employment (unpaid)
    "study_leave": 10,  # Working days per year for UAE students
    "sick_leave_full": 15,  # Full pay days
    "sick_leave_half": 30,  # Half pay days
    "sick_leave_total": 90,  # Total sick leave days
}

LEAVE_TYPES = {
    "Annual Leave": {
        "description": "30 calendar days/year after 1 year of service",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 29",
        "entitlement": "30 calendar days per year after completing 1 year of service. For 6+ months but < 1 year: 2 days per month.",
        "payment": "Full pay (basic salary + allowances)",
        "requirements": "Must complete 6 months of service. Employer sets dates with 1 month notice.",
        "carry_forward": "Allowed with employer consent. Max 2 years accumulation.",
        "color": "#4CAF50",
        "paid": True,
        "max_days": 30,
        "calendar_days": True,
    },
    "Sick Leave": {
        "description": "Up to 90 days/year with medical certificate",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 31",
        "entitlement": "Maximum 90 consecutive or intermittent days per year",
        "payment": "15 days full pay → 30 days half pay → 45 days no pay",
        "requirements": "Medical certificate required from first day of sickness. Not during probation.",
        "carry_forward": "Not applicable - annual limit",
        "color": "#FF9800",
        "paid": True,
        "max_days": 90,
        "calendar_days": True,
    },
    "Maternity Leave": {
        "description": "60 days (45 full pay + 15 half pay)",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 30",
        "entitlement": "60 calendar days for female employees",
        "payment": "45 days full pay + 15 days half pay",
        "requirements": "Must provide medical certificate. Can start up to 30 days before expected delivery.",
        "carry_forward": "Not applicable",
        "color": "#E91E63",
        "paid": True,
        "max_days": 60,
        "calendar_days": True,
    },
    "Parental Leave": {
        "description": "5 working days (within 6 months of child's birth)",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 30",
        "entitlement": "5 working days for either parent",
        "payment": "Full pay",
        "requirements": "Must be taken within 6 months of child's birth. For private sector employees.",
        "carry_forward": "Cannot be carried forward - use it or lose it",
        "color": "#2196F3",
        "paid": True,
        "max_days": 5,
        "calendar_days": False,  # Working days
    },
    "Bereavement Leave": {
        "description": "3-5 days for death of family members",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 32",
        "entitlement": "5 days for spouse's death, 3 days for parent/child/sibling/grandparent/grandchild",
        "payment": "Full pay",
        "requirements": "Must provide death certificate. Must be taken within days of death.",
        "carry_forward": "Not applicable",
        "color": "#9E9E9E",
        "paid": True,
        "max_days": 5,
        "calendar_days": True,
    },
    "Hajj Leave": {
        "description": "30 days once during employment (unpaid)",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 32",
        "entitlement": "Maximum 30 days once during entire employment period",
        "payment": "Unpaid leave",
        "requirements": "Employee must have completed 1 year of service. Granted only once.",
        "carry_forward": "Not applicable - one-time entitlement",
        "color": "#795548",
        "paid": False,
        "max_days": 30,
        "calendar_days": True,
    },
    "Study Leave": {
        "description": "10 working days/year for UAE students",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 32",
        "entitlement": "10 working days per academic year",
        "payment": "Full pay",
        "requirements": "Must be enrolled in UAE-accredited educational institution. Requires proof of enrollment.",
        "carry_forward": "Annual entitlement - cannot accumulate",
        "color": "#673AB7",
        "paid": True,
        "max_days": 10,
        "calendar_days": False,  # Working days
    },
    "Compassionate Leave (Iddah)": {
        "description": "Muslim woman after husband's death (fully paid)",
        "uae_law": "Federal Decree Law No. 33 of 2021 - Article 32",
        "entitlement": "Full Iddah period (approximately 4 months and 10 days)",
        "payment": "Full pay",
        "requirements": "For Muslim female employees whose husband has passed away. Requires death certificate.",
        "carry_forward": "Not applicable",
        "color": "#8E24AA",
        "paid": True,
        "max_days": 130,
        "calendar_days": True,
    },
    "Emergency Leave": {
        "description": "Short-term emergency leave",
        "uae_law": "Company Policy / Common Practice",
        "entitlement": "1-2 days for urgent personal matters",
        "payment": "Full pay (usually)",
        "requirements": "For unforeseen emergencies. Subject to employer approval.",
        "carry_forward": "Not applicable",
        "color": "#F44336",
        "paid": True,
        "max_days": 2,
        "calendar_days": True,
    },
    "Unpaid Leave": {
        "description": "At employer's discretion",
        "uae_law": "Employer Discretion",
        "entitlement": "As agreed between employer and employee",
        "payment": "No pay",
        "requirements": "Requires written approval from employer. Duration mutually agreed.",
        "carry_forward": "Not applicable",
        "color": "#607D8B",
        "paid": False,
        "max_days": None,
        "calendar_days": True,
    },
}


# ============== DATA CLASSES ==============
@dataclass
class Employee:
    id: str
    name: str
    email: str
    department: str
    position: str
    join_date: str
    employment_type: str = "Full-time"  # Full-time, Part-time, Contract
    annual_leave_balance: float = 30.0
    status: str = "Active"
    nationality: str = ""
    gender: str = "Unknown"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "position": self.position,
            "join_date": self.join_date,
            "employment_type": self.employment_type,
            "annual_leave_balance": self.annual_leave_balance,
            "status": self.status,
            "nationality": self.nationality,
            "gender": self.gender,
        }
    
    @classmethod
    def from_dict(cls, data):
        # Filter out keys that are not in the class
        valid_keys = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


@dataclass
class User:
    """User account for authentication"""
    username: str
    password_hash: str  # Hashed password
    salt: str
    employee_id: str
    role: str  # employee, admin, manager
    is_active: bool = True
    created_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    last_login: Optional[str] = None
    
    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "employee_id": self.employee_id,
            "role": self.role,
            "is_active": self.is_active,
            "created_date": self.created_date,
            "last_login": self.last_login,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class AuthManager:
    """Handle authentication and user management"""
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        salted_password = password + salt
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        salted_password = password + salt
        return hashlib.sha256(salted_password.encode()).hexdigest() == password_hash
    
    @staticmethod
    def generate_temporary_password() -> str:
        """Generate a secure temporary password"""
        import random
        import string
        # Generate 10-character password with mixed case, numbers, and symbols
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(12))
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username format"""
        if len(username) < 4:
            return False, "Username must be at least 4 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, "Valid"


@dataclass
class LeaveRequest:
    id: str
    employee_id: str
    employee_name: str
    leave_type: str
    start_date: str
    end_date: str
    days_requested: int
    reason: str
    status: str  # Pending, Admin_Approved, Manager_Approved, Rejected, Cancelled
    submitted_date: str
    submitted_by: str  # Username who submitted
    # Level 1 Approval (Admin/HR)
    admin_approved_by: Optional[str] = None
    admin_approval_date: Optional[str] = None
    admin_remarks: str = ""
    # Level 2 Approval (Manager)
    manager_approved_by: Optional[str] = None
    manager_approval_date: Optional[str] = None
    manager_remarks: str = ""
    # Conflict detection
    conflict_warning: bool = False
    conflict_details: str = ""
    # Legacy fields for backward compatibility
    approved_by: Optional[str] = None
    approval_date: Optional[str] = None
    remarks: str = ""
    
    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "leave_type": self.leave_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "days_requested": self.days_requested,
            "reason": self.reason,
            "status": self.status,
            "submitted_date": self.submitted_date,
            "submitted_by": self.submitted_by,
            "admin_approved_by": self.admin_approved_by,
            "admin_approval_date": self.admin_approval_date,
            "admin_remarks": self.admin_remarks,
            "manager_approved_by": self.manager_approved_by,
            "manager_approval_date": self.manager_approval_date,
            "manager_remarks": self.manager_remarks,
            "conflict_warning": self.conflict_warning,
            "conflict_details": self.conflict_details,
            "approved_by": self.approved_by,
            "approval_date": self.approval_date,
            "remarks": self.remarks,
        }
    
    @classmethod
    def from_dict(cls, data):
        # Handle backward compatibility
        if "submitted_by" not in data:
            data["submitted_by"] = data.get("employee_id", "")
        if "admin_approved_by" not in data:
            data["admin_approved_by"] = None
            data["admin_approval_date"] = None
            data["admin_remarks"] = ""
        if "manager_approved_by" not in data:
            data["manager_approved_by"] = None
            data["manager_approval_date"] = None
            data["manager_remarks"] = ""
        return cls(**data)


# ============== DATA MANAGEMENT ==============
class DataManager:
    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.leave_requests: Dict[str, LeaveRequest] = {}
        self.users: Dict[str, User] = {}
        self.load_data()
    
    def load_data(self):
        """Load data from JSON files"""
        if os.path.exists(EMPLOYEES_FILE):
            try:
                with open(EMPLOYEES_FILE, 'r') as f:
                    data = json.load(f)
                    self.employees = {k: Employee.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, IOError):
                self.employees = {}
        
        # Create sample employees if none exist
        if not self.employees:
            self._create_sample_employees()
        
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.leave_requests = {k: LeaveRequest.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, IOError):
                self.leave_requests = {}
        
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r') as f:
                    data = json.load(f)
                    self.users = {k: User.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, IOError):
                self.users = {}
        
        # Create default users if none exist (fresh deployment or reset)
        if not self.users:
            self._create_default_users()
    
    def save_data(self):
        """Save data to JSON files"""
        with open(EMPLOYEES_FILE, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.employees.items()}, f, indent=2)
        with open(DATA_FILE, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.leave_requests.items()}, f, indent=2)
        with open(USERS_FILE, 'w') as f:
            json.dump({k: v.to_dict() for k, v in self.users.items()}, f, indent=2)
    
    def _create_sample_employees(self):
        """Create sample employees for demonstration"""
        sample_employees = [
            Employee("EMP001", "Ahmed Hassan", "ahmed@company.com", "Engineering", "Senior Developer", "2020-03-15"),
            Employee("EMP002", "Fatima Al Zahra", "fatima@company.com", "Engineering", "Software Engineer", "2021-06-01"),
            Employee("EMP003", "Mohammed Ali", "mohammed@company.com", "Engineering", "DevOps Engineer", "2019-11-20"),
            Employee("EMP004", "Sarah Johnson", "sarah@company.com", "HR", "HR Manager", "2018-01-10"),
            Employee("EMP005", "Omar Farooq", "omar@company.com", "HR", "HR Specialist", "2022-03-01"),
            Employee("EMP006", "Layla Mahmoud", "layla@company.com", "Finance", "Finance Manager", "2017-08-15"),
            Employee("EMP007", "Khalid Ibrahim", "khalid@company.com", "Finance", "Accountant", "2021-02-14"),
            Employee("EMP008", "Aisha Noor", "aisha@company.com", "Marketing", "Marketing Director", "2019-05-20"),
            Employee("EMP009", "Yusuf Khan", "yusuf@company.com", "Marketing", "Marketing Specialist", "2023-01-15"),
            Employee("EMP010", "Zainab Omar", "zainab@company.com", "Operations", "Operations Manager", "2020-09-01"),
        ]
        for emp in sample_employees:
            self.employees[emp.id] = emp
        self.save_data()
    
    def _create_default_users(self):
        """Create default admin and manager accounts"""
        auth = AuthManager()
        
        # Create admin user (linked to Sarah Johnson - HR Manager)
        admin_pass, admin_salt = auth.hash_password("admin123")
        admin_user = User(
            username="admin",
            password_hash=admin_pass,
            salt=admin_salt,
            employee_id="EMP004",
            role="admin",
            is_active=True
        )
        self.users["admin"] = admin_user
        
        # Create manager user (linked to Layla Mahmoud - Finance Manager)
        manager_pass, manager_salt = auth.hash_password("manager123")
        manager_user = User(
            username="manager",
            password_hash=manager_pass,
            salt=manager_salt,
            employee_id="EMP006",
            role="manager",
            is_active=True
        )
        self.users["manager"] = manager_user
        
        # Create sample employee users
        for emp_id, username, password in [
            ("EMP001", "ahmed.hassan", "employee123"),
            ("EMP002", "fatima.zahra", "employee123"),
            ("EMP003", "mohammed.ali", "employee123"),
        ]:
            emp_pass, emp_salt = auth.hash_password(password)
            emp_user = User(
                username=username,
                password_hash=emp_pass,
                salt=emp_salt,
                employee_id=emp_id,
                role="employee",
                is_active=True
            )
            self.users[username] = emp_user
        
        self.save_data()
    
    def add_user(self, user: User):
        self.users[user.username] = user
        self.save_data()
    
    def update_user(self, username: str, **kwargs):
        if username in self.users:
            for key, value in kwargs.items():
                setattr(self.users[username], key, value)
            self.save_data()
    
    def delete_user(self, username: str):
        if username in self.users:
            del self.users[username]
            self.save_data()
    
    def add_employee(self, employee: Employee):
        self.employees[employee.id] = employee
        self.save_data()
    
    def update_employee(self, employee_id: str, **kwargs):
        if employee_id in self.employees:
            for key, value in kwargs.items():
                setattr(self.employees[employee_id], key, value)
            self.save_data()
    
    def delete_employee(self, employee_id: str):
        if employee_id in self.employees:
            del self.employees[employee_id]
            self.save_data()
    
    def add_leave_request(self, request: LeaveRequest):
        self.leave_requests[request.id] = request
        self.save_data()
    
    def update_leave_request(self, request_id: str, **kwargs):
        if request_id in self.leave_requests:
            for key, value in kwargs.items():
                setattr(self.leave_requests[request_id], key, value)
            self.save_data()
    
    def delete_leave_request(self, request_id: str):
        if request_id in self.leave_requests:
            del self.leave_requests[request_id]
            self.save_data()


# ============== LEAVE CALCULATOR ==============
class LeaveCalculator:
    @staticmethod
    def calculate_working_days(start_date: str, end_date: str) -> int:
        """Calculate working days between two dates (excluding weekends)"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if end < start:
            return 0
        
        # UAE weekends are Saturday and Sunday
        days = 0
        current = start
        while current <= end:
            if current.weekday() < 5:  # Monday = 0, Friday = 4
                days += 1
            current += timedelta(days=1)
        
        return days
    
    @staticmethod
    def calculate_calendar_days(start_date: str, end_date: str) -> int:
        """Calculate total calendar days"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1
    
    @staticmethod
    def check_conflicts(
        data_manager: DataManager,
        employee_id: str,
        start_date: str,
        end_date: str,
        exclude_request_id: str = None
    ) -> Tuple[bool, str, List[Dict]]:
        """
        Check if the requested leave conflicts with other approved leaves.
        Returns: (has_conflict, warning_message, conflicting_leaves)
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        conflicting_leaves = []
        
        for req_id, req in data_manager.leave_requests.items():
            if req_id == exclude_request_id:
                continue
            if req.status not in ["Manager_Approved", "Admin_Approved", "Pending"]:
                continue
            if req.employee_id == employee_id:
                continue
            
            req_start = datetime.strptime(req.start_date, "%Y-%m-%d")
            req_end = datetime.strptime(req.end_date, "%Y-%m-%d")
            
            # Check if dates overlap
            if not (end < req_start or start > req_end):
                conflicting_leaves.append({
                    "employee_id": req.employee_id,
                    "employee_name": req.employee_name,
                    "start_date": req.start_date,
                    "end_date": req.end_date,
                    "leave_type": req.leave_type,
                    "status": req.status,
                })
        
        if len(conflicting_leaves) >= 2:
            names = ", ".join([c["employee_name"] for c in conflicting_leaves])
            message = f"⚠️ **WARNING**: {len(conflicting_leaves)} other employees have overlapping leave dates: {names}. Consider staggering leave dates for business continuity."
            return True, message, conflicting_leaves
        elif len(conflicting_leaves) == 1:
            names = conflicting_leaves[0]["employee_name"]
            message = f"ℹ️ **Note**: {names} also has leave during this period."
            return False, message, conflicting_leaves
        
        return False, "", []
    
    @staticmethod
    def get_department_conflicts(
        data_manager: DataManager,
        department: str,
        start_date: str,
        end_date: str,
        exclude_employee_id: str = None
    ) -> List[Dict]:
        """Get conflicts within the same department"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        conflicts = []
        department_employees = [
            e for e in data_manager.employees.values()
            if e.department == department and e.id != exclude_employee_id
        ]
        
        for req in data_manager.leave_requests.values():
            if req.status not in ["Manager_Approved", "Admin_Approved", "Pending"]:
                continue
            if req.employee_id not in [e.id for e in department_employees]:
                continue
            
            req_start = datetime.strptime(req.start_date, "%Y-%m-%d")
            req_end = datetime.strptime(req.end_date, "%Y-%m-%d")
            
            if not (end < req_start or start > req_end):
                conflicts.append({
                    "employee_name": req.employee_name,
                    "leave_type": req.leave_type,
                    "dates": f"{req.start_date} to {req.end_date}",
                })
        
        return conflicts


# ============== STREAMLIT UI ==============
def init_session_state():
    """Initialize session state variables"""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    if 'calculator' not in st.session_state:
        st.session_state.calculator = LeaveCalculator()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'employee_id' not in st.session_state:
        st.session_state.employee_id = None


def render_login():
    """Render login page"""
    st.title("🔐 Login - UAE Leave Management System")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="background-color: #1e3a5f; padding: 30px; border-radius: 15px; border: 2px solid #4a90d9; text-align: center;">
            <h2 style="color: #ffffff; margin-bottom: 20px;">🇦🇪 Welcome</h2>
            <p style="color: #e0e0e0; margin-bottom: 20px;">
                Please login with your credentials to access the system.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submitted:
                data_manager = st.session_state.data_manager
                auth = AuthManager()
                
                if username in data_manager.users:
                    user = data_manager.users[username]
                    if user.is_active and auth.verify_password(password, user.password_hash, user.salt):
                        # Login successful
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.session_state.user_role = user.role
                        st.session_state.employee_id = user.employee_id
                        
                        # Update last login
                        user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data_manager.save_data()
                        
                        st.success(f"✅ Welcome, {username}!")
                        st.rerun()
                    else:
                        if not user.is_active:
                            st.error("❌ Your account has been deactivated. Please contact admin.")
                        else:
                            st.error("❌ Invalid password. Please try again.")
                else:
                    st.error("❌ Username not found. Please check your username.")
        
        # Password change recommendation for first-time login
        st.info("🔒 For security, please change default passwords after first login in User Management.")


def logout():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    st.session_state.employee_id = None
    st.rerun()


def render_header():
    """Render the app header with user info"""
    # Top bar with user info and logout
    if st.session_state.authenticated:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("🇦🇪 UAE Annual Leave Management System")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            user_badge = {
                "admin": "🔴 Admin",
                "manager": "🟢 Manager", 
                "employee": "🔵 Employee"
            }.get(st.session_state.user_role, "⚪ User")
            
            st.markdown(f"""
            <div style="text-align: right; padding: 10px; background-color: #1e3a5f; border-radius: 8px;">
                <span style="color: #ffffff; font-size: 14px;">
                    {user_badge} | <strong>{st.session_state.current_user}</strong>
                </span>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Logout", use_container_width=True):
                logout()
    else:
        st.title("🇦🇪 UAE Annual Leave Management System")
    
    st.markdown("""
    <div style="background-color: #1e3a5f; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #4a90d9;">
        <h4 style="margin: 0; color: #ffffff;">📋 Compliant with UAE Federal Decree Law No. 33 of 2021</h4>
        <p style="margin: 5px 0 0 0; font-size: 14px; color: #e0e0e0;">
            This system helps manage employee leave entitlements while ensuring compliance with UAE Labour Law.
            The system automatically detects conflicts when 2+ employees are on leave simultaneously.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_dashboard(data_manager: DataManager):
    """Render the main dashboard"""
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_employees = len(data_manager.employees)
    active_requests = sum(1 for r in data_manager.leave_requests.values() if r.status in ["Pending", "Admin_Approved"])
    approved_this_month = sum(
        1 for r in data_manager.leave_requests.values()
        if r.status == "Manager_Approved" and datetime.strptime(r.start_date, "%Y-%m-%d").month == datetime.now().month
    )
    on_leave_today = sum(
        1 for r in data_manager.leave_requests.values()
        if r.status == "Manager_Approved"
        and datetime.strptime(r.start_date, "%Y-%m-%d") <= datetime.now()
        and datetime.strptime(r.end_date, "%Y-%m-%d") >= datetime.now()
    )
    
    with col1:
        st.metric("Total Employees", total_employees)
    with col2:
        st.metric("Pending Requests", active_requests)
    with col3:
        st.metric("Approved (This Month)", approved_this_month)
    with col4:
        st.metric("On Leave Today", on_leave_today)
    
    # Today's leave overview
    st.subheader("🗓️ Who's On Leave Today")
    today = datetime.now().strftime("%Y-%m-%d")
    on_leave_today_list = []
    
    for req in data_manager.leave_requests.values():
        if req.status == "Manager_Approved":
            if req.start_date <= today <= req.end_date:
                emp = data_manager.employees.get(req.employee_id)
                on_leave_today_list.append({
                    "Name": req.employee_name,
                    "Department": emp.department if emp else "N/A",
                    "Leave Type": req.leave_type,
                    "Until": req.end_date,
                })
    
    if on_leave_today_list:
        st.dataframe(pd.DataFrame(on_leave_today_list), use_container_width=True)
    else:
        st.info("No one is on leave today.")
    
    # Upcoming leaves
    st.subheader("📅 Upcoming Leaves (Next 30 Days)")
    upcoming = []
    today_dt = datetime.now()
    
    for req in data_manager.leave_requests.values():
        if req.status == "Manager_Approved":
            start = datetime.strptime(req.start_date, "%Y-%m-%d")
            if today_dt <= start <= today_dt + timedelta(days=30):
                emp = data_manager.employees.get(req.employee_id)
                upcoming.append({
                    "Name": req.employee_name,
                    "Department": emp.department if emp else "N/A",
                    "Leave Type": req.leave_type,
                    "From": req.start_date,
                    "To": req.end_date,
                    "Days": req.days_requested,
                })
    
    if upcoming:
        upcoming_df = pd.DataFrame(upcoming).sort_values("From")
        st.dataframe(upcoming_df, use_container_width=True)
    else:
        st.info("No upcoming leaves in the next 30 days.")
    
    # Conflict warnings
    st.subheader("⚠️ Leave Conflict Alerts")
    conflicts = []
    approved_requests = [r for r in data_manager.leave_requests.values() if r.status == "Manager_Approved"]
    
    for i, req1 in enumerate(approved_requests):
        for req2 in approved_requests[i+1:]:
            start1 = datetime.strptime(req1.start_date, "%Y-%m-%d")
            end1 = datetime.strptime(req1.end_date, "%Y-%m-%d")
            start2 = datetime.strptime(req2.start_date, "%Y-%m-%d")
            end2 = datetime.strptime(req2.end_date, "%Y-%m-%d")
            
            if not (end1 < start2 or start1 > end2):
                emp1 = data_manager.employees.get(req1.employee_id)
                emp2 = data_manager.employees.get(req2.employee_id)
                if emp1 and emp2 and emp1.department == emp2.department:
                    conflicts.append({
                        "Department": emp1.department,
                        "Employee 1": req1.employee_name,
                        "Employee 2": req2.employee_name,
                        "Dates": f"{max(start1, start2).strftime('%Y-%m-%d')} to {min(end1, end2).strftime('%Y-%m-%d')}",
                    })
    
    if conflicts:
        st.error("⚠️ **Same Department Conflicts Detected!**")
        st.dataframe(pd.DataFrame(conflicts), use_container_width=True)
    else:
        st.success("✅ No department conflicts detected.")


def render_employee_management(data_manager: DataManager):
    """Render employee management section"""
    st.header("👥 Employee Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["View Employees", "Add Employee", "Edit/Delete", "📥 Bulk Import"])
    
    with tab1:
        if data_manager.employees:
            emp_data = []
            for emp in data_manager.employees.values():
                # Calculate leave balance based on UAE law
                join_date = datetime.strptime(emp.join_date, "%Y-%m-%d")
                years_of_service = (datetime.now() - join_date).days / 365.25
                
                emp_data.append({
                    "ID": emp.id,
                    "Name": emp.name,
                    "Email": emp.email,
                    "Department": emp.department,
                    "Position": emp.position,
                    "Join Date": emp.join_date,
                    "Years of Service": round(years_of_service, 1),
                    "Leave Balance": emp.annual_leave_balance,
                    "Status": emp.status,
                })
            
            df = pd.DataFrame(emp_data)
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                dept_filter = st.multiselect(
                    "Filter by Department",
                    options=df["Department"].unique(),
                    default=[]
                )
            with col2:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=["Active", "Inactive"],
                    default=["Active"]
                )
            
            if dept_filter:
                df = df[df["Department"].isin(dept_filter)]
            if status_filter:
                df = df[df["Status"].isin(status_filter)]
            
            st.dataframe(df, use_container_width=True)
            
            # Summary statistics
            st.subheader("Department Summary")
            dept_summary = df.groupby("Department").agg({
                "ID": "count",
                "Leave Balance": "mean"
            }).round(1)
            dept_summary.columns = ["Employee Count", "Avg Leave Balance"]
            st.dataframe(dept_summary, use_container_width=True)
        else:
            st.info("No employees found. Add employees to get started.")
    
    with tab2:
        st.subheader("Add New Employee")
        with st.form("add_employee_form"):
            col1, col2 = st.columns(2)
            with col1:
                emp_id = st.text_input("Employee ID", value=f"EMP{len(data_manager.employees)+1:03d}")
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                department = st.selectbox(
                    "Department",
                    ["Administration", "Finance & Accounting", "IT", "Legal", "Management", "Operations", "Projects", "Sales & Marketing", "Engineering", "HR", "Customer Service", "Other"]
                )
            with col2:
                position = st.text_input("Position")
                join_date = st.date_input("Join Date", value=datetime.now())
                employment_type = st.selectbox(
                    "Employment Type",
                    ["Full-time", "Part-time", "Contract", "Intern"]
                )
                initial_leave = st.number_input("Initial Leave Balance (Days)", min_value=0.0, max_value=60.0, value=30.0)
            
            submitted = st.form_submit_button("Add Employee", type="primary")
            if submitted:
                if name and email and position:
                    new_employee = Employee(
                        id=emp_id,
                        name=name,
                        email=email,
                        department=department,
                        position=position,
                        join_date=join_date.strftime("%Y-%m-%d"),
                        employment_type=employment_type,
                        annual_leave_balance=initial_leave,
                        status="Active"
                    )
                    data_manager.add_employee(new_employee)
                    st.success(f"✅ Employee '{name}' added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields.")
    
    with tab3:
        st.subheader("Edit/Delete Employee")
        if data_manager.employees:
            selected_emp = st.selectbox(
                "Select Employee",
                options=list(data_manager.employees.values()),
                format_func=lambda x: f"{x.name} ({x.id})"
            )
            
            if selected_emp:
                with st.form("edit_employee_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Full Name", value=selected_emp.name)
                        new_email = st.text_input("Email", value=selected_emp.email)
                        dept_options = ["Administration", "Finance & Accounting", "IT", "Legal", "Management", "Operations", "Projects", "Sales & Marketing", "Engineering", "HR", "Customer Service", "Other"]
                        # Handle case where department is not in the list
                        try:
                            dept_index = dept_options.index(selected_emp.department)
                        except ValueError:
                            dept_index = 0  # Default to first option
                        new_dept = st.selectbox(
                            "Department",
                            dept_options,
                            index=dept_index
                        )
                    with col2:
                        new_position = st.text_input("Position", value=selected_emp.position)
                        new_status = st.selectbox(
                            "Status",
                            ["Active", "Inactive"],
                            index=0 if selected_emp.status == "Active" else 1
                        )
                        new_balance = st.number_input(
                            "Leave Balance",
                            min_value=0.0,
                            max_value=60.0,
                            value=float(selected_emp.annual_leave_balance)
                        )
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        update_btn = st.form_submit_button("Update Employee", type="primary")
                    with col4:
                        delete_btn = st.form_submit_button("Delete Employee", type="secondary")
                    
                    if update_btn:
                        data_manager.update_employee(
                            selected_emp.id,
                            name=new_name,
                            email=new_email,
                            department=new_dept,
                            position=new_position,
                            status=new_status,
                            annual_leave_balance=new_balance
                        )
                        st.success("✅ Employee updated successfully!")
                        st.rerun()
                    
                    if delete_btn:
                        # Check if employee has pending/approved leave
                        has_leave = any(
                            r.employee_id == selected_emp.id and r.status in ["Pending", "Approved"]
                            for r in data_manager.leave_requests.values()
                        )
                        if has_leave:
                            st.error("Cannot delete employee with pending or approved leave requests.")
                        else:
                            data_manager.delete_employee(selected_emp.id)
                            st.success("✅ Employee deleted successfully!")
                            st.rerun()
    
    with tab4:
        st.subheader("📥 Bulk Data Import")
        
        st.markdown("""
        Import employees and leave records in bulk using JSON, Excel, or CSV files.
        """)
        
        import_type = st.selectbox(
            "Select Import Type",
            ["👤 Employee Data (JSON)", "👤 Employee Data (Excel/CSV)", "📅 Leave Data (JSON)", "📅 Leave Data (Excel/CSV)"],
            help="Choose the type of data you want to import"
        )
        
        if import_type == "👤 Employee Data (JSON)":
            st.markdown("""
            **JSON File Format:**
            ```json
            {
                "EMP001": {
                    "id": "EMP001",
                    "name": "Employee Name",
                    "email": "email@example.com",
                    "department": "Department",
                    "position": "Position",
                    "join_date": "2023-01-15",
                    "employment_type": "Full-time",
                    "annual_leave_balance": 30.0,
                    "status": "Active",
                    "nationality": "UAE",
                    "gender": "Male"
                }
            }
            ```
            """)
            
            uploaded_file = st.file_uploader(
                "Upload Employee JSON File",
                type=['json'],
                help="Upload your employees.json file"
            )
            
            if uploaded_file is not None:
                try:
                    import json
                    data = json.load(uploaded_file)
                    
                    st.markdown(f"**Preview:** Found {len(data)} employee(s)")
                    
                    # Show preview
                    preview_data = []
                    for emp_id, emp_data in list(data.items())[:5]:
                        preview_data.append({
                            "ID": emp_id,
                            "Name": emp_data.get("name", "N/A"),
                            "Email": emp_data.get("email", "N/A"),
                            "Department": emp_data.get("department", "N/A"),
                            "Position": emp_data.get("position", "N/A")
                        })
                    
                    st.dataframe(pd.DataFrame(preview_data))
                    
                    if len(data) > 5:
                        st.info(f"... and {len(data) - 5} more")
                    
                    # Import options
                    col1, col2 = st.columns(2)
                    with col1:
                        skip_existing = st.checkbox("Skip existing employees", value=True, 
                            help="Skip employees that already exist in the system")
                    with col2:
                        create_users = st.checkbox("Create user accounts", value=True,
                            help="Automatically create login accounts for imported employees")
                    
                    if st.button("🚀 Import Employees", type="primary"):
                        success_count = 0
                        skipped_count = 0
                        error_count = 0
                        created_users = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, (emp_id, emp_data) in enumerate(data.items()):
                            progress = (i + 1) / len(data)
                            progress_bar.progress(progress)
                            status_text.text(f"Processing {i+1} of {len(data)}: {emp_data.get('name', emp_id)}")
                            
                            try:
                                # Check if employee exists
                                if emp_id in data_manager.employees:
                                    if skip_existing:
                                        skipped_count += 1
                                        continue
                                
                                # Create Employee object
                                employee = Employee(
                                    id=emp_id,
                                    name=emp_data.get("name", ""),
                                    email=emp_data.get("email", ""),
                                    department=emp_data.get("department", "Other"),
                                    position=emp_data.get("position", ""),
                                    join_date=emp_data.get("join_date", datetime.now().strftime("%Y-%m-%d")),
                                    employment_type=emp_data.get("employment_type", "Full-time"),
                                    annual_leave_balance=emp_data.get("annual_leave_balance", 30.0),
                                    status=emp_data.get("status", "Active"),
                                    nationality=emp_data.get("nationality", ""),
                                    gender=emp_data.get("gender", "Unknown")
                                )
                                
                                data_manager.add_employee(employee)
                                success_count += 1
                                
                                # Create user account if requested
                                if create_users:
                                    auth = AuthManager()
                                    username = emp_data.get("email", "").split("@")[0].lower() if emp_data.get("email") else emp_id.lower()
                                    username = username.replace(".", "_")
                                    
                                    # Ensure unique username
                                    base_username = username
                                    counter = 1
                                    while username in data_manager.users:
                                        username = f"{base_username}{counter}"
                                        counter += 1
                                    
                                    temp_password = auth.generate_temporary_password()
                                    password_hash, salt = auth.hash_password(temp_password)
                                    
                                    new_user = User(
                                        username=username,
                                        password_hash=password_hash,
                                        salt=salt,
                                        employee_id=emp_id,
                                        role="employee",
                                        is_active=True
                                    )
                                    
                                    data_manager.add_user(new_user)
                                    created_users.append({
                                        "name": emp_data.get("name", ""),
                                        "username": username,
                                        "password": temp_password
                                    })
                                
                            except Exception as e:
                                error_count += 1
                                st.error(f"Error importing {emp_id}: {str(e)}")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Show results
                        st.success(f"✅ Import Complete!")
                        st.markdown(f"""
                        **Results:**
                        - ✅ Successfully imported: {success_count}
                        - ⏭️ Skipped (existing): {skipped_count}
                        - ❌ Errors: {error_count}
                        """)
                        
                        if created_users:
                            st.markdown("#### 🔐 Created User Accounts")
                            st.warning("⚠️ Please save these credentials! They cannot be viewed again.")
                            
                            user_df = pd.DataFrame(created_users)
                            st.dataframe(user_df)
                            
                            # Download link
                            csv = user_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Credentials CSV",
                                data=csv,
                                file_name=f"employee_credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        elif import_type == "👤 Employee Data (Excel/CSV)":
            st.markdown("""
            **Excel/CSV File Format:**
            Required columns: `id`, `name`, `email`, `department`, `position`, `join_date`
            
            Optional columns: `employment_type`, `annual_leave_balance`, `status`, `nationality`, `gender`
            """)
            
            uploaded_file = st.file_uploader(
                "Upload Excel or CSV File",
                type=['xlsx', 'csv'],
                help="Upload your employee data file"
            )
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.markdown(f"**Preview:** {len(df)} employee(s) found")
                    st.dataframe(df.head(10))
                    
                    # Import options
                    col1, col2 = st.columns(2)
                    with col1:
                        skip_existing = st.checkbox("Skip existing employees", value=True)
                    with col2:
                        create_users = st.checkbox("Create user accounts", value=True)
                    
                    if st.button("🚀 Import Employees", type="primary"):
                        success_count = 0
                        skipped_count = 0
                        error_count = 0
                        created_users = []
                        
                        progress_bar = st.progress(0)
                        
                        for i, row in df.iterrows():
                            progress = (i + 1) / len(df)
                            progress_bar.progress(progress)
                            
                            try:
                                emp_id = str(row.get('id', f"EMP{i+1:03d}"))
                                
                                # Check if exists
                                if emp_id in data_manager.employees:
                                    if skip_existing:
                                        skipped_count += 1
                                        continue
                                
                                employee = Employee(
                                    id=emp_id,
                                    name=str(row.get('name', '')),
                                    email=str(row.get('email', '')),
                                    department=str(row.get('department', 'Other')),
                                    position=str(row.get('position', '')),
                                    join_date=str(row.get('join_date', datetime.now().strftime("%Y-%m-%d"))),
                                    employment_type=str(row.get('employment_type', 'Full-time')),
                                    annual_leave_balance=float(row.get('annual_leave_balance', 30.0)) if pd.notna(row.get('annual_leave_balance')) else 30.0,
                                    status=str(row.get('status', 'Active')),
                                    nationality=str(row.get('nationality', '')),
                                    gender=str(row.get('gender', 'Unknown'))
                                )
                                
                                data_manager.add_employee(employee)
                                success_count += 1
                                
                                # Create user account
                                if create_users:
                                    auth = AuthManager()
                                    email = str(row.get('email', ''))
                                    username = email.split("@")[0].lower() if email and '@' in email else emp_id.lower()
                                    username = username.replace(".", "_").replace(" ", "_")
                                    
                                    # Ensure unique
                                    base_username = username
                                    counter = 1
                                    while username in data_manager.users:
                                        username = f"{base_username}{counter}"
                                        counter += 1
                                    
                                    temp_password = auth.generate_temporary_password()
                                    password_hash, salt = auth.hash_password(temp_password)
                                    
                                    new_user = User(
                                        username=username,
                                        password_hash=password_hash,
                                        salt=salt,
                                        employee_id=emp_id,
                                        role="employee",
                                        is_active=True
                                    )
                                    
                                    data_manager.add_user(new_user)
                                    created_users.append({
                                        "name": str(row.get('name', '')),
                                        "username": username,
                                        "password": temp_password
                                    })
                                
                            except Exception as e:
                                error_count += 1
                                st.error(f"Error on row {i+1}: {str(e)}")
                        
                        progress_bar.empty()
                        
                        st.success(f"✅ Import Complete!")
                        st.markdown(f"""
                        **Results:**
                        - ✅ Successfully imported: {success_count}
                        - ⏭️ Skipped (existing): {skipped_count}
                        - ❌ Errors: {error_count}
                        """)
                        
                        if created_users:
                            st.markdown("#### 🔐 Created User Accounts")
                            st.warning("⚠️ Save these credentials! They cannot be viewed again.")
                            
                            user_df = pd.DataFrame(created_users)
                            st.dataframe(user_df)
                            
                            csv = user_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Credentials CSV",
                                data=csv,
                                file_name=f"employee_credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        elif import_type == "📅 Leave Data (JSON)":
            st.markdown("""
            **Leave Data JSON Format:**
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
                    "submitted_date": "2024-02-15",
                    "approved_by": "admin",
                    "approved_date": "2024-02-16",
                    "comments": "Approved as requested"
                }
            }
            ```
            **Status options:** `Pending`, `Admin_Approved`, `Manager_Approved`, `Rejected`, `Cancelled`
            """)
            
            uploaded_file = st.file_uploader(
                "Upload Leave Data JSON File",
                type=['json'],
                help="Upload your leave_data.json file"
            )
            
            if uploaded_file is not None:
                try:
                    data = json.load(uploaded_file)
                    
                    st.markdown(f"**Preview:** Found {len(data)} leave record(s)")
                    
                    # Show preview
                    preview_data = []
                    for leave_id, leave_data in list(data.items())[:5]:
                        emp = data_manager.employees.get(leave_data.get("employee_id", ""))
                        preview_data.append({
                            "ID": leave_id,
                            "Employee": emp.name if emp else leave_data.get("employee_id", "N/A"),
                            "Type": leave_data.get("leave_type", "N/A"),
                            "From": leave_data.get("start_date", "N/A"),
                            "To": leave_data.get("end_date", "N/A"),
                            "Status": leave_data.get("status", "N/A")
                        })
                    
                    st.dataframe(pd.DataFrame(preview_data))
                    
                    if len(data) > 5:
                        st.info(f"... and {len(data) - 5} more")
                    
                    # Import options
                    skip_invalid = st.checkbox("Skip records for non-existing employees", value=True,
                        help="Skip leave records if employee ID doesn't exist")
                    
                    update_balance = st.checkbox("Deduct leave balance for approved leaves", value=False,
                        help="Update employee leave balance (use with caution)")
                    
                    if st.button("🚀 Import Leave Data", type="primary"):
                        success_count = 0
                        skipped_count = 0
                        error_count = 0
                        invalid_employees = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i, (leave_id, leave_data) in enumerate(data.items()):
                            progress = (i + 1) / len(data)
                            progress_bar.progress(progress)
                            
                            emp_id = leave_data.get("employee_id", "")
                            status_text.text(f"Processing {i+1} of {len(data)}: {leave_id}")
                            
                            try:
                                # Check if employee exists
                                if emp_id not in data_manager.employees:
                                    if skip_invalid:
                                        skipped_count += 1
                                        invalid_employees.append(emp_id)
                                        continue
                                    else:
                                        st.warning(f"Employee {emp_id} not found, but importing anyway")
                                
                                # Create LeaveRequest object
                                leave_request = LeaveRequest(
                                    id=leave_data.get("id", leave_id),
                                    employee_id=emp_id,
                                    leave_type=leave_data.get("leave_type", "Annual Leave"),
                                    start_date=leave_data.get("start_date", datetime.now().strftime("%Y-%m-%d")),
                                    end_date=leave_data.get("end_date", datetime.now().strftime("%Y-%m-%d")),
                                    days_requested=leave_data.get("days_requested", 0),
                                    reason=leave_data.get("reason", ""),
                                    status=leave_data.get("status", "Pending"),
                                    submitted_date=leave_data.get("submitted_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                    approved_by=leave_data.get("approved_by"),
                                    approved_date=leave_data.get("approved_date"),
                                    comments=leave_data.get("comments", "")
                                )
                                
                                data_manager.add_leave_request(leave_request)
                                success_count += 1
                                
                                # Update leave balance if requested and approved
                                if update_balance and leave_request.status == "Manager_Approved":
                                    emp = data_manager.employees.get(emp_id)
                                    if emp:
                                        new_balance = emp.annual_leave_balance - leave_request.days_requested
                                        data_manager.update_employee(emp_id, annual_leave_balance=new_balance)
                                
                            except Exception as e:
                                error_count += 1
                                st.error(f"Error importing {leave_id}: {str(e)}")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Show results
                        st.success(f"✅ Import Complete!")
                        st.markdown(f"""
                        **Results:**
                        - ✅ Successfully imported: {success_count}
                        - ⏭️ Skipped (invalid employee): {skipped_count}
                        - ❌ Errors: {error_count}
                        """)
                        
                        if invalid_employees and skip_invalid:
                            st.warning(f"⚠️ Skipped records for non-existing employees: {', '.join(set(invalid_employees))}")
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        elif import_type == "📅 Leave Data (Excel/CSV)":
            st.markdown("""
            **Leave Data Excel/CSV Format:**
            Required columns: `id`, `employee_id`, `leave_type`, `start_date`, `end_date`, `days_requested`
            
            Optional columns: `reason`, `status`, `submitted_date`, `approved_by`, `approved_date`, `comments`
            
            **Supported date formats:** YYYY-MM-DD or DD/MM/YYYY
            """)
            
            uploaded_file = st.file_uploader(
                "Upload Leave Data Excel or CSV File",
                type=['xlsx', 'csv'],
                help="Upload your leave data file"
            )
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.markdown(f"**Preview:** {len(df)} leave record(s) found")
                    
                    # Map common column name variations
                    column_mapping = {
                        'employee id': 'employee_id',
                        'emp_id': 'employee_id',
                        'emp id': 'employee_id',
                        'leave type': 'leave_type',
                        'type': 'leave_type',
                        'start date': 'start_date',
                        'from': 'start_date',
                        'from_date': 'start_date',
                        'end date': 'end_date',
                        'to': 'end_date',
                        'to_date': 'end_date',
                        'days': 'days_requested',
                        'num_days': 'days_requested',
                        'number_of_days': 'days_requested'
                    }
                    
                    # Rename columns (case insensitive)
                    df.columns = [column_mapping.get(col.lower().strip(), col) for col in df.columns]
                    
                    st.dataframe(df.head(10))
                    
                    # Import options
                    col1, col2 = st.columns(2)
                    with col1:
                        skip_invalid = st.checkbox("Skip records for non-existing employees", value=True)
                    with col2:
                        update_balance = st.checkbox("Deduct leave balance for approved leaves", value=False)
                    
                    if st.button("🚀 Import Leave Data", type="primary"):
                        success_count = 0
                        skipped_count = 0
                        error_count = 0
                        invalid_employees = []
                        
                        progress_bar = st.progress(0)
                        
                        for i, row in df.iterrows():
                            progress = (i + 1) / len(df)
                            progress_bar.progress(progress)
                            
                            try:
                                leave_id = str(row.get('id', f"LEAVE{i+1:05d}"))
                                emp_id = str(row.get('employee_id', ''))
                                
                                # Check if employee exists
                                if emp_id not in data_manager.employees:
                                    if skip_invalid:
                                        skipped_count += 1
                                        invalid_employees.append(emp_id)
                                        continue
                                
                                # Parse dates
                                start_date = str(row.get('start_date', ''))
                                end_date = str(row.get('end_date', ''))
                                
                                # Try different date formats
                                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                                    try:
                                        if pd.notna(row.get('start_date')):
                                            start_date = pd.to_datetime(row.get('start_date')).strftime("%Y-%m-%d")
                                        if pd.notna(row.get('end_date')):
                                            end_date = pd.to_datetime(row.get('end_date')).strftime("%Y-%m-%d")
                                        break
                                    except:
                                        continue
                                
                                # Get days requested
                                days = row.get('days_requested', 0)
                                if pd.isna(days):
                                    days = 0
                                else:
                                    days = int(float(days))
                                
                                # Get status with default
                                status = str(row.get('status', 'Pending'))
                                if status.lower() in ['approved', 'manager_approved', 'final approved']:
                                    status = 'Manager_Approved'
                                elif status.lower() in ['admin_approved', 'level 1 approved']:
                                    status = 'Admin_Approved'
                                elif status.lower() in ['rejected', 'declined', 'denied']:
                                    status = 'Rejected'
                                elif status.lower() in ['cancelled', 'canceled']:
                                    status = 'Cancelled'
                                else:
                                    status = 'Pending'
                                
                                leave_request = LeaveRequest(
                                    id=leave_id,
                                    employee_id=emp_id,
                                    leave_type=str(row.get('leave_type', 'Annual Leave')),
                                    start_date=start_date if start_date else datetime.now().strftime("%Y-%m-%d"),
                                    end_date=end_date if end_date else datetime.now().strftime("%Y-%m-%d"),
                                    days_requested=days,
                                    reason=str(row.get('reason', '')) if pd.notna(row.get('reason')) else '',
                                    status=status,
                                    submitted_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    approved_by=str(row.get('approved_by')) if pd.notna(row.get('approved_by')) else None,
                                    approved_date=str(row.get('approved_date')) if pd.notna(row.get('approved_date')) else None,
                                    comments=str(row.get('comments', '')) if pd.notna(row.get('comments')) else ''
                                )
                                
                                data_manager.add_leave_request(leave_request)
                                success_count += 1
                                
                                # Update leave balance if requested and approved
                                if update_balance and status == 'Manager_Approved':
                                    emp = data_manager.employees.get(emp_id)
                                    if emp:
                                        new_balance = emp.annual_leave_balance - days
                                        data_manager.update_employee(emp_id, annual_leave_balance=new_balance)
                                
                            except Exception as e:
                                error_count += 1
                                st.error(f"Error on row {i+1}: {str(e)}")
                        
                        progress_bar.empty()
                        
                        st.success(f"✅ Import Complete!")
                        st.markdown(f"""
                        **Results:**
                        - ✅ Successfully imported: {success_count}
                        - ⏭️ Skipped (invalid employee): {skipped_count}
                        - ❌ Errors: {error_count}
                        """)
                        
                        if invalid_employees and skip_invalid:
                            st.warning(f"⚠️ Skipped records for non-existing employees: {', '.join(set(invalid_employees))}")
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")


def render_leave_request(data_manager: DataManager, calculator: LeaveCalculator):
    """Render leave request section"""
    st.header("📝 Submit Leave Request")
    
    if not data_manager.employees:
        st.warning("No employees in the system. Please add employees first.")
        return
    
    with st.form("leave_request_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            employee = st.selectbox(
                "Select Employee",
                options=[e for e in data_manager.employees.values() if e.status == "Active"],
                format_func=lambda x: f"{x.name} ({x.department}) - Balance: {x.annual_leave_balance} days"
            )
            
            leave_type = st.selectbox(
                "Leave Type",
                options=list(LEAVE_TYPES.keys()),
                format_func=lambda x: f"{x} - {LEAVE_TYPES[x]['description']}"
            )
            
            # Show detailed UAE law information
            leave_info = LEAVE_TYPES[leave_type]
            st.markdown(f"""
            <div style="background-color: #1e3a5f; padding: 15px; border-radius: 8px; border: 1px solid #4a90d9; margin: 10px 0;">
                <h4 style="color: #ffffff; margin: 0 0 10px 0;">📋 {leave_type}</h4>
                <table style="width: 100%; color: #e0e0e0; font-size: 13px;">
                    <tr>
                        <td style="padding: 4px; width: 30%;"><strong>🇦🇪 UAE Law:</strong></td>
                        <td style="padding: 4px;">{leave_info['uae_law']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><strong>📊 Entitlement:</strong></td>
                        <td style="padding: 4px;">{leave_info['entitlement']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><strong>💰 Payment:</strong></td>
                        <td style="padding: 4px;">{leave_info['payment']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><strong>📋 Requirements:</strong></td>
                        <td style="padding: 4px;">{leave_info['requirements']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><strong>🔄 Carry Forward:</strong></td>
                        <td style="padding: 4px;">{leave_info['carry_forward']}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Start Date", min_value=datetime.now())
            with col_date2:
                end_date = st.date_input("End Date", min_value=start_date)
        
        with col2:
            # Calculate days
            calendar_days = calculator.calculate_calendar_days(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            working_days = calculator.calculate_working_days(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            st.metric("Calendar Days", calendar_days)
            st.metric("Working Days (Excl. Weekends)", working_days)
            
            # Days to request based on leave type (UAE Law)
            # Working days: Parental Leave, Study Leave (as per UAE law)
            # Calendar days: Annual Leave, Sick Leave, Maternity Leave, Bereavement Leave, etc.
            if leave_type in ["Parental Leave", "Study Leave"]:
                days_requested = working_days  # Working days per UAE law
            else:
                days_requested = calendar_days  # Calendar days for all other leave types
            
            st.metric("Days to be Deducted", days_requested)
            
            # Check leave balance for annual leave
            if leave_type == "Annual Leave":
                if employee and employee.annual_leave_balance < days_requested:
                    st.error(f"⚠️ Insufficient leave balance! Available: {employee.annual_leave_balance} days")
            
            reason = st.text_area("Reason for Leave", placeholder="Please provide details...")
        
        # Check for conflicts
        has_conflict = False
        conflict_message = ""
        conflict_details = []
        
        if employee:
            has_conflict, conflict_message, conflict_details = calculator.check_conflicts(
                data_manager,
                employee.id,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            # Check department conflicts
            dept_conflicts = calculator.get_department_conflicts(
                data_manager,
                employee.department,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                employee.id
            )
            
            if dept_conflicts:
                st.warning("⚠️ **Same Department Conflicts:**")
                for conf in dept_conflicts:
                    st.write(f"- {conf['employee_name']} ({conf['leave_type']}): {conf['dates']}")
        
        if conflict_message:
            if has_conflict:
                st.error(conflict_message)
            else:
                st.info(conflict_message)
        
        # UAE Labour Law Notice Requirements
        st.markdown("""
        <div style="background-color: #1e3a5f; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #4a90d9;">
            <span style="color: #ffffff;"><strong>📋 UAE Labour Law Notice:</strong> Employers must notify employees of leave dates at least 1 month in advance. 
            However, emergency leave requests may be considered based on company policy.</span>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Submit Request", type="primary")
        
        if submitted:
            if not reason:
                st.error("Please provide a reason for the leave.")
                return
            
            if end_date < start_date:
                st.error("End date cannot be before start date.")
                return
            
            # Check balance for annual leave
            if leave_type == "Annual Leave" and employee.annual_leave_balance < days_requested:
                st.error("Cannot submit: Insufficient leave balance.")
                return
            
            # Create leave request
            request_id = f"REQ{len(data_manager.leave_requests)+1:04d}"
            new_request = LeaveRequest(
                id=request_id,
                employee_id=employee.id,
                employee_name=employee.name,
                leave_type=leave_type,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                days_requested=days_requested,
                reason=reason,
                status="Pending",
                submitted_date=datetime.now().strftime("%Y-%m-%d"),
                conflict_warning=has_conflict,
                conflict_details=conflict_message if has_conflict else ""
            )
            
            data_manager.add_leave_request(new_request)
            
            if has_conflict:
                st.warning("✅ Request submitted with **CONFLICT WARNING**. Please review with management.")
            else:
                st.success(f"✅ Leave request submitted successfully! Request ID: {request_id}")
            
            st.rerun()


def render_leave_approvals(data_manager: DataManager):
    """Render leave approvals section"""
    st.header("✅ Leave Approvals")
    
    tab1, tab2, tab3 = st.tabs(["Pending Requests", "Approved Leaves", "All Requests"])
    
    with tab1:
        pending = [r for r in data_manager.leave_requests.values() if r.status == "Pending"]
        
        if pending:
            for req in pending:
                emp = data_manager.employees.get(req.employee_id)
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{req.employee_name}** ({emp.department if emp else 'N/A'})")
                        st.write(f"📝 {req.leave_type}: {req.start_date} to {req.end_date} ({req.days_requested} days)")
                        st.write(f"💬 {req.reason}")
                        
                        if req.conflict_warning:
                            st.error(f"⚠️ {req.conflict_details}")
                    
                    with col2:
                        st.write(f"Submitted: {req.submitted_date}")
                        st.write(f"Current Balance: {emp.annual_leave_balance if emp else 'N/A'} days")
                    
                    with col3:
                        if st.button("Approve", key=f"approve_{req.id}"):
                            # Update leave balance for annual leave
                            if req.leave_type == "Annual Leave" and emp:
                                new_balance = emp.annual_leave_balance - req.days_requested
                                data_manager.update_employee(req.employee_id, annual_leave_balance=new_balance)
                            
                            data_manager.update_leave_request(
                                req.id,
                                status="Approved",
                                approved_by="Manager",
                                approval_date=datetime.now().strftime("%Y-%m-%d")
                            )
                            st.success("Approved!")
                            st.rerun()
                        
                        if st.button("Reject", key=f"reject_{req.id}"):
                            data_manager.update_leave_request(req.id, status="Rejected")
                            st.error("Rejected!")
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No pending leave requests.")
    
    with tab2:
        approved = [r for r in data_manager.leave_requests.values() if r.status == "Manager_Approved"]
        
        if approved:
            approved_data = []
            for req in approved:
                emp = data_manager.employees.get(req.employee_id)
                approved_data.append({
                    "ID": req.id,
                    "Name": req.employee_name,
                    "Department": emp.department if emp else "N/A",
                    "Leave Type": req.leave_type,
                    "From": req.start_date,
                    "To": req.end_date,
                    "Days": req.days_requested,
                    "Approved By": req.approved_by,
                    "Approved On": req.approval_date,
                })
            
            df = pd.DataFrame(approved_data)
            st.dataframe(df, use_container_width=True)
            
            # Cancel approved leave
            st.subheader("Cancel Approved Leave")
            cancel_req = st.selectbox(
                "Select request to cancel",
                options=approved,
                format_func=lambda x: f"{x.employee_name} - {x.leave_type} ({x.start_date} to {x.end_date})"
            )
            
            if cancel_req:
                cancel_reason = st.text_input("Cancellation Reason")
                if st.button("Cancel Leave"):
                    # Restore leave balance for annual leave
                    emp = data_manager.employees.get(cancel_req.employee_id)
                    if cancel_req.leave_type == "Annual Leave" and emp:
                        new_balance = emp.annual_leave_balance + cancel_req.days_requested
                        data_manager.update_employee(cancel_req.employee_id, annual_leave_balance=new_balance)
                    
                    data_manager.update_leave_request(cancel_req.id, status="Cancelled", remarks=cancel_reason)
                    st.success("Leave cancelled and balance restored.")
                    st.rerun()
        else:
            st.info("No approved leaves.")
    
    with tab3:
        all_requests = list(data_manager.leave_requests.values())
        
        if all_requests:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.multiselect(
                    "Filter by Status",
                    options=["Pending", "Approved", "Rejected", "Cancelled"],
                    default=[]
                )
            with col2:
                type_filter = st.multiselect(
                    "Filter by Leave Type",
                    options=list(LEAVE_TYPES.keys()),
                    default=[]
                )
            
            all_data = []
            for req in all_requests:
                emp = data_manager.employees.get(req.employee_id)
                
                # Apply filters
                if status_filter and req.status not in status_filter:
                    continue
                if type_filter and req.leave_type not in type_filter:
                    continue
                
                all_data.append({
                    "ID": req.id,
                    "Name": req.employee_name,
                    "Department": emp.department if emp else "N/A",
                    "Leave Type": req.leave_type,
                    "From": req.start_date,
                    "To": req.end_date,
                    "Days": req.days_requested,
                    "Status": req.status,
                    "Submitted": req.submitted_date,
                })
            
            df = pd.DataFrame(all_data)
            st.dataframe(df, use_container_width=True)
            
            # Export option
            if st.button("Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"leave_requests_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No leave requests found.")


def render_leave_calendar(data_manager: DataManager):
    """Render leave calendar view"""
    st.header("📅 Leave Calendar")
    
    # Month/Year selector
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Year", options=range(2024, 2027), index=1)
    with col2:
        selected_month = st.selectbox("Month", options=range(1, 13), index=datetime.now().month - 1)
    
    # Department filter
    departments = list(set(e.department for e in data_manager.employees.values()))
    selected_depts = st.multiselect("Filter by Department", options=departments, default=departments)
    
    # Get approved leaves for the selected month
    month_start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        month_end = datetime(selected_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(selected_year, selected_month + 1, 1) - timedelta(days=1)
    
    approved_leaves = [
        r for r in data_manager.leave_requests.values()
        if r.status == "Manager_Approved"
        and datetime.strptime(r.start_date, "%Y-%m-%d") <= month_end
        and datetime.strptime(r.end_date, "%Y-%m-%d") >= month_start
    ]
    
    # Filter by department
    filtered_leaves = []
    for req in approved_leaves:
        emp = data_manager.employees.get(req.employee_id)
        if emp and emp.department in selected_depts:
            filtered_leaves.append({
                "employee_name": req.employee_name,
                "department": emp.department,
                "leave_type": req.leave_type,
                "start_date": req.start_date,
                "end_date": req.end_date,
                "color": LEAVE_TYPES.get(req.leave_type, {}).get("color", "#999999")
            })
    
    # Display calendar visualization
    if filtered_leaves:
        st.subheader(f"Leave Overview - {month_start.strftime('%B %Y')}")
        
        # Create a day-by-day view
        days_in_month = (month_end - month_start).days + 1
        
        for leave in filtered_leaves:
            leave_start = datetime.strptime(leave["start_date"], "%Y-%m-%d")
            leave_end = datetime.strptime(leave["end_date"], "%Y-%m-%d")
            
            # Clip to month boundaries
            display_start = max(leave_start, month_start)
            display_end = min(leave_end, month_end)
            
            start_day = display_start.day
            end_day = display_end.day
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin: 5px 0; padding: 8px; 
                        background-color: {leave['color']}20; border-left: 4px solid {leave['color']}; 
                        border-radius: 4px;">
                <div style="flex: 1;">
                    <strong>{leave['employee_name']}</strong> ({leave['department']})<br>
                    <small>{leave['leave_type']} - {leave['start_date']} to {leave['end_date']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Summary statistics
        st.subheader("Monthly Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Leave Requests", len(filtered_leaves))
        with col2:
            unique_employees = len(set(l["employee_name"] for l in filtered_leaves))
            st.metric("Employees on Leave", unique_employees)
        with col3:
            leave_by_type = {}
            for l in filtered_leaves:
                lt = l["leave_type"]
                leave_by_type[lt] = leave_by_type.get(lt, 0) + 1
            most_common = max(leave_by_type.items(), key=lambda x: x[1])[0] if leave_by_type else "N/A"
            st.metric("Most Common Leave", most_common)
    else:
        st.info(f"No approved leaves for {month_start.strftime('%B %Y')} in selected departments.")


def render_leave_entitlements():
    """Render UAE leave entitlements information"""
    st.header("📖 UAE Leave Entitlements Guide")
    
    st.markdown("""
    <div style="background-color: #1e3a5f; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #4a90d9;">
        <h4 style="color: #ffffff;">🇦🇪 Federal Decree Law No. 33 of 2021 on the Regulation of Employment Relationships</h4>
        <p style="color: #e0e0e0;">This guide outlines the leave entitlements for private sector employees in the UAE.</p>
    </div>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs(["Annual Leave", "Sick Leave", "Special Leaves", "Key Provisions", "Calculations"])
    
    with tabs[0]:
        st.subheader("🌴 Annual Leave Entitlements")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Full Year Service", "30 Calendar Days")
            st.write("After completing 1 full year of service")
        with col2:
            st.metric("6 Months - 1 Year", "2 Days per Month")
            st.write("For service exceeding 6 months but less than 1 year")
        
        st.info("""
        **Important Notes:**
        - Part-time employees are entitled to annual leave proportional to their working hours
        - Public holidays falling within annual leave are counted as part of the leave
        - Employer must notify employee of leave dates at least 1 month in advance
        """)
    
    with tabs[1]:
        st.subheader("🏥 Sick Leave Details")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Maximum Duration", "90 Calendar Days/year")
            st.metric("Full Pay Period", "First 15 Days")
            st.metric("Half Pay Period", "Next 30 Days (Days 16-45)")
        with col2:
            st.metric("Unpaid Period", "Days 46-90")
            st.metric("Maximum Consecutive", "90 Days")
            st.metric("Medical Certificate", "Required from Day 1")
        
        st.markdown("""
        #### 📝 Important Rules:
        - **Medical Certificate Required**: Must provide valid medical certificate from the first day of sickness
        - **Not During Probation**: Sick leave cannot be taken during probation period
        - **Consecutive or Intermittent**: Can be taken as consecutive days or spread throughout the year
        - **Payment Structure**:
          - Days 1-15: 100% of salary
          - Days 16-45: 50% of salary  
          - Days 46-90: No pay
        - **Termination Protection**: Employer cannot terminate employee during sick leave (with exceptions for gross misconduct)
        - **Serious Illness**: For serious illnesses, employer may grant additional unpaid leave at their discretion
        """)
        
        # Sick Leave Calculator
        st.subheader("🧮 Sick Leave Salary Calculator")
        col1, col2 = st.columns(2)
        with col1:
            basic_salary = st.number_input("Basic Salary (AED)", min_value=1000, max_value=100000, value=10000, step=500)
            sick_days = st.slider("Sick Leave Days", min_value=1, max_value=90, value=30)
        with col2:
            daily_wage = basic_salary / 30
            
            if sick_days <= 15:
                paid_days = sick_days
                half_days = 0
                unpaid_days = 0
                full_pay = daily_wage * paid_days
                half_pay = 0
                total_pay = full_pay
            elif sick_days <= 45:
                paid_days = 15
                half_days = sick_days - 15
                unpaid_days = 0
                full_pay = daily_wage * paid_days
                half_pay = (daily_wage * 0.5) * half_days
                total_pay = full_pay + half_pay
            else:
                paid_days = 15
                half_days = 30
                unpaid_days = sick_days - 45
                full_pay = daily_wage * paid_days
                half_pay = (daily_wage * 0.5) * half_days
                total_pay = full_pay + half_pay
            
            st.metric("Daily Wage", f"AED {daily_wage:.2f}")
            st.metric("Total Pay for Sick Period", f"AED {total_pay:.2f}")
            st.caption(f"Full pay: {paid_days} days | Half pay: {half_days} days | Unpaid: {unpaid_days} days")
    
    with tabs[2]:
        st.subheader("🍼 Special Leave Types")
        
        special_leaves = {
            "Maternity Leave": {
                "duration": "60 Calendar Days",
                "pay": "45 days full pay + 15 days half pay",
                "notes": "For female employees"
            },
            "Parental Leave": {
                "duration": "5 Working Days",
                "pay": "Full pay",
                "notes": "Within first 6 months of child's birth (either parent)"
            },
            "Sick Leave": {
                "duration": "Up to 90 Calendar Days/year",
                "pay": "15 days full + 30 days half + 45 days no pay",
                "notes": "Medical certificate required from first day"
            },
            "Bereavement Leave": {
                "duration": "3-5 Days",
                "pay": "Full pay",
                "notes": "Death of spouse (5 days), parent/child/sibling/grandparent/grandchild (3 days)"
            },
            "Hajj Leave": {
                "duration": "Up to 30 Days",
                "pay": "Unpaid",
                "notes": "Once during entire employment period"
            },
            "Study Leave": {
                "duration": "10 Working Days/year",
                "pay": "Full pay",
                "notes": "For employees in UAE-accredited educational institutions"
            },
        }
        
        for leave_name, details in special_leaves.items():
            with st.expander(f"📌 {leave_name}"):
                st.write(f"**Duration:** {details['duration']}")
                st.write(f"**Payment:** {details['pay']}")
                st.write(f"**Notes:** {details['notes']}")
    
    with tabs[3]:
        st.subheader("⚖️ Key Legal Provisions")
        
        provisions = [
            ("🔄 Carry Forward", "Employees can carry forward unused leave to the next year with employer consent and payment for unused days."),
            ("⏰ Time Limit", "Employer cannot prevent employee from using accrued annual leave for more than 2 consecutive years."),
            ("💰 Leave Encashment", "Unused leave upon termination must be paid based on basic salary, regardless of duration."),
            ("📅 Public Holidays", "Public holidays during annual leave count as part of the leave unless company policy is more favorable."),
            ("⚠️ Fractional Leave", "Employees leaving before using leave are entitled to payment for the fraction of the last year worked."),
        ]
        
        for icon_title, description in provisions:
            st.markdown(f"**{icon_title}** - {description}")
    
    with tabs[4]:
        st.subheader("🧮 Leave Calculation Examples")
        
        st.markdown("""
        **Example 1: Annual Leave Calculation**
        
        Employee joined on: January 1, 2023  
        Requesting leave on: February 1, 2024  
        Service completed: 1 year and 1 month  
        **Entitlement:** 30 calendar days
        
        ---
        
        **Example 2: Partial Year Calculation**
        
        Employee joined on: March 1, 2023  
        Requesting leave on: October 1, 2023  
        Service completed: 7 months  
        **Entitlement:** 7 months × 2 days = 14 calendar days
        
        ---
        
        **Example 3: Leave Salary Calculation**
        
        Basic Salary: AED 10,000  
        Daily Salary: 10,000 ÷ 30 = AED 333.33  
        30 Days Leave: 333.33 × 30 = **AED 10,000**
        """)


def render_reports(data_manager: DataManager):
    """Render reports and analytics section"""
    st.header("📊 Reports & Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Leave Summary", "Department Analysis", "Employee Report", "Leave Calendar Report"])
    
    with tab1:
        st.subheader("Leave Summary by Type")
        
        approved_requests = [r for r in data_manager.leave_requests.values() if r.status == "Manager_Approved"]
        
        if approved_requests:
            # Summary by leave type
            leave_summary = defaultdict(lambda: {"count": 0, "total_days": 0})
            for req in approved_requests:
                leave_summary[req.leave_type]["count"] += 1
                leave_summary[req.leave_type]["total_days"] += req.days_requested
            
            summary_data = []
            for leave_type, data in leave_summary.items():
                summary_data.append({
                    "Leave Type": leave_type,
                    "Number of Requests": data["count"],
                    "Total Days": data["total_days"],
                    "Average Days": round(data["total_days"] / data["count"], 1) if data["count"] > 0 else 0
                })
            
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)
            
            # Monthly trend
            st.subheader("Monthly Leave Trend")
            monthly_data = defaultdict(int)
            for req in approved_requests:
                month_key = datetime.strptime(req.start_date, "%Y-%m-%d").strftime("%Y-%m")
                monthly_data[month_key] += req.days_requested
            
            trend_df = pd.DataFrame([
                {"Month": k, "Total Days": v} for k, v in sorted(monthly_data.items())
            ])
            st.line_chart(trend_df.set_index("Month"))
        else:
            st.info("No approved leaves to analyze.")
    
    with tab2:
        st.subheader("Department Analysis")
        
        if approved_requests:
            dept_summary = defaultdict(lambda: {"requests": 0, "days": 0, "employees": set()})
            
            for req in approved_requests:
                emp = data_manager.employees.get(req.employee_id)
                if emp:
                    dept_summary[emp.department]["requests"] += 1
                    dept_summary[emp.department]["days"] += req.days_requested
                    dept_summary[emp.department]["employees"].add(req.employee_id)
            
            dept_data = []
            for dept, data in dept_summary.items():
                dept_data.append({
                    "Department": dept,
                    "Leave Requests": data["requests"],
                    "Total Days": data["days"],
                    "Employees on Leave": len(data["employees"]),
                })
            
            df = pd.DataFrame(dept_data)
            st.dataframe(df, use_container_width=True)
            
            # Bar chart
            st.bar_chart(df.set_index("Department")[["Total Days"]])
        else:
            st.info("No approved leaves to analyze.")
    
    with tab3:
        st.subheader("Individual Employee Report")
        
        if data_manager.employees:
            selected_emp = st.selectbox(
                "Select Employee",
                options=list(data_manager.employees.values()),
                format_func=lambda x: f"{x.name} ({x.id})"
            )
            
            if selected_emp:
                emp_requests = [r for r in data_manager.leave_requests.values() if r.employee_id == selected_emp.id]
                current_year = datetime.now().year
                
                # Filter requests for this year
                this_year_requests = [
                    r for r in emp_requests 
                    if datetime.strptime(r.start_date, "%Y-%m-%d").year == current_year
                ]
                
                # Overall metrics
                st.markdown(f"### 📊 Overall Statistics (All Time)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Requests", len(emp_requests))
                with col2:
                    approved_count = sum(1 for r in emp_requests if r.status == "Manager_Approved")
                    st.metric("Approved", approved_count)
                with col3:
                    pending_count = sum(1 for r in emp_requests if r.status == "Pending")
                    st.metric("Pending", pending_count)
                with col4:
                    total_days = sum(r.days_requested for r in emp_requests if r.status == "Manager_Approved")
                    st.metric("Total Days Taken", total_days)
                
                # This Year Summary
                st.markdown(f"### 📅 This Year ({current_year}) Summary")
                
                if this_year_requests:
                    this_year_approved = [r for r in this_year_requests if r.status == "Manager_Approved"]
                    total_days_this_year = sum(r.days_requested for r in this_year_approved)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"Requests in {current_year}", len(this_year_requests))
                    with col2:
                        st.metric(f"Approved in {current_year}", len(this_year_approved))
                    with col3:
                        st.metric(f"Days Taken in {current_year}", total_days_this_year)
                    
                    # Leave breakdown by month
                    st.markdown(f"#### 📆 Monthly Breakdown ({current_year})")
                    
                    monthly_breakdown = defaultdict(lambda: {"count": 0, "days": 0, "leaves": []})
                    for req in this_year_approved:
                        month = datetime.strptime(req.start_date, "%Y-%m-%d").strftime("%B")
                        monthly_breakdown[month]["count"] += 1
                        monthly_breakdown[month]["days"] += req.days_requested
                        monthly_breakdown[month]["leaves"].append({
                            "type": req.leave_type,
                            "days": req.days_requested,
                            "dates": f"{req.start_date} to {req.end_date}"
                        })
                    
                    # Display monthly table
                    month_data = []
                    month_order = ["January", "February", "March", "April", "May", "June",
                                  "July", "August", "September", "October", "November", "December"]
                    
                    for month in month_order:
                        if month in monthly_breakdown:
                            data = monthly_breakdown[month]
                            leave_types = ", ".join(set(l["type"] for l in data["leaves"]))
                            month_data.append({
                                "Month": month,
                                "Leave Requests": data["count"],
                                "Total Days": data["days"],
                                "Leave Types": leave_types
                            })
                    
                    if month_data:
                        st.dataframe(pd.DataFrame(month_data), use_container_width=True)
                        
                        # Monthly bar chart
                        chart_df = pd.DataFrame(month_data)
                        st.bar_chart(chart_df.set_index("Month")[["Total Days"]], use_container_width=True)
                    
                    # Detailed leave list for this year
                    with st.expander(f"📋 View All {current_year} Leave Details"):
                        for i, req in enumerate(this_year_approved, 1):
                            month = datetime.strptime(req.start_date, "%Y-%m-%d").strftime("%B")
                            st.markdown(f"""
                            <div style="background-color: #1e3a5f; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #4a90d9;">
                                <strong>#{i} - {req.leave_type}</strong> ({req.days_requested} days)<br>
                                <span style="color: #aaaaaa;">📅 {req.start_date} to {req.end_date} | Month: {month}</span><br>
                                <span style="color: #aaaaaa;">💬 {req.reason}</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info(f"ℹ️ No leave taken in {current_year}")
                
                # Leave history (all time)
                st.markdown("### 📜 Complete Leave History (All Time)")
                
                if emp_requests:
                    # Add year column for sorting
                    history_data = []
                    for req in emp_requests:
                        req_date = datetime.strptime(req.start_date, "%Y-%m-%d")
                        history_data.append({
                            "Leave Type": req.leave_type,
                            "Year": req_date.year,
                            "Month": req_date.strftime("%B"),
                            "From": req.start_date,
                            "To": req.end_date,
                            "Days": req.days_requested,
                            "Status": req.status,
                        })
                    
                    history_df = pd.DataFrame(history_data).sort_values(["Year", "From"], ascending=[False, False])
                    st.dataframe(history_df, use_container_width=True)
                    
                    # Leave type breakdown
                    st.markdown("#### 📊 Leave Type Breakdown (All Time)")
                    type_breakdown = defaultdict(lambda: {"count": 0, "days": 0})
                    for req in emp_requests:
                        if req.status == "Manager_Approved":
                            type_breakdown[req.leave_type]["count"] += 1
                            type_breakdown[req.leave_type]["days"] += req.days_requested
                    
                    type_data = []
                    for leave_type, data in type_breakdown.items():
                        type_data.append({
                            "Leave Type": leave_type,
                            "Times Taken": data["count"],
                            "Total Days": data["days"]
                        })
                    
                    if type_data:
                        st.dataframe(pd.DataFrame(type_data), use_container_width=True)
                else:
                    st.info("No leave history for this employee.")
        else:
            st.info("No employees in the system.")
    
    with tab4:
        st.subheader("📅 Leave Calendar Report")
        st.markdown("View all employees on leave between specific dates.")
        
        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "From Date",
                value=datetime.now(),
                key="report_start_date"
            )
        with col2:
            end_date = st.date_input(
                "To Date",
                value=datetime.now() + pd.Timedelta(days=30),
                key="report_end_date"
            )
        
        # Convert to string format for comparison
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Validate date range
        if start_date > end_date:
            st.error("❌ Start date must be before end date!")
        else:
            # Filter leave requests that overlap with the selected date range
            overlapping_leaves = []
            
            for req in data_manager.leave_requests.values():
                # Check if leave overlaps with selected date range
                # Leave overlaps if: leave_start <= range_end AND leave_end >= range_start
                leave_starts_before_range_ends = req.start_date <= end_date_str
                leave_ends_after_range_starts = req.end_date >= start_date_str
                
                if leave_starts_before_range_ends and leave_ends_after_range_starts:
                    emp = data_manager.employees.get(req.employee_id)
                    if emp:
                        overlapping_leaves.append({
                            "Employee ID": req.employee_id,
                            "Employee Name": req.employee_name,
                            "Department": emp.department,
                            "Leave Type": req.leave_type,
                            "From": req.start_date,
                            "To": req.end_date,
                            "Days": req.days_requested,
                            "Status": req.status
                        })
            
            # Display results
            if overlapping_leaves:
                # Sort by start date
                overlapping_leaves.sort(key=lambda x: x["From"])
                
                # Summary metrics
                st.markdown("### 📊 Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Employees on Leave", len(set(l["Employee ID"] for l in overlapping_leaves)))
                with col2:
                    st.metric("Total Leave Records", len(overlapping_leaves))
                with col3:
                    total_days = sum(l["Days"] for l in overlapping_leaves)
                    st.metric("Total Days", total_days)
                with col4:
                    unique_depts = len(set(l["Department"] for l in overlapping_leaves))
                    st.metric("Departments Affected", unique_depts)
                
                # Department breakdown
                st.markdown("### 📈 Department Breakdown")
                dept_breakdown = defaultdict(lambda: {"count": 0, "employees": set()})
                for leave in overlapping_leaves:
                    dept_breakdown[leave["Department"]]["count"] += 1
                    dept_breakdown[leave["Department"]]["employees"].add(leave["Employee ID"])
                
                dept_data = []
                for dept, data in sorted(dept_breakdown.items()):
                    dept_data.append({
                        "Department": dept,
                        "Employees on Leave": len(data["employees"]),
                        "Leave Records": data["count"]
                    })
                
                st.dataframe(pd.DataFrame(dept_data), use_container_width=True)
                
                # Detailed leave table
                st.markdown("### 📋 Detailed Leave Schedule")
                
                # Create a styled dataframe
                df = pd.DataFrame(overlapping_leaves)
                
                # Add a color indicator for status
                def color_status(val):
                    if val == "Manager_Approved":
                        return 'background-color: #2ecc71; color: white'
                    elif val == "Pending":
                        return 'background-color: #f39c12; color: white'
                    elif val == "Admin_Approved":
                        return 'background-color: #3498db; color: white'
                    elif val == "Rejected":
                        return 'background-color: #e74c3c; color: white'
                    return ''
                
                styled_df = df.style.applymap(color_status, subset=['Status'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Timeline view
                st.markdown("### 📅 Timeline View")
                
                # Group by date
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                timeline_data = []
                
                for single_date in date_range:
                    date_str = single_date.strftime("%Y-%m-%d")
                    employees_on_leave = []
                    
                    for leave in overlapping_leaves:
                        if leave["From"] <= date_str <= leave["To"]:
                            employees_on_leave.append(f"{leave['Employee Name']} ({leave['Leave Type']})")
                    
                    if employees_on_leave:
                        timeline_data.append({
                            "Date": single_date.strftime("%Y-%m-%d (%a)"),
                            "Employees on Leave": len(employees_on_leave),
                            "Names": ", ".join(employees_on_leave[:3]) + ("..." if len(employees_on_leave) > 3 else "")
                        })
                
                if timeline_data:
                    timeline_df = pd.DataFrame(timeline_data)
                    st.dataframe(timeline_df, use_container_width=True)
                    
                    # Chart showing daily count
                    st.markdown("#### 📊 Daily Leave Count")
                    chart_data = timeline_df.copy()
                    chart_data["Date_Only"] = chart_data["Date"].str.extract(r'(\d{4}-\d{2}-\d{2})')
                    st.line_chart(chart_data.set_index("Date_Only")[["Employees on Leave"]], use_container_width=True)
                
                # Export option
                st.markdown("### 📥 Export")
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Report as CSV",
                    data=csv,
                    file_name=f"leave_report_{start_date_str}_to_{end_date_str}.csv",
                    mime="text/csv"
                )
            else:
                st.info("ℹ️ No employees on leave during the selected date range.")


def render_user_management(data_manager: DataManager):
    """Render user management section (Admin only)"""
    st.header("👤 User Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["View Users", "Create User", "Reset Password", "Change My Password"])
    
    with tab1:
        st.subheader("System Users")
        if data_manager.users:
            user_data = []
            for user in data_manager.users.values():
                emp = data_manager.employees.get(user.employee_id)
                user_data.append({
                    "Username": user.username,
                    "Role": user.role.capitalize(),
                    "Employee": emp.name if emp else "N/A",
                    "Department": emp.department if emp else "N/A",
                    "Status": "Active" if user.is_active else "Inactive",
                    "Created": user.created_date,
                    "Last Login": user.last_login or "Never",
                })
            
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No users found.")
    
    with tab2:
        st.subheader("Create New User Account")
        
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username", placeholder="e.g., john.doe")
                role = st.selectbox(
                    "User Role",
                    options=list(USER_ROLES.keys()),
                    format_func=lambda x: USER_ROLES[x]
                )
                
                # Employee selection
                available_employees = [
                    e for e in data_manager.employees.values()
                    if e.id not in [u.employee_id for u in data_manager.users.values()]
                ]
                
                if available_employees:
                    employee = st.selectbox(
                        "Link to Employee",
                        options=available_employees,
                        format_func=lambda x: f"{x.name} ({x.id} - {x.department})"
                    )
                else:
                    st.warning("All employees already have user accounts.")
                    employee = None
            
            with col2:
                password_option = st.radio(
                    "Password Option",
                    ["Generate Temporary Password", "Set Custom Password"]
                )
                
                if password_option == "Set Custom Password":
                    custom_password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Min 6 characters"
                    )
                else:
                    custom_password = None
                    st.info("A secure temporary password will be generated.")
            
            submitted = st.form_submit_button("Create User", type="primary")
            
            if submitted:
                if not username:
                    st.error("Username is required.")
                    return
                
                if username in data_manager.users:
                    st.error("Username already exists.")
                    return
                
                auth = AuthManager()
                is_valid, msg = auth.validate_username(username)
                if not is_valid:
                    st.error(msg)
                    return
                
                if not employee:
                    st.error("Please select an employee.")
                    return
                
                # Generate or use custom password
                if password_option == "Generate Temporary Password":
                    password = auth.generate_temporary_password()
                else:
                    password = custom_password
                    if len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                        return
                
                # Create user
                password_hash, salt = auth.hash_password(password)
                new_user = User(
                    username=username,
                    password_hash=password_hash,
                    salt=salt,
                    employee_id=employee.id,
                    role=role,
                    is_active=True
                )
                
                data_manager.add_user(new_user)
                
                st.success(f"✅ User '{username}' created successfully!")
                st.markdown(f"""
                <div style="background-color: #1a5c1a; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <h4 style="color: #ffffff; margin: 0;">🔐 Login Credentials</h4>
                    <p style="color: #ffffff; margin: 10px 0;">
                        <strong>Username:</strong> {username}<br>
                        <strong>Password:</strong> {password}<br>
                        <strong>Role:</strong> {role.capitalize()}
                    </p>
                    <p style="color: #ffff00; font-size: 12px;">
                        ⚠️ Please save these credentials! The password cannot be viewed again.
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader("Reset User Password")
        
        if data_manager.users:
            user_to_reset = st.selectbox(
                "Select User",
                options=list(data_manager.users.values()),
                format_func=lambda x: f"{x.username} ({x.role})"
            )
            
            if user_to_reset:
                new_password = st.text_input(
                    "New Password",
                    type="password",
                    placeholder="Min 6 characters"
                )
                
                if st.button("Reset Password"):
                    if len(new_password) < 6:
                        st.error("Password must be at least 6 characters.")
                        return
                    
                    auth = AuthManager()
                    password_hash, salt = auth.hash_password(new_password)
                    
                    data_manager.update_user(
                        user_to_reset.username,
                        password_hash=password_hash,
                        salt=salt
                    )
                    
                    st.success(f"✅ Password reset for '{user_to_reset.username}'")
        else:
            st.info("No users to reset.")
    
    with tab4:
        st.subheader("🔐 Change My Password")
        
        current_user = st.session_state.current_user
        st.markdown(f"**Current User:** `{current_user}`")
        
        with st.form("change_my_password_form"):
            st.markdown("### Enter Password Details")
            
            current_password = st.text_input(
                "Current Password",
                type="password",
                placeholder="Enter your current password"
            )
            
            new_password = st.text_input(
                "New Password",
                type="password",
                placeholder="Min 8 characters, include numbers and symbols"
            )
            
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter new password"
            )
            
            submitted = st.form_submit_button("Change Password", type="primary")
            
            if submitted:
                if not current_password or not new_password or not confirm_password:
                    st.error("All fields are required.")
                    return
                
                # Verify current password
                user = data_manager.users.get(current_user)
                if not user:
                    st.error("User not found.")
                    return
                
                auth = AuthManager()
                if not auth.verify_password(current_password, user.password_hash, user.salt):
                    st.error("❌ Current password is incorrect.")
                    return
                
                # Validate new password
                if len(new_password) < 8:
                    st.error("New password must be at least 8 characters long.")
                    return
                
                if new_password != confirm_password:
                    st.error("❌ New passwords do not match.")
                    return
                
                if current_password == new_password:
                    st.error("❌ New password must be different from current password.")
                    return
                
                # Update password
                password_hash, salt = auth.hash_password(new_password)
                data_manager.update_user(
                    current_user,
                    password_hash=password_hash,
                    salt=salt
                )
                
                st.success("✅ Password changed successfully!")
                st.info("🔒 Your password has been updated. Please use the new password for your next login.")


def render_employee_dashboard(data_manager: DataManager, calculator: LeaveCalculator):
    """Render employee-specific dashboard"""
    emp_id = st.session_state.employee_id
    employee = data_manager.employees.get(emp_id)
    
    if not employee:
        st.error("Employee record not found.")
        return
    
    st.header(f"👋 Welcome, {employee.name}!")
    
    # Employee stats
    col1, col2, col3, col4 = st.columns(4)
    
    my_requests = [r for r in data_manager.leave_requests.values() if r.employee_id == emp_id]
    pending = sum(1 for r in my_requests if r.status == "Pending")
    admin_approved = sum(1 for r in my_requests if r.status == "Admin_Approved")
    final_approved = sum(1 for r in my_requests if r.status == "Manager_Approved")
    total_taken = sum(r.days_requested for r in my_requests if r.status == "Manager_Approved")
    
    with col1:
        st.metric("Leave Balance", f"{employee.annual_leave_balance} days")
    with col2:
        st.metric("Pending Approval", pending)
    with col3:
        st.metric("Approved (Final)", final_approved)
    with col4:
        st.metric("Total Days Taken", total_taken)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Submit New Leave Request", use_container_width=True):
            st.session_state.show_leave_form = True
    
    with col2:
        if st.button("📊 View My Leave History", use_container_width=True):
            st.session_state.show_history = True
    
    # My Leave Requests
    st.subheader("📋 My Leave Requests")
    
    if my_requests:
        my_requests_sorted = sorted(my_requests, key=lambda x: x.submitted_date, reverse=True)
        
        for req in my_requests_sorted:
            # Status color and icon
            status_config = {
                "Pending": ("⏳", "#FF9800", "Awaiting Admin/HR Review"),
                "Admin_Approved": ("✅", "#4CAF50", "Approved by Admin - Awaiting Manager"),
                "Manager_Approved": ("🎉", "#2196F3", "Fully Approved"),
                "Rejected": ("❌", "#F44336", "Rejected"),
                "Cancelled": ("🚫", "#9E9E9E", "Cancelled"),
            }
            icon, color, desc = status_config.get(req.status, ("❓", "#999999", "Unknown"))
            
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1e3a5f; padding: 15px; border-radius: 8px; 
                            border-left: 4px solid {color}; margin: 10px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 20px;">{icon}</span>
                            <strong style="color: #ffffff; font-size: 16px;">{req.leave_type}</strong>
                            <span style="color: {color}; font-size: 12px;">({req.status})</span>
                        </div>
                        <div style="color: #aaaaaa; font-size: 12px;">
                            Submitted: {req.submitted_date}
                        </div>
                    </div>
                    <div style="color: #e0e0e0; margin-top: 8px;">
                        📅 {req.start_date} to {req.end_date} ({req.days_requested} days)<br>
                        💬 {req.reason}
                    </div>
                    <div style="color: #aaaaaa; font-size: 12px; margin-top: 5px;">
                        {desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Cancel button for pending requests
                if req.status == "Pending":
                    if st.button("Cancel Request", key=f"cancel_{req.id}"):
                        data_manager.update_leave_request(req.id, status="Cancelled")
                        st.success("Request cancelled.")
                        st.rerun()
    else:
        st.info("You haven't submitted any leave requests yet.")
    
    # Show leave form if requested
    if st.session_state.get("show_leave_form"):
        st.markdown("---")
        render_employee_leave_request(data_manager, calculator, employee)
    
    # Show detailed history if requested
    if st.session_state.get("show_history"):
        st.markdown("---")
        render_employee_history(data_manager, employee)


def render_employee_leave_request(data_manager: DataManager, calculator: LeaveCalculator, employee: Employee):
    """Render leave request form for employee"""
    st.subheader("📝 Submit New Leave Request")
    
    with st.form("employee_leave_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            leave_type = st.selectbox(
                "Leave Type",
                options=list(LEAVE_TYPES.keys()),
                format_func=lambda x: f"{x} - {LEAVE_TYPES[x]['description']}"
            )
            
            # Show detailed UAE law information
            leave_info = LEAVE_TYPES[leave_type]
            st.markdown(f"""
            <div style="background-color: #1e3a5f; padding: 15px; border-radius: 8px; border: 1px solid #4a90d9; margin: 10px 0;">
                <h4 style="color: #ffffff; margin: 0 0 10px 0;">📋 {leave_type}</h4>
                <table style="width: 100%; color: #e0e0e0; font-size: 13px;">
                    <tr><td style="padding: 4px;"><strong>📊 Entitlement:</strong></td><td>{leave_info['entitlement']}</td></tr>
                    <tr><td style="padding: 4px;"><strong>💰 Payment:</strong></td><td>{leave_info['payment']}</td></tr>
                    <tr><td style="padding: 4px;"><strong>📋 Requirements:</strong></td><td>{leave_info['requirements']}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Start Date", min_value=datetime.now())
            with col_date2:
                end_date = st.date_input("End Date", min_value=start_date)
        
        with col2:
            # Calculate days
            calendar_days = calculator.calculate_calendar_days(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            working_days = calculator.calculate_working_days(
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            st.metric("Calendar Days", calendar_days)
            st.metric("Working Days", working_days)
            
            # Days to request based on leave type
            if leave_type in ["Parental Leave", "Study Leave"]:
                days_requested = working_days
            else:
                days_requested = calendar_days
            
            st.metric("Days to be Deducted", days_requested)
            
            # Check leave balance for annual leave
            if leave_type == "Annual Leave":
                if employee.annual_leave_balance < days_requested:
                    st.error(f"⚠️ Insufficient leave balance! Available: {employee.annual_leave_balance} days")
            
            reason = st.text_area("Reason for Leave", placeholder="Please provide details...")
        
        # Check for conflicts
        has_conflict, conflict_message, conflict_details = calculator.check_conflicts(
            data_manager,
            employee.id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if conflict_message:
            if has_conflict:
                st.error(conflict_message)
            else:
                st.info(conflict_message)
        
        submitted = st.form_submit_button("Submit Request", type="primary")
        
        if submitted:
            if not reason:
                st.error("Please provide a reason for the leave.")
                return
            
            if leave_type == "Annual Leave" and employee.annual_leave_balance < days_requested:
                st.error("Cannot submit: Insufficient leave balance.")
                return
            
            # Create leave request
            request_id = f"REQ{len(data_manager.leave_requests)+1:04d}"
            new_request = LeaveRequest(
                id=request_id,
                employee_id=employee.id,
                employee_name=employee.name,
                leave_type=leave_type,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                days_requested=days_requested,
                reason=reason,
                status="Pending",
                submitted_date=datetime.now().strftime("%Y-%m-%d"),
                submitted_by=st.session_state.current_user,
                conflict_warning=has_conflict,
                conflict_details=conflict_message if has_conflict else ""
            )
            
            data_manager.add_leave_request(new_request)
            st.success(f"✅ Leave request submitted! ID: {request_id}")
            st.session_state.show_leave_form = False
            st.rerun()


def render_employee_history(data_manager: DataManager, employee: Employee):
    """Render employee's leave history"""
    st.subheader("📊 My Leave History")
    
    emp_requests = [r for r in data_manager.leave_requests.values() if r.employee_id == employee.id]
    current_year = datetime.now().year
    
    # This year summary
    this_year_requests = [
        r for r in emp_requests 
        if datetime.strptime(r.start_date, "%Y-%m-%d").year == current_year
        and r.status == "Manager_Approved"
    ]
    
    total_days_this_year = sum(r.days_requested for r in this_year_requests)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(f"Approved Leaves in {current_year}", len(this_year_requests))
    with col2:
        st.metric(f"Days Taken in {current_year}", total_days_this_year)
    
    if this_year_requests:
        st.write(f"**Leave taken this year ({current_year}):**")
        for req in this_year_requests:
            month = datetime.strptime(req.start_date, "%Y-%m-%d").strftime("%B")
            st.write(f"- {req.leave_type}: {req.start_date} to {req.end_date} ({req.days_requested} days) - {month}")
    
    # Complete history table
    st.markdown("---")
    if emp_requests:
        history_data = []
        for req in emp_requests:
            req_date = datetime.strptime(req.start_date, "%Y-%m-%d")
            history_data.append({
                "Leave Type": req.leave_type,
                "Year": req_date.year,
                "Month": req_date.strftime("%B"),
                "From": req.start_date,
                "To": req.end_date,
                "Days": req.days_requested,
                "Status": req.status,
            })
        
        history_df = pd.DataFrame(history_data).sort_values(["Year", "From"], ascending=[False, False])
        st.dataframe(history_df, use_container_width=True)
    else:
        st.info("No leave history found.")


def render_two_level_approvals(data_manager: DataManager):
    """Render two-level approval workflow (Admin and Manager)"""
    user_role = st.session_state.user_role
    user_emp = data_manager.employees.get(st.session_state.employee_id)
    
    st.header("✅ Leave Approvals")
    
    # Tabs for different approval stages
    if user_role == "admin":
        tab1, tab2, tab3, tab4 = st.tabs(["⏳ Pending Review", "✓ Admin Approved", "🎉 Fully Approved", "❌ Rejected"])
        
        with tab1:
            st.subheader("Leave Requests Awaiting Your Review (Level 1)")
            pending_requests = [r for r in data_manager.leave_requests.values() if r.status == "Pending"]
            render_approval_list(data_manager, pending_requests, "admin")
        
        with tab2:
            st.subheader("Approved by You (Awaiting Manager)")
            admin_approved = [r for r in data_manager.leave_requests.values() if r.status == "Admin_Approved"]
            render_approval_list(data_manager, admin_approved, "view_only")
        
        with tab3:
            st.subheader("Fully Approved (Manager Finalized)")
            fully_approved = [r for r in data_manager.leave_requests.values() if r.status == "Manager_Approved"]
            render_approval_list(data_manager, fully_approved, "view_only")
        
        with tab4:
            st.subheader("Rejected Requests")
            rejected = [r for r in data_manager.leave_requests.values() if r.status == "Rejected"]
            render_approval_list(data_manager, rejected, "view_only")
    
    elif user_role == "manager":
        tab1, tab2, tab3, tab4 = st.tabs(["⏳ Awaiting Your Final Approval", "🎉 Fully Approved", "✓ Admin Approved (Pending)", "❌ Rejected"])
        
        with tab1:
            st.subheader("Leave Requests Awaiting Final Approval (Level 2)")
            # Show requests that are admin approved (or pending if admin hasn't acted)
            awaiting_final = [r for r in data_manager.leave_requests.values() if r.status in ["Admin_Approved", "Pending"]]
            render_approval_list(data_manager, awaiting_final, "manager")
        
        with tab2:
            st.subheader("Fully Approved by You")
            fully_approved = [r for r in data_manager.leave_requests.values() if r.status == "Manager_Approved"]
            render_approval_list(data_manager, fully_approved, "view_only")
        
        with tab3:
            st.subheader("Admin Approved (Waiting for Your Approval)")
            admin_approved = [r for r in data_manager.leave_requests.values() if r.status == "Admin_Approved"]
            render_approval_list(data_manager, admin_approved, "manager")
        
        with tab4:
            st.subheader("Rejected Requests")
            rejected = [r for r in data_manager.leave_requests.values() if r.status == "Rejected"]
            render_approval_list(data_manager, rejected, "view_only")


def render_approval_list(data_manager: DataManager, requests: List[LeaveRequest], action_role: str):
    """Render list of requests with approval actions"""
    if not requests:
        st.info("No requests to display.")
        return
    
    for req in requests:
        emp = data_manager.employees.get(req.employee_id)
        
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**{req.employee_name}** ({emp.department if emp else 'N/A'})")
                st.write(f"📝 {req.leave_type}: {req.start_date} to {req.end_date} ({req.days_requested} days)")
                st.write(f"💬 {req.reason}")
                
                if req.conflict_warning:
                    st.error(f"⚠️ {req.conflict_details}")
                
                # Show approval trail
                if req.admin_approved_by:
                    st.success(f"✅ Approved by Admin: {req.admin_approved_by} on {req.admin_approval_date}")
                    if req.admin_remarks:
                        st.caption(f"Admin remarks: {req.admin_remarks}")
            
            with col2:
                st.write(f"Submitted: {req.submitted_date}")
                st.write(f"Current Balance: {emp.annual_leave_balance if emp else 'N/A'} days")
                
                # Show status
                status_badge = {
                    "Pending": "🟡 Pending",
                    "Admin_Approved": "🟢 Admin Approved",
                    "Manager_Approved": "🔵 Fully Approved",
                    "Rejected": "🔴 Rejected",
                    "Cancelled": "⚪ Cancelled"
                }.get(req.status, req.status)
                st.write(f"Status: {status_badge}")
            
            with col3:
                if action_role == "admin" and req.status == "Pending":
                    remarks = st.text_input("Remarks", key=f"remarks_{req.id}", placeholder="Optional")
                    
                    if st.button("✅ Approve", key=f"approve_{req.id}"):
                        # Update leave balance for annual leave
                        if req.leave_type == "Annual Leave" and emp:
                            new_balance = emp.annual_leave_balance - req.days_requested
                            data_manager.update_employee(req.employee_id, annual_leave_balance=new_balance)
                        
                        data_manager.update_leave_request(
                            req.id,
                            status="Admin_Approved",
                            admin_approved_by=st.session_state.current_user,
                            admin_approval_date=datetime.now().strftime("%Y-%m-%d"),
                            admin_remarks=remarks
                        )
                        st.success("Approved at Level 1!")
                        st.rerun()
                    
                    if st.button("❌ Reject", key=f"reject_{req.id}"):
                        data_manager.update_leave_request(
                            req.id,
                            status="Rejected",
                            admin_remarks=remarks
                        )
                        st.error("Rejected!")
                        st.rerun()
                
                elif action_role == "manager" and req.status in ["Admin_Approved", "Pending"]:
                    remarks = st.text_input("Final Remarks", key=f"mgr_remarks_{req.id}", placeholder="Optional")
                    
                    if req.status == "Pending":
                        st.warning("⚠️ Admin hasn't reviewed yet. You can approve directly as final authority.")
                    
                    if st.button("✅ Final Approve", key=f"final_approve_{req.id}"):
                        # Deduct balance if not already done by admin
                        if req.leave_type == "Annual Leave" and emp and not req.admin_approved_by:
                            new_balance = emp.annual_leave_balance - req.days_requested
                            data_manager.update_employee(req.employee_id, annual_leave_balance=new_balance)
                        
                        data_manager.update_leave_request(
                            req.id,
                            status="Manager_Approved",
                            manager_approved_by=st.session_state.current_user,
                            manager_approval_date=datetime.now().strftime("%Y-%m-%d"),
                            manager_remarks=remarks
                        )
                        st.success("Fully Approved!")
                        st.rerun()
                    
                    if st.button("❌ Reject", key=f"mgr_reject_{req.id}"):
                        data_manager.update_leave_request(
                            req.id,
                            status="Rejected",
                            manager_remarks=remarks
                        )
                        st.error("Rejected!")
                        st.rerun()
            
            st.divider()


def render_change_password(data_manager: DataManager):
    """Render change password page for current user"""
    st.header("🔐 Change Password")
    
    current_user = st.session_state.current_user
    user_role = st.session_state.user_role
    
    st.markdown(f"**Current User:** `{current_user}`")
    st.markdown(f"**Role:** {USER_ROLES.get(user_role, user_role)}")
    
    st.markdown("---")
    
    with st.form("change_password_form"):
        st.markdown("### Enter Password Details")
        
        current_password = st.text_input(
            "Current Password",
            type="password",
            placeholder="Enter your current password"
        )
        
        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Min 8 characters, include numbers and symbols"
        )
        
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Re-enter new password"
        )
        
        # Password requirements
        st.markdown("""
        <div style="font-size: 12px; color: #888888; margin-top: 10px;">
        <strong>Password Requirements:</strong>
        <ul style="margin-top: 5px;">
            <li>At least 8 characters long</li>
            <li>Include uppercase and lowercase letters</li>
            <li>Include at least one number</li>
            <li>Include at least one special character (!@#$%^&*)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Change Password", type="primary")
        
        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("❌ All fields are required.")
                return
            
            # Verify current password
            user = data_manager.users.get(current_user)
            if not user:
                st.error("❌ User not found.")
                return
            
            auth = AuthManager()
            if not auth.verify_password(current_password, user.password_hash, user.salt):
                st.error("❌ Current password is incorrect.")
                return
            
            # Validate new password strength
            if len(new_password) < 8:
                st.error("❌ New password must be at least 8 characters long.")
                return
            
            if not any(c.isupper() for c in new_password):
                st.error("❌ Password must include at least one uppercase letter.")
                return
            
            if not any(c.islower() for c in new_password):
                st.error("❌ Password must include at least one lowercase letter.")
                return
            
            if not any(c.isdigit() for c in new_password):
                st.error("❌ Password must include at least one number.")
                return
            
            if not any(c in '!@#$%^&*' for c in new_password):
                st.error("❌ Password must include at least one special character (!@#$%^&*).")
                return
            
            if new_password != confirm_password:
                st.error("❌ New passwords do not match.")
                return
            
            if current_password == new_password:
                st.error("❌ New password must be different from current password.")
                return
            
            # Update password
            password_hash, salt = auth.hash_password(new_password)
            data_manager.update_user(
                current_user,
                password_hash=password_hash,
                salt=salt
            )
            
            st.success("✅ Password changed successfully!")
            st.balloons()
            st.info("🔒 Your password has been updated. Please use the new password for your next login.")


def render_settings(data_manager: DataManager):
    """Render settings page with app reset functionality (Admin only)"""
    st.header("⚙️ Settings")
    
    # Show current data stats
    st.subheader("📊 Current Data Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Employees", len(data_manager.employees))
    with col2:
        st.metric("Total Users", len(data_manager.users))
    with col3:
        st.metric("Leave Requests", len(data_manager.leave_requests))
    with col4:
        active_requests = sum(1 for r in data_manager.leave_requests.values() if r.status == "Pending")
        st.metric("Pending Requests", active_requests)
    
    st.markdown("---")
    
    # Danger Zone - Reset Application
    st.subheader("🚨 Danger Zone")
    
    with st.container():
        st.markdown("""
        <div style="background-color: #5c1a1a; padding: 20px; border-radius: 10px; border: 2px solid #ff4444;">
            <h3 style="color: #ff4444; margin-top: 0;">⚠️ Reset Application</h3>
            <p style="color: #ffffff;">
                This will permanently delete <strong>ALL DATA</strong> and reset to defaults:
            </p>
            <ul style="color: #ffcccc;">
                <li>All employee records (reset to sample data)</li>
                <li>All user accounts (reset to default)</li>
                <li>All leave requests and history (deleted)</li>
                <li>Admin password reset to: <code>admin123</code></li>
            </ul>
            <p style="color: #00ff00; font-weight: bold;">
                ✅ You will stay logged in as admin after reset
            </p>
            <p style="color: #ffff00; font-weight: bold;">
                This action cannot be undone!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Step 1: Show confirmation checkbox
        confirm_reset = st.checkbox("I understand this will delete all data permanently", key="confirm_reset")
        
        if confirm_reset:
            # Step 2: Type confirmation code
            st.warning("Please type **DELETE ALL** to confirm:")
            confirmation_code = st.text_input("Confirmation Code", placeholder="Type DELETE ALL here", key="reset_code")
            
            if confirmation_code == "DELETE ALL":
                # Step 3: Final confirmation button
                st.error("🔴 FINAL WARNING: This action is irreversible!")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🗑️ RESET APP", type="primary", use_container_width=True):
                        try:
                            # Store current admin username before reset
                            current_admin = st.session_state.current_user
                            
                            # Clear all data
                            data_manager.employees = {}
                            data_manager.users = {}
                            data_manager.leave_requests = {}
                            
                            # Delete data files
                            for file_path in [EMPLOYEES_FILE, USERS_FILE, DATA_FILE]:
                                if os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                    except:
                                        pass
                            
                            # Recreate fresh default data
                            data_manager._create_sample_employees()
                            data_manager._create_default_users()
                            
                            # Update admin password to default (admin123)
                            auth = AuthManager()
                            default_admin_hash, default_admin_salt = auth.hash_password("admin123")
                            data_manager.update_user(
                                "admin",
                                password_hash=default_admin_hash,
                                salt=default_admin_salt
                            )
                            
                            # Keep admin logged in
                            st.session_state.current_user = "admin"
                            st.session_state.user_role = "admin"
                            st.session_state.employee_id = "EMP004"  # Admin's employee ID
                            st.session_state.authenticated = True
                            
                            # Success message
                            st.success("✅ Application has been reset successfully!")
                            st.balloons()
                            
                            st.markdown("""
                            <div style="background-color: #1a5c1a; padding: 20px; border-radius: 10px; margin: 20px 0;">
                                <h4 style="color: #ffffff; margin-top: 0;">🔄 Reset Complete</h4>
                                <p style="color: #ffffff;">
                                    All data has been reset to default. You are still logged in as admin.
                                </p>
                                <p style="color: #ffff00;">
                                    <strong>Your Admin Credentials:</strong><br>
                                    Username: <code>admin</code><br>
                                    Password: <code>admin123</code>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.info("🔄 Reloading app...")
                            time.sleep(2)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error during reset: {str(e)}")
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("Clicking this button will immediately erase all data")
            elif confirmation_code and confirmation_code != "DELETE ALL":
                st.error("❌ Incorrect confirmation code. Please type exactly: DELETE ALL")
    
    st.markdown("---")
    
    # Backup Section
    st.subheader("💾 Data Backup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Export All Data**")
        if st.button("📥 Download Backup JSON Files", use_container_width=True):
            # Create a zip of all data files
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add employees
                if data_manager.employees:
                    emp_json = json.dumps({k: v.to_dict() for k, v in data_manager.employees.items()}, indent=2)
                    zip_file.writestr('employees_backup.json', emp_json)
                
                # Add users
                if data_manager.users:
                    users_json = json.dumps({k: v.to_dict() for k, v in data_manager.users.items()}, indent=2)
                    zip_file.writestr('users_backup.json', users_json)
                
                # Add leave requests
                if data_manager.leave_requests:
                    leaves_json = json.dumps({k: v.to_dict() for k, v in data_manager.leave_requests.items()}, indent=2)
                    zip_file.writestr('leave_data_backup.json', leaves_json)
            
            zip_buffer.seek(0)
            st.download_button(
                label="📦 Download ZIP Backup",
                data=zip_buffer.getvalue(),
                file_name=f"leave_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True
            )
    
    with col2:
        st.markdown("**System Info**")
        st.markdown(f"""
        - **App Version:** 1.0.0
        - **Data Files:** JSON (Local Storage)
        - **Employees:** {len(data_manager.employees)}
        - **Users:** {len(data_manager.users)}
        - **Leave Records:** {len(data_manager.leave_requests)}
        """)


def main():
    """Main application function with authentication"""
    st.set_page_config(
        page_title="UAE Annual Leave System",
        page_icon="🇦🇪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better visibility in both light and dark modes
    st.markdown("""
    <style>
    .stMarkdown { color: inherit; }
    .info-box { background-color: #1e3a5f; color: #ffffff; padding: 10px; border-radius: 5px; border-left: 4px solid #4a90d9; }
    .warning-box { background-color: #5c3a00; color: #ffffff; padding: 10px; border-radius: 5px; border-left: 4px solid #ffa500; }
    .error-box { background-color: #5c1a1a; color: #ffffff; padding: 10px; border-radius: 5px; border-left: 4px solid #ff4444; }
    .success-box { background-color: #1a5c1a; color: #ffffff; padding: 10px; border-radius: 5px; border-left: 4px solid #44ff44; }
    .css-1d391kg, .css-1lcbmhc { color: #fafafa; }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    data_manager = st.session_state.data_manager
    calculator = st.session_state.calculator
    
    # Check authentication
    if not st.session_state.authenticated:
        render_login()
        return
    
    # Get user role
    user_role = st.session_state.user_role
    
    # Sidebar navigation based on role
    with st.sidebar:
        st.title("🇦🇪 Leave System")
        st.markdown("---")
        
        if user_role == "employee":
            menu = st.radio(
                "Navigation",
                ["🏠 My Dashboard", "📝 Submit Leave Request", "📖 UAE Entitlements"]
            )
        elif user_role == "admin":
            menu = st.radio(
                "Navigation",
                ["📊 Dashboard", "👥 Employees", "👤 User Management", "✅ Approvals", 
                 "📅 Calendar", "📖 UAE Entitlements", "📊 Reports", "🔐 Change Password", "⚙️ Settings"]
            )
        elif user_role == "manager":
            menu = st.radio(
                "Navigation",
                ["📊 Dashboard", "👥 Employees", "✅ Final Approvals", 
                 "📅 Calendar", "📖 UAE Entitlements", "📊 Reports", "🔐 Change Password"]
            )
        else:
            menu = st.radio("Navigation", ["📊 Dashboard"])
        
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size: 12px; color: #aaaaaa;">
            <strong style="color: #ffffff;">Logged in as:</strong><br>
            {st.session_state.current_user}<br>
            ({USER_ROLES.get(user_role, user_role)})
        </div>
        """, unsafe_allow_html=True)
    
    render_header()
    
    # Route based on role and menu selection
    if user_role == "employee":
        if menu == "🏠 My Dashboard":
            render_employee_dashboard(data_manager, calculator)
        elif menu == "📝 Submit Leave Request":
            employee = data_manager.employees.get(st.session_state.employee_id)
            if employee:
                render_employee_leave_request(data_manager, calculator, employee)
        elif menu == "📖 UAE Entitlements":
            render_leave_entitlements()
    
    elif user_role == "admin":
        if menu == "📊 Dashboard":
            render_dashboard(data_manager)
        elif menu == "👥 Employees":
            render_employee_management(data_manager)
        elif menu == "👤 User Management":
            render_user_management(data_manager)
        elif menu == "✅ Approvals":
            render_two_level_approvals(data_manager)
        elif menu == "📅 Calendar":
            render_leave_calendar(data_manager)
        elif menu == "📖 UAE Entitlements":
            render_leave_entitlements()
        elif menu == "📊 Reports":
            render_reports(data_manager)
        elif menu == "🔐 Change Password":
            render_change_password(data_manager)
        elif menu == "⚙️ Settings":
            render_settings(data_manager)
    
    elif user_role == "manager":
        if menu == "📊 Dashboard":
            render_dashboard(data_manager)
        elif menu == "👥 Employees":
            render_employee_management(data_manager)
        elif menu == "✅ Final Approvals":
            render_two_level_approvals(data_manager)
        elif menu == "📅 Calendar":
            render_leave_calendar(data_manager)
        elif menu == "📖 UAE Entitlements":
            render_leave_entitlements()
        elif menu == "📊 Reports":
            render_reports(data_manager)
        elif menu == "🔐 Change Password":
            render_change_password(data_manager)
    elif menu == "📅 Calendar":
        render_leave_calendar(data_manager)
    elif menu == "📖 UAE Entitlements":
        render_leave_entitlements()
    elif menu == "📊 Reports":
        render_reports(data_manager)


if __name__ == "__main__":
    main()
