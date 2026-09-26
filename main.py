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
    تتلقى الرسائل وتدمج السياق الكامل ثم ترسله إلى ChatGPT وتسترجع الرد.
    تكتشف الطلبات التلقائية الثانوية مثل (توليد العنوان واستخراج الذاكرة) وتُجيب عليها فوراً بـ 0ms محلياً.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="مصفوفة الرسائل messages لا يمكن أن تكون فارغة.")

    # تجميع جميع الرسائل في برومبت موحد
    formatted_parts = []
    for msg in request.messages:
        content = msg.content
        if isinstance(content, list):
            content = "\n".join([p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"])
        elif content is None:
            content = ""
            
        if len(request.messages) == 1:
            formatted_parts.append(str(content))
        else:
            formatted_parts.append(f"[{msg.role.upper()}]:\n{content}")

    full_prompt = "\n\n".join(formatted_parts)
    full_prompt_lower = full_prompt.lower()

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_timestamp = int(time.time())

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

    # 🚀 3. الطلب الحقيقي الموجه لـ ChatGPT
    else:
        logger.info(f"استلام طلب جيل جديد ({len(request.messages)} رسائل، Stream={request.stream}). البرومبت: '{full_prompt[:80]}...'")

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
