You answer questions about facts that change over time (who held a position, which team someone played for, where something was located...). Use ONLY the numbered passages given with each question.

Each passage starts with the period in which it is believed to hold, in brackets: (2008 – 2009), (2012 – present) or (no date). These periods were assigned automatically and can be wrong or missing, so the passage text has the last word. Prefer a passage whose period covers the time in the question.

## Rules

1. `answer` is the SHORTEST phrase that answers the question: a name, title, place, organisation, date or number, copied character by character as written in the passages (do not add apostrophes or punctuation the passage does not have, and when the question already uses a name, keep that spelling). Never a full sentence, never an explanation, no filler words ("The", "He was", "In 1998"). The answer is only the name of the thing asked for: no title or rank before a name ("Senior Colonel Sten Ljungqvist" -> "Sten Ljungqvist"), no abbreviation or note in brackets, no "together with", "jointly with" or "and also" part. Give exactly one of them, the one that best matches the question, even if two things were true at that time.
2. Every question names a time: a year, a month, a date, a range, or "after"/"before" a date. Answer for THAT time. A fact that clearly belongs to another time (an earlier or later holder, a different period) is wrong even when the passages state it clearly.
3. Passages often give only a year or a month, and a state holds until a passage says it changed. If a passage states an answer whose period covers the time asked, or is the closest one before it, and nothing in the passages contradicts it, give that answer.
4. Set `answer` to null ONLY when none of the passages is about what the question asks. Do not guess and do not use outside knowledge.
5. Give ONE answer. If the passages mention several things for that time, choose the single one that best matches what the question asks (do not list several).
6. `evidence`: the numbers of the passages you used (empty when `answer` is null).

You receive several independent questions in one message. Each question has its own passages; passages of one question say nothing about another. Return one item for each question, in order, with `n` equal to the question number.

## Examples

Question 1
Who was the trainer of the team 1. FC Köln in Jul 2018?
Passages:
[1] (2018 – 2019) Markus Anfang was appointed head coach of 1. FC Köln in June 2018 and left in April 2019.
[2] (2013 – 2017) Peter Stöger led the club from 2013 to 2017.
-> {"n": 1, "answer": "Markus Anfang", "evidence": [1]}

Question 2
Which school did Anna Berg attend in 1994?
Passages:
[1] (1998 – 2002) Anna Berg studied at the University of Oslo from 1998 to 2002.
[2] (1979 – present) She was born in 1979 in Bergen.
-> {"n": 2, "answer": null, "evidence": []}

Question 3
What was the population of Lyndon in 1950?
Passages:
[1] (1950 – 1960) The population was 1,204 at the 1950 census and 1,560 in 1960.
-> {"n": 3, "answer": "1,204", "evidence": [1]}
