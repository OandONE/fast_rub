from typing import Optional, Literal, TYPE_CHECKING
import logging
import asyncio
if TYPE_CHECKING:
    from .client import Client
    from ..type import WebhookConfig


class WebhookServer:
    """سرور وب‌هوک داخلی — پشتیبانی از FastAPI و Flask"""
    
    def __init__(
        self,
        client: "Client",
        config: 'WebhookConfig',
        logger: Optional[logging.Logger] = None
    ):
        self.client = client
        self.config = config
        self.logger = logger or logging.getLogger("fast_rub.webhook")
        backend = config.backend
        self.backend = backend
        self._server = None
        
        if backend == "fastapi":
            try:
                from fastapi import FastAPI
            except ImportError:
                raise ImportError(
                    "FastAPI not installed !",
                    "install: pip install fast_rub[fastapi]"
                )
            self.app = FastAPI(title="Fast Rub Webhook Server", version="1.0.0")
            self._setup_fastapi_routes()
        
        elif backend == "flask":
            try:
                from flask import Flask
            except ImportError:
                raise ImportError(
                    "Flask not installed !",
                    "install: pip install fast_rub[flask]"
                )
            self.app = Flask(__name__)
            self._setup_flask_routes()
        
        else:
            raise ValueError(f"backend باید fastapi یا flask باشد، نه {backend}")
    
    
    # ═══════════════════════════════════
    # region 🛣️ مسیرها — FastAPI
    # ═══════════════════════════════════
    
    def _setup_fastapi_routes(self):
        from fastapi import Request, Path
        from fastapi.responses import JSONResponse
        
        if self.config.use_token_in_url:
            @self.app.post(f"{self.config.path_prefix}/message/{{token}}") # pyright: ignore[reportArgumentType]
            async def webhook_message_with_token(
                request: Request,
                token: str = Path(...)
            ):
                if token != self.client.token:
                    return JSONResponse({"error": "Unauthorized"}, status_code=403)
                return await self._handle_webhook(request, "ReceiveUpdate")
            
            @self.app.post(f"{self.config.path_prefix}/inline/{{token}}") # pyright: ignore[reportArgumentType]
            async def webhook_inline_with_token(
                request: Request,
                token: str = Path(...)
            ):
                if token != self.client.token:
                    return JSONResponse({"error": "Unauthorized"}, status_code=403)
                return await self._handle_webhook(request, "ReceiveInlineMessage")
        
        else:
            @self.app.post(f"{self.config.path_prefix}/message") # pyright: ignore[reportArgumentType]
            async def webhook_message(request: Request):
                return await self._handle_webhook(request, "ReceiveUpdate")
            
            @self.app.post(f"{self.config.path_prefix}/inline") # pyright: ignore[reportArgumentType]
            async def webhook_inline(request: Request):
                return await self._handle_webhook(request, "ReceiveInlineMessage")
        
        @self.app.get(f"{self.config.path_prefix}/health")
        async def health():
            return {"status": "running"}
        
        @self.app.get("/")
        async def root():
            return {
                "name": "Fast Rub Webhook Server",
                "backend": "fastapi",
                "endpoints": {
                    "message": f"{self.config.path_prefix}/message",
                    "inline": f"{self.config.path_prefix}/inline",
                }
            }
    
    # endregion
    
    # ═══════════════════════════════════
    # region 🛣️ مسیرها — Flask
    # ═══════════════════════════════════
    
    def _setup_flask_routes(self):
        from flask import request, jsonify
        
        if self.config.use_token_in_url:
            # با توکن توی URL
            @self.app.post(f"{self.config.path_prefix}/message/<token>")
            def webhook_message_with_token(token):
                if token != self.client.token:
                    return jsonify({"error": "Unauthorized"}), 403
                return self._handle_webhook_flask(request, "ReceiveUpdate")
            
            @self.app.post(f"{self.config.path_prefix}/inline/<token>")
            def webhook_inline_with_token(token):
                if token != self.client.token:
                    return jsonify({"error": "Unauthorized"}), 403
                return self._handle_webhook_flask(request, "ReceiveInlineMessage")
        
        else:
            # بدون توکن (هر کسی می‌تونه بفرسته)
            @self.app.post(f"{self.config.path_prefix}/message")
            def webhook_message():
                return self._handle_webhook_flask(request, "ReceiveUpdate")
            
            @self.app.post(f"{self.config.path_prefix}/inline")
            def webhook_inline():
                return self._handle_webhook_flask(request, "ReceiveInlineMessage")
        
        # Health Check (همیشه بدون توکن)
        @self.app.get(f"{self.config.path_prefix}/health")
        def health():
            return jsonify({"status": "running"})
    # endregion
    
    
    # ═══════════════════════════════════
    # region 📩 پردازش Webhook
    # ═══════════════════════════════════
    
    async def _handle_webhook(self, request, endpoint_type: str):
        """پردازش وب‌هوک — نسخه FastAPI"""
        from fastapi.responses import JSONResponse
        
        try:
            data = await request.json()
            self.logger.debug(f"📩 Webhook دریافت شد: {endpoint_type}")
            
            if endpoint_type == "ReceiveInlineMessage":
                await self.client._process_button_push(data)
            else:
                await self.client._process_webhook_push(data, endpoint_type)
            
            return JSONResponse({"status": "ok"})
        
        except Exception as e:
            self.logger.error(f"❌ خطا در پردازش Webhook: {e}")
            return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)
    
    
    def _handle_webhook_flask(self, request, endpoint_type: str):
        """پردازش وب‌هوک — نسخه Flask"""
        from flask import jsonify
        
        try:
            data = request.get_json()
            self.logger.debug(f"📩 Webhook دریافت شد: {endpoint_type}")
            
            loop = asyncio.new_event_loop()
            
            if endpoint_type == "ReceiveInlineMessage":
                loop.run_until_complete(self.client._process_button_push(data))
            else:
                loop.run_until_complete(self.client._process_webhook_push(data, endpoint_type))
            
            loop.close()
            return jsonify({"status": "ok"})
        
        except Exception as e:
            self.logger.error(f"❌ خطا در پردازش Webhook: {e}")
            return jsonify({"status": "error", "detail": str(e)}), 500
    
    # endregion
    
    
    # ═══════════════════════════════════
    # region 🚀 شروع و توقف
    # ═══════════════════════════════════
    
    async def start(self):
        """شروع سرور"""
        if self.backend == "fastapi":
            import uvicorn
            config = uvicorn.Config(self.app, host=self.config.host, port=self.config.port, log_level="warning")
            self._server = uvicorn.Server(config)
            self.logger.info(f"🚀 Webhook Server (FastAPI) روی http://{self.config.host}:{self.config.port} اجرا شد")
            await self._server.serve()
        
        elif self.backend == "flask":
            self.logger.info(f"🚀 Webhook Server (Flask) روی http://{self.config.host}:{self.config.port} اجرا شد")
            self.app.run(host=self.config.host, port=self.config.port) # type: ignore
    
    
    async def stop(self):
        """توقف سرور"""
        if self.backend == "fastapi" and self._server:
            self._server.should_exit = True
            self.logger.info("🛑 Webhook Server متوقف شد")
    
    # endregion
