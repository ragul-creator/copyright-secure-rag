from __future__ import annotations
import argparse
import json
import uuid
from src.services.db import query

p=argparse.ArgumentParser()
p.add_argument("--tenant",default="default")
a=p.parse_args()
sources=query("SELECT source_id,name,rights_holder,license_spdx,status,sha256 FROM sources WHERE tenant_id=?",(a.tenant,))
components=[]
for s in sources:
    licenses=[{"expression":s["license_spdx"]}] if s["license_spdx"].startswith("LicenseRef-") else [{"license":{"id":s["license_spdx"]}}]
    components.append({"type":"data","bom-ref":f"source:{a.tenant}:{s['source_id']}","name":s["name"],"version":"1",
      "licenses":licenses,"properties":[
        {"name":"ai.tenant_id","value":a.tenant},
        {"name":"ai.source_id","value":s["source_id"]},
        {"name":"ai.rights_holder","value":s["rights_holder"]},
        {"name":"ai.approval_status","value":s["status"]}
      ]})
bom={"bomFormat":"CycloneDX","specVersion":"1.6","serialNumber":f"urn:uuid:{uuid.uuid4()}","version":1,"components":components}
print(json.dumps(bom,indent=2))
