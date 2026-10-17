"""
Test settings for glass_factor_system.
"""

from typing import Any, cast

from .base import *  # noqa: F401, F403

DEBUG = False

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

cast(dict[str, Any], LOGGING)["handlers"]["file"]["filename"] = (  # noqa: F405
    BASE_DIR / "logs" / "test.log"
)
cast(dict[str, Any], LOGGING)["handlers"]["error_file"]["filename"] = (  # noqa: F405
    BASE_DIR / "logs" / "test_error.log"
)  # noqa: F405
