# phishing_checker.py — Fishing/Scam havola tekshiruv moduli
import os
import ssl
import socket
import sqlite3
import base64
import unicodedata
import urllib.parse
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

import requests

executor = ThreadPoolExecutor(max_workers=10)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phishing_stats.db")

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".click", ".tk", ".ml", ".ga", ".cf", ".gq",
    ".pw", ".cc", ".su", ".icu", ".live", ".online", ".site", ".fun", ".space"
}
SUSPICIOUS_COUNTRIES = {"Russia", "China", "North Korea", "Iran", "Belarus"}
SHORT_URL_DOMAINS = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "ow.ly", "short.link",
    "rebrand.ly", "cutt.ly", "clck.ru", "vk.cc"
}
SUSPICIOUS_KEYWORDS = {
    "login", "verify", "secure", "account", "update", "confirm", "bank",
    "payment", "signin", "password", "credential", "recover", "wallet",
    "billing", "kirish", "tasdiqlash", "xavfsiz", "hisob", "karta"
}
SCAM_BUTTON_WORDS = {
    "bonus", "sovg'a", "yutdi", "prize", "olish", "win", "gift",
    "бонус", "приз", "получить", "награда", "free", "tekin", "bepul",
    "yutuq", "lotereya", "lottery", "jackpot", "cash", "money"
}
TELEGRAM_DOMAINS = {"t.me", "telegram.me", "telegram.dog"}
UZBEK_BRANDS = {
    "payme": "payme.uz", "click": "click.uz", "uzcard": "uzcard.uz",
    "humo": "humo.uz", "kapitalbank": "kapitalbank.uz",
    "hamkorbank": "hamkorbank.uz", "myuzcard": "myuzcard.uz",
    "davrbank": "davrbank.uz", "aloqabank": "aloqabank.uz", "nbu": "nbu.uz",
}
GLOBAL_BRANDS = {
    "google": "google.com", "facebook": "facebook.com",
    "instagram": "instagram.com", "telegram": "telegram.org",
    "paypal": "paypal.com", "apple": "apple.com",
    "microsoft": "microsoft.com", "amazon": "amazon.com",
    "netflix": "netflix.com",
}
ALL_BRANDS = {**UZBEK_BRANDS, **GLOBAL_BRANDS}


# ── Ma'lumotlar bazasi ──────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS phishing_stats (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            url     TEXT,
            risk    INTEGER,
            checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_stat(url: str, risk: int):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO phishing_stats (url, risk) VALUES (?, ?)", (url, risk))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_stats() -> tuple:
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT COUNT(*), SUM(CASE WHEN risk >= 50 THEN 1 ELSE 0 END) FROM phishing_stats"
        ).fetchone()
        conn.close()
        return (row[0] or 0), (row[1] or 0)
    except Exception:
        return 0, 0


# ── Tarmoq tekshiruvlari ────────────────────────────────────────────────────

def get_redirect_chain(url: str) -> list:
    chain = []
    current = url
    try:
        for _ in range(10):
            resp = requests.get(current, allow_redirects=False, timeout=5, stream=True)
            chain.append(current)
            if resp.is_redirect and resp.headers.get("Location"):
                nxt = resp.headers["Location"]
                if not nxt.startswith("http"):
                    p = urllib.parse.urlparse(current)
                    nxt = f"{p.scheme}://{p.netloc}{nxt}"
                current = nxt
            else:
                break
    except Exception:
        pass
    return chain if chain else [url]

