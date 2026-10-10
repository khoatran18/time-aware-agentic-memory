You extract the validity period of text chunks taken from one document.

Document title: {doc_title}

You will receive numbered chunks of the SAME document, in reading order. You see all of them, so you may use the other chunks to understand one chunk. For EACH chunk return one item with the same index and these fields:

- `start`: the earliest date of the facts the chunk states (events, positions held, stints, life dates).
- `end`: the date the situation stopped, or the latest date of the facts the chunk states.
- `ongoing`: true when the situation continues up to the present ("since 2010", "currently", "to date", "incumbent", "present", or a later chunk says it still continues). Then set `end` to null.

## The three states of `end`

1. Known: the situation stopped on a known date. Set `end` to that date.
2. Ongoing: it still continues. Set `end` = null and `ongoing` = true.
3. Unknown: nothing says when it stopped and nothing says it continues. Set `end` = null and `ongoing` = false. Do NOT guess, and do NOT mark it ongoing just because no end is given.

## Rules

- Format: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. Keep exactly the precision the text gives; never invent a month or a day.
- A single date that is the whole fact (a birth year, a one-day event) -> `start` and `end` are the same value. A date that only starts a situation ("joined in 2001") is NOT the whole fact: see the three states of `end`.
- Dates may come from the chunk itself, the document title, or OTHER CHUNKS OF THIS DOCUMENT. Do NOT add dates from your own knowledge or from outside the document.
- Start of a chunk without its own date: if it clearly continues the same episode as a neighbouring chunk (same stint, same job, same marriage), reuse that episode's start. If it is about something unrelated, leave it null.
- End of a situation: set `end` only when the text shows it stopped ("left", "moved to", "was replaced by", "resigned", "until", "retired", "divorced", "died"). A later event ends an earlier one only when the two cannot hold at the same time (one team, one office, one spouse at a time). Facts that can overlap (several employers, several memberships, several awards) are not ended by a later one: use state 3.
- If the situation lasted until the person's death and the document gives the death date, `end` = the death date.
- Ignore dates that do not describe the facts themselves, such as years of cited books or articles.
- Dates before year 1 (BC/BCE) -> treat as no date.
- If no date can be derived even from the other chunks, return `start` = null, `end` = null, `ongoing` = false.

## Examples

Chunk: "Sir Samuel Knox Cunningham , QC ( 3 April 1909 – 29 July 1976 ) , was a Northern Irish barrister and politician ."
-> start 1909-04-03, end 1976-07-29, ongoing false

Chunk: "He joined Rangers in July 2005 and stayed until November 2005 , when he moved to Southampton ."
-> start 2005-07, end 2005-11, ongoing false

Chunk: "She has served as chairperson of the board since 2012 , after joining the company in 2008 ."
-> start 2008, end null, ongoing true

Chunk: "Cunningham was from an Ulster family . His father was Samuel Cunningham ."
-> start null, end null, ongoing false

## Examples using the other chunks

Document title: Sam Rivera
[0] Rivera joined Rovers in 2001 and became their captain .
[1] In 2005 he moved to United , where he played until 2010 .
[2] He then signed for City in 2010 and is still at the club .
-> [0] start 2001, end 2005 (he moved away, and one player has one club at a time), ongoing false
-> [1] start 2005, end 2010, ongoing false
-> [2] start 2010, end null, ongoing true

Document title: Gary Mills
[0] In March 2004 Mills was appointed manager of Tamworth .
[1] Under his management the club reached the cup final and finished twelfth in the league .
[2] He left the club by mutual consent in January 2007 .
-> [0] start 2004-03, end 2007-01, ongoing false (the end comes from chunk 2)
-> [1] start 2004-03, end 2007-01, ongoing false (same stint as chunk 0: reuse its start, and its end)
-> [2] start 2007-01, end 2007-01, ongoing false

Document title: Pat Moore
[0] Pat Moore ( born 1920 , died 14 May 1990 ) was a mayor .
[1] Moore served as mayor of Springfield from 1962 until his death .
-> [0] start 1920, end 1990-05-14, ongoing false
-> [1] start 1962, end 1990-05-14, ongoing false (until his death; the death date comes from chunk 0)

Document title: Dr Lee
[0] Lee became a member of the Royal Society in 1990 .
[1] In 1995 she joined the Academy of Sciences as a member .
-> [0] start 1990, end null, ongoing false (nothing says the membership stopped: state 3)
-> [1] start 1995, end null, ongoing false (memberships can overlap, so chunk 1 does not end chunk 0)

Document title: Riverside FC
[0] The club plays in red shirts and its stadium holds 20,000 people .
[1] Its mascot is a lion called Leo .
-> [0] start null, end null, ongoing false
-> [1] start null, end null, ongoing false
