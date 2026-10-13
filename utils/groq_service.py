# Groq AI Multi-Key Course Ingestion and Copywriting Engine
import os
import re
import json
import logging
import html
from typing import Dict, Any, List, Optional
import aiohttp
from bs4 import BeautifulSoup
from database.db import db
from config import get_live_usd_rate

logger = logging.getLogger(__name__)

class GroqKeyPool:
    """
    Manages multiple Groq API keys with round-robin load balancing,
    failover, and automatic rotation on rate-limits (HTTP 429) or exhaustion.
    """
    def __init__(self):
        self._current_idx = 0
        self._failed_keys: set = set()

    def get_all_keys(self) -> List[str]:
        keys = []
        # 1. From database dynamic settings
        db_keys = db.get_setting("groq_api_keys", "").strip()
        if db_keys:
            for k in re.split(r"[,\n]+", db_keys):
                k = k.strip()
                if k and k not in keys:
                    keys.append(k)

        # 2. From environment variables (.env)
        env_multi = os.getenv("GROQ_API_KEYS", "").strip()
        if env_multi:
            for k in re.split(r"[,\n]+", env_multi):
                k = k.strip()
                if k and k not in keys:
                    keys.append(k)

        env_single = os.getenv("GROQ_API_KEY", "").strip()
        if env_single and env_single not in keys:
            keys.append(env_single)

        return keys

    def add_key_to_db(self, new_key: str) -> bool:
        new_key = new_key.strip()
        if not new_key:
            return False
        existing = self.get_all_keys()
        if new_key not in existing:
            existing.append(new_key)
            db.set_setting("groq_api_keys", ",".join(existing))
            return True
        return False

    def remove_key_from_db(self, key_to_remove: str) -> bool:
        existing = self.get_all_keys()
        updated = [k for k in existing if k != key_to_remove]
        db.set_setting("groq_api_keys", ",".join(updated))
        return True

    def get_active_key(self) -> Optional[str]:
        keys = self.get_all_keys()
        if not keys:
            return None
        # Clean failed keys if all were marked failed
        if len(self._failed_keys) >= len(keys):
            self._failed_keys.clear()

        # Find first non-failed key starting from current index
        for i in range(len(keys)):
            idx = (self._current_idx + i) % len(keys)
            candidate = keys[idx]
            if candidate not in self._failed_keys:
                self._current_idx = idx
                return candidate

        return keys[0]

    def mark_key_failed(self, key: str, reason: str = "Rate limit or error"):
        logger.warning(f"Groq API Key marked failed/rate-limited: ...{key[-6:] if len(key)>6 else key} (Reason: {reason})")
        self._failed_keys.add(key)
        keys = self.get_all_keys()
        if keys:
            self._current_idx = (self._current_idx + 1) % len(keys)

groq_pool = GroqKeyPool()