def check_ssl(domain: str) -> dict:
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
        expire = datetime.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (expire.replace(tzinfo=datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).days
        issuer = dict(x[0] for x in cert.get("issuer", []))
        return {"valid": True, "days_left": days_left, "issuer": issuer.get("organizationName", "Noma'lum")}
    except Exception:
        return {"valid": False, "days_left": 0, "issuer": "Noma'lum"}

def check_whois(domain: str) -> dict:
    try:
        import whois
        w = whois.whois(domain)
        created = w.creation_date
        if isinstance(created, list):
            created = created[0]
        if created:
            if isinstance(created, str):
                created = datetime.datetime.fromisoformat(created)
            if created.tzinfo is None:
                created = created.replace(tzinfo=datetime.timezone.utc)
            age = (datetime.datetime.now(datetime.timezone.utc) - created).days
            return {"age_days": age, "registrar": w.registrar or "Noma'lum"}
    except Exception:
        pass
    return {"age_days": None, "registrar": "Noma'lum"}

def _get_geo(ip: str) -> dict:
    try:
        return requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
    except Exception:
        return {}

def check_virustotal(url: str) -> dict:
    vt_key = os.getenv("VIRUSTOTAL_API_KEY", "").strip()
    if not vt_key:
        return {"available": False}
    try:
        url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        headers = {"x-apikey": vt_key}
        resp = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=10)
        if resp.status_code == 200:
            stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            if stats:
                return {"available": True, "malicious": stats.get("malicious", 0),
                        "suspicious": stats.get("suspicious", 0), "total": sum(stats.values())}
        sub = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url}, timeout=10)
        if sub.status_code == 200:
            return {"available": True, "malicious": 0, "suspicious": 0, "total": 0, "pending": True}
    except Exception:
        pass
    return {"available": False}

def check_urlhaus(url: str) -> dict:
    try:
        resp = requests.post("https://urlhaus-api.abuse.ch/v1/url/", data={"url": url}, timeout=10).json()
        status = resp.get("query_status", "")
        if status == "is_available":
            return {"available": True, "found": True,
                    "threat": resp.get("threat", "malware"), "tags": resp.get("tags") or []}
        return {"available": True, "found": False, "threat": "", "tags": []}
    except Exception:
        return {"available": False}

def check_abuseipdb(ip: str) -> dict:
    abuse_key = os.getenv("ABUSEIPDB_API_KEY", "").strip()
    if not abuse_key or ip == "Noma'lum":
        return {"available": False}
    try:
        resp = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": ip, "maxAgeInDays": 90},
            headers={"Key": abuse_key, "Accept": "application/json"}, timeout=8
        ).json()
        data = resp.get("data", {})
        return {"available": True, "abuse_score": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0)}
    except Exception:
        return {"available": False}


# ── Telegram tekshiruvlari ─────────────────────────────────────────────────

async def probe_telegram_bot(userbot, username: str) -> dict:
    """Userbot orqali shubhali botga /start yuborib yashirin havolalarni topadi."""
    if not userbot:
        return {"available": False}
    try:
        entity = await userbot.get_entity(username)
        await userbot.send_message(entity, "/start")
        await asyncio.sleep(5)
        messages = await userbot.get_messages(entity, limit=8)

        urls = set()
        texts = []
        clicked_buttons = []
        last_msg_id = 0

        def _extract(msg):
            if msg.entities:
                for ent in msg.entities:
                    if hasattr(ent, "url") and ent.url:
                        urls.add(ent.url)
            if msg.reply_markup and hasattr(msg.reply_markup, 'rows'):
                for row in msg.reply_markup.rows:
                    for btn in row.buttons:
                        if hasattr(btn, "url") and btn.url:
                            urls.add(btn.url)

        for msg in messages:
            if msg.out:
                continue
            if msg.text:
                texts.append(msg.text[:300])
            _extract(msg)
            if msg.id > last_msg_id:
                last_msg_id = msg.id

        # Inline tugmalarni bosish (URL tugmalar emas)
        for msg in messages:
            if msg.out or not msg.reply_markup:
                continue
            if not hasattr(msg.reply_markup, 'rows'):
                continue
            for row in msg.reply_markup.rows:
                for btn in row.buttons:
                    if hasattr(btn, "url") and btn.url:
                        continue
                    btn_text = getattr(btn, "text", "") or ""
                    if len(clicked_buttons) >= 4:
                        break
                    try:
                        await btn.click()
                        clicked_buttons.append(btn_text)
                        await asyncio.sleep(3)
                        new_msgs = await userbot.get_messages(entity, limit=6)
                        for nm in new_msgs:
                            if nm.out or nm.id <= last_msg_id:
                                continue
                            if nm.text:
                                texts.append(f"[{btn_text[:30]}] {nm.text[:200]}")
                            _extract(nm)
                            last_msg_id = max(last_msg_id, nm.id)
                    except Exception:
                        pass

        return {"available": True, "urls": list(urls),
                "msg_count": len([m for m in messages if not m.out]),
                "sample_text": texts[0][:200] if texts else "",
                "clicked_buttons": clicked_buttons}
    except Exception as e:
        return {"available": False, "error": str(e)[:150]}

async def check_telegram_channel_info(bot_client, url: str) -> dict:
    """Bot API orqali Telegram kanal/bot ma'lumotlarini oladi."""
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in TELEGRAM_DOMAINS:
        return {}
    path = parsed.path.strip("/")
    if not path:
        return {}
    if path.startswith("+"):
        return {"is_private_invite": True}
    username = path.split("?")[0].split("/")[0]
    if not username:
        return {}
    try:
        from telethon.tl.functions.contacts import ResolveUsernameRequest
        result = await bot_client(ResolveUsernameRequest(username))
        chat = result.chats[0] if result.chats else (result.users[0] if result.users else None)
        if not chat:
            return {"found": False, "username": username, "deleted": True}
        title = getattr(chat, 'title', '') or getattr(chat, 'first_name', '') or ''
        title_lower = title.lower().replace(" ", "").replace("_", "").replace("-", "")
        title_homograph = any(
            any(s in unicodedata.name(ch, "") for s in ("CYRILLIC", "GREEK"))
            for ch in title if ch.isalpha()
        )
        brand_in_title = []
        for brand in ALL_BRANDS:
            if brand.replace("_", "").replace("-", "") in title_lower:
                brand_in_title.append(brand)
        verified = getattr(chat, 'verified', False)
        members = getattr(chat, 'participants_count', None)
        un = getattr(chat, 'username', username)
        return {"found": True, "username": un, "title": title,
                "verified": verified, "member_count": members,
                "brand_in_title": brand_in_title, "title_has_homograph": title_homograph}
    except Exception:
        return {"found": False, "username": username, "deleted": True}

async def check_with_browser(url: str) -> dict:
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            ctx = await browser.new_context(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ))
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="networkidle", timeout=15000)
            except Exception:
                pass
            final_url = page.url
            title = await page.title()
            has_password   = await page.locator("input[type='password']").count() > 0
            has_card_input = await page.locator(
                "input[name*='card'], input[placeholder*='card'], input[placeholder*='karta'], "
                "input[name*='pan'], input[maxlength='16'], input[maxlength='19']"
            ).count() > 0
            has_form = await page.locator("form").count() > 0
            await browser.close()
            return {"available": True, "final_url": final_url, "title": title[:120],
                    "redirected": final_url.rstrip("/") != url.rstrip("/"),
                    "has_password": has_password, "has_card_input": has_card_input,
                    "has_form": has_form}
    except ImportError:
        return {"available": False}
    except Exception:
        return {"available": False}


# ── Heuristik tekshiruvlar ──────────────────────────────────────────────────

def check_url_patterns(url: str, domain: str) -> list:
    warnings = []
    try:
        socket.inet_aton(domain)
        warnings.append("⚠️ Domain o'rniga IP manzil ishlatilgan")
    except socket.error:
        pass
    if "@" in url:
        warnings.append("⚠️ URL da `@` belgisi — asl manzil yashirilgan bo'lishi mumkin")
    found = [kw for kw in SUSPICIOUS_KEYWORDS if kw in url.lower()]
    if found:
        warnings.append(f"⚠️ Shubhali so'zlar URL da: `{', '.join(found[:4])}`")
    if len(domain.split(".")) > 4:
        warnings.append(f"⚠️ Ko'p subdomen: {len(domain.split('.')) - 2} ta")
    if len(url) > 150:
        warnings.append(f"⚠️ URL juda uzun: {len(url)} ta belgi")
    if domain.count("-") >= 2:
        warnings.append("⚠️ Domenda ko'p `-` — phishing belgisi")
    return warnings

def check_brand_impersonation(domain: str) -> list:
    warnings = []
    dl = domain.lower()
    for brand, official in ALL_BRANDS.items():
        if brand in dl and dl != official and not dl.endswith("." + official):
            tag = "🇺🇿" if brand in UZBEK_BRANDS else "🌐"
            warnings.append(f"⚠️ {tag} `{brand}` brendini taqlid qilishi mumkin! Rasmiy: `{official}`")
    return warnings

