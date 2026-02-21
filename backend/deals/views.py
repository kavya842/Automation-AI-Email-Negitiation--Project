from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives


def _sanitize_header(value):
    """Sanitize header values by removing newlines and collapsing whitespace."""
    if value is None:
        return ""
    return " ".join(str(value).splitlines()).strip()
import json
import requests

from .models import Deal, EmailMessage, Client


#  SAVE EMAIL (n8n ENTRY POINT)
@csrf_exempt
def save_email(request):
    """
    API endpoint for n8n to save emails.
    Accepts JSON only with required fields:
    - thread_id (required)
    - subject (required)
    - body (required)
    - from_email (required)
    - to_email (required)
    - direction (required: INCOMING or OUTGOING)
    - ai_generated_reply (optional) - AI generated reply text
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    # Parse JSON body
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Try to parse as JSON anyway
            data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            "error": "Invalid JSON. Please send JSON data only."
        }, status=400)

    # Validate required fields
    required_fields = ['thread_id', 'subject', 'body', 'from_email', 'to_email', 'direction']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return JsonResponse({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }, status=400)

    thread_id = data.get("thread_id")
    subject = data.get("subject")
    body = data.get("body")
    from_email = data.get("from_email")
    to_email = data.get("to_email")
    direction = data.get("direction", "INCOMING").upper()

    # Validate direction
    if direction not in ['INCOMING', 'OUTGOING']:
        return JsonResponse({
            "error": "direction must be either 'INCOMING' or 'OUTGOING'"
        }, status=400)

    try:
        # 1️ Get or create Client using from_email
        client, client_created = Client.objects.get_or_create(
            email=from_email,
            defaults={'brand_name': data.get('brand_name', '')}
        )

        # 2 Get or create Deal using thread_id (1 thread = 1 Deal)
        # Initial status: NEW for new deals (don't set PENDING until we reply and client replies back)
        initial_status = "NEW"
        deal, deal_created = Deal.objects.get_or_create(
            thread_id=thread_id,
            defaults={
                "client": client,
                "subject": subject,
                "status": initial_status
            }
        )

        # Update subject if it changed
        if deal.subject != subject:
            deal.subject = subject
            deal.save()

        #  Save AI-generated reply if provided
        ai_reply = data.get("ai_generated_reply", "")
        if ai_reply:
            deal.ai_generated_reply = ai_reply
            deal.save()

        #  Create EmailMessage linked to the Deal
        email_message = EmailMessage.objects.create(
            deal=deal,
            direction=direction,
            subject=subject,
            body=body,
            from_email=from_email,
            to_email=to_email,
        )

        # 5️Update Deal status based on direction:
        # - OUTGOING (we replied with AI) → WAITING_FOR_CLIENT (waiting for client response)
        # - INCOMING (client replied) → PENDING_CREATOR (if we were WAITING, meaning it's their 2nd reply)
        if direction == "OUTGOING":
            # We replied with AI, so now waiting for client response
            deal.status = "WAITING_FOR_CLIENT"
            deal.our_reply_sent_at = timezone.now()
            deal.updated_at = timezone.now()
            deal.save()
        elif direction == "INCOMING":
            # Client replied - if we were WAITING for their response, move to PENDING
            # (This means client sent 2nd email after our AI reply)
            if deal.status == "WAITING_FOR_CLIENT":
                deal.status = "PENDING_CREATOR"
                deal.client_replied_at = timezone.now()
                deal.updated_at = timezone.now()
                deal.save()
            # If status is NEW, keep it as NEW (first email, we haven't replied yet)

        return JsonResponse({
            "status": "success",
            "deal_id": deal.id,
            "deal_created": deal_created,
            "email_message_id": email_message.id,
            "deal_status": deal.status
        }, status=201)

    except Exception as e:
        return JsonResponse({
            "error": f"Server error: {str(e)}"
        }, status=500)


#  DASHBOARD
@login_required
def dashboard(request):
    deals = Deal.objects.all().order_by("-created_at")

    stats = {
        "NEW": deals.filter(status="NEW").count(),
        "WAITING_FOR_CLIENT": deals.filter(status="WAITING_FOR_CLIENT").count(),
        "PENDING_CREATOR": deals.filter(status="PENDING_CREATOR").count(),
        "COMPLETED": deals.filter(status="COMPLETED").count(),
        "REJECTED": deals.filter(status="REJECTED").count(),
        "AUTO_REJECTED": deals.filter(status="AUTO_REJECTED").count(),
    }
    
    # Status colors for badge styling
    status_colors = {
        "NEW": "bg-blue-500",
        "WAITING_FOR_CLIENT": "bg-yellow-500",
        "PENDING_CREATOR": "bg-purple-500",
        "COMPLETED": "bg-green-500",
        "REJECTED": "bg-red-500",
        "AUTO_REJECTED": "bg-gray-500",
    }

    return render(request, "deals/dashboard.html", {
        "deals": deals,
        "stats": stats,
        "status_colors": status_colors
    })


# DEAL DETAIL
@login_required
def deal_detail(request, deal_id):
    deal = get_object_or_404(Deal, id=deal_id)
    messages_qs = deal.emails.all().order_by("created_at")
    
    # Show Accept/Reject buttons if status is NEW or PENDING_CREATOR
    can_accept_reject = deal.status in ["NEW", "PENDING_CREATOR"]
    
    # Status colors for badge styling
    status_colors = {
        "NEW": "bg-blue-500",
        "WAITING_FOR_CLIENT": "bg-yellow-500",
        "PENDING_CREATOR": "bg-purple-500",
        "COMPLETED": "bg-green-500",
        "REJECTED": "bg-red-500",
        "AUTO_REJECTED": "bg-gray-500",
    }

    return render(request, "deals/deal_detail.html", {
        "deal": deal,
        "email_messages": messages_qs,
        "can_accept_reject": can_accept_reject,
        "status_colors": status_colors
    })


# ACCEPT DEAL
@login_required
@require_POST
def accept_deal(request, deal_id):
    deal = get_object_or_404(Deal, id=deal_id)

    deal.status = "COMPLETED"
    deal.updated_at = timezone.now()
    deal.save()

    # Trigger n8n webhook
    if hasattr(settings, "N8N_WEBHOOK_URL") and settings.N8N_WEBHOOK_URL:
        try:
            requests.post(settings.N8N_WEBHOOK_URL, json={
                "action": "accept",
                "thread_id": deal.thread_id,
                "deal_id": deal.id,
                "ai_reply": deal.ai_generated_reply,
                "from_email": deal.client.email
            }, timeout=5)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send webhook: {e}")

    # Send acceptance email to client (SMTP)
    try:
        sanitized_subject = _sanitize_header(deal.subject)
        subject = f"Congratulations — your deal '{sanitized_subject}' is complete"
        plain_body = (
            f"Hello {deal.client.brand_name or deal.client.email},\n\n"
            f"Congratulations! Your deal titled '{deal.subject}' has been completed successfully.\n\n"
            "Thank you for working with us.\n\n"
            "Best regards,\n"
            "The Team"
        )
        html_body = (
            f"<p>Hello {deal.client.brand_name or deal.client.email},</p>"
            f"<p>Congratulations! Your deal titled <strong>{deal.subject}</strong> has been completed successfully.</p>"
            "<p>Thank you for working with us.</p>"
            "<p>Best regards,<br/>The Team</p>"
        )

        from_email = settings.DEFAULT_FROM_EMAIL
        # Check if email credentials are configured
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise Exception("Email credentials not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD environment variables.")
        
        msg = EmailMultiAlternatives(subject=subject, body=plain_body, from_email=from_email, to=[deal.client.email])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
    except Exception as e:
        messages.error(request, f"Failed to send acceptance email: {str(e)}")
        print(f"Failed to send acceptance email: {e}")

    messages.success(request, "Deal accepted")
    return redirect("deal_detail", deal_id=deal.id)


#  REJECT DEAL
@login_required
@require_POST
def reject_deal(request, deal_id):
    deal = get_object_or_404(Deal, id=deal_id)

    deal.status = "REJECTED"
    deal.updated_at = timezone.now()
    deal.save()

    # Trigger n8n webhook
    if hasattr(settings, "N8N_WEBHOOK_URL") and settings.N8N_WEBHOOK_URL:
        try:
            requests.post(settings.N8N_WEBHOOK_URL, json={
                "action": "reject",
                "thread_id": deal.thread_id,
                "deal_id": deal.id,
                "ai_reply": deal.ai_generated_reply,
                "from_email": deal.client.email
            }, timeout=5)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send webhook: {e}")

    # Send polite rejection email to client (SMTP)
    try:
        sanitized_subject = _sanitize_header(deal.subject)
        subject = f"Update on your deal '{sanitized_subject}'"
        plain_body = (
            f"Hello {deal.client.brand_name or deal.client.email},\n\n"
            "Thank you for reaching out and for your interest in collaborating with us. "
            "After careful consideration, we regret to inform you that we are unable to proceed with this collaboration at this time.\n\n"
            "We appreciate your understanding and hope we can work together on future opportunities.\n\n"
            "Best regards,\n"
            "The Team"
        )
        html_body = (
            f"<p>Hello {deal.client.brand_name or deal.client.email},</p>"
            "<p>Thank you for reaching out and for your interest in collaborating with us. "
            "After careful consideration, we regret to inform you that we are unable to proceed with this collaboration at this time.</p>"
            "<p>We appreciate your understanding and hope we can work together on future opportunities.</p>"
            "<p>Best regards,<br/>The Team</p>"
        )

        from_email = settings.DEFAULT_FROM_EMAIL
        # Check if email credentials are configured
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            raise Exception("Email credentials not configured. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD environment variables.")
        
        msg = EmailMultiAlternatives(subject=subject, body=plain_body, from_email=from_email, to=[deal.client.email])
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
    except Exception as e:
        messages.error(request, f"Failed to send rejection email: {str(e)}")
        print(f"Failed to send rejection email: {e}")

    messages.success(request, "Deal rejected")
    return redirect("deal_detail", deal_id=deal.id)


#  UPDATE AI REPLY
@login_required
@require_POST
def update_ai_reply(request, deal_id):
    deal = get_object_or_404(Deal, id=deal_id)
    ai_reply = request.POST.get("ai_reply", "").strip()
    
    deal.ai_generated_reply = ai_reply
    deal.updated_at = timezone.now()
    deal.save()
    
    messages.success(request, "AI reply updated successfully")
    return redirect("deal_detail", deal_id=deal.id)


#  LOGIN VIEW
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", "dashboard")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, "deals/login.html")


#  LOGOUT VIEW
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")



#  CHECK DEAL EXISTS
@csrf_exempt
@require_GET
def check_deal_exists(request):
    """
    API endpoint to check if a deal exists based on thread_id.
    GET /api/deals/check/?thread_id=<thread_id>
    
    Returns:
        - {"exists": true} if deal exists
        - {"exists": false} if deal does not exist
        - {"error": "thread_id parameter is required"} if thread_id is missing
    """
    thread_id = request.GET.get("thread_id")
    
    if not thread_id:
        return JsonResponse({
            "error": "thread_id parameter is required"
        }, status=400)
    
    exists = Deal.objects.filter(thread_id=thread_id).exists()
    
    return JsonResponse({
        "exists": exists
    })


#  SAVE DASHBOARD DEAL (Manual Deal Creation)
@csrf_exempt
def save_dashboard_deal(request):
    """
    API endpoint to manually create a deal from dashboard.
    Accepts JSON with:
    - from_email (required)
    - subject (required)
    - incoming_body (required) - will be saved as EmailMessage
    - ai_reply_body (optional) - will be saved as ai_generated_reply
    - thread_id (optional) - will be auto-generated if not provided
    - status (optional) - defaults to WAITING_FOR_CLIENT
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed. Use POST."}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            "error": "Invalid JSON. Please send JSON data only."
        }, status=400)

    # Validate required fields
    required_fields = ['from_email', 'subject', 'incoming_body']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return JsonResponse({
            "error": f"Missing required fields: {', '.join(missing_fields)}"
        }, status=400)

    try:
        from_email = data.get("from_email")
        subject = data.get("subject")
        incoming_body = data.get("incoming_body")
        ai_reply_body = data.get("ai_reply_body", "")
        thread_id = data.get("thread_id") or f"manual_{timezone.now().timestamp()}"
        status = data.get("status", "WAITING_FOR_CLIENT")
        to_email = data.get("to_email", "")

        # Validate status
        valid_statuses = [choice[0] for choice in Deal.STATUS_CHOICES]
        if status not in valid_statuses:
            status = "WAITING_FOR_CLIENT"

        # Get or create Client
        client, _ = Client.objects.get_or_create(
            email=from_email,
            defaults={'brand_name': data.get('brand_name', '')}
        )

        # Create Deal
        deal = Deal.objects.create(
            client=client,
            subject=subject,
            thread_id=thread_id,
            status=status,
            ai_generated_reply=ai_reply_body
        )

        # Create EmailMessage for incoming email
        EmailMessage.objects.create(
            deal=deal,
            direction="INCOMING",
            subject=subject,
            body=incoming_body,
            from_email=from_email,
            to_email=to_email
        )

        return JsonResponse({
            "status": "success",
            "deal_id": deal.id,
            "thread_id": deal.thread_id
        }, status=201)

    except Exception as e:
        return JsonResponse({
            "error": f"Server error: {str(e)}"
        }, status=500)
