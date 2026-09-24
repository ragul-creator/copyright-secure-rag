from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
import jwt
from src.config import settings

p=argparse.ArgumentParser()
p.add_argument("--sub",default="developer")
p.add_argument("--tenant",default="default")
p.add_argument("--roles",default="admin,knowledge_manager,support,viewer")
p.add_argument("--hours",type=int,default=8)
a=p.parse_args()
now=datetime.now(timezone.utc)
payload={"sub":a.sub,"tenant_id":a.tenant,"roles":[x.strip() for x in a.roles.split(",") if x.strip()],
         "iss":settings.jwt_issuer,"aud":settings.jwt_audience,"iat":now,"exp":now+timedelta(hours=a.hours)}
print(jwt.encode(payload,settings.jwt_secret,algorithm="HS256"))
