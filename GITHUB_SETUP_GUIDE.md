# GitHub Setup Guide

This guide will walk you through publishing this app to your GitHub account.

---

## Step 1: Install Git

### Download Git
1. Go to https://git-scm.com/download/win
2. Download the Windows installer
3. Run the installer with default settings

### Verify Installation
Open Command Prompt and run:
```cmd
git --version
```

You should see something like: `git version 2.x.x`

---

## Step 2: Configure Git

Open Command Prompt and run:

```cmd
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Step 3: Create a GitHub Account (if needed)

1. Go to https://github.com
2. Sign up for a free account
3. Verify your email address

---

## Step 4: Create a New Repository on GitHub

1. Log in to GitHub
2. Click the **+** icon in the top right → **New repository**
3. Enter repository name: `uae-leave-management`
4. Add a description: "UAE Annual Leave Management System - Streamlit App"
5. Choose **Public** or **Private**
6. **DO NOT** initialize with README (we already have one)
7. Click **Create repository**

---

## Step 5: Prepare Your Local Files

The following files are ready for GitHub:

| File | Purpose |
|------|---------|
| `annual_leave_system.py` | Main application |
| `requirements.txt` | Python dependencies |
| `README_GitHub.md` | GitHub documentation (rename to README.md) |
| `LICENSE` | MIT License |
| `.gitignore` | Files to exclude from Git |
| `run_app.bat` | Windows run script |
| `run_app_with_browser.bat` | Windows run script (with browser) |
| `sample_employees.json` | Sample employee data |

### Files NOT included (due to .gitignore):
- `employees.json` (real employee data)
- `users.json` (login credentials)
- `leave_data.json` (leave records)
- `employee_credentials.txt` (passwords)
- `*.xlsx` (Excel files)

---

## Step 6: Initialize Git and Push to GitHub

Open Command Prompt in your project folder:

```cmd
cd "C:\Users\Lenovo\Desktop\Safawat Leave app"

:: Initialize Git repository
git init

:: Add all files
git add .

:: Commit files
git commit -m "Initial commit - UAE Leave Management System"

:: Rename README
git mv README_GitHub.md README.md

:: Add remote repository (replace with your username)
git remote add origin https://github.com/YOUR_USERNAME/uae-leave-management.git

:: Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 7: Verify on GitHub

1. Go to https://github.com/YOUR_USERNAME/uae-leave-management
2. You should see all your files
3. The README will be displayed on the main page

---

## Optional: Add Screenshots

To add a screenshot to your README:

1. Take a screenshot of your app running
2. Save it as `screenshot.png` in your project folder
3. Run:
```cmd
git add screenshot.png
git commit -m "Add screenshot"
git push
```

---

## Updating Your Repository

After making changes:

```cmd
git add .
git commit -m "Description of changes"
git push
```

---

## Troubleshooting

### Authentication Issues
If prompted for password, use a **Personal Access Token**:
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token
3. Use token as password

### Large Files Error
If you get errors about large files, make sure `.gitignore` excludes:
- Excel files (*.xlsx)
- JSON data files

### Push Rejected
If push is rejected:
```cmd
git pull origin main --rebase
git push
```

---

## Quick Reference Commands

```cmd
:: Check status
git status

:: See what files changed
git diff

:: View commit history
git log --oneline

:: Pull latest changes
git pull

:: Push changes
git push
```

---

## Need Help?

- GitHub Docs: https://docs.github.com
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf
