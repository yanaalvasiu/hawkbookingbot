import os
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from supabase import create_client, Client
from realtime import Client as RealtimeClient

# ===== CONFIG =====
SUPABASE_URL = "https://cbnfbvqddvlxjmfsruvx.supabase.co/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNibmZidnFkZHZseGptZnNydXZ4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDQ2OTUzMiwiZXhwIjoyMDcwMDQ1NTMyfQ.HPJ5mBneLobNfDU87pN1d1XvlSpKHF6JRsk8bq0rkMQ"
TELEGRAM_TOKEN = "8369113975:AAGgvvkS--4ztnQLgK2Uo8UqyXUBRTC8-cw"
CHAT_ID = "910947008"
BOOKINGS_TABLE = "bookings"
GUESTS_TABLE = "guest_forms"
# ==================

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== Telegram Helper =====
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

# ===== Realtime Listener for Bookings =====
def start_realtime_listener():
    realtime = RealtimeClient(SUPABASE_URL.replace("https", "wss") + "/realtime/v1")
    realtime.connect()
    realtime.subscribe(
        BOOKING_CHANNEL := f"realtime:*:public:{BOOKINGS_TABLE}",
        callback=handle_new_booking,
        event="INSERT"
    )
    print("✅ Realtime booking listener started...")
    realtime.listen()

def handle_new_booking(payload):
    new_booking = payload["new"]
    message = (
        f"📸 <b>New Booking</b>\n"
        f"🏠 Room: {new_booking['room']}\n"
        f"⏰ Time: {new_booking['time']}\n"
        f"🎁 Package: {new_booking['package']}"
    )
    send_to_telegram(message)

# ===== Daily Guest Form Report =====
def send_guest_forms_summary():
    today = datetime.now().date()
    result = supabase.table(GUESTS_TABLE).select("*").eq("date", str(today)).execute()
    
    if not result.data:
        send_to_telegram("📋 No guest forms submitted today.")
        return
    
    message = "📋 <b>Today's Guest Forms</b>\n"
    for guest in result.data:
        message += (
            f"👤 Name: {guest['name']}\n"
            f"🏠 Room: {guest['room']}\n"
            f"🎁 Package: {guest['package']}\n"
            f"💵 Price: {guest['price']}\n\n"
        )
    send_to_telegram(message)

# ===== Scheduler for 10 PM report =====
scheduler = BackgroundScheduler()
scheduler.add_job(send_guest_forms_summary, "cron", hour=22, minute=0)  # 10:00 PM
scheduler.start()

print("🚀 Bot running — waiting for bookings...")

# Start realtime listener
start_realtime_listener()
