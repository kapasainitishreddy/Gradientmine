"""HTTP boundary: bounded strict JSON, signed wallet sessions and explicit transaction intent."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from starlette.middleware.cors import CORSMiddleware

from .config import Settings
from .crypto import safe_json, validate_address
from .service import Marketplace, Problem


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Challenge(StrictModel):
    address: str = Field(min_length=32, max_length=44)

    @field_validator("address")
    @classmethod
    def valid(cls, value):
        return validate_address(value)


class Authentication(StrictModel):
    nonce: str = Field(min_length=43, max_length=43)
    signature: str = Field(min_length=80, max_length=100)


class JobInput(StrictModel):
    title: str = Field(min_length=3, max_length=100)
    duration_seconds: int = Field(default=600, ge=5, le=86400)
    reward_lamports: int = Field(default=0, ge=0, le=1_000_000_000)
    minimum_delta: float = Field(default=0.01, ge=0, le=1)
    parent_job_id: str | None = Field(default=None, max_length=36)

    @field_validator("title")
    @classmethod
    def title_valid(cls, value):
        if len(value.strip()) < 3 or any(ord(char) < 32 for char in value):
            raise ValueError("Use a readable title with at least three nonblank characters")
        return value.strip()


class SubmissionInput(StrictModel):
    artifact: dict
    manifest: dict


class IntentInput(StrictModel):
    action: str = Field(pattern=r"^(fund|register|refund)$")
    submission_id: str | None = Field(default=None, max_length=36)


class BroadcastInput(IntentInput):
    transaction_base64: str = Field(min_length=4, max_length=2400)


class ConfirmationInput(IntentInput):
    signature: str = Field(min_length=64, max_length=88)


class Boundary:
    """Reject oversized request streams before framework buffering, including missing Content-Length."""

    def __init__(self, app, origin):
        self.app, self.origin = app, origin

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        origin = headers.get("origin")
        if scope["method"] not in {"GET", "HEAD", "OPTIONS"} and origin and origin != self.origin:
            return await JSONResponse(
                {"error": "Request origin does not match this deployment"}, status_code=403
            )(scope, receive, send)
        body = bytearray()
        if scope["method"] not in {"GET", "HEAD"}:
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > 262144:
                    return await JSONResponse(
                        {"error": "Request exceeds the 256 KiB limit"}, status_code=413
                    )(scope, receive, send)
                if not message.get("more_body", False):
                    break
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def secure_send(message):
            if message["type"] == "http.response.start":
                extra = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"),
                    (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                    (
                        b"content-security-policy",
                        b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
                    ),
                ]
                if scope["path"].startswith("/api/"):
                    extra.append((b"cache-control", b"no-store"))
                message["headers"] = [*message.get("headers", []), *extra]
            await send(message)

        await self.app(scope, replay, secure_send)


async def body(request, model):
    try:
        return model.model_validate(safe_json(await request.body()))
    except ValidationError as exc:
        details = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
        raise Problem(422, details) from exc
    except ValueError as exc:
        raise Problem(400, str(exc)) from exc


def create_app(settings=None, clock=time.time, scheduler=False):
    settings = settings or Settings.from_env()
    market = Marketplace(settings, clock)

    @asynccontextmanager
    async def lifespan(app):
        async def run():
            while True:
                await asyncio.sleep(2)
                await asyncio.to_thread(market.tick)

        task = asyncio.create_task(run()) if scheduler else None
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    app = FastAPI(title="GradientMine", version="0.2.0", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.market = market
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.origin],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
    )
    app.add_middleware(Boundary, origin=settings.origin)

    @app.exception_handler(Problem)
    async def problem_handler(request, exc):
        return JSONResponse({"error": exc.message}, status_code=exc.status)

    @app.exception_handler(ValueError)
    async def value_handler(request, exc):
        return JSONResponse({"error": str(exc)}, status_code=422)

    def auth(request):
        return market.session(request.headers.get("authorization"))

    def ip(request):
        return request.client.host if request.client else "unknown"

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": settings.mode, "validator": market.validator.address}

    @app.get("/api/config")
    def config():
        return market.config()

    @app.post("/api/auth/challenge")
    async def challenge(request: Request):
        value = await body(request, Challenge)
        return market.challenge(value.address, ip(request))

    @app.post("/api/auth/verify")
    async def verify(request: Request):
        value = await body(request, Authentication)
        return market.authenticate(value.nonce, value.signature, ip(request))

    @app.get("/api/auth/me")
    def me(request: Request):
        return {"address": auth(request)}

    @app.post("/api/auth/logout")
    def logout(request: Request):
        market.logout(request.headers.get("authorization"))
        return {"signed_out": True}

    @app.get("/api/jobs")
    def jobs():
        return {"jobs": market.jobs(), "mode": settings.mode}

    @app.post("/api/jobs")
    async def create(request: Request):
        address = auth(request)
        market.rate(("create", address), 10)
        value = await body(request, JobInput)
        return market.create_job(address, value.model_dump(), request.headers.get("idempotency-key"))

    @app.get("/api/jobs/{job_id}")
    def detail(job_id: str):
        return market.detail(job_id)

    @app.get("/api/jobs/{job_id}/training")
    def training(job_id: str, request: Request):
        auth(request)
        return market.training(job_id)

    @app.post("/api/jobs/{job_id}/submissions")
    async def submit(job_id: str, request: Request):
        address = auth(request)
        market.rate(("submission", address), 20)
        value = await body(request, SubmissionInput)
        return market.submit(job_id, address, value.artifact, value.manifest)

    @app.post("/api/jobs/{job_id}/evaluate")
    def evaluate(job_id: str, request: Request):
        auth(request)
        return market.evaluate(job_id)

    @app.post("/api/jobs/{job_id}/settle")
    def settle(job_id: str, request: Request):
        auth(request)
        return market.settle(job_id)

    @app.post("/api/jobs/{job_id}/recover-settlement")
    def recover_settlement(job_id: str, request: Request):
        address = auth(request)
        market.rate(("recover", address), 6)
        return market.recover_settlement(job_id)

    @app.post("/api/jobs/{job_id}/transaction")
    async def transaction(job_id: str, request: Request):
        address = auth(request)
        value = await body(request, IntentInput)
        return market.transaction_intent(job_id, address, value.action, value.submission_id)

    @app.post("/api/jobs/{job_id}/broadcast")
    async def broadcast(job_id: str, request: Request):
        address = auth(request)
        market.rate(("broadcast", address), 20)
        value = await body(request, BroadcastInput)
        return await asyncio.to_thread(
            market.broadcast, job_id, address, value.action, value.transaction_base64, value.submission_id
        )

    @app.post("/api/jobs/{job_id}/confirm")
    async def confirm(job_id: str, request: Request):
        address = auth(request)
        value = await body(request, ConfirmationInput)
        return await asyncio.to_thread(
            market.confirm, job_id, address, value.action, value.signature, value.submission_id
        )

    @app.get("/api/artifacts/{sha}")
    def artifact(sha: str):
        return Response(
            market.artifact_bytes(sha), media_type="application/json", headers={"ETag": f'"{sha}"'}
        )

    # Only explicitly public, packaged web assets are served. No catch-all path to the data directory.
    web = Path(__file__).parent / "web"
    if not web.is_dir():
        web = Path(__file__).resolve().parent.parent / "web"
    if web.is_dir():
        app.mount("/assets", StaticFiles(directory=web / "assets"), name="assets")

        @app.get("/")
        def index():
            if not (web / "index.html").is_file():
                raise Problem(404, "Frontend is not installed")
            return FileResponse(web / "index.html")

    return app
