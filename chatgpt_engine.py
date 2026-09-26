import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Playwright, BrowserContext, Page

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ChatGPTEngine")


def cleanup_profile_locks(profile_dir: Path):
    """تنظيف ملفات القفل القديمة المتبقية من جلسات متصفح سابقة."""
    lock_files = ["SingletonLock", "SingletonCookie", "SingletonSocket", "lockfile"]
    for lock_file in lock_files:
        p = profile_dir / lock_file
        if p.exists():
            try:
                p.unlink()
                logger.info(f"تم حذف ملف القفل القديم: {lock_file}")
            except Exception as e:
                logger.warning(f"تعذر حذف ملف القفل {lock_file}: {e}")


class ChatGPTResponseCapturer:
    """مستقبل الردود الذكي لـ ChatGPT عبر اعتراض شبكة الـ API."""

    def __init__(self):
        self.captured_text = ""

    async def handle_response(self, response):
        url = response.url
        if "backend-api/" in url:
            try:
                text = await response.text()
                if "parts" in text or "message" in text:
                    lines = text.split("\n")
                    for line in reversed(lines):
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                data = json.loads(line[6:])
                                parts = (
                                    data.get("message", {})
                                    .get("content", {})
                                    .get("parts", [])
                                )
                                if parts and isinstance(parts[0], str) and parts[0].strip():
                                    self.captured_text = parts[0]
                                    break
                            except Exception:
                                continue
            except Exception:
                pass


