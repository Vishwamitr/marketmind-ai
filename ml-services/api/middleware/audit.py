from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from utils.audit_logger import audit_logger
import jwt

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only log write operations or critical paths
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            user_id = "anonymous"
            # Try to get user from Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    # We decode without verification just to extract sub (verification happens in auth router)
                    # OR we could rely on request.state if we set it in Auth middleware (but Depends is used there)
                    # For simplicity, we just mark as "authenticated_user" or try decode if key available
                    # A better way is to let endpoints log specific user actions, 
                    # middleware just logs the request.
                    payload = jwt.decode(token, options={"verify_signature": False})
                    user_id = payload.get("sub", "unknown")
                except:
                    pass
            
            audit_logger.log_event(
                event_type="HTTP_REQUEST",
                user_id=user_id,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code
                },
                status="SUCCESS" if response.status_code < 400 else "FAILURE",
                ip_address=request.client.host if request.client else "unknown"
            )
            
        return response
