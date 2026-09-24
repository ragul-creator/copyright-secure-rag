from pathlib import Path
from src.models import SourceRegistration
from src.security.licenses import register_source
from src.services.ingestion import ingest_document

base=Path(__file__).resolve().parents[1]
tenant="default"
for sid,name,file in [
 ("SRC-REFUND","Refund Policy","refund_policy.txt"),
 ("SRC-SHIPPING","Shipping Policy","shipping_policy.txt")]:
    register_source(tenant,SourceRegistration(source_id=sid,name=name,rights_holder="Example Corp",
      license_spdx="LicenseRef-ExampleCorp-Internal",rag_allowed=True,generation_allowed=True,
      attribution_required=False,quote_word_limit=22,status="approved"))
    ingest_document(tenant,sid,"DOC-"+sid.split("-")[-1],(base/"sample_data"/file).read_text())
print("Demo sources registered and ingested for tenant 'default'.")
