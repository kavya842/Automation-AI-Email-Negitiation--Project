# Django Backend API Documentation

## Overview

This document describes the backend API and web endpoints for the Django Deals system. The application integrates with n8n automation to manage collaboration emails and track deal workflows.

---

## API Endpoints (n8n Integration)

* Root URL: `http://127.0.0.1:8000/`
* API endpoints are accessible at:

  * `http://127.0.0.1:8000/save-email/`
  * `http://127.0.0.1:8000/api/save-email/`

---

# API Endpoints (n8n Integration)

## 1. Save Email — Primary n8n Entry Point

**Endpoint**
`POST /save-email/` or `POST /api/save-email/`

**Purpose**
This endpoint acts as the primary entry point for n8n automation. It saves incoming and outgoing emails, creates or updates deals, and maintains conversation history.

**Authentication**
Not required (CSRF exempt)

### Request Body (JSON)

```
json
{
  "thread_id": "19ba740d2519c1e2",
  "subject": "Collaboration mail",
  "body": "Hi, I want to collaborate...",
  "from_email": "client@gmail.com",
  "to_email": "your@gmail.com",
  "direction": "INCOMING",
  "ai_generated_reply": "Thanks for...",
  "brand_name": "Brand Name"
}
```

### Processing Logic

1. Validates required fields:

   * thread_id, subject, body, from_email, to_email, direction
2. Creates or retrieves a Client using the sender email.
3. Creates or retrieves a Deal using the thread ID (one thread = one deal).
4. Saves the AI reply if provided.
5. Creates an EmailMessage record.
6. Updates deal status automatically:

   * OUTGOING → `WAITING_FOR_CLIENT`
   * INCOMING (after waiting) → `PENDING_CREATOR`

### Success Response (201)

```
json
{
  "status": "success",
  "deal_id": 4,
  "deal_created": true,
  "email_message_id": 5,
  "deal_status": "WAITING_FOR_CLIENT"
}
```

### Error Responses

**400**

```
json
{
  "error": "Missing required fields"
}
```

**500**

```
json
{
  "error": "Server error"
}
```

---

## 2. Save Dashboard Deal — Manual Creation

**Endpoint**
`POST /api/dashboard/deal/`

**Purpose**
Allows manual creation of deals from the dashboard.

**Authentication**
Not required (CSRF exempt)

### Request Body

```
json
{
  "from_email": "client@gmail.com",
  "subject": "Test Deal",
  "incoming_body": "Email body text",
  "ai_reply_body": "AI reply text",
  "thread_id": "manual_123",
  "status": "WAITING_FOR_CLIENT",
  "to_email": "your@gmail.com",
  "brand_name": "Brand Name"
}
```

### Success Response

```
json
{
  "status": "success",
  "deal_id": 5,
  "thread_id": "manual_123"
}
```

---

## Web Pages (HTML Views)

## 3. Dashboard Page

**Endpoint:** `GET /dashboard/`

**Purpose:** All deal dashboard.

**Authentication:** Required (login required)

**What it Shows:**
-  Statistics cards: NEW, WAITING, PENDING, COMPLETED, REJECTED counts
-  All deals list with status badges
-  "View Details" button for each deal

