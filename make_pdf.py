#!/usr/bin/env python3
"""Kiber-Stansiya OSINT Pro — Admin Qo'llanma PDF generator (v2)"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── SHRIFT ──────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))

def reg(name, path):
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            return True
        except Exception:
            pass
    return False

FONT      = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
for base_path in ["/usr/share/fonts", "/usr/local/share/fonts", os.path.join(BASE)]:
    for fn, fb in [("DejaVuSans","DejaVuSans-Bold"),("FreeSans","FreeSansBold"),("LiberationSans","LiberationSans-Bold")]:
        p1 = os.path.join(base_path, f"{fn}.ttf")
        p2 = os.path.join(base_path, f"{fb}.ttf")
        if reg(fn, p1) and reg(fb, p2):
            FONT, FONT_BOLD = fn, fb
            break
    if FONT != "Helvetica":
        break

# DejaVuSans directly in bot folder
deja = os.path.join(BASE, "DejaVuSans.ttf")
deja_b = deja.replace(".ttf", "-Bold.ttf")
if os.path.exists(deja) and FONT == "Helvetica":
    if reg("DejaVuSans", deja):
        FONT = "DejaVuSans"
    if os.path.exists(deja_b) and reg("DejaVuSans-Bold", deja_b):
        FONT_BOLD = "DejaVuSans-Bold"

# ── RANGLAR ─────────────────────────────────────────────────────────────
BLUE_DARK   = colors.HexColor("#1565C0")
BLUE_MED    = colors.HexColor("#1976D2")
BLUE_LIGHT  = colors.HexColor("#E3F2FD")
BLUE_HEADER = colors.HexColor("#0D47A1")
ORANGE      = colors.HexColor("#E65100")
ORANGE_LIGHT= colors.HexColor("#FFF3E0")
GREEN_DARK  = colors.HexColor("#1B5E20")
GREEN_LIGHT = colors.HexColor("#E8F5E9")
RED_DARK    = colors.HexColor("#B71C1C")
RED_LIGHT   = colors.HexColor("#FFEBEE")
PURPLE_DARK = colors.HexColor("#4A148C")
PURPLE_LIGHT= colors.HexColor("#EDE7F6")
TEAL_DARK   = colors.HexColor("#004D40")
TEAL_LIGHT  = colors.HexColor("#E0F2F1")
GRAY_LIGHT  = colors.HexColor("#F5F5F5")
GRAY_MED    = colors.HexColor("#BDBDBD")
WHITE       = colors.white
BLACK       = colors.black

W, H = A4
ML = MR = 2.0 * cm
TW = W - ML - MR  # usable width

# ── STIL YORDAMCHILARI ──────────────────────────────────────────────────
def ps(name, font=None, size=10, leading=None, color=BLACK, bold=False,
       space_before=0, space_after=4, align="LEFT"):
    f = (font or (FONT_BOLD if bold else FONT))
    return ParagraphStyle(
        name, fontName=f, fontSize=size,
        leading=(leading or size * 1.35),
        textColor=color,
        spaceBefore=space_before, spaceAfter=space_after,
        alignment={"LEFT":0,"CENTER":1,"RIGHT":2,"JUSTIFY":4}[align]
    )

S_TITLE   = ps("title",  bold=True,  size=28, color=BLUE_DARK,   align="CENTER", leading=34)
S_SUBT    = ps("subt",   bold=True,  size=13, color=BLUE_MED,    align="CENTER", space_after=6)
S_BODY    = ps("body",   size=9.5,   leading=14, space_after=4)
S_SMALL   = ps("small",  size=8.5,   color=colors.HexColor("#424242"), space_after=2)
S_BOLD    = ps("sbold",  bold=True,  size=9.5, space_after=4)
S_CENTER  = ps("scenter",size=9,     align="CENTER")
S_WHITE   = ps("swhite", bold=True,  size=9.5, color=WHITE)
S_BLUE_H  = ps("sblueh", bold=True,  size=10,  color=WHITE)
S_CMD     = ps("scmd",   bold=True,  size=9,   color=WHITE)
S_GREEN   = ps("sgreen", bold=True,  size=9,   color=GREEN_DARK)
S_RED_T   = ps("sredt",  bold=True,  size=9,   color=RED_DARK)
S_ORANGE  = ps("sorang", bold=True,  size=9,   color=ORANGE)

def hr():
    return HRFlowable(width="100%", thickness=1, color=BLUE_MED, spaceAfter=8)

def sp(h=6):
    return Spacer(1, h)

# ── BOʻLIM SARLAVHASI ───────────────────────────────────────────────────
def section_header(num, title, subtitle):
    data = [[
        Paragraph(str(num), ps("sn", bold=True, size=22, color=WHITE, align="CENTER")),
        [Paragraph(title,    ps("st", bold=True, size=14, color=WHITE)),
         Paragraph(subtitle, ps("ss", size=9,    color=colors.HexColor("#BBDEFB")))]
    ]]
    t = Table(data, colWidths=[1.4*cm, TW - 1.4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BLUE_HEADER),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",(0,0),(0,0), 6),
        ("LEFTPADDING",(1,0),(1,0), 10),
        ("TOPPADDING", (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("ROUNDEDCORNERS",[4,4,4,4]),
    ]))
    return t

# ── FUNKSIYA SARLAVHASI ─────────────────────────────────────────────────
def func_header(icon, title, bg=BLUE_MED):
    data = [[Paragraph(f"{icon}  {title}", ps("fh", bold=True, size=10, color=WHITE))]]
    t = Table(data, colWidths=[TW])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), bg),
        ("TOPPADDING",(0,0),(-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING",(0,0),(-1,-1), 10),
    ]))
    return t

# ── ODDIY JADVAL ────────────────────────────────────────────────────────
def simple_table(rows, col_widths=None, header_bg=BLUE_MED, alt=True):
    cw = col_widths or [TW*0.35, TW*0.65]
    data = []
    for i, row in enumerate(rows):
        r = [Paragraph(str(c), ps("tc", bold=(i==0), size=9,
                       color=WHITE if i==0 else BLACK)) for c in row]
        data.append(r)
    t = Table(data, colWidths=cw)
    style = [
        ("BACKGROUND",(0,0),(-1,0), header_bg),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]
    if alt:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND",(0,i),(-1,i), GRAY_LIGHT))
    t.setStyle(TableStyle(style))
    return t

# ── KATAGCHA (colored box) ───────────────────────────────────────────────
def box(text, bg=ORANGE_LIGHT, border=ORANGE, icon="!", bold_icon=True):
    data = [[
        Paragraph(icon, ps("bi", bold=bold_icon, size=11, color=border, align="CENTER")),
        Paragraph(text, ps("bt", size=9, leading=13))
    ]]
    t = Table(data, colWidths=[0.5*cm, TW - 0.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), bg),
        ("BOX",(0,0),(-1,-1), 1, border),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("TOPPADDING",(0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",(0,0),(0,0), 8),
        ("LEFTPADDING",(1,0),(1,0), 8),
    ]))
    return t

def info_box(text):  return box(text, GREEN_LIGHT, GREEN_DARK, "i", False)
def warn_box(text):  return box(text, ORANGE_LIGHT, ORANGE, "!", True)
def danger_box(text):return box(text, RED_LIGHT, RED_DARK, "!", True)
def blue_box(text):  return box(text, BLUE_LIGHT, BLUE_MED, "i", False)

# ── KOMANDA SATRI ───────────────────────────────────────────────────────
def cmd_row(cmd, desc, cmd_color=BLUE_MED):
    data = [[
        Paragraph(cmd,  ps("c1", bold=True, size=9, color=WHITE)),
        Paragraph(desc, ps("c2", size=9))
    ]]
    t = Table(data, colWidths=[TW*0.32, TW*0.68])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0), cmd_color),
        ("BACKGROUND",(1,0),(1,0), GRAY_LIGHT),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    return t

def steps_table(steps):
    data = []
    for i, (n, text) in enumerate(steps):
        data.append([
            Paragraph(str(n), ps("sn2", bold=True, size=10, color=WHITE, align="CENTER")),
            Paragraph(text,   ps("st2", size=9))
        ])
    t = Table(data, colWidths=[0.7*cm, TW - 0.7*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1), BLUE_MED),
        ("BACKGROUND",(1,0),(1,-1), BLUE_LIGHT),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("TOPPADDING",(0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",(0,0),(0,0), 4),
        ("LEFTPADDING",(1,0),(1,0), 8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    return t

# ── SARLAVHA / FOOTER ────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(colors.HexColor("#757575"))
    canvas.drawString(ML, 0.7*cm, "KIBER-STANSIYA OSINT PRO")
    canvas.drawRightString(W - MR, 0.7*cm, "Admin Qo'llanmasi")
    canvas.setStrokeColor(GRAY_MED)
    canvas.setLineWidth(0.5)
    canvas.line(ML, 0.9*cm, W - MR, 0.9*cm)
    page = doc.page
    canvas.drawCentredString(W/2, 0.4*cm, f"— {page} —")
    canvas.restoreState()

# ════════════════════════════════════════════════════════════════════════
# KONTENT
# ════════════════════════════════════════════════════════════════════════
def build_story():
    story = []

    # ── MUQOVA ──────────────────────────────────────────────────────────
    story += [sp(60),
        Paragraph("KIBER-STANSIYA", ps("cov1", bold=True, size=32, color=BLUE_DARK, align="CENTER")),
        Paragraph("OSINT PRO", ps("cov2", bold=True, size=32, color=BLUE_DARK, align="CENTER")),
        sp(4),
        HRFlowable(width="70%", thickness=3, color=BLUE_DARK, spaceAfter=16),
        Paragraph("ADMIN QO'LLANMASI", ps("cov3", bold=True, size=15, align="CENTER")),
        Paragraph("To'liq foydalanish yo'riqnomasi — v2", ps("cov4", size=10, color=colors.HexColor("#757575"), align="CENTER")),
        sp(30),
    ]
    info = [
        ["Maqsad:",       "Telegram OSINT, tergov, firibgarlarni aniqlash"],
        ["Foydalanuvchi:","Faqat ruxsat etilgan adminlar"],
        ["Tizim:",        "2× Userbot + Bot (Telethon asosida)"],
        ["Ma'lumotnoma:", "Barcha funksiyalar va komandalar"],
    ]
    cov_t = Table(info, colWidths=[TW*0.28, TW*0.72])
    cov_t.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1), 1, BLUE_MED),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("BACKGROUND",(0,0),(0,-1), BLUE_LIGHT),
        ("FONTNAME",(0,0),(0,-1), FONT_BOLD),
        ("FONTNAME",(1,0),(1,-1), FONT),
        ("FONTSIZE",(0,0),(-1,-1), 9.5),
        ("TEXTCOLOR",(0,0),(0,-1), BLUE_DARK),
        ("TOPPADDING",(0,0),(-1,-1),7),
        ("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("LEFTPADDING",(0,0),(-1,-1),10),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story += [cov_t, sp(20),
        danger_box("Ushbu qo'llanma maxfiy. Faqat ruxsat etilgan adminlar bilan ulashing.\n"
                   "Bot noto'g'ri maqsadlarda ishlatilishi qat'iyan taqiqlanadi."),
        PageBreak()
    ]

    # ── MUNDARIJA ────────────────────────────────────────────────────────
    story += [sp(10), Paragraph("MUNDARIJA", ps("toc_h", bold=True, size=16, color=BLUE_DARK, align="CENTER")), sp(12)]
    toc = [
        ["Bo'lim", "Sarlavha",                  "Tarkib"],
        ["1",  "Umumiy Ma'lumot",               "Bot nima va qanday ishlaydi"],
        ["2",  "2× Userbot Tizimi",             "Parallel userbot ishlashi"],
        ["3",  "Asosiy Tugmalar",               "Barcha tugmalar va vazifalari"],
        ["4",  "Skanerlash Qo'llanmasi",        "Guruh, kanal, yopiq guruh"],
        ["5",  "Tergov Vositalari",             "/tergov komandasi va funksiyalar"],
        ["6",  "Kamentariya Xisoboti (PDF)",    "To'liq PDF hisobot yaratish"],
        ["7",  "Alert Tizimi",                  "Kalit so'z bildirishnomalar"],
        ["8",  "Musiqa Monitoring",             "Audio fingerprint tizimi"],
        ["9",  "Phishing Tekshiruvi",           "APK, URL, inline tugma tekshiruvi"],
        ["10", "Xabar Keshi & Qidiruv",         "messages_cache va FTS5 qidiruv"],
        ["11", "Monitoring Tizimi",             "Fon jarayonlari"],
        ["12", "Trust Score",                   "Ishonchlilik bali tushuntirishi"],
        ["13", "Admin Boshqaruvi",              "Admin qo'shish va o'chirish"],
        ["14", "Muhim Qoidalar",                "To'g'ri foydalanish"],
        ["15", "Tezkor Yordam",                 "Vaziyat — Nima qilish jadvali"],
    ]
    toc_t = Table(toc, colWidths=[0.8*cm, TW*0.38, TW*0.52])
    toc_style = [
        ("BACKGROUND",(0,0),(-1,0), BLUE_HEADER),
        ("FONTNAME",(0,0),(-1,0), FONT_BOLD),
        ("TEXTCOLOR",(0,0),(-1,0), WHITE),
        ("FONTSIZE",(0,0),(-1,-1), 9),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("TOPPADDING",(0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]
    for i in range(1, len(toc)):
        if i % 2 == 0:
            toc_style.append(("BACKGROUND",(0,i),(-1,i), GRAY_LIGHT))
        else:
            bg_map = {1:BLUE_LIGHT,2:colors.HexColor("#E8EAF6"),3:BLUE_LIGHT,4:colors.HexColor("#E8EAF6"),
                      5:BLUE_LIGHT,6:colors.HexColor("#E8EAF6"),7:BLUE_LIGHT,8:colors.HexColor("#E8EAF6"),
                      9:BLUE_LIGHT,10:colors.HexColor("#E8EAF6"),11:BLUE_LIGHT,12:colors.HexColor("#E8EAF6"),
                      13:BLUE_LIGHT,14:colors.HexColor("#E8EAF6"),15:BLUE_LIGHT}
            toc_style.append(("BACKGROUND",(0,i),(-1,i), bg_map.get(i, WHITE)))
        toc_style.append(("FONTNAME",(0,i),(0,i), FONT_BOLD))
        toc_style.append(("TEXTCOLOR",(0,i),(0,i), BLUE_DARK))
    toc_t.setStyle(TableStyle(toc_style))
    story += [toc_t, PageBreak()]

    # ════ 1. UMUMIY MA'LUMOT ════════════════════════════════════════════
    story += [section_header(1, "UMUMIY MA'LUMOT", "Bot nima va qanday ishlaydi"), sp(10)]
    story.append(Paragraph(
        "Kiber-Stansiya OSINT Pro — Telegram guruh va kanallaridan ma'lumot yig'ish, "
        "firibgarlar va bank kartasi bilan bog'liq shaxslarni tergov qilish uchun mo'ljallangan "
        "maxsus razvedka tizimidir.", S_BODY))
    story.append(sp(6))
    arch = [
        ["USERBOT 1 & 2", "BOT"],
        ["Telegram API orqali\nma'lumot yig'adi\nFon da ishlaydi\nParallel skanerlash",
         "Siz bilan muloqot qiladi\nBuyruqlarni qabul qiladi\nNatijalarni yuboradi"],
    ]
    arch_t = Table(arch, colWidths=[TW/2, TW/2])
    arch_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), BLUE_HEADER),
        ("BACKGROUND",(0,1),(0,1), BLUE_MED),
        ("BACKGROUND",(1,1),(1,1), colors.HexColor("#37474F")),
        ("FONTNAME",(0,0),(-1,-1), FONT_BOLD),
        ("FONTSIZE",(0,0),(-1,-1), 9.5),
        ("TEXTCOLOR",(0,0),(-1,-1), WHITE),
        ("GRID",(0,0),(-1,-1), 1, WHITE),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 10),
    ]))
    story += [arch_t, sp(8)]
    users = [["Daraja","Huquqlar"],
             ["Super Admin","Barcha huquqlar + admin qo'shish/o'chirish"],
             ["Admin","Skanerlash, qidiruv, tergov, fayl olish"]]
    story += [Paragraph("Foydalana oluvchilar:", S_BOLD), simple_table(users), PageBreak()]

    # ════ 2. 2× USERBOT TIZIMI ══════════════════════════════════════════
    story += [section_header(2, "2× USERBOT TIZIMI", "Parallel userbot ishlashi"), sp(10)]
    story.append(Paragraph(
        "Bot bir vaqtda 2 ta userbot (telefon akkaunt) bilan ishlaydi. "
        "Bu skanerlash tezligini 2 barobarga oshiradi va kanallarni to'g'ri taqsimlaydi.", S_BODY))
    story.append(sp(6))
    ub_rows = [
        ["Vazifa","Userbot 1","Userbot 2"],
        ["Ochiq kanallar","1-yarmini skanerlaydi","2-yarmini skanerlaydi"],
        ["Maxfiy kanallar","O'zi join qilganlarni","O'zi join qilganlarni"],
        ["t.me/c/NUMERIC","Numeric ID tekshiradi","Numeric ID tekshiradi"],
        ["Profil monitoring","Juft user_id lar","Toq user_id lar"],
        ["Xabar skanerlash","Faqat UB1 (barcha)","Hozircha ishlatilmaydi"],
    ]
    story += [simple_table(ub_rows, [TW*0.34, TW*0.33, TW*0.33]), sp(8)]
    story.append(Paragraph("Kanal routing mantiq:", S_BOLD))
    routing = [
        ["Kanal turi","Qanday aniqlanadi","Qaysi userbot"],
        ["Ochiq (@username)","Public = true","Teng bo'linadi"],
        ["Invite link (t.me/+xxx)","hidden_channel_knocker jadvalida","Join qilgan userbot"],
        ["t.me/c/2364619052/1","numeric_id =-1002364619052","Join qilgan userbot"],
        ["-1001234567890","Raqamli ID bevosita","Numeric ID bo'yicha"],
    ]
    story += [simple_table(routing, [TW*0.3, TW*0.38, TW*0.32]), sp(8)]
    story += [
        info_box("Qr_login2.py orqali ikkinchi userbot sessiyasini yaratish:\n"
                 "python qr_login2.py — QR kodini Telegram ilovasida skan qiling"),
        PageBreak()
    ]

    # ════ 3. ASOSIY TUGMALAR ════════════════════════════════════════════
    story += [section_header(3, "ASOSIY TUGMALAR", "Barcha tugmalar va vazifalari"), sp(10)]

    funcs = [
        ("🔍", "Skanerlash", BLUE_MED,
         "Guruh yoki kanal a'zorlarini skanerlaydi.\nLink turini o'zi avtomatik aniqlab oladi:",
         [("Ochiq guruh → @username yoki t.me/username", "A'zolar ro'yxatidan har bir profil yig'iladi"),
          ("Yopiq guruh → t.me/+xxxxxxxxxx (invite link)", "Xabarlardan foydalanuvchilar aniqlanadi"),
          ("Kanal → @kanal nomi yoki t.me/kanal", "Postlar ostidagi kommentariyalar skanerlanadi")],
         "Natija: Excel (.xlsx) fayl — barcha profillar ma'lumotlari"),
        ("🔎", "Kalit So'z Qidiruv", colors.HexColor("#1565C0"),
         "Monitoring yig'gan xabarlardan kalit so'z yoki ID qidiradi.",
         [("So'z yoki ID raqam kiriting", ""),
          ("Qidiruv davrini tanlang: 1 kun / 7 kun / 30 kun / Barchasi", ""),
          ("Natija: xabarlar ro'yxati (manba, sana, kimdan)", ""),
          ("Katta bazada: FTS5 orqali tez qidiruv ishlaydi", "")],
         "Faqat raqam kiritilsa — Telegram ID bo'yicha qidiradi"),
        ("📊", "Kuzatuv Holati (Status)", colors.HexColor("#00695C"),
         "Botning joriy holati va boshqaruv tugmalari.",
         [("Monitoring ishlayaptimi yoki to'xtapganmi", ""),
          ("Skanerlash navbatida nechta topshiriq bor", ""),
          ("Profil kuzatuvi va musiqa monitoring holati", ""),
          ("FTS5 indeks holati va kesh statistikasi", "")],
         "Tugmalar: ⏸ To'xtatish | ▶ Davom etish | 🔄 Navbatni tozalash"),
        ("📁", "Monitoringdan Fayl Olish", colors.HexColor("#4527A0"),
         "Monitoring yig'gan barcha profillarni Excel fayl sifatida yuboradi.",
         [("Лист1 — barcha yig'ilgan profillar (to'liq ma'lumotlar)", ""),
          ("Лист2 — faqat karta/telefon ma'lumotli profillar", "")],
         "Katta fayllar (1000+ profil) biroz vaqt oladi"),
        ("📦", "Arxiv / Savatcha", colors.HexColor("#E65100"),
         "Barcha oldingi skanerlash natijalari saqlanadi.",
         [("Kerakli faylni tanlang — bot yuboradi", ""),
          ("Fayllar sana bo'yicha tartiblanadi", "")], ""),
        ("🔐", "Maxfiy Kanal Qo'shish", colors.HexColor("#880E4F"),
         "Monitoringga yangi kanal/guruh qo'shadi.",
         [("Link yuboring — userbot avtomatik qo'shiladi", ""),
          ("Qo'shilgandan so'ng monitoring darhol boshlanadi", ""),
          ("Qaysi userbot join qilsa — shu userbot skanerlaydi", "")], ""),
        ("📋", "Kamentariya Xisoboti", colors.HexColor("#BF360C"),
         "Shaxs haqida to'liq rasmiy PDF hisobot yaratadi.",
         [("Telefon: +998901234567", ""),
          ("Username: @username", ""),
          ("Profil ID: 123456789", "")],
         "Natija: PDF fayl (profil, karta, faollik, tarmoq, trust score)"),
    ]

    for icon, title, bg, desc, items, note in funcs:
        block = [func_header(icon, title, bg), ]
        block.append(Paragraph(desc, ps("fd", size=9, leading=13, space_before=4)))
        for item, sub in items:
            if sub:
                block.append(Paragraph(f"• <b>{item}</b>", ps("fi", size=9, space_before=1)))
                block.append(Paragraph(f"  {sub}", ps("fs", size=8.5, color=colors.HexColor("#424242"))))
            else:
                block.append(Paragraph(f"• {item}", ps("fi2", size=9, space_before=1)))
        if note:
            block.append(Paragraph(note, ps("fn", size=8.5, color=ORANGE, space_before=2)))
        block.append(sp(6))
        story.append(KeepTogether(block))

    story.append(PageBreak())

    # ════ 4. SKANERLASH QO'LLANMASI ═════════════════════════════════════
    story += [section_header(4, "SKANERLASH QO'LLANMASI", "Guruh, kanal, yopiq guruh"), sp(10)]
    story.append(Paragraph("Qo'llanish tartibi:", S_BOLD))
    story += [steps_table([
        (1, "🔍 Skanerlash tugmasini bosing"),
        (2, "Link yuboring (bot tur ini o'zi aniqlab oladi)"),
        (3, "Skanerlash fonda boshlanadi — tugagach Excel fayl yuboriladi"),
    ]), sp(10)]
    story.append(Paragraph("Link turlari:", S_BOLD))
    link_rows = [
        ["Link", "Tur"],
        ["@guruh_nomi", "Ochiq guruh — a'zolar ro'yxatidan"],
        ["https://t.me/guruh_nomi", "Ochiq guruh — URL format"],
        ["https://t.me/+AbCdEfGhIjKlMn", "Yopiq guruh — invite link (+bilan)"],
        ["@kanal_nomi", "Kanal — kommentariyalardan"],
        ["-1001234567890", "Guruh ID raqam (manfiy)"],
        ["https://t.me/c/2364619052/1", "Maxfiy kanal — numeric format"],
    ]
    story += [simple_table(link_rows), sp(10)]
    story.append(Paragraph("Taxminiy skanerlash vaqti:", S_BOLD))
    time_rows = [
        ["Hajm", "Vaqt"],
        ["Kichik guruh (100 kishi)","≈ 1–2 daqiqa"],
        ["O'rta guruh (500 kishi)","≈ 5–8 daqiqa"],
        ["Katta guruh (2000 kishi)","≈ 20–40 daqiqa"],
        ["Juda katta (5000+ kishi)","≈ 1–2 soat"],
    ]
    story += [simple_table(time_rows), sp(8),
        warn_box("Bir vaqtda faqat BITTA skanerlash ishlaydi.\n"
                 "Ikkinchi link yuborsangiz — navbatga qo'shiladi va birinchisi tugagach boshlanadi.\n"
                 "Flood xatosi chiqsa — bot o'zi kutib qayta urinadi, siz hech narsa qilmang."),
        PageBreak()]

    # ════ 5. TERGOV VOSITALARI ═══════════════════════════════════════════
    story += [section_header(5, "TERGOV VOSITALARI", "/tergov komandasi"), sp(6)]
    story.append(Paragraph(
        "Tergov vositalari tugmachasi klaviaturadan yashirilgan. Ishlatish uchun /tergov yozing — menyu ochiladi.", S_BODY))
    story.append(sp(6))

    story.append(Paragraph("Profil tahlili:", ps("sh", bold=True, size=10, color=BLUE_DARK, space_after=4)))
    for cmd, desc, bg in [
        ("/trust [ID]", "Trust Score — 0-100 ishonchlilik bali. Profil rasmi, bio, akkaunt yoshi, xabarlar soniga qarab hisoblanadi", BLUE_MED),
        ("/changes [ID]", "Profil o'zgarishlar tarixi — ism, familiya, username, rasm qachon o'zgargani", BLUE_MED),
        ("/photo [ID]", "Profil rasm tarixi — rasmlar qachon almashtirilgani", BLUE_MED),
        ("/timeline [ID]", "Faollik tarixi grafigi — xabarlar soat/kun/oy bo'yicha taqsimoti", BLUE_MED),
        ("/lifecycle [ID]", "Akkaunt \"hayoti\" — birinchi va oxirgi xabar sanasi, umumiy faollik davri", BLUE_MED),
        ("/style [ID]", "Yozuv uslubi tahlili — xabar uzunligi, emoji ishlatishi, kecha/kunduz faollik", BLUE_MED),
        ("/evidence [ID]", "To'liq dalillar to'plami — bazadagi barcha ma'lumot", BLUE_MED),
    ]:
        story.append(cmd_row(cmd, desc, bg))
    story.append(sp(8))

    story.append(Paragraph("Qidiruv:", ps("sh2", bold=True, size=10, color=GREEN_DARK, space_after=4)))
    for cmd, desc in [
        ("/lookup [username]", "Username bo'yicha qidiruv → ID, ism, bio, karta/tel"),
        ("/phone [+raqam]", "Telefon bo'yicha qidiruv → +998xxxxxxxxx → profil"),
    ]:
        story.append(cmd_row(cmd, desc, GREEN_DARK))
    story.append(sp(8))

    story.append(Paragraph("Tahlil:", ps("sh3", bold=True, size=10, color=PURPLE_DARK, space_after=4)))
    for cmd, desc in [
        ("/compare [ID1] [ID2]", "Ikki shaxs yozuv uslubini solishtirish — bir xil odam bo'lishi mumkinmi?"),
        ("/common [link1] [link2]", "Ikki guruhning umumiy a'zolari — kim ikkalasida ham bor?"),
        ("/coordinated [link]", "Koordinatsiyali xatti-harakat — bir vaqtda bir xil mazmun yuborganlap"),
        ("/temporal", "Bir vaqtda faol shaxslar — barcha kanallardan bir lahzada aktiv bo'lganlar"),
        ("/deleted [link]", "O'chirilgan xabarlar bazasi — guruh/kanaldan o'chirilgan xabarlar"),
        ("/network [link]", "Tarmoq xaritasi — guruh a'zolarining o'zaro aloqalari"),
    ]:
        story.append(cmd_row(cmd, desc, PURPLE_DARK))
    story.append(sp(8))

    story.append(Paragraph("Tergov ishlari:", ps("sh4", bold=True, size=10, color=ORANGE, space_after=4)))
    story.append(Paragraph("Bir nechta tergovni alohida-alohida yuritish imkoni:", S_SMALL))
    for cmd, desc in [
        ("/case new [nom]", "Yangi tergov ishi ochish. Misol: /case new Firibgar_Akbar"),
        ("/case list", "Barcha ochiq tergov ishlari ro'yxati"),
        ("/case add [ID] [nom]", "Tergovga shaxs qo'shish. Misol: /case add 3 123456789"),
        ("/case report [ID]", "Tergov bo'yicha hisobot — barcha qo'shilgan shaxslar va dalillar"),
        ("/case del [ID]", "Tergov ishini yopish / o'chirish"),
    ]:
        story.append(cmd_row(cmd, desc, ORANGE))
    story.append(PageBreak())

    # ════ 6. KAMENTARIYA XISOBOTI ════════════════════════════════════════
    story += [section_header(6, "KAMENTARIYA XISOBOTI", "To'liq PDF hisobot yaratish"), sp(10)]
    story.append(Paragraph("Shaxs haqida to'liq rasmiy PDF hisobot yaratadi.", S_BODY))
    story.append(sp(6))
    story.append(Paragraph("Foydalanish tartibi:", S_BOLD))
    story += [steps_table([
        (1, "📋 Kamentariya Xisoboti tugmasini bosing"),
        (2, "Shaxsni quyidagi usullardan biri bilan kiriting"),
        (3, "Bot biroz kutib PDF fayl yuboradi"),
    ]), sp(8)]
    ki_rows = [
        ["Kiritish usuli","Format"],
        ["Telefon raqam","+998901234567"],
        ["Username","@username"],
        ["Telegram ID","123456789"],
    ]
    story += [simple_table(ki_rows), sp(8)]
    story.append(Paragraph("PDF tarkibi:", S_BOLD))
    pdf_rows = [
        ["Bo'lim","Tarkib"],
        ["Asosiy ma'lumotlar","Ism, familiya, username, Telegram ID"],
        ["Profil rasmi","Joriy va avvalgi rasmlar"],
        ["Bio matni","Profil tavsifi"],
        ["Telefon raqamlar","Topilgan telefon raqamlar"],
        ["Bank karta","Topilgan karta raqamlari"],
        ["Faollik statistikasi","Xabarlar soni, birinchi/oxirgi sana"],
        ["Manbalar","Qaysi guruh/kanallarda uchragan"],
        ["Trust Score","Ishonchlilik bali (0-100)"],
        ["Tarmoq aloqalari","Kimlar bilan aloqada bo'lgani"],
    ]
    story += [simple_table(pdf_rows), PageBreak()]

    # ════ 7. ALERT TIZIMI ════════════════════════════════════════════════
    story += [section_header(7, "ALERT TIZIMI", "/alert komandasi"), sp(10)]
    story.append(Paragraph(
        "Monitoring jarayonida muayyan so'z uchrasa darhol sizga bildirishnoma yuboradi.", S_BODY))
    story.append(sp(6))
    for cmd, desc, bg in [
        ("/alert", "Alert boshqaruv oynasi (menyu ko'rinishida)", BLUE_MED),
        ("/alert add [so'z]", "Yangi alert qo'shish. Misol: /alert add karta raqam", BLUE_MED),
        ("/alert del [ID]", "Alertni o'chirish", RED_DARK),
        ("/alert list", "Barcha alertlar ro'yxati", colors.HexColor("#37474F")),
    ]:
        story.append(cmd_row(cmd, desc, bg))
    story.append(sp(8))
    story += [
        info_box("Misol: /alert add kartadan pul o'tkazish\n"
                 "Monitoring biror kanalda \"kartadan pul o'tkazish\" so'zini topsa —\n"
                 "darhol sizga xabar, qaysi kanal, kim yozgani, sana bilan yuboradi."),
        PageBreak()
    ]

    # ════ 8. MUSIQA MONITORING ══════════════════════════════════════════
    story += [section_header(8, "MUSIQA MONITORING", "Audio fingerprint tizimi"), sp(10)]
    story.append(Paragraph(
        "Bot audio \"barmoq izi\" (fingerprint) texnologiyasi orqali musiqalarni taniydi — "
        "hatto sifat past yoki qisqartirilgan bo'lsa ham.", S_BODY))
    story.append(sp(6))

    mus_funcs = [
        ("🎵", "Ko'p Musiqa Qidirish", BLUE_MED,
         ["Tugmani bosing",
          "Audio fayllarni birin-ketin yuboring (10+ ta bo'lishi mumkin)",
          "Yuborib bo'lgach /search_done yozing",
          "Natija: har bir musiqa qaysi kanalda, qachon, kim tomonidan joylashtirilgani"]),
        ("👁", "Kuzatiladigan Musiqalar", colors.HexColor("#1B5E20"),
         ["Muayyan musiqalar uchun kuzatuv o'rnatish",
          "Kanal shu musiqani joylashtirsa darhol xabar beradi",
          "Kuzatiladigan musiqalar ro'yxatini boshqarish"]),
    ]
    for icon, title, bg, items in mus_funcs:
        block = [func_header(icon, title, bg)]
        for item in items:
            block.append(Paragraph(f"• {item}", ps("mi", size=9, space_before=2)))
        block.append(sp(6))
        story.append(KeepTogether(block))

    story.append(sp(6))
    story.append(Paragraph("2× Userbot bilan musiqa monitoring:", S_BOLD))
    mus_ub = [
        ["UB1 ishlaydi","UB2 ishlaydi"],
        ["O'zi join qilgan maxfiy kanallar\nOchiq kanallarning 1-yarmi",
         "O'zi join qilgan maxfiy kanallar\nOchiq kanallarning 2-yarmi"],
    ]
    mus_t = Table(mus_ub, colWidths=[TW/2, TW/2])
    mus_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), BLUE_MED),
        ("BACKGROUND",(0,1),(0,1), BLUE_LIGHT),
        ("BACKGROUND",(1,1),(1,1), colors.HexColor("#E8F5E9")),
        ("FONTNAME",(0,0),(-1,0), FONT_BOLD),
        ("TEXTCOLOR",(0,0),(-1,0), WHITE),
        ("FONTSIZE",(0,0),(-1,-1), 9),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),8),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    story += [mus_t, sp(8),
        warn_box("Flood storm himoyasi: 10 ketma-ket kanal 2 soniyadan tez tugasa →\n"
                 "Music tracker avtomatik 20 daqiqa pauza qiladi.\nLogda: [MUSIQA-UB1] Flood storm aniqlandi — 20 daqiqa pauza..."),
        PageBreak()]

    # ════ 9. PHISHING TEKSHIRUVI ═════════════════════════════════════════
    story += [section_header(9, "PHISHING TEKSHIRUVI", "APK, URL, inline tugma tekshiruvi"), sp(10)]
    story.append(Paragraph(
        "Bot kanallar/guruhlardagi xavfli fayllar va havolalarni avtomatik tekshiradi.", S_BODY))
    story.append(sp(6))

    ph_funcs = [
        ("📱", "APK Fayl Tahlili", RED_DARK,
         "Android o'rnatish fayllari (APK) xavfli bo'lishi mumkin.",
         ["Barcha ruxsatlar ro'yxati (kamera, mikrofon, GPS, SMS...)",
          "Shubhali URL va domenlar ichidan topiladi",
          "Shifrlangan APK → 40+ umumiy parol sinab buziladi",
          "Buzib olinsa — to'liq tahlil davom etadi"],
         "Umumiy parollar: infected, virus, malware, 123, apk va boshqalar"),
        ("🌐", "URL / Havola Tekshiruvi", ORANGE,
         "Xabarlar va inline tugmalardagi URL lar avtomatik tekshiriladi.",
         ["Playwright (headless brauzer) orqali sahifa ochiladi",
          "Agar Playwright bo'lmasa — requests+BeautifulSoup bilan tekshiriladi",
          "Login forma aniqlash (phishing belgi)",
          "Bank karta maydonlari aniqlash",
          "Yashirin iframe va JS redirect aniqlash",
          "Inline tugmadagi URL ham tekshiriladi (rasm/video bilan birga ham)"],
         ""),
        ("🔘", "Inline Tugma Tekshiruvi", colors.HexColor("#880E4F"),
         "Xabarda rasm yoki video bo'lsa ham inline tugmalar tekshiriladi.",
         ["Avval \"Bonusni olish\", \"Yuklab olish\" kabi tugmalar bor-yo'qligi ko'riladi",
          "Tugmadagi URL avtomatik tekshiriladi",
          "Phishing belgilari topilsa — darhol bildirishnoma"],
         ""),
    ]
    for icon, title, bg, desc, items, note in ph_funcs:
        block = [func_header(icon, title, bg)]
        block.append(Paragraph(desc, ps("phd", size=9, leading=13, space_before=4)))
        for item in items:
            block.append(Paragraph(f"• {item}", ps("phi", size=9, space_before=2)))
        if note:
            block.append(Paragraph(note, ps("phn", size=8.5, color=ORANGE, space_before=2)))
        block.append(sp(6))
        story.append(KeepTogether(block))

    story.append(PageBreak())

    # ════ 10. XABAR KESHI & QIDIRUV ══════════════════════════════════════
    story += [section_header(10, "XABAR KESHI & QIDIRUV", "messages_cache va FTS5 qidiruv"), sp(10)]
    story.append(Paragraph(
        "Barcha skanerlar o'qigan matnli xabarlarni SQLite bazasiga saqlaydi. "
        "Bu keshdan tez qidiruv imkonini beradi — Telegram API ga qayta murojaat qilmasdan.", S_BODY))
    story.append(sp(6))

    story.append(Paragraph("Kesh saqlaydi skanerlar:", S_BOLD))
    cache_rows = [
        ["Skaner","Saqlaydi","Limit"],
        ["deep_scan_group","Guruh barcha xabarlari","2000 belgi"],
        ["scan_messages","Yopiq guruh xabarlari","2000 belgi"],
        ["scan_channel_comments","Kanal kommentariyalari","2000 belgi"],
        ["search_keywords","Kalit so'z qidiruv","2000 belgi"],
        ["_music_process_one_source","Kanal musiqa xabarlari","2000 belgi"],
        ["_scan_user_music","Foydalanuvchi musiqasi","2000 belgi"],
        ["_scan_channel_music_after_join","Maxfiy kanal musiqasi","2000 belgi"],
        ["_read_msg_chunk","UB2 chunk xabarlari","2000 belgi"],
    ]
    story += [simple_table(cache_rows, [TW*0.42, TW*0.38, TW*0.20]), sp(8)]

    story.append(Paragraph("FTS5 tez qidiruv:", S_BOLD))
    story.append(Paragraph(
        "SQLite FTS5 (Full-Text Search) texnologiyasi qidiruv tezligini 10-100 marta oshiradi. "
        "Oddiy LIKE so'rovidan farqli o'laroq, FTS5 indeks orqali ishlaydi.", S_BODY))
    story.append(sp(4))
    fts_rows = [
        ["Xususiyat","LIKE (eski)","FTS5 (yangi)"],
        ["Tezlik","2.5M xabar ≈ 3-10s","2.5M xabar ≈ 0.1-0.5s"],
        ["Qidiruv usuli","Har satrni ketma-ket","Indeks orqali"],
        ["Ko'p so'z","OR bilan","Avtomatik"],
        ["Zaxira","—","FTS5 ishlamasa LIKE ishga tushadi"],
    ]
    story += [simple_table(fts_rows, [TW*0.32, TW*0.34, TW*0.34]), sp(8)]

    story.append(Paragraph("Ishga tushganda:", S_BOLD))
    story += [
        info_box("Bot birinchi marta ishga tushganda FTS5 indeks avtomatik quriladi:\n"
                 "[FTS5] 2,569,684 ta xabar indekslanmoqda...\n"
                 "[FTS5] Indeks tayyor (2,569,684 ta xabar).\n"
                 "Bu bir martalik jarayon — keyingi ishga tushishlarda takrorlanmaydi."),
        sp(6),
        Paragraph("Kesh statistikasini ko'rish: 📊 Kuzatuv Holati (Status) tugmasini bosing", S_SMALL),
        PageBreak()
    ]

    # ════ 11. MONITORING TIZIMI ══════════════════════════════════════════
    story += [section_header(11, "MONITORING TIZIMI", "Fon jarayonlari"), sp(10)]
    story.append(Paragraph(
        "Monitoring fonda doimo ishlaydi — siz hech narsa qilmasangiz ham qo'shilgan "
        "kanallarni avtomatik kuzatib turadi.", S_BODY))
    story.append(sp(6))
    mon_rows = [
        ["Jarayon","Nima qiladi","Userbot"],
        ["Xabarlar yig'ish","Yangi xabarlarni o'qib bazaga saqlaydi","UB1 + UB2"],
        ["Profil yig'ish","Yangi a'zorlarning profillarini saqlaydi","UB1 + UB2"],
        ["Alert tekshiruvi","Alert so'zlari uchrasa darhol bildirishnoma","UB1"],
        ["Musiqa aniqlash","Audio fayllarni tanib fingerprint saqlaydi","UB1 + UB2"],
        ["Profil kuzatuvi","Ism, rasm, username o'zgarishlarini kuzatadi","UB1+UB2 bo'linadi"],
        ["FTS5 rebuild","Bir martalik indeks qurish (startup)","Background"],
    ]
    story += [simple_table(mon_rows, [TW*0.3, TW*0.45, TW*0.25]), sp(8)]

    story.append(Paragraph("Profil monitoring split (40,000+ profil):", S_BOLD))
    split_rows = [
        ["UB1 (Userbot 1)","UB2 (Userbot 2)"],
        ["user_id % 2 == 0\n(juft raqamli ID lar)","user_id % 2 == 1\n(toq raqamli ID lar)"],
        ["≈ 20,000 profil","≈ 20,000 profil"],
    ]
    split_t = Table(split_rows, colWidths=[TW/2, TW/2])
    split_t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), BLUE_MED),
        ("BACKGROUND",(0,1),(0,1), BLUE_LIGHT),
        ("BACKGROUND",(1,1),(1,1), colors.HexColor("#E8F5E9")),
        ("BACKGROUND",(0,2),(0,2), colors.HexColor("#BBDEFB")),
        ("BACKGROUND",(1,2),(1,2), colors.HexColor("#C8E6C9")),
        ("FONTNAME",(0,0),(-1,0), FONT_BOLD),
        ("TEXTCOLOR",(0,0),(-1,0), WHITE),
        ("FONTSIZE",(0,0),(-1,-1), 9),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),8),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    story += [split_t, sp(8),
        info_box("Skanerlash vaqtida monitoring avtomatik pauza qiladi.\n"
                 "Skanerlash tugagach monitoring o'zi qayta boshlanadi.\n"
                 "📊 Kuzatuv Holati (Status) → ⏸/▶ orqali boshqarish mumkin."),
        PageBreak()]

    # ════ 12. TRUST SCORE ════════════════════════════════════════════════
    story += [section_header(12, "TRUST SCORE", "Ishonchlilik bali tushuntirishi"), sp(10)]
    story.append(Paragraph("Bot har bir shaxsga 0 dan 100 gacha ball beradi:", S_BODY))
    story.append(sp(6))
    trust_data = [
        ["90–100","Ishonchli","Eski akkaunt, to'liq profil, faol"],
        ["70–89","Yaxshi","Odatdagi foydalanuvchi"],
        ["50–69","O'rtacha","Diqqat talab qiladi"],
        ["30–49","Shubhali","Tekshirish kerak"],
        ["0–29","Xavfli","Firibgar bo'lishi mumkin"],
    ]
    tr_t = Table(trust_data, colWidths=[TW*0.18, TW*0.22, TW*0.60])
    tr_style = [
        ("FONTNAME",(0,0),(-1,-1), FONT),
        ("FONTSIZE",(0,0),(-1,-1), 9.5),
        ("GRID",(0,0),(-1,-1), 0.4, GRAY_MED),
        ("TOPPADDING",(0,0),(-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
        ("ALIGN",(0,0),(1,-1),"CENTER"),
        ("FONTNAME",(1,0),(1,-1), FONT_BOLD),
        ("BACKGROUND",(0,0),(1,0), colors.HexColor("#1B5E20")),
        ("TEXTCOLOR",(0,0),(1,0), WHITE),
        ("BACKGROUND",(0,1),(1,1), colors.HexColor("#388E3C")),
        ("TEXTCOLOR",(0,1),(1,1), WHITE),
        ("BACKGROUND",(0,2),(1,2), colors.HexColor("#F9A825")),
        ("TEXTCOLOR",(0,2),(1,2), WHITE),
        ("BACKGROUND",(0,3),(1,3), colors.HexColor("#E65100")),
        ("TEXTCOLOR",(0,3),(1,3), WHITE),
        ("BACKGROUND",(0,4),(1,4), colors.HexColor("#B71C1C")),
        ("TEXTCOLOR",(0,4),(1,4), WHITE),
    ]
    tr_t.setStyle(TableStyle(tr_style))
    story += [tr_t, sp(10)]
    story.append(Paragraph("Ball qanday hisoblanadi:", S_BOLD))
    ball_rows = [
        ["Omil","Ta'sir"],
        ["+ Profil rasmi bor","+ ball qo'shiladi"],
        ["+ Bio to'ldirilgan","+ ball qo'shiladi"],
        ["+ Telefon bog'langan","+ ball qo'shiladi"],
        ["+ Akkaunt 1 yildan eski","+ ball qo'shiladi"],
        ["+ Ko'p xabar yozgan","+ ball qo'shiladi"],
        ["+ Telegram Premium","+ ball qo'shiladi"],
        ["– Yaqinda ro'yxatdan o'tgan","– ball ayiriladi"],
        ["– Username yo'q","– ball ayiriladi"],
        ["– Hech qanday ma'lumot yo'q","– ball ayiriladi"],
    ]
    story += [simple_table(ball_rows), PageBreak()]

    # ════ 13. ADMIN BOSHQARUVI ════════════════════════════════════════════
    story += [section_header(13, "ADMIN BOSHQARUVI", "Faqat Super Admin"), sp(10)]
    story.append(Paragraph("Super Admin barcha adminlarni boshqaradi:", S_BODY))
    story.append(sp(6))
    adm_rows = [
        ["Komanda","Vazifa"],
        ["/add_admin [ID]","Yangi admin qo'shish. ID — Telegram profil raqami"],
        ["/del_admin [ID]","Adminni o'chirish"],
        ["/start","Botni qayta ishga tushirish, menyu ochish"],
    ]
    story += [simple_table(adm_rows), sp(8),
        info_box("Telegram ID ni bilish: @userinfobot ga xabar yozing → ID yuboradi.\n"
                 "Super Admin o'zi adminlar ro'yxatida ko'rinmaydi, lekin to'liq huquqqa ega."),
        PageBreak()]

    # ════ 14. MUHIM QOIDALAR ═════════════════════════════════════════════
    story += [section_header(14, "MUHIM QOIDALAR", "To'g'ri foydalanish"), sp(10)]

    story.append(Paragraph("✅ To'g'ri foydalanish:", ps("ok", bold=True, size=10, color=GREEN_DARK)))
    for item in ["Firibgarlarni aniqlash va hujjatlash",
                 "Bank kartasi bilan bog'liq shaxslarni tekshirish",
                 "Rasmiy tergov ishi yuritish",
                 "Shubhali faoliyatni monitoring qilish"]:
        story.append(Paragraph(f"• {item}", ps("qi", size=9, space_before=2)))
    story.append(sp(8))

    story.append(Paragraph("❌ Noto'g'ri foydalanish (taqiqlangan):", ps("nok", bold=True, size=10, color=RED_DARK)))
    for item in ["Shaxsiy ma'lumotlarni ruxsatsiz tarqatish",
                 "Shantaj yoki tahdid maqsadida ishlatish",
                 "Raqobatchilarni shaxsiy maqsadda kuzatish",
                 "Bot ma'lumotlarini uchinchi shaxslarga sotish"]:
        story.append(Paragraph(f"• {item}", ps("ni", size=9, color=RED_DARK, space_before=2)))
    story.append(sp(8))

    story.append(Paragraph("⚙ Texnik qoidalar:", ps("tx", bold=True, size=10, color=ORANGE)))
    for item in ["Bir vaqtda bitta skanerlash — ikkinchisi navbatga turadi",
                 "Katta guruhlarni kechasi skanerlash tavsiya etiladi",
                 "Flood xatosi chiqsa — bot o'zi boshqaradi, kutish kerak",
                 "Bot javob bermasa — /start yozing yoki Qayta Yuklash bosing",
                 "Monitoring fayli katta bo'lsa — bir necha soniya kuting",
                 "Flood storm bo'lsa — Music tracker 20 daqiqa pauza oladi (normal holat)"]:
        story.append(Paragraph(f"• {item}", ps("ti", size=9, space_before=2)))
    story.append(PageBreak())

    # ════ 15. TEZKOR YORDAM ══════════════════════════════════════════════
    story += [section_header(15, "TEZKOR YORDAM KARTOCHKASI", "Vaziyat → Nima qilish"), sp(10)]
    help_rows = [
        ["Vaziyat","Nima qilish"],
        ["Guruh a'zorlarini yig'moq","🔍 Skanerlash → link yuboring"],
        ["Shaxsni ID bo'yicha qidirish","🔎 Kalit So'z Qidiruv → ID raqam"],
        ["Shaxs PDF hisoboti","📋 Kamentariya Xisoboti → tel/username/ID"],
        ["Ishonchlilik tekshiruvi","/trust [ID]"],
        ["Telefon bo'yicha qidiruv","/phone +998xxxxxxxxx"],
        ["Profil o'zgarishlari","/changes [ID]"],
        ["Ikkala guruh a'zolari","/common [link1] [link2]"],
        ["Alert sozlash","/alert add [so'z]"],
        ["Bot holati","📊 Kuzatuv Holati (Status)"],
        ["Monitoring fayli","📁 Monitoringdan Fayl Olish"],
        ["Tergov vositalari","/tergov → menyu ochiladi"],
        ["Yangi kanal qo'shish","🔐 Maxfiy Kanal Qo'shish → link"],
        ["Qidiruv indeksini yangilash","Bot restart qilish (FTS5 auto-rebuild)"],
        ["Bot muzladi","Botni qayta ishga tushiring (flood o'tadi)"],
        ["Bot ishlamayapti","/start yoki 🔄 Botni Qayta Yuklash"],
    ]
    story += [simple_table(help_rows, [TW*0.42, TW*0.58]), sp(20)]

    # Yakuniy
    story += [
        HRFlowable(width="100%", thickness=1.5, color=BLUE_DARK, spaceAfter=10),
        Paragraph("KIBER-STANSIYA OSINT PRO", ps("fin", bold=True, size=12, color=BLUE_DARK, align="CENTER")),
        Paragraph("Ushbu hujjat maxfiy. Faqat ruxsat etilgan adminlar bilan ulashing.",
                  ps("fins", size=9, color=colors.HexColor("#757575"), align="CENTER")),
    ]
    return story


# ════════════════════════════════════════════════════════════════════════
# GENERATE
# ════════════════════════════════════════════════════════════════════════
OUT = os.path.join(BASE, "Kiber_Stansiya_Qollanma_v2.pdf")
doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=ML, rightMargin=MR,
    topMargin=1.8*cm, bottomMargin=1.4*cm
)
doc.build(build_story(), onFirstPage=on_page, onLaterPages=on_page)
print(f"PDF tayyor: {OUT}")
