from __future__ import annotations
import json, uuid
from src.services.db import query

sources=query("SELECT source_id,name,rights_holder,license_spdx,status,sha256 FROM sources")
components=[]
for s in sources:
    components.append({
      "type":"data","bom-ref":f"source:{s['source_id']}","name":s["name"],"version":"1",
      "licenses":[{"license":{"id":s["license_spdx"]}}] if not s["license_spdx"].startswith("LicenseRef-") else [{"expression":s["license_spdx"]}],
      "properties":[
        {"name":"ai.source_id","value":s["source_id"]},
        {"name":"ai.rights_holder","value":s["rights_holder"]},
        {"name":"ai.approval_status","value":s["status"]}
      ]
    })
bom={"bomFormat":"CycloneDX","specVersion":"1.6","serialNumber":f"urn:uuid:{uuid.uuid4()}","version":1,"components":components}
print(json.dumps(bom,indent=2))
