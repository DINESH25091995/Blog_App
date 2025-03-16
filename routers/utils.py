import random
import smtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime,timedelta,time


# def send_email(to_email: str, Username: str, Shopname: str):
def send_email(appointment,sub_msg):
    #appointment.user.email,appointment.user.username,appointment.shop.shop_name,start_time
    appointment_time = datetime.strptime(appointment.time, "%H:%M")
    report_time = (appointment_time - timedelta(minutes=10)).time()
    to_email = appointment.user.email
    """Function to send OTP via email (Use an actual email service in production)"""
    sender_email = "dinesh.kumar.tech1995@gmail.com"
    sender_password = "jtskfipxjcapfxuo"
    
    subject = f"{sub_msg} from {appointment.shop.shop_name}"
    message = f"Hi {appointment.user.username}, \n\nThanks for the appointment\nYou have the next turn\nget ready to shape your look\nPlease report to the shop at: {report_time}\nyour appointment will start at: {appointment_time.time()}\n\nThanks, and Regards\n{appointment.shop.shop_name}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, f"Subject: {subject}\n\n{message}")
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")