from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    Form,
    Request,
    UploadFile,
)

from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
)

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field

from starlette.middleware.sessions import SessionMiddleware

from pypdf import PdfReader

from . import ai_service

from .config import settings

from .database import (
    add_log,
    authenticate,
    create_user,
    get_logs,
    init_db,
)


BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):

    init_db()

    yield


app = FastAPI(
    title="EduGenie",
    description="Google Gemini Powered Learning Assistant",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_secret_key,
)


app.mount(
    "/static",
    StaticFiles(
        directory=BASE_DIR / "static"
    ),
    name="static",
)


templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# ---------------------------------------------------------
# REQUEST MODELS
# ---------------------------------------------------------


class ChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=6000,
    )

    history: list[dict[str, str]] = Field(
        default_factory=list
    )


class ExplainRequest(BaseModel):

    topic: str = Field(
        min_length=1,
        max_length=2000,
    )

    level: str = "beginner"


class QuizRequest(BaseModel):

    topic: str = Field(
        min_length=1,
        max_length=3000,
    )

    count: int = Field(
        default=5,
        ge=1,
        le=15,
    )

    difficulty: str = "medium"


class PathRequest(BaseModel):

    goal: str = Field(
        min_length=1,
        max_length=2000,
    )

    level: str = "beginner"

    weeks: int = Field(
        default=4,
        ge=1,
        le=12,
    )


# ---------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------


def current_user(request: Request):

    return request.session.get(
        "user"
    )


def require_user(request: Request):

    user = current_user(request)

    if not user:
        raise PermissionError(
            "Login required."
        )

    return user


# ---------------------------------------------------------
# PAGES
# ---------------------------------------------------------


@app.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": current_user(request)
        },
    )


@app.get(
    "/login",
    response_class=HTMLResponse,
)
async def login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------


@app.post("/api/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):

    username = username.strip()

    if len(username) < 3:

        return JSONResponse(
            {
                "error": (
                    "Username must contain "
                    "at least 3 characters."
                )
            },
            status_code=400,
        )

    if len(password) < 6:

        return JSONResponse(
            {
                "error": (
                    "Password must contain "
                    "at least 6 characters."
                )
            },
            status_code=400,
        )

    user_id = create_user(
        username,
        password,
    )

    if not user_id:

        return JSONResponse(
            {
                "error": (
                    "Username already exists."
                )
            },
            status_code=409,
        )

    request.session["user"] = {
        "id": user_id,
        "username": username,
    }

    return {
        "ok": True
    }


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------


@app.post("/api/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):

    user = authenticate(
        username.strip(),
        password,
    )

    if not user:

        return JSONResponse(
            {
                "error": (
                    "Invalid username or password."
                )
            },
            status_code=401,
        )

    request.session["user"] = user

    return {
        "ok": True
    }


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------


@app.post("/api/logout")
async def logout(request: Request):

    request.session.clear()

    return {
        "ok": True
    }


# ---------------------------------------------------------
# HISTORY
# ---------------------------------------------------------


@app.get("/api/history")
async def history(request: Request):

    try:

        user = require_user(
            request
        )

        return {
            "items": get_logs(
                user["id"]
            )
        }

    except PermissionError as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=401,
        )


# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------


@app.post("/api/chat")
async def api_chat(
    request: Request,
    payload: ChatRequest,
):

    try:

        user = require_user(
            request
        )

        result = ai_service.chat(
            payload.message,
            payload.history,
        )

        add_log(
            user["id"],
            "chat",
            payload.message,
            result,
        )

        return {
            "answer": result
        }

    except PermissionError as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=401,
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )


# ---------------------------------------------------------
# EXPLAIN
# ---------------------------------------------------------


@app.post("/api/explain")
async def api_explain(
    request: Request,
    payload: ExplainRequest,
):

    try:

        user = require_user(
            request
        )

        result = ai_service.explain(
            payload.topic,
            payload.level,
        )

        add_log(
            user["id"],
            "explain",
            payload.topic,
            result,
        )

        return {
            "answer": result
        }

    except PermissionError as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=401,
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )


# ---------------------------------------------------------
# TEXT SUMMARY
# ---------------------------------------------------------


@app.post("/api/summarize")
async def api_summarize(
    request: Request,
    text: str = Form(...),
):

    try:

        user = require_user(
            request
        )

        if not text.strip():

            return JSONResponse(
                {
                    "error": (
                        "Study text is required."
                    )
                },
                status_code=400,
            )

        limited_text = text[:50000]

        result = ai_service.summarize(
            limited_text
        )

        add_log(
            user["id"],
            "summarize",
            text[:5000],
            result,
        )

        return {
            "answer": result
        }

    except PermissionError as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=401,
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )


# ---------------------------------------------------------
# PDF SUMMARY
# ---------------------------------------------------------


@app.post("/api/upload-summary")
async def upload_summary(
    request: Request,
    file: UploadFile = File(...),
):

    try:

        user = require_user(
            request
        )

        filename = (
            file.filename or ""
        )

        if (
            file.content_type != "application/pdf"
            and not filename.lower().endswith(".pdf")
        ):

            return JSONResponse(
                {
                    "error": (
                        "Please upload a PDF file."
                    )
                },
                status_code=400,
            )

        raw = await file.read()

        max_bytes = (
            settings.max_upload_mb
            * 1024
            * 1024
        )

        if len(raw) > max_bytes:

            return JSONResponse(
                {
                    "error": (
                        f"PDF is larger than "
                        f"{settings.max_upload_mb} MB."
                    )
                },
                status_code=413,
            )

        temp_path = (
            BASE_DIR.parent
            / "data"
            / "_upload.pdf"
        )

        temp_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path.write_bytes(raw)

        try:

            reader = PdfReader(
                str(temp_path)
            )

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        finally:

            temp_path.unlink(
                missing_ok=True
            )

        if not text.strip():

            return JSONResponse(
                {
                    "error": (
                        "No selectable text "
                        "was found in this PDF."
                    )
                },
                status_code=400,
            )

        result = ai_service.summarize(
            text[:50000]
        )

        add_log(
            user["id"],
            "pdf_summary",
            filename,
            result,
        )

        return {
            "answer": result,
            "pages": len(reader.pages),
        }

    except PermissionError as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=401,
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )


# ---------------------------------------------------------
# QUIZ
# ---------------------------------------------------------


@app.post("/api/quiz")
async def api_quiz(
    request: Request,
    payload: QuizRequest,
):

    try:

        user = require_user(
            request
        )

        result = ai_service.quiz(
            payload.topic,
            payload.count,
            payload.difficulty,
        )

        add_log(
            user["id"],
            "quiz",
            payload.topic,
            str(result),
        )

        return {
            "questions": result
        }

    except PermissionError as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=401,
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )


# ---------------------------------------------------------
# LEARNING PATH
# ---------------------------------------------------------


@app.post("/api/learning-path")
async def api_learning_path(
    request: Request,
    payload: PathRequest,
):

    try:

        user = require_user(
            request
        )

        result = ai_service.learning_path(
            payload.goal,
            payload.level,
            payload.weeks,
        )

        add_log(
            user["id"],
            "learning_path",
            payload.goal,
            result,
        )

        return {
            "answer": result
        }

    except PermissionError as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=401,
        )

    except Exception as exc:

        return JSONResponse(
            {
                "error": str(exc)
            },
            status_code=500,
        )


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "gemini_configured": bool(
            settings.gemini_api_key
        ),
        "model": settings.gemini_model,
    }