# 🧑‍💼 JobMate – Django Job Portal

JobMate is a full-featured job portal built with **Django**, offering three user roles:

- 👤 **Job Seekers** – create profiles, search jobs, apply
- 🏢 **Employers** – post jobs, manage applicants
- ⚙️ **Admin** – manage users, jobs, applications, analytics dashboard

This project includes authentication, role-based access, admin analytics (Chart.js), and modern UI using Bootstrap 5.

---

## 🚀 Features

### 🔹 **Job Seekers**
- Registration & login  
- Upload resume  
- Browse & search jobs  
- Apply to jobs  
- View application history  

### 🔹 **Employers**
- Register & login  
- Create & manage job posts  
- View applicants  
- Edit & delete job listings  

### 🔹 **Admin Panel**
- Dashboard analytics  
  - Total users  
  - Total employers  
  - Active job seekers  
  - Applications per day  
  - Jobs per employer  
- Manage all users  
- Activate / deactivate accounts  
- Delete users  
- View recent applicants & employers  
- Admin charts using **Chart.js**

## ✉️ Email System

JobMate includes built-in email features using Django’s `django.core.mail` and token-based verification.

### 🔹 Email Verification (Account Activation)
When a new user registers, the system sends an **email verification link**.  
The user must click the link to activate their account.

✔️ Secure token (Django built-in)  
✔️ Activation link expires  
✔️ Protects against fake signups  
✔️ Works for both Employers and Job Seekers

### 🔹 Password Reset via Email
Users can request a password reset by entering their email.

The system sends a secure link that allows them to create a new password.

✔️ Token-based secure reset link  
✔️ Auto-expiring password reset token  
✔️ Works for both employers and job seekers  
✔️ Fully compatible with Django Auth system

### 🔹🛠️ Tech Stack

Backend: Django 5+

Frontend: Bootstrap 5, FontAwesome

Database: SQLite (default), MySQL compatible

Charts: Chart.js

Email: SMTP (Gmail / Custom)

Authentication: Django Auth + Role-Based Access

### 🔹❤️ Credits

**Developer: Juven T. Pinoy**  
🎓 Information Technology Graduate – Carlos Hilado Memorial State University (2025)  
🌐 [GitHub Profile](https://github.com/Juven65)

Code Assistance: ChatGPT

UI: Bootstrap 5

---

### 🔹🏗️ Project Structure

## ⚙️ Setup Instructions

```bash
# Clone the repository
git clone https://github.com/Juven65/jobmate.git
cd jobmate

# Create a virtual environment
python -m venv venv

# Activate it
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Migrate the database
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run the development server
python manage.py runserver

```





