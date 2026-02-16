# 📧 Django Deals Project

A Django-based system for managing incoming collaboration emails and tracking brand deals.
This project provides an API for saving emails, a dashboard for managing deals, and integration-ready workflows.

---

# 🚀 Features

* Save incoming emails via API
* Manage clients and collaboration deals
* Track deal status and conversations
* AI-generated reply support
* Admin dashboard and authentication
* Webhook integration (n8n ready)

---

# 📂 Project Structure

```
backend/
│
├── deals/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│
├── backend/
│   ├── settings.py
│   ├── urls.py
│
└── db.sqlite3
```

---

# 🧠 Models Overview

## 1️⃣ Email

Stores incoming emails from external systems.

Fields:

* subject
* body
* thread_id
* category
* created_at

---

## 2️⃣ Client

Stores brand/client details.

Fields:

* email (unique)
* brand_name
* created_at

---

## 3️⃣ Deal

Stores collaboration deal information.

Status Options:

* NEW
* WAITING_FOR_CLIENT
* PENDING_CREATOR
* COMPLETED
* REJECTED
* AUTO_REJECTED

Fields include:

* client (ForeignKey)
* subject
* thread_id
* ai_generated_reply
* timestamps

---

## 4️⃣ EmailMessage

Stores conversation messages related to a deal.

Fields:

* deal (ForeignKey)
* direction (INCOMING / OUTGOING)
* body
* from_email
* to_email
* created_at

---

# 🔗 Database Relationships

```
Client → Multiple Deals  
Deal → Multiple EmailMessages
```

---

# 🔌 API Endpoint

## Save Email API

**POST** `/save-email/`

### Request

```json
{
  "subject": "Brand Collaboration",
  "body": "We want to collaborate...",
  "thread_id": "thread_123",
  "category": "useful"
}
```

### Response

```json
{
  "status": "success",
  "id": 1
}
```

Purpose:

* Accept incoming emails from external systems
* Store data in the database using Django ORM

---

# 🗄️ Data Flow

### Email Save Flow

1. External system sends POST request
2. Django parses JSON data
3. ORM saves record to database
4. Success response returned

### Deal Accept / Reject Flow

1. User clicks Accept/Reject
2. Deal status updated
3. Database updated
4. Optional webhook sent to n8n

### Update AI Reply Flow

1. User edits AI reply
2. Reply saved to database
3. Deal updated

---

# 🧪 API Testing

## Using cURL

```bash
curl -X POST http://localhost:8000/save-email/ \
-H "Content-Type: application/json" \
-d '{"subject":"Test","body":"Test body","thread_id":"123"}'
```

## Using Python

```python
requests.post(url, json=data)
```

## Using Postman

* Method: POST
* URL: `/save-email/`
* Body: JSON

---

# 🌐 URL Routes

| URL                  | Purpose         |
| -------------------- | --------------- |
| `/save-email/`       | Save email API  |
| `/dashboard/`        | Deals dashboard |
| `/deal/<id>/`        | Deal details    |
| `/deal/<id>/accept/` | Accept deal     |
| `/deal/<id>/reject/` | Reject deal     |
| `/login/`            | Login           |
| `/logout/`           | Logout          |

---

# 👨‍💻 Views Overview

| View            | Description                |
| --------------- | -------------------------- |
| save_email      | API endpoint to save email |
| dashboard       | Shows all deals            |
| deal_detail     | Shows deal information     |
| accept_deal     | Accept a deal              |
| reject_deal     | Reject a deal              |
| update_ai_reply | Update AI reply            |
| login_view      | User login                 |
| logout_view     | User logout                |

---

# ⚙️ Setup Guide

## 1️⃣ Install Dependencies

```bash
pip install django
```

## 2️⃣ Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 3️⃣ Create Superuser

```bash
python manage.py createsuperuser
```

## 4️⃣ Start Server

```bash
python manage.py runserver
```

---

# 🔑 Access URLs

| Feature     | URL                               |
| ----------- | --------------------------------- |
| API         | http://localhost:8000/save-email/ |
| Dashboard   | http://localhost:8000/dashboard/  |
| Admin Panel | http://localhost:8000/admin/      |
| Login       | http://localhost:8000/login/      |

---

# 🔒 Authentication

* Uses Django’s built-in authentication system
* Dashboard requires login
* API endpoint is CSRF exempt for external integrations

---

# 📡 Webhook Integration

When a deal is accepted or rejected, a webhook can be triggered to **n8n** using the configured `N8N_WEBHOOK_URL`.

---

# 🗃️ Database

* Database: SQLite
* File: `db.sqlite3`
* Managed via Django ORM

---

# 📌 Project Summary

| Component     | Count  |
| ------------- | ------ |
| Models        | 4      |
| API Endpoints | 1      |
| Views         | 8      |
| Database      | SQLite |

**Purpose:**
A collaboration email and deal management system for creators and brands.
