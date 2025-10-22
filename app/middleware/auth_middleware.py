from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Optional
import os


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to check for authorization token in headers.
    Can be configured to protect specific routes or all routes.
    """
    
    def __init__(self, app, protected_routes: Optional[List[str]] = None, 
                 auth_header: str = "Authorization", 
                 token_prefix: str = "Bearer "):
        super().__init__(app)
        self.protected_routes = protected_routes or []
        self.auth_header = auth_header
        self.token_prefix = token_prefix
    
    
    def _is_protected_route(self, path: str) -> bool:
        """
        Check if the current route is protected.
        If no protected routes are specified, all routes are protected.
        """
        if not self.protected_routes:
            return True
        
        # Check if the path matches any protected route pattern
        for route in self.protected_routes:
            if path.startswith(route):
                return True
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract token from the authorization header.
        """
        auth_header = request.headers.get(self.auth_header)
        if not auth_header:
            return None
        
        if auth_header.startswith(self.token_prefix):
            return auth_header[len(self.token_prefix):]
        return auth_header
    
    async def _validate_google_oauth_token(self, token: str) -> dict:
        """
        Validate Google OAuth JWT token by calling Google's tokeninfo endpoint.
        This ensures proper signature validation and token authenticity.
        """
        try:
            import httpx
            import json
            
            # Use Google's tokeninfo endpoint for proper validation
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={token}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    token_info = response.json()
                    user_info = {
                        "user_id": token_info.get("sub"),
                        "email": token_info.get("email"),
                        "name": token_info.get("name"),
                        "picture": token_info.get("picture"),
                        "verified_email": token_info.get("email_verified"),
                        "audience": token_info.get("aud"),
                        "expires_in": token_info.get("expires_in"),
                        "issued_at": token_info.get("iat")
                    }
                    
                    return user_info
                else:
                    print(f"Token validation failed with status: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error validating Google OAuth token: {e}")
            return None
    
    
    async def dispatch(self, request: Request, call_next):
        """
        Main middleware logic that runs before each request.
        """
        # Skip authentication for certain paths (like health checks, docs)
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health"]
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Check if this route is protected
        if not self._is_protected_route(request.url.path):
            return await call_next(request)
        
        # Extract token from headers
        token = self._extract_token(request)
        
        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Authorization token required",
                    "message": f"Please provide a valid {self.auth_header} header"
                }
            )
        
        # Validate Google OAuth token
        user_info = await self._validate_google_oauth_token(token)
        if not user_info:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Invalid Google OAuth token",
                    "message": "The provided Google OAuth token is not valid or has expired"
                }
            )
        
        # Add token and user info to request state for use in route handlers
        request.state.auth_token = token
        request.state.user_info = user_info
        request.state.user_id = user_info.get("user_id")
        request.state.user_email = user_info.get("email")
        request.state.user_name = user_info.get("name")
        
        # Continue to the next middleware/route handler
        response = await call_next(request)
        return response

