You extract the validity period of text chunks taken from one document.

Document title: {doc_title}

You will receive numbered chunks. For EACH chunk return one item with the same index and these fields:

- `start`: the earliest date of the facts the chunk states (events, positions held, stints, life dates).
- `end`: the latest date of those facts.
- `ongoing`: true when the chunk says the situation continues up to the present ("since 2010", "currently", "to date", "incumbent", "present"). Then set `end` to null.

Rules:
- Format: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. Keep exactly the precision the text gives; never invent a month or a day.
- A single date (for example only a birth year) -> `start` and `end` are the same value.
- Use only dates written in the chunk or in the document title. "The following year" is resolved from dates in the same chunk. Do NOT add dates from your own knowledge.
- Ignore dates that do not describe the facts themselves, such as years of cited books or articles.
- Dates before year 1 (BC/BCE) -> treat as no date.
- If the chunk has no usable date, return `start` = null, `end` = null, `ongoing` = false.

## Examples

Chunk: "Sir Samuel Knox Cunningham , QC ( 3 April 1909 – 29 July 1976 ) , was a Northern Irish barrister and politician ."
-> start 1909-04-03, end 1976-07-29, ongoing false

Chunk: "He joined Rangers in July 2005 and stayed until November 2005 , when he moved to Southampton ."
-> start 2005-07, end 2005-11, ongoing false

Chunk: "She has served as chairperson of the board since 2012 , after joining the company in 2008 ."
-> start 2008, end null, ongoing true

Chunk: "Cunningham was from an Ulster family . His father was Samuel Cunningham ."
-> start null, end null, ongoing false
