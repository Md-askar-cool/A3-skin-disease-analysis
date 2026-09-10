"""
SafeSkin AI – Supabase Service
Singleton client + helper methods for DB and Storage operations.
"""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.config import get_settings

logger = logging.getLogger(__name__)


# ======================================================================
# Singleton factory
# ======================================================================

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Return a cached Supabase client using the service-role key.
    The service-role key bypasses Row Level Security, allowing the
    backend to operate on behalf of any user.
    """
    settings = get_settings()
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=ClientOptions(auto_refresh_token=False, persist_session=False),
    )
    logger.info("Supabase client initialised (service role).")
    return client


def get_anon_supabase_client() -> Client:
    """
    Return a Supabase client using the anon key.
    Used for operations that should respect Row Level Security.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


# ======================================================================
# SupabaseService — database helpers
# ======================================================================

class SupabaseService:
    """
    Thin wrapper around the Supabase Python client.
    All methods return plain dicts / lists so routers stay dependency-free.
    """

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._settings = get_settings()

    # ------------------------------------------------------------------ #
    # Auth – token verification
    # ------------------------------------------------------------------ #

    def verify_token(self, jwt_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a Supabase JWT and return the user payload, or None if invalid.
        Uses the anon client so Supabase handles token validation.
        """
        try:
            anon_client = get_anon_supabase_client()
            # set_session validates the token server-side
            response = anon_client.auth.get_user(jwt_token)
            if response and response.user:
                user = response.user
                return {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                    "app_metadata": user.app_metadata or {},
                    "user_metadata": user.user_metadata or {},
                }
        except Exception as exc:
            logger.warning("Token verification failed: %s", exc)
        return None

    # ------------------------------------------------------------------ #
    # Generic DB helpers
    # ------------------------------------------------------------------ #

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a row and return the created record."""
        try:
            response = self._client.table(table).insert(data).execute()
            if response.data:
                return response.data[0]
        except Exception as exc:
            logger.error("DB insert error [%s]: %s", table, exc)
        return None

    def select(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: str = "*",
        order_by: Optional[str] = None,
        ascending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Select rows with optional filters, ordering, and pagination."""
        try:
            query = self._client.table(table).select(columns)
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            if order_by:
                query = query.order(order_by, desc=not ascending)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.range(offset, offset + (limit or 100) - 1)
            response = query.execute()
            return response.data or []
        except Exception as exc:
            logger.error("DB select error [%s]: %s", table, exc)
            return []

    def select_one(
        self,
        table: str,
        filters: Dict[str, Any],
        columns: str = "*",
    ) -> Optional[Dict[str, Any]]:
        """Return the first matching row or None."""
        rows = self.select(table, filters=filters, columns=columns, limit=1)
        return rows[0] if rows else None

    def update(
        self,
        table: str,
        filters: Dict[str, Any],
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update rows matching filters; return first updated row."""
        try:
            query = self._client.table(table).update(data)
            for key, value in filters.items():
                query = query.eq(key, value)
            response = query.execute()
            if response.data:
                return response.data[0]
        except Exception as exc:
            logger.error("DB update error [%s]: %s", table, exc)
        return None

    def delete(self, table: str, filters: Dict[str, Any]) -> bool:
        """Delete rows matching filters; return True on success."""
        try:
            query = self._client.table(table).delete()
            for key, value in filters.items():
                query = query.eq(key, value)
            query.execute()
            return True
        except Exception as exc:
            logger.error("DB delete error [%s]: %s", table, exc)
            return False

    def count(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Return the number of rows matching filters."""
        try:
            query = self._client.table(table).select("id", count="exact")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.execute()
            return response.count or 0
        except Exception as exc:
            logger.error("DB count error [%s]: %s", table, exc)
            return 0

    # ------------------------------------------------------------------ #
    # Storage helpers
    # ------------------------------------------------------------------ #

    def upload_file(
        self,
        bucket: str,
        storage_path: str,
        file_bytes: bytes,
        content_type: str = "image/jpeg",
    ) -> bool:
        """
        Upload raw bytes to Supabase Storage.
        Returns True on success.
        """
        try:
            self._client.storage.from_(bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            logger.info("Uploaded %s to bucket '%s'.", storage_path, bucket)
            return True
        except Exception as exc:
            logger.error("Storage upload error [%s/%s]: %s", bucket, storage_path, exc)
            return False

    def get_signed_url(
        self,
        bucket: str,
        storage_path: str,
        expires_in: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate a signed URL for a private object.
        expires_in defaults to settings.signed_url_expiry.
        """
        expiry = expires_in or self._settings.signed_url_expiry
        try:
            response = self._client.storage.from_(bucket).create_signed_url(
                storage_path, expiry
            )
            return response.get("signedURL") or response.get("signed_url")
        except Exception as exc:
            logger.error("Signed URL error [%s/%s]: %s", bucket, storage_path, exc)
            return None

    def delete_file(self, bucket: str, storage_path: str) -> bool:
        """Delete a single file from Supabase Storage."""
        try:
            self._client.storage.from_(bucket).remove([storage_path])
            logger.info("Deleted %s from bucket '%s'.", storage_path, bucket)
            return True
        except Exception as exc:
            logger.error("Storage delete error [%s/%s]: %s", bucket, storage_path, exc)
            return False

    def delete_files(self, bucket: str, paths: List[str]) -> bool:
        """Batch-delete multiple files from Supabase Storage."""
        if not paths:
            return True
        try:
            self._client.storage.from_(bucket).remove(paths)
            return True
        except Exception as exc:
            logger.error("Storage batch delete error [%s]: %s", bucket, exc)
            return False

    def download_file(self, bucket: str, storage_path: str) -> Optional[bytes]:
        """Download a file from storage and return raw bytes."""
        try:
            response = self._client.storage.from_(bucket).download(storage_path)
            return response
        except Exception as exc:
            logger.error("Storage download error [%s/%s]: %s", bucket, storage_path, exc)
            return None


# ======================================================================
# Module-level singleton accessor
# ======================================================================

_service: Optional[SupabaseService] = None


def get_supabase_service() -> SupabaseService:
    """Return (or create) the module-level SupabaseService singleton."""
    global _service
    if _service is None:
        _service = SupabaseService()
    return _service
