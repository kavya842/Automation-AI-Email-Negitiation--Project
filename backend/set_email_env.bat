@echo off
REM Set these environment variables in Command Prompt or PowerShell before running Django
REM Replace xxxxxxxxxxxxxxxx with your 16-character Gmail App Password

echo To fix the Gmail SMTP error, run these commands in your terminal:
echo.
echo Set EMAIL_HOST_USER (your Gmail address):
echo $env:EMAIL_HOST_USER = "kavyavankayalapati9999@gmail.com"
echo.
echo Set EMAIL_HOST_PASSWORD (your 16-character App Password):
echo $env:EMAIL_HOST_PASSWORD = "xxxxxxxxxxxxxxxx"
echo.
echo Then run your Django server in the same terminal:
echo python manage.py runserver
echo.
echo Or set both at once:
echo $env:EMAIL_HOST_USER = "kavyavankayalapati9999@gmail.com"; $env:EMAIL_HOST_PASSWORD = "xxxxxxxxxxxxxxxx"; python manage.py runserver
pause
