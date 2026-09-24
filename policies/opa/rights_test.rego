package rights_test

import rego.v1
import data.rights

test_approved_ingest if {
  result := rights.decision with input as {"action":"ingest","source":{"status":"approved","rag_allowed":true,"generation_allowed":true}}
  result.allow == true
}

test_revoked_denied if {
  result := rights.decision with input as {"action":"retrieve","source":{"status":"revoked","rag_allowed":true,"generation_allowed":true}}
  result.allow == false
}
