"""
Development settings for glass_factor_system.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Allow all origins in development for convenience
CORS_ALLOW_ALL_ORIGINS = True
