package copyright_test

import rego.v1
import data.copyright

test_no_context_escalates if {
  result := copyright.decision with input as {"contexts": [], "signals": {"max_exact_span_words": 0, "max_ngram_overlap": 0, "max_minhash_similarity": 0, "answer_words": 0}}
  result.decision == "ESCALATE"
}

test_exact_copy_rewrites if {
  result := copyright.decision with input as {"contexts": [{"quote_word_limit": 20, "attribution_required": false}], "signals": {"max_exact_span_words": 30, "max_ngram_overlap": 0.1, "max_minhash_similarity": 0.1, "answer_words": 40}}
  result.decision == "REWRITE"
  result.reason == "EXACT_SPAN_LIMIT"
}

test_attribution if {
  result := copyright.decision with input as {"contexts": [{"quote_word_limit": 20, "attribution_required": true}], "signals": {"max_exact_span_words": 5, "max_ngram_overlap": 0.1, "max_minhash_similarity": 0.1, "answer_words": 10}}
  result.decision == "ALLOW_WITH_ATTRIBUTION"
}
