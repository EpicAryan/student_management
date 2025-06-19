# 📊 Academic Performance Tracking System (APTS)

An end-to-end full-stack solution for efficient and centralized academic performance management, developed as a final year Computer Science Engineering project (2021–2025 Batch).

## 👨‍💻 Team Members

- **Aniket Kumar** -  University Roll No:-18700121119  
- **Disha Mukhopadhyay** - University Roll No:-18700121156  
- **Aryan Kumar** - University Roll No:-18700121095  
- **Subhajit Dutta** - University Roll No:-18700121114  
- **Guided by:** Dr. Chinmay Kar

---

## 🧠 Project Overview

Academic Performance Tracking System (APTS) is a comprehensive digital platform built to streamline and automate student performance tracking in educational institutions.

### 🎯 Purpose

- Centralize student records including marks, attendance, and course feedback.
- Enable real-time monitoring for students, faculty, and administrators.
- Provide actionable academic insights through dashboards and analytics.

### 🔑 Key Features

- 📁 **Centralized Database** for batches, semesters, subjects, and results.
- 📊 **Interactive Dashboards** with real-time charts and visual reports.
- 🧑‍🏫 **Role-Based Access** for Admins, Professors, and Students.
- 🔐 **Secure & Scalable**: Encrypted access, session management, and backup mechanisms.
- 🧮 **Automated Result Calculation** with grade generation.
- 🧠 **Personalized Learning Insights** for student improvement.

---

## 🚩 Problem Statement

Traditional academic record-keeping systems suffer from:

- ❌ Fragmented data systems and inefficient mark entry.
- ❌ Lack of real-time visualization for performance trends.
- ❌ Laborious manual calculations prone to human error.

---

## 💡 Proposed Solution

- ✅ Centralized, unified academic data management.
- ✅ Role-specific functionalities and dashboards.
- ✅ Conditional redirection and access control using Django middleware.
- ✅ JSON-based client-server communication for interactive features.

---

## 🛠️ Tech Stack

| Layer        | Technologies                           |
|--------------|----------------------------------------|
| Frontend     | HTML, CSS, JavaScript, Bootstrap       |
| Backend      | Python, Django                         |
| Database     | SQLite / PostgreSQL                    |
| APIs         | Google reCAPTCHA, Django REST Framework|
| Deployment   | Django Server (development)            |

---

## 🔄 Architecture

A robust **three-tier architecture** ensures separation of concerns and scalability:

1. **Presentation Layer**: User Interfaces (Admin, Faculty, Student)
2. **Application Layer**: Business Logic (Django Views & Middleware)
3. **Data Layer**: Database Models (ORM-based)

---

## 🧪 Key Functional Modules

### 🔐 Login & Session Management
- Google reCAPTCHA validation
- Custom session and access control

### 👨‍🏫 Professor View
- Add/edit marks for theory & lab
- Attendance management
- Leave application & profile update

### 🧑‍🎓 Student View
- Real-time results & attendance
- Leave applications
- Feedback submission

### 🧑‍💼 Admin View
- Department/batch/subject/user management
- Centralized analytics & dashboards

---



---

## 🚀 Future Enhancements

- ✅ Plagiarism Detection for assignment uploads  
- ✅ Attendance–Performance Correlation Analysis  
- ✅ Career and Skill Recommendation Engine  
- ✅ CSV/XLS Bulk Upload  
- ✅ Push Notification Integration  
- ✅ AI-based Performance Alerts  

---



---

## 🏁 Conclusion

This project successfully delivers a scalable academic platform that:

- Improves administrative efficiency
- Enhances academic transparency
- Enables data-driven educational decisions












## How to Install and Run this project?

 ### Pre-Requisites:
1. Install Git Version Control
[ https://git-scm.com/ ]

2. Install Python Latest Version
[ https://www.python.org/downloads/ ]

3. Install Pip (Package Manager)
[ https://pip.pypa.io/en/stable/installing/ ]

*Alternative to Pip is Homebrew*

### Installation
**1. Create a Folder where you want to save the project**

**2. Create a Virtual Environment and Activate**

Install Virtual Environment First
```
$  pip install virtualenv
```

Create Virtual Environment

For Windows
```
$  python -m venv venv
```
For Mac
```
$  python3 -m venv venv
```
For Linux
```
$  virtualenv .
```

Activate Virtual Environment

For Windows
```
$  source venv/scripts/activate
```

For Mac
```
$  source venv/bin/activate
```

For Linux
```
$  source bin/activate
```

**3. Clone this project**
```
$  git clone https://github.com/jobic10/student-management-using-django.git
```

Then, Enter the project
```
$  cd student-management-using-django
```

**4. Install Requirements from 'requirements.txt'**
```python
$  pip3 install -r requirements.txt
```

**5. Add the hosts**

- Got to settings.py file 
- Then, On allowed hosts, Use **[]** as your host. 
```python
ALLOWED_HOSTS = []
```
*Do not use the fault allowed settings in this repo. It has security risk!*


**6. Now Run Server**

Command for PC:
```python
$ python manage.py runserver
```

Command for Mac:
```python
$ python3 manage.py runserver
```

Command for Linux:
```python
$ python3 manage.py runserver
```

**7. Login Credentials**

Create Super User (HOD)
Command for PC:
```
$  python manage.py createsuperuser
```

Command for Mac:
```
$  python3 manage.py createsuperuser
```

Command for Linux:
```
$  python3 manage.py createsuperuser
```
 -->


