from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from src.config import settings


def write_worm_event(payload: dict) -> None:
    if not settings.audit_s3_bucket:
        if settings.audit_worm_required:
            raise RuntimeError("AUDIT_WORM_REQUIRED=true but AUDIT_S3_BUCKET is not configured")
        return
    try:
        import boto3
        s3=boto3.client("s3")
        key=f"{settings.audit_s3_prefix.rstrip('/')}/{payload['tenant_id']}/{payload['event_hash']}.json"
        kwargs={
            "Bucket":settings.audit_s3_bucket,
            "Key":key,
            "Body":json.dumps(payload,sort_keys=True,separators=(",",":")).encode(),
            "ContentType":"application/json",
        }
        if settings.audit_retention_days > 0:
            kwargs["ObjectLockMode"]="COMPLIANCE"
            kwargs["ObjectLockRetainUntilDate"]=datetime.now(timezone.utc)+timedelta(days=settings.audit_retention_days)
        s3.put_object(**kwargs)
    except Exception:
        if settings.audit_worm_required:
            raise
