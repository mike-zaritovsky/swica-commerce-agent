# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""Host code the SWICA demo API uses: credential loading, the app and its middleware, the
session store, and the storefront routes; ``storefront_fixtures`` holds the help-search helper
and ``gateway`` the dentsu gateway client."""

from .host import REPO_ROOT, load_demo_env, spawn_background
from .memory import MemorySeeder
from .sessions import (
    SESSION_HEADER,
    SessionConflictError,
    SessionRecord,
    SessionStore,
    UnknownSessionError,
    session_dependency,
)
from .storefront import CartAddRequest, StorefrontHost, build_storefront_host

__all__ = [
    "REPO_ROOT",
    "SESSION_HEADER",
    "CartAddRequest",
    "MemorySeeder",
    "SessionConflictError",
    "SessionRecord",
    "SessionStore",
    "StorefrontHost",
    "UnknownSessionError",
    "build_storefront_host",
    "load_demo_env",
    "session_dependency",
    "spawn_background",
]
