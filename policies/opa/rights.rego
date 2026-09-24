package rights

import rego.v1

default decision := {"allow": false, "reason": "DEFAULT_DENY"}

decision := {"allow": true, "reason": "APPROVED"} if {
  input.source.status == "approved"
  action_allowed
}

action_allowed if {
  input.action == "ingest"
  input.source.rag_allowed == true
}
action_allowed if {
  input.action == "retrieve"
  input.source.rag_allowed == true
}
action_allowed if {
  input.action == "generate"
  input.source.generation_allowed == true
}
