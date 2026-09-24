package copyright

import rego.v1

default decision := {"decision":"BLOCK","reason":"DEFAULT_DENY"}

decision := {"decision":"ESCALATE","reason":"NO_APPROVED_CONTEXT"} if {
  count(input.contexts) == 0
} else := {"decision":"REWRITE","reason":"EXACT_SPAN_LIMIT"} if {
  some c in input.contexts
  input.signals.max_exact_span_words > c.quote_word_limit
} else := {"decision":"REWRITE","reason":"NGRAM_OVERLAP"} if {
  input.signals.max_ngram_overlap >= 0.55
} else := {"decision":"REWRITE","reason":"MINHASH_NEAR_COPY"} if {
  input.signals.max_minhash_similarity >= 0.70
  some c in input.contexts
  input.signals.answer_words > c.quote_word_limit
} else := {"decision":"ALLOW_WITH_ATTRIBUTION","reason":"ATTRIBUTION_REQUIRED"} if {
  some c in input.contexts
  c.attribution_required == true
} else := {"decision":"ALLOW","reason":"WITHIN_POLICY"} if {
  count(input.contexts) > 0
}
