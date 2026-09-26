# Personal OpenAI-Compatible ChatGPT Local API Server 🚀

سيرفر محلي متكامل ومرن يحوّل أتمتة Playwright لموقع ChatGPT إلى API متوافق 100% مع واجهة برمجة تطبيقات **OpenAI** المعيارية (`POST /v1/chat/completions`).

---

## 🌟 الميزات الرئيسية

- **توافق معيار OpenAI الرسمية**: يعمل مباشرة مع جميع الملحقات (Plugins)، منشئي المواقع (Site Builders)، وأطر عمل الذكاء الاصطناعي (مثل TypingMind, LangChain, AutoGen, Firebase, NextChat).
- **دعم البث المباشر (SSE Stream)**: يدعم نمط البث `stream: true` و `stream: false` كواجهة OpenAI الرسمية.
- **استراتيجية جلب النص المبتكرة الرباعية**:
  1. زر النسخ المباشر والحافظة (Clipboard)
  2. اعتراض حزم بيانات شبكة الـ API (`backend-api/*`)
  3. مسح العناصر الذكي المعاصر عبر JavaScript DOM
  4. خطة طوارئ لاستخراج النص الخام لآخر `<article>`
- **مرونة واستعادة تلقائية (Auto-Recovery)**: في حال إغلاق أو انهيار متصفح Playwright، يعيد السيرفر فتح المتصفح تلقائياً دون سقوط السيرفر.
- **مشغل بضغطة زر واحدة (1-Click Desktop Launcher)**: يتوفر سكريبت `Start_ChatGPT_API.bat` لتشغيل السيرفر والنفق بضغطة زر واحدة دون الحاجة لإعادة أوامر التثبيت.
- **مرونة الأنفاق والبدائل**: يدعم الربط عبر **Ngrok (رابط ثابت)**، **Cloudflare Tunnel**، **LocalTunnel**، أو **Firebase Functions**.

---

## 🛠️ التثبيت والتشغيل السريع

للاطلاع على دليل التثبيت الشامل للمرة الأولى والتشغيل اليومي، راجع الملف المخصص:  
📖 **[دليل التثبيت والتشغيل التفصيلي (INSTALLATION.md)](INSTALLATION.md)**

```bash
# 1. تثبيت الحزم (مرة واحدة)
pip install -r requirements.txt

# 2. تثبيت متصفح Playwright (مرة واحدة)
playwright install chromium

# 3. التشغيل اليومي (بضغطة زر)
انقر مرتين على ملف Start_ChatGPT_API.bat
```

---

## 🔑 بيانات الربط بالمواقع والإضافات الخارجية

- **API Base URL**: `https://your-domain.ngrok-free.dev/v1` *(أو رابط Cloudflare/Proxy الخاص بك)*
- **API Key**: `sk-chatgpt-local-secret-key` *(المحدد في `config.py`)*
- **Model**: `gpt-4o`

---

## 🧪 اختبار السيرفر محلياً

يمكنك تشغيل سكريبت الاختبار في نافذة جديدة:

```bash
python test_client.py
```

أو استخدام `curl`:

```bash
curl -X POST http://127.0.0.1:8008/v1/chat/completions \
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
- `PORT`: منفذ السيرفر المحلي (الافتراضي 8008).
- `RESPONSE_TIMEOUT_SECONDS`: مهلة انتظار التوليد (الافتراضي 120 ثانية).
- `PROFILE_DIR`: مسار المجلد الدائم لجلسة المتصفح.
