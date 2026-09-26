# دليل التثبيت والتشغيل (Installation & Setup Guide)

هذا المستند يشرح خطوة بخطوة كيفية تثبيت وتشغيل **Local ChatGPT OpenAI API Server** على جهازك وربطه بالمنصات والمواقع الخارجية.

---

> [!NOTE]
> **ملاحظة هامة حول الخصوصية والاستقلالية (Self-Hosted):**  
> هذا المشروع هو سيرفر محلي مستقل وخاص لكل مستخدم. عندما يقوم أي شخص باستنساخ هذا المستودع وتثبيته على جهازه، سينشئ **سيرفره الخاص وحسابه الخاص في ChatGPT ونفقه المستقل**. لن يستخدم أحد حسابك أو سيرفرك أو بياناتك الخاصة على الإطلاق.

---

## 📋 المتطلبات الأساسية (Prerequisites)

- **نظام التشغيل**: Windows 10 / 11
- **بيئة العمل**: Python 3.10 أو أحدث
- **المتصفح**: متصفح Chromium (سيتم تثبيته تلقائياً بواسطة Playwright)

---

## 🛠️ 1. التثبيت والتهيئة (Installation)

### الخطوة 1: استنساخ المستودع (Clone Repository)
```bash
git clone https://github.com/Amino997h/local-API.git
cd local-API
```

### الخطوة 2: تثبيت الحزم والمكتبات المطلوبة
```bash
pip install -r requirements.txt
```

### الخطوة 3: تثبيت متصفحات Playwright
```bash
playwright install chromium
```

---

## 🚀 2. التشغيل (Running the Server)

### الخيار 1: التشغيل اليدوي المباشر (Manual Execution)
```bash
python main.py
```
*سيعمل السيرفر المحلي على العنوان:* `http://127.0.0.1:8008/v1`

---

### الخيار 2: التشغيل بضغطة زر واحدة (1-Click Desktop Launcher)
يمكنك استخدام السكريبت `Start_ChatGPT_API.bat` المرفق مع المشروع. بمجرد النقر عليه مرتين:
1. يقوم بإغلاق أية جلسات قديمة للمتصفح.
2. يشغل سيرفر Python المحلي على المنفذ `8008`.
3. يشغل نفق Ngrok الثابت تلقائياً.

---

## 🌐 3. الربط بالنفق الثابت (Ngrok Static Domain)

لربط السيرفر بمواقع خارجيّة عبر إنترنت برابط ثابت دائم:

1. قم بإنشاء حساب مجاني على موقع [Ngrok](https://dashboard.ngrok.com/signup).
2. احصل على **Authtoken** الخاص بك وقم بتسجيله:
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```
3. احصل على رابطك الثابت المجاني من تبويب **Domains** (مثال: `your-domain.ngrok-free.dev`).
4. قم بتشغيل النفق برابطك الثابت:
   ```bash
   ngrok http --url=your-domain.ngrok-free.dev 8008
   ```

---

## 🔑 4. بيانات الربط بالمواقع والإضافات الخارجية

عند ربط السيرفر بـ WordPress أو TypingMind أو أي تطبيق آخر، استخدم البيانات التالية الخاصة بك:

- **API Base URL**: `https://your-domain.ngrok-free.dev/v1`
- **API Key**: `sk-chatgpt-local-secret-key` *(المحدد في `config.py` ويمكنك تغييره)*
- **Model**: `gpt-4o`

---

## 🧪 5. فحص واختبار السيرفر (Testing)

يمكنك تشغيل سكريبت الاختبار في نافذة جديدة للتأكد من جاهزية السيرفر:

```bash
python test_client.py
```
