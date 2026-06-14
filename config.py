# config.py

API_ID = 12345678
API_HASH = "abcdef1234567890abcdef1234567890"
BOT_TOKEN = "1234567890:ABCdefGhIJKlmNoPQRsTUVwXyZ"

# 👑 Loyihaning mutloq egasi (Faqat u yangi admin qo'shishi yoki o'chirishi mumkin)
SUPER_ADMIN_ID = 987654321  # Sizning asosiy ID raqamingiz

# 👥 Botning 5ta tugmasidan foydalana oladigan barcha ishonchli adminlar ro'yxati
ADMIN_LIST = [987654321, 555666777, 111222333]

# ══════════════════════════════════════════════════
# IKKINCHI USERBOT (IXTIYORIY) — skanerlash 2x tez
# ══════════════════════════════════════════════════
# Agar ikkinchi Telegram hisobi bo'lsa, quyidagilarni .env ga qo'shing:
#
#   USERBOT2_PHONE=+998901234567
#
# Agar 2-hisob uchun alohida API_ID/API_HASH bo'lsa (ixtiyoriy):
#   USERBOT2_API_ID=12345678
#   USERBOT2_API_HASH=abcdef1234567890abcdef1234567890
#
# Bo'sh qoldirilsa — faqat 1 userbot bilan ishlaydi (eski rejim)

# ══════════════════════════════════════════════════
# 🛡 HAVOLA TEKSHIRISH — Ixtiyoriy API kalitlar
# ══════════════════════════════════════════════════
# VirusTotal (bepul hisob, kuniga 500 so'rov):
#   https://www.virustotal.com/gui/my-apikey
#   VIRUSTOTAL_API_KEY=abc123...
#
# AbuseIPDB (bepul hisob, oyiga 1000 so'rov):
#   https://www.abuseipdb.com/account/api
#   ABUSEIPDB_API_KEY=abc123...
#
# URLhaus — API kalit shart EMAS (bepul, ochiq)
# playwright — "pip install playwright && playwright install chromium"
#   (ixtiyoriy: brauzer ichida sahifani ochib karta/parol shakli topadi)