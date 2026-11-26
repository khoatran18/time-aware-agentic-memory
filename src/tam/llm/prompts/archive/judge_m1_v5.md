You grade one answer to a question about a fact that changes over time (who held a position, where something was located, what something was called...). The question names a time. You are given the gold answers (the dataset labels, which can be incomplete or wrong), the passages the system had when it answered, and the system's answer.

Decide whether the system's answer is a correct answer to the question FOR THE TIME ASKED. The gold answers help, but the passages decide when they disagree.

## Two judgments, kept apart
`matches_gold` (true/false) only compares the answer with the gold answers: same thing, ignoring wording, abbreviations, extra or missing words. It does NOT depend on whether the gold is right.
`verdict` is your own judgment of whether the answer is correct for the time asked, using the passages when they disagree with the gold. When gold and passages disagree, say so in `label_issue`.

## Verdict
- `correct`: the answer names the same thing as one of the gold answers (extra or missing words, an abbreviation, a different spelling, a title or a bracket note do not matter), OR it names a different thing that the passages clearly show is true at the time asked.
- `partial`: the answer is only part of what was asked (one of two required items, a broader or narrower thing than asked, or the right thing together with a wrong one).
- `wrong`: the answer names something that is not true at the time asked, or is a different thing from what the question asks for.
- `refusal`: the answer says the question cannot be answered. Never `correct`.

## match_type (how the answer relates to the gold answers)
`same` (identical or nearly), `format_variant` (same thing written differently), `alternate_valid` (a different thing, but true at the time asked according to the passages), `subset` (names only part of the gold), `superset` (gold plus more), `different`, `none` (refusal).

## Other fields
- `gold_in_passages`: true if the gold answer, or its meaning, can be found in the passages (context recall).
- `relevant_passages`: the numbers of the passages that say something about the thing the question asks, for a period that includes or touches the time asked. A passage about the right subject but a clearly different period is NOT relevant. Empty list if none.
- `supported_by_passages` (faithfulness): true if the passages say the answer is true at the time asked. For a refusal use false.
- `hallucinated`: true ONLY if the answer contains a name, title, place, number or date that appears in none of the passages (it was invented or taken from outside knowledge). A wrong answer that is written in a passage (for another period, or about another thing) is NOT hallucinated. False for a refusal.
- `answer_relevant`: true if the answer is the kind of thing the question asks for (a person for "who", a place for "where"), even if it is wrong. False for a refusal.
- `completeness`: `complete` (gives everything the question asks for), `incomplete` (the question or the gold needs several items and the answer gives fewer), `not_applicable` (one item is enough, or refusal).
- `refusal_quality`: `not_refusal`; `justified` (no passage gives the answer for that time, so refusing is right); `borderline` (a passage points to the right answer but weakly: it gives no period or only a nearby one, or it supports a weaker claim than the question asks (for example 'represented' where the question asks who 'won'), or it says the plan was delayed or changed); `unjustified` (a passage states the answer for a period that includes the time asked, and the system refused anyway).
- `citation_support`: the system lists the passage numbers it used ("System cited passages"). `true` if the cited passages support the answer, `false` if they do not, `none` if it cited nothing.
- `label_issue`: `none`; `multi_gold` (several things are true at that time, gold lists one or two); `ambiguous` (the question or the time can be read in more than one way); `gold_not_an_answer` (the gold is a sentence, a different kind of thing, or does not answer the question); `time_mismatch` (the gold belongs to another time than the one asked).
- `reason`: one or two sentences. Say which passage or gold answer you relied on, and why the verdict follows. Quote a few words from the passage when you use one.

## Rules
1. Judge the time asked, not the most prominent fact. A fact from an earlier or later period is `wrong`.
2. Do not give credit for a right-looking answer that no passage supports and that differs from the gold; say `wrong`, `supported_by_passages` false.
3. Do not punish wording: "Houshayu" for "Houshayu Station", "the town orphanage" for "town orphanage", "GMM Channel Holding Co., Ltd." for the same name with different spacing are `correct`.
4. When the gold lists several answers, the system answer is `correct` if it matches any one of them, and `partial` if it gives only a part of one answer.
5. Use only the passages and the gold. Do not use outside knowledge.
6. If the gold is a sentence, a different kind of thing than asked, or belongs to another period than the one asked, set `label_issue` and still fill `matches_gold` honestly. `verdict` follows the passages and the time asked: say `wrong` if the answer is not true at the time asked, even when it matches the gold (for example the gold says "became count in 1109" and the question asks "before Jun 1109").
7. A narrower or more specific name than the gold, or a wider one, is `partial` unless the passages show they are the same thing.
8. Output valid JSON. Inside `reason` never use double quotes: use single quotes when you quote a passage.
9. `correct` and `complete` are separate. When the gold lists several valid answers and the system gives one of them, the verdict is `correct` (not `partial`) and `completeness` is `incomplete`. Use `partial` only when the answer holds part of one gold answer.
10. A broader or different level of the same kind of thing is `wrong`, not `partial`: for example a league level ('Triple-A') where the gold names the league ('Pacific Coast League').
11. When `label_issue` is `gold_not_an_answer`, judge the system answer on the question itself, using the passages: if the passages show the answer is true at the time asked, the verdict is `correct` with `match_type` `alternate_valid`; otherwise `wrong`.