async def scrape_course_page(url: str) -> Dict[str, Any]:
    """
    Fetches real course metadata from any course sales page:
    Extracts real title, banner image URL, description, and curriculum points.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,bn;q=0.8"
    }
    
    data = {
        "url": url,
        "title": "",
        "image_url": None,
        "raw_description": "",
        "curriculum_points": [],
        "scraped_success": False
    }

    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    html_text = await response.text()
                    soup = BeautifulSoup(html_text, "html.parser")

                    # 1. Real Title Extraction
                    title_candidate = ""
                    # og:title
                    og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
                    if og_title and og_title.get("content"):
                        title_candidate = og_title["content"].strip()
                    
                    # twitter:title
                    if not title_candidate:
                        tw_title = soup.find("meta", attrs={"name": "twitter:title"})
                        if tw_title and tw_title.get("content"):
                            title_candidate = tw_title["content"].strip()

                    # <title> tag
                    if not title_candidate and soup.title and soup.title.string:
                        title_candidate = soup.title.string.strip()

                    # <h1> fallback
                    if not title_candidate:
                        h1 = soup.find("h1")
                        if h1:
                            title_candidate = h1.get_text(strip=True)

                    # Clean common brand suffixes from real title
                    cleaned_title = clean_course_title(title_candidate)
                    generic_phrases = ["largest online classroom", "online classroom", "home", "course access", "homepage", "online courses", "aslaf academy", "10 minute school", "interactive cares"]
                    if not cleaned_title or any(gp in cleaned_title.lower() for gp in generic_phrases):
                        slug = url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()
                        if slug and len(slug) > 3:
                            cleaned_title = slug
                    data["title"] = cleaned_title if cleaned_title else "Premium Course"

                    # 2. Image Extraction
                    og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
                    if og_img and og_img.get("content"):
                        data["image_url"] = og_img["content"].strip()
                    else:
                        tw_img = soup.find("meta", attrs={"name": "twitter:image"})
                        if tw_img and tw_img.get("content"):
                            data["image_url"] = tw_img["content"].strip()
                        else:
                            # link rel=image_src
                            link_img = soup.find("link", rel="image_src")
                            if link_img and link_img.get("href"):
                                data["image_url"] = link_img["href"].strip()

                    # 3. Description Extraction
                    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
                    if og_desc and og_desc.get("content"):
                        data["raw_description"] = og_desc["content"].strip()

                    # 4. Curriculum / Headings Extraction
                    points = []
                    for h in soup.find_all(["h2", "h3"], limit=8):
                        txt = h.get_text(strip=True)
                        if txt and len(txt) > 3 and len(txt) < 120 and txt not in points:
                            points.append(txt)
                    data["curriculum_points"] = points[:6]
                    data["scraped_success"] = True

    except Exception as e:
        logger.error(f"Error scraping course URL {url}: {e}")
        # Even if network fails, extract title from URL slug
        slug = url.rstrip("/").split("/")[-1].replace("-", " ").replace("_", " ").title()
        data["title"] = slug if slug else "Course Access"

    return data


def clean_course_title(raw_title: str) -> str:
    """Strips website suffixes like '| 10 Minute School', '- Bohubrihi', etc."""
    if not raw_title:
        return ""
    # Remove pipe or dash website branding
    cleaned = re.sub(r"\s*\|\s*(10\s*Minute\s*School|Bohubrihi|Ostad|Udemy|Coursera|Interactive\s*Cares|Shikho).*$", "", raw_title, flags=re.I)
    cleaned = re.sub(r"\s*-\s*(10\s*Minute\s*School|Bohubrihi|Ostad|Udemy|Coursera|Interactive\s*Cares|Shikho).*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*\|\s*Online Course.*$", "", cleaned, flags=re.I)
    return cleaned.strip()


async def generate_course_with_groq(scraped_data: Dict[str, Any], raw_url: str) -> Dict[str, Any]:
    """
    Calls Groq AI with multi-key failover to format the course presentation,
    craft compelling Bengali copywriting, extract curriculum highlights,
    and suggest default dual pricing.
    """
    keys = groq_pool.get_all_keys()
    real_title = scraped_data.get("title", "Premium Course")
    raw_desc = scraped_data.get("raw_description", "")
    points = scraped_data.get("curriculum_points", [])
    img_url = scraped_data.get("image_url")

    # If no Groq keys exist at all, construct high quality template directly
    if not keys:
        return build_fallback_course_data(real_title, raw_desc, points, raw_url, img_url)

    system_prompt = (
        "You are an expert Bangladeshi e-commerce copywriter for digital courses. "
        "Your task is to take real course metadata and produce high-converting Telegram post copy in Bengali. "
        "Strict rules:\n"
        "1. Real Course Name: You MUST keep the real course title as given. Do not make up a fake title.\n"
        "2. Structure of description (Bengali):\n"
        "   - 📌 কোর্স ওভারভিউ: Brief 1-2 sentence compelling summary\n"
        "   - 🎯 কী কী শেখানো হবে / কারিকুলাম হাইলাইটস: 4-5 bullet points\n"
        "   - 💡 বিশেষ সুবিধাসমূহ: High-definition videos, complete resource files, projects\n"
        "   - 🎁 স্পেশাল বোনাস: Exclusive bonus resources & templates\n"
        "   - ⚡ ইনস্ট্যান্ট ডেলিভারি গ্যারান্টি\n"
        "3. Use standard Telegram HTML tags (<b>, <i>, <code>). Do NOT use markdown asterisks (**) or markdown formatting.\n"
        "4. Suggest default Channel Price (BDT, integer e.g. 150) and Account Price (BDT, integer e.g. 350).\n"
        "5. Output MUST be ONLY valid JSON matching this schema:\n"
        "{\n"
        '  "title": "Exact Real Course Title",\n'
        '  "description": "Formatted Bengali marketing description in HTML",\n'
        '  "channel_price_bdt": 150,\n'
        '  "account_price_bdt": 350,\n'
        '  "category_name": "Suggested Category Name"\n'
        "}"
    )

    user_prompt = (
        f"Real Course Title: {real_title}\n"
        f"Sales Page URL: {raw_url}\n"
        f"Original Description: {raw_desc}\n"
        f"Extracted Highlights: {', '.join(points) if points else 'Comprehensive curriculum'}\n"
        "Generate the structured course JSON now."
    )

    CANDIDATE_MODELS = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant"
    ]

    # Try each available key in the pool until success
    max_attempts = len(keys)
    for attempt in range(max_attempts):
        active_key = groq_pool.get_active_key()
        if not active_key:
            break

        key_success = False
        # Try candidate models for this key
        for model_name in CANDIDATE_MODELS:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.5,
                        "max_tokens": 1200,
                        "response_format": {"type": "json_object"}
                    }
                    headers = {
                        "Authorization": f"Bearer {active_key}",
                        "Content-Type": "application/json"
                    }
                    async with session.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            res_json = await resp.json()
                            content = res_json["choices"][0]["message"]["content"]
                            parsed = json.loads(content)

                            # Enforce real title
                            final_title = parsed.get("title") or real_title
                            final_desc = parsed.get("description") or raw_desc
                            ch_p = int(parsed.get("channel_price_bdt") or 150)
                            acc_p = int(parsed.get("account_price_bdt") or 350)
                            cat = parsed.get("category_name", "কোর্স (Courses)")

                            return {
                                "title": final_title,
                                "description": clean_telegram_html(final_desc),
                                "price_channel_bdt": ch_p,
                                "price_account_bdt": acc_p,
                                "sales_page_url": raw_url,
                                "photo_file_id": img_url,
                                "category_hint": cat,
                                "category_name": cat,
                                "success": True,
                                "key_used": f"...{active_key[-6:]} ({model_name})"
                            }
                        elif resp.status == 404:
                            # Model not found on this Groq instance, try next candidate model
                            logger.info(f"Model {model_name} not available on Groq (404), trying next model...")
                            continue
                        elif resp.status in (429, 401, 403):
                            # Key exhausted or invalid, mark failed and try next key
                            groq_pool.mark_key_failed(active_key, f"HTTP {resp.status}")
                            break
                        else:
                            err_text = await resp.text()
                            logger.error(f"Groq API Error {resp.status} with model {model_name}: {err_text}")
                            continue
            except Exception as e:
                logger.error(f"Groq invocation failed on model {model_name} with key ...{active_key[-6:]}: {e}")
                continue

    # All keys exhausted or errored — fallback cleanly to template
    logger.info("Falling back to structured OpenGraph course template generation.")
    return build_fallback_course_data(real_title, raw_desc, points, raw_url, img_url)


def build_fallback_course_data(title: str, desc: str, points: List[str], url: str, img: Optional[str]) -> Dict[str, Any]:
    """Fallback generator when Groq is unavailable or all keys exhausted."""
    bullet_text = ""
    if points:
        bullet_text = "\n".join([f"• 🎯 {html.escape(p)}" for p in points])
    else:
        bullet_text = "• 🎯 সম্পূর্ণ কারিকুলাম ও বিগিনার টু অ্যাডভান্সড গাইডলাইন\n• 🎯 রিয়েল-লাইফ প্রজেক্ট এবং কেস স্টাডি\n• 🎯 লাইফটাইম রিসোর্স এবং সোর্স কোড"

    clean_summary = html.escape(desc) if desc else "এই কোর্সে সম্পূর্ণ বেসিক থেকে অ্যাডভান্সড পর্যন্ত প্র্যাকটিক্যাল গাইডলাইন দেওয়া হয়েছে।"

    formatted_desc = (
        f"📌 <b>কোর্স পরিচিতি:</b>\n"
        f"{clean_summary}\n\n"
        f"🎯 <b>কারিকুলাম হাইলাইটস:</b>\n"
        f"{bullet_text}\n\n"
        f"💡 <b>বিশেষ সুবিধাসমূহ:</b>\n"
        f"• 🎬 ফুল এইচডি (HD) কোয়ালিটির সব লেকচার\n"
        f"• 📁 সম্পূর্ণ প্রজেক্ট সোর্স কোড ও প্র্যাকটিস ফাইলস\n"
        f"• ⚡ ইনস্ট্যান্ট অ্যাক্সেস ও আনলিমিটেড ভিউ সুবিধা\n\n"
        f"🎁 <b>বোনাস মেটেরিয়াল:</b>\n"
        f"• এক্সক্লুসিভ গাইডবুক ও প্রিমিয়াম রিসোর্স প্যাক"
    )

    return {
        "title": title,
        "description": formatted_desc,
        "price_channel_bdt": 150,
        "price_account_bdt": 350,
        "sales_page_url": url,
        "photo_file_id": img,
        "category_hint": "কোর্স (Courses)",
        "category_name": "কোর্স (Courses)",
        "success": True,
        "key_used": "Fallback (Metadata)"
    }


def clean_telegram_html(text: str) -> str:
    """Ensures text complies with Telegram HTML formatting and strips markdown stars."""
    # Replace markdown bold **text** with <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Replace markdown italics *text* or _text_
    text = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<i>\1</i>", text)
    return text.strip()