def check_homograph(domain: str) -> list:
    found = []
    for ch in domain:
        if ch in ".-0123456789":
            continue
        name = unicodedata.name(ch, "")
        if any(s in name for s in ("CYRILLIC", "GREEK", "ARABIC", "ARMENIAN")):
            found.append(ch)
    if found:
        return [f"⚠️ Homograf hujum! Unicode harflar: `{''.join(set(found))}`"]
    return []

def check_telegram_url(url: str) -> list:
    warnings = []
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in TELEGRAM_DOMAINS:
        return warnings
    path = parsed.path.strip("/").lower().replace("_", "").replace("-", "")
    if not path or path.startswith("+"):
        if path.startswith("+"):
            warnings.append("⚠️ Yopiq Telegram kanal taklifi — ehtiyot bo'ling")
        return warnings
    for brand in ALL_BRANDS:
        if brand.replace("_", "").replace("-", "") in path:
            tag = "🇺🇿" if brand in UZBEK_BRANDS else "🌐"
            warnings.append(f"⚠️ {tag} Telegram username `{brand}` brendini taqlid qilishi mumkin")
    return warnings

def check_message_context_telethon(message) -> list:
    """Telethon xabar tuzilmasidan fishing belgilarini topadi."""
    warnings = []
    fwd = getattr(message, 'fwd_from', None)
    if fwd:
        from_name = getattr(fwd, 'from_name', '') or ''
        if from_name:
            nl = from_name.lower()
            if "postbot" in nl or "post bot" in nl:
                warnings.append("⚠️ @PostBot orqali forward — asl manba ataylab yashirilgan")
            for brand in ALL_BRANDS:
                if brand in nl:
                    warnings.append(f"⚠️ Forward yuboruvchi nomi `{brand}` brendini taqlid qilishi mumkin")
                    break
        if not getattr(fwd, 'channel_id', None) and not from_name:
            warnings.append("⚠️ Forward manba — nomi yo'q yashirin kanal")
    # Inline tugmalar
    markup = getattr(message, 'reply_markup', None)
    if markup and hasattr(markup, 'rows'):
        for row in markup.rows:
            for btn in row.buttons:
                btn_text = getattr(btn, 'text', '') or ''
                if btn_text:
                    found = [kw for kw in SCAM_BUTTON_WORDS if kw in btn_text.lower()]
                    if found:
                        warnings.append(f"⚠️ Tugma matni ijtimoiy muhandislik: '{btn_text}'")
                if hasattr(btn, 'url') and btn.url and 'web' in type(btn).__name__.lower():
                    warnings.append(f"⚠️ WebApp tugmasi — havola yashiringan: `{btn.url[:80]}`")
    return warnings


# ── Xavf hisoblash ──────────────────────────────────────────────────────────