class ChatGPTEngine:
    """
    محرك أتمتة ChatGPT المرن والمدعوم باستراتيجيات استخراج متعددة
    وآليات تعافي تلقائي عند الانهيار.
    """

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.capturer: ChatGPTResponseCapturer = ChatGPTResponseCapturer()
        self.lock = asyncio.Lock()
        self._is_initialized = False

    async def _launch_context(self, headless: bool):
        return await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(config.PROFILE_DIR),
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized",
            ],
            viewport=None,
        )

    async def initialize(self, headless: bool = False):
        """تهيئة متصفح Playwright بسياق دائم مع آلية تنظيف الأقفال السابقة."""
        logger.info("جارٍ إطلاق سياق متصفح Playwright الدائم...")
        config.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.playwright = await async_playwright().start()

        try:
            self.context = await self._launch_context(headless)
        except Exception as e:
            if "ProcessSingleton" in str(e) or "lock" in str(e).lower():
                logger.warning("تنبيه: مجلد البروفايل مقفول بواسطة عملية سابقة. جارٍ محاولة إزالة القفل والإعادة...")
                cleanup_profile_locks(config.PROFILE_DIR)
                await asyncio.sleep(1)
                self.context = await self._launch_context(headless)
            else:
                raise e

        # منح صلاحيات الحافظة مسبقاً
        await self.context.grant_permissions(["clipboard-read", "clipboard-write"])

        pages = self.context.pages
        self.page = pages[0] if pages else await self.context.new_page()

        # إعداد مستمع استجابات الشبكة
        self.page.on("response", lambda resp: asyncio.create_task(self.capturer.handle_response(resp)))

        logger.info(f"التوجه إلى رابط ChatGPT: {config.CHATGPT_URL}")
        await self.page.goto(config.CHATGPT_URL, wait_until="domcontentloaded", timeout=config.TIMEOUT_MS)
        await asyncio.sleep(2)
        self._is_initialized = True
        logger.info("تمت تهيئة محرك ChatGPT بنجاح.")

    async def ensure_healthy_page(self):
        """التحقق من صحة المتصفح وإعادة التشغيل التلقائي عند الانهيار."""
        try:
            if not self._is_initialized or not self.page or self.page.is_closed():
                logger.warning("تنبيه: المتصفح مغلق أو غير مهيأ. جارٍ إعادة التشغيل التلقائي...")
                await self.close()
                await self.initialize()
            else:
                await self.page.evaluate("1 + 1")
        except Exception as e:
            logger.error(f"خطأ في فحص صحة المتصفح: {e}. جارٍ إعادة التهيئة...")
            await self.close()
            await self.initialize()

    async def get_prompt_box(self):
        """البحث عن مربع كتابة الرسالة في ChatGPT."""
        if not self.page:
            return None

        for selector in config.PROMPT_SELECTORS:
            try:
                locator = self.page.locator(selector).first
                if await locator.is_visible(timeout=2000):
                    return locator
            except Exception:
                continue
        return None

    async def send_prompt(self, prompt: str):
        """إرسال البرومبت بمحاكاة أدوات الدخل ونظافة المربع."""
        prompt_box = await self.get_prompt_box()

        if prompt_box is None:
            raise RuntimeError(
                "لم يتم العثور على مربع كتابة الرسالة في ChatGPT. قد يكون هناك تحقق (CAPTCHA) أو يتطلب تسجيل الدخول."
            )

        await prompt_box.click()
        await asyncio.sleep(0.2)

        # مسح أي نص قديم في مربع الإدخال
        await self.page.keyboard.press("Control+A")
        await self.page.keyboard.press("Backspace")
        await asyncio.sleep(0.2)

        await self.page.keyboard.insert_text(prompt)
        await asyncio.sleep(0.5)

        send_button = None
        for sel in config.SEND_BUTTON_SELECTORS:
            btn = self.page.locator(sel).first
            try:
                if await btn.is_visible(timeout=1000) and await btn.is_enabled():
                    send_button = btn
                    break
            except Exception:
                continue

        if send_button:
            try:
                await send_button.click()
                return
            except Exception:
                pass

        await self.page.keyboard.press("Enter")

    async def wait_for_generation_to_finish(self):
        """الانتظار حتى يكتمل التوليد عبر متابعة زر التوقف."""
        start_time = time.time()
        
        while time.time() - start_time < 12:
            for sel in config.STOP_SELECTORS:
                try:
                    if await self.page.locator(sel).is_visible():
                        break
                except Exception:
                    pass
            await asyncio.sleep(0.5)

        deadline = time.time() + config.RESPONSE_TIMEOUT_SECONDS
        while time.time() < deadline:
            generating = False
            for sel in config.STOP_SELECTORS:
                try:
                    if await self.page.locator(sel).is_visible():
                        generating = True
                        break
                except Exception:
                    pass

            if not generating:
                await asyncio.sleep(1.5)
                break
            await asyncio.sleep(0.8)

        if time.time() >= deadline:
            logger.warning("تجاوز التوليد المهلة المحددة (120 ثانية). محاولة النقر على زر الإيقاف...")
            for sel in config.STOP_SELECTORS:
                try:
                    btn = self.page.locator(sel).first
                    if await btn.is_visible():
                        await btn.click()
                        break
                except Exception:
                    pass

    async def extract_response(self) -> str:
        """
        الاستراتيجية المبتكرة لاستخراج النص المحسنة لتركيز الصفحة والـ DOM المعاصر:
        1. إحضار النافذة إلى المقدمة (bring to front)
        2. زر النسخ المباشر والحافظة
        3. اعتراض حزم البيانات من الشبكة
        4. مسح DOM المتقدم للرابط والمساعد
        """
        try:
            await self.page.bring_to_front()
        except Exception:
            pass

        # ─── 🥇 1. تقنية زر النسخ المباشر والحافظة ───
        try:
            copy_buttons = self.page.locator(', '.join(config.COPY_BUTTON_SELECTORS))
            count = await copy_buttons.count()
            if count > 0:
                last_copy_btn = copy_buttons.nth(count - 1)
                if await last_copy_btn.is_visible():
                    await last_copy_btn.click()
                    await asyncio.sleep(0.5)
                    clipboard_text = await self.page.evaluate("navigator.clipboard.readText()")
                    if clipboard_text and clipboard_text.strip():
                        logger.info("📌 تم جلب الرد بنجاح عبر (تقنية زر النسخ المباشر والحافظة).")
                        return clipboard_text.strip()
        except Exception as e:
            logger.debug(f"(تنبيه محاولة النسخ): {e}")

        # ─── 🥈 2. اعتراض شبكة الـ API ───
        if self.capturer.captured_text and self.capturer.captured_text.strip():
            logger.info("📌 تم جلب الرد بنجاح عبر (اعتراض حزم بيانات الـ API).")
            return self.capturer.captured_text.strip()

        # ─── 🥉 3. المسح الذكي لـ DOM عبر JS الشامل ───
        try:
            js_extracted = await self.page.evaluate("""
                () => {
                    // البحث في عناصر ردود المساعد المخصصة
                    const assistantNodes = document.querySelectorAll('[data-message-author-role="assistant"], [data-testid*="assistant"], article');
                    if (assistantNodes.length > 0) {
                        const lastNode = assistantNodes[assistantNodes.length - 1];
                        
                        const markdown = lastNode.querySelector('.markdown, .prose, [class*="markdown"], [class*="prose"]');
                        if (markdown && markdown.innerText.trim()) {
                            return markdown.innerText.trim();
                        }
                        
                        const parts = [];
                        lastNode.querySelectorAll('p, pre, ul, ol, blockquote').forEach(el => {
                            const txt = el.innerText.trim();
                            if (txt) parts.push(txt);
                        });
                        if (parts.length > 0) {
                            return parts.join('\\n\\n');
                        }
                        
                        if (lastNode.innerText.trim()) {
                            return lastNode.innerText.trim();
                        }
                    }
                    
                    const markdowns = document.querySelectorAll('.markdown, .prose');
                    if (markdowns.length > 0) {
                        return markdowns[markdowns.length - 1].innerText.trim();
                    }
                    
                    return "";
                }
            """)
            if js_extracted and js_extracted.strip():
                logger.info("📌 تم جلب الرد بنجاح عبر (المسح الذكي لـ DOM).")
                return js_extracted.strip()
        except Exception as e:
            logger.debug(f"(تنبيه مسح JS): {e}")

        # ─── 🏅 4. خطة الطوارئ الرابعة: جلب النص الخام ───
        try:
            fallback_text = await self.page.evaluate("""
                () => {
                    const articles = document.querySelectorAll('article');
                    return articles.length > 0 ? articles[articles.length - 1].innerText : "";
                }
            """)
            if fallback_text and fallback_text.strip():
                logger.info("📌 تم جلب الرد بنجاح عبر (خطة الطوارئ - النص الخام).")
                return fallback_text.strip()
        except Exception as e:
            logger.error(f"فشل استخراج النص التكافئي: {e}")

        return ""

    async def generate_chat_response(self, prompt: str) -> str:
        """إرسال الطلب واستخراج الرد مع استخدام asyncio.Lock لضمان التزامن."""
        async with self.lock:
            await self.ensure_healthy_page()

            self.capturer.captured_text = ""

            for attempt in range(1, config.MAX_EXTRACTION_ATTEMPTS + 1):
                try:
                    await self.send_prompt(prompt)
                    await self.wait_for_generation_to_finish()
                    
                    response_text = await self.extract_response()
                    if response_text:
                        return response_text
                    
                    logger.warning(f"محاولة استخراج فارغة ({attempt}/{config.MAX_EXTRACTION_ATTEMPTS})، إعادة محاولة الاستخراج...")
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"خطأ خلال تنفيذ البرومبت (المحاولة {attempt}): {e}")
                    if attempt == config.MAX_EXTRACTION_ATTEMPTS:
                        raise e
                    await asyncio.sleep(1)

            raise RuntimeError("فشل استخراج أي نص من ChatGPT بعد عدة محاولات.")

    async def close(self):
        """إغلاق المتصفح وسياق Playwright بنظافة."""
        try:
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"خطأ أثناء إغلاق المحرك: {e}")
        finally:
            self.context = None
            self.playwright = None
            self.page = None
            self._is_initialized = False