**Status Flow in Dashboard:**
- **NEW** → Blue card ( email)
- **WAITING_FOR_CLIENT** → Yellow card ( AI reply
- **PENDING_CREATOR** → Purple card (Client 2nd reply 
- **COMPLETED** → Green card (Accept 
- **REJECTED** → Red card (Reject 

---

### 4. **Deal Detail Page**
**Endpoint:** `GET /deal/<deal_id>/`

**Purpose:** Specific deal full details 

**Authentication:** Required

Displays:

* Deal statistics (NEW, WAITING, PENDING, COMPLETED, REJECTED)
* List of all deals with status badges
* Access to detailed deal pages

### Status Colors

* NEW → Blue
* WAITING_FOR_CLIENT → Yellow
* PENDING_CREATOR → Purple
* COMPLETED → Green
* REJECTED → Red

---

## 4. Deal Detail Page

**Endpoint:** `GET /deal/<deal_id>/`
**Authentication:** Required

Displays:

* Deal information
* Email thread history
* Editable AI reply
* Accept/Reject actions (when status is PENDING_CREATOR)

---

## 5. Accept Deal

**Endpoint:** `POST /deal/<deal_id>/accept/`

Actions:

1. Updates status to `COMPLETED`
2. Updates timestamp
3. Sends webhook to n8n (if configured)
4. Redirects to deal details page

### Webhook Payload

```
json
{
  "action": "accept",
  "thread_id": "19ba740d2519c1e2",
  "deal_id": 4,
  "ai_reply": "Thanks for collaboration..."
}
```

---

## 6. Reject Deal

**Endpoint:** `POST /deal/<deal_id>/reject/`

Actions:

1. Updates status to `REJECTED`
2. Sends webhook to n8n
3. Redirects to deal details page

---

## 7. Update AI Reply

**Endpoint:** `POST /deal/<deal_id>/update-reply/`

Updates the AI-generated reply and redirects to the deal page.

---

## Authentication

## Login

**Endpoint:** `GET/POST /login/`

Authenticates the user and creates a session.

## Logout

**Endpoint:** `GET/POST /logout/`

Ends the session and redirects to the login page.

## Home Redirect

**Endpoint:** `GET /`

Redirects:

* Logged-in users → Dashboard
* Guests → Login page

---

## Complete Deal Status Flow

```
Client sends email → NEW
You send reply → WAITING_FOR_CLIENT
Client replies again → PENDING_CREATOR
You accept → COMPLETED
```

---

## n8n Integration Flow

### Incoming Email

Gmail → n8n → POST `/save-email/` → Deal created/updated

### Outgoing Email

AI reply → Gmail → POST `/save-email/` → Status updated

### Accept/Reject

Dashboard action → Webhook → n8n workflow

---

## Database Models

## Client

* email (unique)
* brand_name
* created_at

## Deal

* client (FK)
* subject
* thread_id (unique)
* status
* ai_generated_reply
* timestamps

## EmailMessage

* deal (FK)
* direction
* subject
* body
* from_email
* to_email
* created_at

---

## Configuration

### Optional Webhook Setting

```
python
N8N_WEBHOOK_URL = "https://your-n8n-webhook-url"
```

---

## Key Points:

1. Main API: `/save-email/`
2. Thread ID maps one email thread to one deal.
3. Accept/Reject is only available in `PENDING_CREATOR` status.
4. Webhooks trigger n8n workflows automatically.

---

## Quick Reference

| Endpoint                 | Method   | Auth | Purpose              |
| ------------------------ | -------- | ---- | -------------------- |
| /save-email/             | POST     | No   | Save email           |
| /api/dashboard/deal/     | POST     | No   | Manual deal creation |
| /dashboard/              | GET      | Yes  | View deals           |
| /deal/<id>/              | GET      | Yes  | Deal details         |
| /deal/<id>/accept/       | POST     | Yes  | Accept deal          |
| /deal/<id>/reject/       | POST     | Yes  | Reject deal          |
| /deal/<id>/update-reply/ | POST     | Yes  | Update AI reply      |
| /login/                  | GET/POST | No   | Login                |
| /logout/                 | GET/POST | Yes  | Logout               |

---

## Testing Examples

### Test Incoming Email

```
bash
curl -X POST http://127.0.0.1:8000/save-email/ \
-H "Content-Type: application/json" \
-d '{"thread_id":"test123","subject":"Test","body":"Hello","from_email":"client@test.com","to_email":"you@test.com","direction":"INCOMING"}'
```

### Test Outgoing Email

```
bash
curl -X POST http://127.0.0.1:8000/save-email/ \
-H "Content-Type: application/json" \
-d '{"thread_id":"test123","subject":"Re: Test","body":"Thanks","from_email":"you@test.com","to_email":"client@test.com","direction":"OUTGOING"}'
```

---

**Version:** 1.0
**Last Updated:** 2025-01-10
