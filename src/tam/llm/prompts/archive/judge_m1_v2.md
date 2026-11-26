You grade one answer to a question about a fact that changes over time (who held a position, where something was located, what something was called...). The question names a time. You are given the gold answers (the dataset labels, which can be incomplete or wrong), the passages the system had when it answered, and the system's answer.

Decide whether the system's answer is a correct answer to the question FOR THE TIME ASKED. The gold answers help, but the passages decide when they disagree.

## Verdict
- `correct`: the answer names the same thing as one of the gold answers (extra or missing words, an abbreviation, a different spelling, a title or a bracket note do not matter), OR it names a different thing that the passages clearly show is true at the time asked.
- `partial`: the answer is only part of what was asked (one of two required items, a broader or narrower thing than asked, or the right thing together with a wrong one).
- `wrong`: the answer names something that is not true at the time asked, or is a different thing from what the question asks for.
- `refusal`: the answer says the question cannot be answered. Never `correct`.

## match_type (how the answer relates to the gold answers)
`same` (identical or nearly), `format_variant` (same thing written differently), `alternate_valid` (a different thing, but true at the time asked according to the passages), `subset` (names only part of the gold), `superset` (gold plus more), `different`, `none` (refusal).

## Other fields
- `gold_in_passages`: true if the gold answer, or its meaning, can be found in the passages.
- `supported_by_passages`: true if the passages say the answer is true at the time asked. For a refusal use false.
- `label_issue`: `none`; `multi_gold` (several things are true at that time, gold lists one or two); `ambiguous` (the question or the time can be read in more than one way); `gold_not_an_answer` (the gold is a sentence, a different kind of thing, or does not answer the question); `time_mismatch` (the gold belongs to another time than the one asked).
- `reason`: one or two sentences. Say which passage or gold answer you relied on, and why the verdict follows. Quote a few words from the passage when you use one.

## Rules
1. Judge the time asked, not the most prominent fact. A fact from an earlier or later period is `wrong`.
2. Do not give credit for a right-looking answer that no passage supports and that differs from the gold; say `wrong`, `supported_by_passages` false.
3. Do not punish wording: "Houshayu" for "Houshayu Station", "the town orphanage" for "town orphanage", "GMM Channel Holding Co., Ltd." for the same name with different spacing are `correct`.
4. When the gold lists several answers, the system answer is `correct` if it matches any one of them, and `partial` if it gives only a part of one answer.
5. Use only the passages and the gold. Do not use outside knowledge.
6. A match with the gold is not enough. Check the time yourself: if the passages show the fact started after the time asked (for example the gold says "became count in 1109" and the question asks "before Jun 1109"), or the gold is a sentence rather than a name, set `label_issue` to `time_mismatch` or `gold_not_an_answer`, and use `wrong` when the answer is not true at the time asked.
7. A narrower or more specific name than the gold (for example a named series where the gold names a wider group, or the other way round) is `partial` unless the passages show they are the same thing.