def calculate_risk(domain, country, ssl_info, whois_info, redirected,
                   vt, urlhaus, abuse, pattern_w, brand_w, homograph_w,
                   tg_url_w=None, context_w=None) -> tuple:
    score = 0
    reasons = []

    if vt.get("available") and not vt.get("pending") and vt.get("malicious", 0) > 0:
        score += min(vt["malicious"] * 5, 40)
        reasons.append(f"🔴 VirusTotal: {vt['malicious']}/{vt['total']} engine xavfli dedi")
    if urlhaus.get("found"):
        score += 40
        reasons.append(f"🔴 URLhaus: bazada topildi — `{urlhaus.get('threat', 'malware')}`")
    if abuse.get("available") and abuse.get("abuse_score", 0) > 25:
        score += min(abuse["abuse_score"] // 4, 20)
        reasons.append(f"🔴 AbuseIPDB: {abuse['abuse_score']}/100 ({abuse.get('total_reports', 0)} shikoyat)")
    if homograph_w:
        score += 35
        reasons.extend(homograph_w)
    if brand_w:
        score += 25
        reasons.extend(brand_w)
    if tg_url_w:
        deleted = any("O'CHIRILGAN" in w for w in tg_url_w)
        score += 45 if deleted else 30
        reasons.extend(tg_url_w)
    if context_w:
        score += min(len(context_w) * 15, 35)
        reasons.extend(context_w)

    tld = "." + domain.split(".")[-1].lower()
    if tld in SUSPICIOUS_TLDS:
        score += 15
        reasons.append(f"⚠️ Shubhali kengaytma: `{tld}`")
    if country in SUSPICIOUS_COUNTRIES:
        score += 20
        reasons.append(f"⚠️ Server {country}da joylashgan")
    if not ssl_info["valid"]:
        score += 25
        reasons.append("⚠️ SSL sertifikat yo'q yoki yaroqsiz")
    elif ssl_info["days_left"] < 30:
        score += 10
        reasons.append(f"⚠️ SSL {ssl_info['days_left']} kun ichida tugaydi")

    age = whois_info.get("age_days")
    if age is not None:
        if age < 180:
            score += 30
            reasons.append(f"⚠️ Domen {age} kun oldin ro'yxatdan o'tgan — juda yangi")
        elif age < 365:
            score += 15
            reasons.append(f"⚠️ Domen nisbatan yangi ({age} kun)")

    if redirected:
        score += 10
        reasons.append("⚠️ Yashirin yo'naltirish aniqlandi")
    if pattern_w:
        score += min(len(pattern_w) * 8, 25)
        reasons.extend(pattern_w)

    return min(score, 100), reasons

def risk_label(score: int) -> str:
    if score <= 25:
        return "🟢 Xavfsiz"
    elif score <= 50:
        return "🟡 Shubhali"
    elif score <= 75:
        return "🟠 Xavfli"
    else:
        return "🔴 JUDA XAVFLI"

def format_age(days) -> str:
    if days is None:
        return "Noma'lum"
    if days >= 365:
        return f"{days // 365} yil {(days % 365) // 30} oy"
    return f"{days} kun"


# ── Asosiy tahlil ──────────────────────────────────────────────────────────

async def analyze_url(url: str, userbot=None, bot_client=None, context_w=None) -> tuple:
    """
    URL ni to'liq tahlil qiladi.
    Qaytaradi: (report_text, score, probe_urls)
    """
    loop = asyncio.get_event_loop()
    try:
        chain = await loop.run_in_executor(executor, get_redirect_chain, url)
        final_url = chain[-1] if chain else url
        redirected = len(chain) > 1

        parsed = urllib.parse.urlparse(final_url)
        domain = (parsed.netloc or parsed.path).split(":")[0]
        if "@" in domain:
            domain = domain.split("@")[-1]
        if not domain:
            return None, 0, []

        pattern_w   = check_url_patterns(final_url, domain)
        brand_w     = check_brand_impersonation(domain)
        homograph_w = check_homograph(domain)
        tg_url_w    = check_telegram_url(final_url)

        is_tg = domain in TELEGRAM_DOMAINS
        tg_channel = {}
        if is_tg and bot_client:
            tg_channel = await check_telegram_channel_info(bot_client, final_url)

        tg_channel_w = []
        if tg_channel.get("found"):
            if tg_channel.get("brand_in_title") and not tg_channel.get("verified"):
                for brand in tg_channel["brand_in_title"]:
                    tag = "🇺🇿" if brand in UZBEK_BRANDS else "🌐"
                    tg_channel_w.append(f"🔴 {tag} Kanal `{brand}` brendini taqlid qiladi lekin TASDIQLANMAGAN!")
            if tg_channel.get("title_has_homograph"):
                tg_channel_w.append(f"🔴 Kanal nomida unicode harflar: `{tg_channel.get('title', '')}`")
        elif tg_channel.get("deleted"):
            uname = tg_channel.get("username", "")
            tg_channel_w.append(f"🔴 @{uname} — O'CHIRILGAN! Spam yuborib ketishgan — klassik fishing belgisi")
        elif tg_channel.get("is_private_invite"):
            tg_channel_w.append("⚠️ Yopiq Telegram kanal taklifi — kim ekanligini ko'rib bo'lmaydi")

        probe = {"available": False}
        probe_urls = []
        if is_tg and userbot and not tg_channel.get("is_private_invite") and not tg_channel.get("deleted"):
            tg_path = urllib.parse.urlparse(final_url).path.strip("/").split("?")[0]
            if tg_path and not tg_path.startswith("+"):
                probe = await probe_telegram_bot(userbot, tg_path)
                probe_urls = probe.get("urls", [])

        try:
            ip = await loop.run_in_executor(executor, socket.gethostbyname, domain)
        except Exception:
            ip = "Noma'lum"

        results = await asyncio.gather(
            loop.run_in_executor(executor, _get_geo, ip),
            loop.run_in_executor(executor, check_ssl, domain),
            loop.run_in_executor(executor, check_whois, domain),
            loop.run_in_executor(executor, check_virustotal, final_url),
            loop.run_in_executor(executor, check_urlhaus, final_url),
            loop.run_in_executor(executor, check_abuseipdb, ip),
            check_with_browser(final_url),
            return_exceptions=True,
        )

        def _safe(r, default):
            return r if not isinstance(r, Exception) else default

        geo        = _safe(results[0], {})
        ssl_info   = _safe(results[1], {"valid": False, "days_left": 0, "issuer": "Noma'lum"})
        whois_info = _safe(results[2], {"age_days": None, "registrar": "Noma'lum"})
        vt         = _safe(results[3], {"available": False})
        urlhaus    = _safe(results[4], {"available": False})
        abuse      = _safe(results[5], {"available": False})
        browser    = _safe(results[6], {"available": False})

        country = geo.get("country", "Noma'lum")
        isp     = geo.get("isp", "Noma'lum")

        browser_w = []
        if browser.get("available"):
            if browser.get("has_card_input"):
                browser_w.append("🔴 Sahifada karta raqami kiritish shakli topildi!")
            if browser.get("has_password"):
                browser_w.append("🔴 Sahifada parol kiritish shakli topildi!")
            if browser.get("redirected"):
                browser_w.append(f"🔀 Brauzer haqiqiy manzilga o'tkazdi: `{browser.get('final_url', '')[:80]}`")

        all_tg_w = tg_url_w + tg_channel_w
        score, reasons = calculate_risk(
            domain, country, ssl_info, whois_info, redirected,
            vt, urlhaus, abuse, pattern_w, brand_w, homograph_w,
            tg_url_w=all_tg_w,
            context_w=(context_w or []) + browser_w,
        )
        label = risk_label(score)

        ssl_str = (f"✅ Ha ({ssl_info['days_left']} kun · {ssl_info['issuer']})"
                   if ssl_info["valid"] else "❌ Yo'q")

        if redirected and len(chain) > 1:
            chain_lines = "\n🔗 *Yo'naltirish zanjiri:*\n"
            for i, hop in enumerate(chain[:6]):
                prefix = "└→" if i == len(chain) - 1 else "├→"
                chain_lines += f"  {prefix} `{hop[:80]}`\n"
        else:
            chain_lines = "🔗 *Yo'naltirish:* Yo'q"

        if tg_channel.get("found"):
            verified_str = "✅ Tasdiqlangan" if tg_channel.get("verified") else "❌ Tasdiqlanmagan"
            members = tg_channel.get("member_count")
            members_str = f"{members:,}" if members else "Noma'lum"
            tg_block = (f"\n📱 *Telegram kanal:*\n"
                        f"📛 *Nomi:* {tg_channel.get('title', '—')}\n"
                        f"🔖 *Username:* @{tg_channel.get('username', '—')}\n"
                        f"✅ *Tasdiqlangan:* {verified_str}\n"
                        f"👥 *A'zolar:* {members_str}\n")
        elif tg_channel.get("deleted"):
            tg_block = (f"\n📱 *Telegram kanal:*\n"
                        f"🔖 *Username:* @{tg_channel.get('username', '')}\n"
                        f"🗑 *Holat:* O'CHIRILGAN — spam yuborib o'chirib ketishgan\n")
        elif tg_channel.get("is_private_invite"):
            tg_block = "\n📱 *Telegram:* Yopiq kanal taklifi\n"
        elif is_tg:
            tg_block = f"\n📱 *Telegram:* `{urllib.parse.urlparse(final_url).path.strip('/')}` — ma'lumot olishning imkoni yo'q\n"
        else:
            tg_block = ""

        probe_block = ""
        if probe.get("available"):
            msg_count = probe.get("msg_count", 0)
            sample = probe.get("sample_text", "")
            clicked = probe.get("clicked_buttons", [])
            clicked_str = ", ".join(f"'{b}'" for b in clicked[:4]) if clicked else "Yo'q"
            if probe_urls:
                urls_list = "\n".join(f"  🔗 `{u[:80]}`" for u in probe_urls[:5])
                probe_block = (f"\n🤖 *Userbot tekshiruvi ({msg_count} ta javob):*\n"
                               f"🖱 *Bosgan tugmalar:* {clicked_str}\n"
                               f"📨 *Bot matni:* {sample[:100]}\n"
                               f"🔗 *Topilgan havolalar:*\n{urls_list}\n")
            else:
                probe_block = (f"\n🤖 *Userbot tekshiruvi:* {msg_count} ta javob\n"
                               f"🖱 *Bosgan tugmalar:* {clicked_str}\n"
                               f"📨 *Bot matni:* {sample[:100] if sample else '—'}\n"
                               f"🔗 *Havolalar:* Topilmadi\n")

        if vt.get("available"):
            vt_str = ("⏳ Yangi havola — tahlil topshirildi" if vt.get("pending")
                      else f"{'🔴' if vt['malicious'] > 0 else '🟢'} {vt['malicious']}/{vt['total']} engine")
        else:
            vt_str = "⚪ API kalit yo'q (.env da VIRUSTOTAL_API_KEY)"

        uh_str = ("🔴 Bazada topildi!" if urlhaus.get("found")
                  else "🟢 URLhaus bazasida yo'q" if urlhaus.get("available")
                  else "⚪ Tekshirib bo'lmadi")

        if abuse.get("available"):
            s = abuse.get("abuse_score", 0)
            icon = "🔴" if s > 50 else "🟡" if s > 25 else "🟢"
            abuse_str = f"{icon} {s}/100 ({abuse.get('total_reports', 0)} shikoyat)"
        else:
            abuse_str = "⚪ API kalit yo'q (.env da ABUSEIPDB_API_KEY)"

        if browser.get("available"):
            b_title = browser.get("title", "—")
            b_card  = "🔴 BOR" if browser.get("has_card_input") else "🟢 Yo'q"
            b_pass  = "🔴 BOR" if browser.get("has_password") else "🟢 Yo'q"
            browser_block = (f"\n🌐 *Brauzer tekshiruvi:*\n"
                             f"📄 *Sahifa nomi:* {b_title}\n"
                             f"💳 *Karta shakli:* {b_card}\n"
                             f"🔑 *Parol shakli:* {b_pass}\n")
        else:
            browser_block = ""

        report = (
            f"🔍 *Havola tahlili:*\n"
            f"🌐 *Domen:* `{domain}`\n"
            f"📌 *IP:* `{ip}` · {country}\n"
            f"🏢 *Hosting:* {isp}\n"
            f"🛡 *SSL:* {ssl_str}\n"
            f"📅 *Domen yoshi:* {format_age(whois_info.get('age_days'))}\n"
            f"{chain_lines}"
            f"{tg_block}"
            f"{probe_block}"
            f"{browser_block}\n"
            f"*🔬 Threat Intelligence:*\n"
            f"🦠 *VirusTotal:* {vt_str}\n"
            f"☣️ *URLhaus:* {uh_str}\n"
            f"🚨 *AbuseIPDB:* {abuse_str}\n\n"
            f"📊 *Xavf darajasi: {score}/100 — {label}*"
        )

        if reasons:
            reasons_block = "\n\n*⚠️ Topilgan muammolar:*\n" + "\n".join(reasons[:8])
            if len(report) + len(reasons_block) < 4000:
                report += reasons_block

        return report, score, probe_urls

    except Exception:
        return f"🌐 *Havola:* `{url}`\n❌ Tahlil qilib bo'lmadi.", 0, []


def extract_urls_from_telethon_msg(message) -> set:
    """Telethon xabaridan barcha havolalarni topib oladi."""
    urls = set()
    text = message.text or message.message or ""
    entities = message.entities or []
    for ent in entities:
        etype = type(ent).__name__
        if etype == "MessageEntityUrl":
            url = text[ent.offset: ent.offset + ent.length]
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            urls.add(url)
        elif etype == "MessageEntityTextUrl":
            if ent.url:
                urls.add(ent.url)
    # Inline tugmalar
    markup = getattr(message, 'reply_markup', None)
    if markup and hasattr(markup, 'rows'):
        for row in markup.rows:
            for btn in row.buttons:
                if hasattr(btn, 'url') and btn.url:
                    urls.add(btn.url)
    # Oddiy matndan URL ni grep qilish
    import re
    for m in re.finditer(r'https?://[^\s\]>)"\']+', text):
        urls.add(m.group())
    return urls
