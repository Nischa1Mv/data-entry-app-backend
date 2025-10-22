"""
Utility functions for authentication and authorization.
"""
from fastapi import Request, HTTPException
from typing import Optional


def get_current_token(request: Request) -> Optional[str]:
    """
    Get the current authentication token from the request.
    This should be called after the AuthMiddleware has processed the request.
    """
    return getattr(request.state, 'auth_token', None)


def get_current_user_id(request: Request) -> Optional[str]:
    """
    Get the current user ID from the request (Google OAuth).
    """
    return getattr(request.state, 'user_id', None)


def get_current_user_email(request: Request) -> Optional[str]:
    """
    Get the current user email from the request (Google OAuth).
    """
    return getattr(request.state, 'user_email', None)


def get_current_user_name(request: Request) -> Optional[str]:
    """
    Get the current user name from the request (Google OAuth).
    """
    return getattr(request.state, 'user_name', None)


def get_current_user_info(request: Request) -> Optional[dict]:
    """
    Get the complete user info from the request (Google OAuth).
    """
    return getattr(request.state, 'user_info', None)


def require_auth(request: Request) -> str:
    """
    Require authentication and return the token.
    Raises HTTPException if no token is found.
    """
    token = get_current_token(request)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "error": "Authentication required",
                "message": "This endpoint requires authentication"
            }
        )
    return token
