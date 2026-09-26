# Personal OpenAI-Compatible ChatGPT Local API Server 🚀

سيرفر محلي متكامل ومرن يحوّل أتمتة Playwright لموقع ChatGPT إلى API متوافق 100% مع واجهة برمجة تطبيقات **OpenAI** المعيارية (`POST /v1/chat/completions`).

---

## 🌟 الميزات الرئيسية

- **توافق معيار OpenAI**: يعمل مباشرة مع جميع الملحقات (Plugins)، منشئي المواقع (Site Builders)، وتطبيقات الذكاء الاصطناعي (مثل TypingMind, LangChain, NextChat).
- **استراتيجية جلب النص المبتكرة**:
  1. زر النسخ المباشر والحافظة (Clipboard)
  2. اعتراض حزم بيانات شبكة الـ API (`backend-api/conversation`)
  3. مسح العناصر الذكي عبر JavaScript DOM
  4. خطة طوارئ لاستخراج النص الخام لآخر `<article>`
- **مرونة واستعادة تلقائية (Auto-Recovery)**: في حال إغلاق أو انهيار متصفح Playwright، يعيد السيرفر فتح المتصفح تلقائياً دون سقوط السيرفر.
- **إدارة الطلبات المتزامنة**: استخدام `asyncio.Lock()` لمنع تضارب الطلبات في حال وصول طلبات متزامنة من عدة مصادر.
- **حفظ الجلسة والدخول الدائم**: يحفظ ملف الكوكيز والجلسة في مجلد `chatgpt_profile` على سطح المكتب لتجنب الحاجة لتسجيل الدخول في كل مرة.

---

## 🛠️ متطلبات التشغيل والتثبيت

1. **تثبيت الحزم المطلوبة**:
   ```bash
   pip install -r requirements.txt
   ```

2. **تثبيت متصفحات Playwright**:
   ```bash
   playwright install chromium
   ```

---

## 🚀 تشغيل السيرفر

يمكنك تشغيل السيرفر عبر الأمر:

```bash
python main.py
```
أو عبر uvicorn مباشرة:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

سيفتح متصفح Chromium تلقائياً ويتوجه إلى `https://chatgpt.com/`. 
*(في المرة الأولى، يرجى تسجيل الدخول إلى حساب ChatGPT الخاص بك يدوياً في نافذة المتصفح المفتوحة).*

---

## 📡 ربط منشئي المواقع (Site Builders) عبر Ngrok

لربط منشئ المواقع أو أي موقع خارجي بالسيرفر المحلي:

1. **قم بتشغيل tunnel عبر Ngrok**:
   ```bash
   ngrok http 8000
   ```

2. **استخدم الرابط الموفر في تطبيقك**:
   - **Base URL**: `https://xxxx-xx-xx.ngrok-free.app/v1`
   - **API Key**: `sk-chatgpt-local-secret-key` *(أو المفتاح المخصص في `config.py`)*
   - **Model**: `gpt-4o` (أو `gpt-3.5-turbo`)

---

## 🧪 اختبار السيرفر محلياً

يمكنك تشغيل سكريبت الاختبار في نافذة جديدة:

```bash
python test_client.py
```

أو استخدام `curl`:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-chatgpt-local-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "مرحبا، من أنت؟"}]
  }'
```

---

## ⚙️ الإعدادات (`config.py`)

يمكنك تخصيص الإعدادات التالية داخل `config.py`:
- `API_KEY`: رمز الحماية للطلبات.
- `RESPONSE_TIMEOUT_SECONDS`: مهلة انتظار التوليد (الافتراضي 120 ثانية).
- `PROFILE_DIR`: مسار المجلد الدائم لجلسة المتصفح.
