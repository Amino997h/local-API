import time
import uuid
import json
import logging
from typing import List, Optional, Union, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

import config
from chatgpt_engine import ChatGPTEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ChatGPTLocalAPI")

# Security
security = HTTPBearer(auto_error=False)

# Initialize Engine
engine = ChatGPTEngine()


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """التحقق من رمز الحماية (Bearer Token)."""
    if config.API_KEY:
        if not credentials or credentials.credentials != config.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="رمز التفويض غير صحيح أو مفقود (Invalid or missing Bearer token).",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق عبر lifespan."""
    logger.info("جارٍ تشغيل السيرفر وتهيئة محرك ChatGPT...")
    await engine.initialize(headless=False)
    yield
    logger.info("جارٍ إيقاف السيرفر وإغلاق متصفح Playwright...")
    await engine.close()


# Pydantic Schemas matching OpenAI official specification strictly
class ChatMessage(BaseModel):
    role: str
    content: Optional[Union[str, List[Dict[str, Any]]]] = ""
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="gpt-4o", description="اسم النموذج المطلوب")
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None


class ChoiceMessage(BaseModel):
    role: str = "assistant"
    content: Optional[str] = None
    refusal: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class Choice(BaseModel):
    index: int = 0
    message: ChoiceMessage
    logprobs: Optional[Any] = None
    finish_reason: str = "stop"


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage
    system_fingerprint: Optional[str] = "fp_local"


app = FastAPI(
    title="Personal OpenAI-Compatible ChatGPT Local API Server",
    version="1.0.0",
    description="سيرفر محلي متوافق تماماً مع OpenAI API لمعالجة برومبتات ChatGPT عبر Playwright.",
    lifespan=lifespan,
)


def format_clean_prompt(messages: List[ChatMessage]) -> str:
    """
    تنسيق البرومبت بذكاء عالي:
    1. تصفية كليشات الحماية وسياسات النظام المكررة.
    2. عدم تكرار محادثات Assistant السابقة (لأن ChatGPT يحتفظ بها في المتصفح).
    3. إرسال الرسالة الحالية للمستخدم مسبوقة بالتاريخ فقط إن وجد.
    """
    if not messages:
        return ""

    if len(messages) == 1:
        content = messages[0].content or ""
        if isinstance(content, list):
            content = "\n".join([p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"])
        return str(content).strip()

    latest_user_text = ""
    date_context = ""

    for msg in reversed(messages):
        content = msg.content or ""
        if isinstance(content, list):
            content = "\n".join([p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"])
        content_str = str(content)

        if msg.role == "user" and not latest_user_text:
            clean_text = content_str
            
            # إزالة وسوم بيانات المصادر غير الموثوقة الكثيفة إن وجدت
            if "<<<UNTRUSTED_SOURCE_DATA>>>" in clean_text:
                parts = clean_text.split("<<<END_UNTRUSTED_SOURCE_DATA>>>")
                clean_text = parts[-1] if len(parts) > 1 else clean_text

            # استخراج التاريخ إن وجد
            if "[Context — current date/time" in content_str:
                lines = clean_text.split("\n")
                date_lines = [l.strip() for l in lines if "Today is" in l or "User local time" in l]
                if date_lines:
                    date_context = " | ".join(date_lines)
                
                # استخراج آخر سطر نصي غير فارغ يعبر عن طلب المستخدم
                non_empty = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("[Context")]
                if non_empty:
                    clean_text = non_empty[-1]

            latest_user_text = clean_text.strip()
            if latest_user_text:
                break

    parts = []
    if date_context:
        parts.append(f"[{date_context}]")
    if latest_user_text:
        parts.append(latest_user_text)
    else:
        parts.append(str(messages[-1].content or "").strip())

    return "\n".join(parts)


@app.get("/health", tags=["Health"])
async def health_check():
    """فحص حالة السيرفر والمحرك."""
    healthy = engine._is_initialized and engine.page is not None and not engine.page.is_closed()
    return {
        "status": "healthy" if healthy else "degraded",
        "engine_initialized": engine._is_initialized,
        "browser_open": engine.page is not None and not engine.page.is_closed() if engine.page else False,
    }


@app.get("/v1/models", tags=["OpenAI Compatibility"])
async def list_models(authenticated: bool = Depends(verify_api_key)):
    """إرجاع قائمة النماذج المتاحة بنمط OpenAI."""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4o",
                "object": "model",
                "created": 1700000000,
                "owned_by": "openai-local-bridge",
            },
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1700000000,
                "owned_by": "openai-local-bridge",
            },
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1700000000,
                "owned_by": "openai-local-bridge",
            },
        ],
    }


@app.post("/v1/chat/completions", tags=["OpenAI Compatibility"])
async def create_chat_completion(
    request: ChatCompletionRequest,
    authenticated: bool = Depends(verify_api_key),
):
    """
    نقطة النهاية الرئيسية المحاكية لـ OpenAI Chat Completions.
    تتلقى الرسائل وتفلتر الكليشات المكررة ثم ترسل الرسالة الحالية بنظافة لـ ChatGPT.
    تكتشف الطلبات التلقائية الثانوية وتجيب عليها فوراً بـ 0ms محلياً.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="مصفوفة الرسائل messages لا يمكن أن تكون فارغة.")

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_timestamp = int(time.time())

    # تجميع وتنظيف النص بالكامل عبر format_clean_prompt
    full_prompt = format_clean_prompt(request.messages)
    full_prompt_lower = full_prompt.lower()

    # ⚡ 1. رصد طلبات تسمية شريط المحادثة التلقائية (Auto-Title Generation)
    if "generate a short title" in full_prompt_lower or "generate a title" in full_prompt_lower:
        logger.info("⚡ رصد طلب تلقائي لتسمية المحادثة (Auto-Title Request) - إرجاع عنوان سريع محلياً بـ 0ms بدون إرساله لـ ChatGPT.")
        user_snippet = ""
        for m in request.messages:
            if m.role == "user" and m.content:
                user_snippet = str(m.content).strip()
                break
        reply_text = user_snippet[:35] if user_snippet else "محادثة جديدة"

    # ⚡ 2. رصد طلبات تحليل الذاكرة واستخراج الحقائق الخلفية (Memory Extraction)
    elif "memory extraction assistant" in full_prompt_lower or "durable personal facts" in full_prompt_lower or "extract durable" in full_prompt_lower:
        logger.info("⚡ رصد طلب تلقائي لاستخراج الذاكرة (Memory Extraction Request) - إرجاع '[]' محلياً بـ 0ms بدون إرساله لـ ChatGPT.")
        reply_text = "[]"

    # 🚀 3. الطلب النظيف الموجه لـ ChatGPT
    else:
        logger.info(f"استلام طلب جيل جديد ({len(request.messages)} رسائل، Stream={request.stream}). البرومبت النظيف: '{full_prompt}'")

        try:
            reply_text = await engine.generate_chat_response(full_prompt)
        except RuntimeError as r_err:
            logger.error(f"خطأ في جلسة ChatGPT: {r_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ChatGPT session error or intervention required: {str(r_err)}",
            )
        except Exception as e:
            logger.error(f"خطأ غير متوقع أثناء المعالجة: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal Server Error: {str(e)}",
            )

    logger.info(f"📤 الرد الجاهز للإرسال (الطول: {len(reply_text)} حرف): '{reply_text[:100]}...'")

    # إذا كان التطبيق طالب للـ Streaming (SSE)
    if request.stream:
        async def event_generator():
            chunk_data = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_timestamp,
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": reply_text},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            stop_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_timestamp,
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield f"data: {json.dumps(stop_chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # الرد المعياري JSON
    response_obj = ChatCompletionResponse(
        id=completion_id,
        created=created_timestamp,
        model=request.model,
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(
                    role="assistant",
                    content=reply_text,
                    refusal=None,
                    tool_calls=None,
                ),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=len(full_prompt.split()),
            completion_tokens=len(reply_text.split()),
            total_tokens=len(full_prompt.split()) + len(reply_text.split()),
        ),
        system_fingerprint="fp_local",
    )
    return JSONResponse(content=response_obj.model_dump())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=False)
