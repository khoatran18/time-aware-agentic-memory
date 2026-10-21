You extract the validity period of text chunks taken from one document.

Document title: {doc_title}

You will receive numbered chunks of the SAME document, in reading order. You see all of them, so you may use the other chunks to understand one chunk. For EACH chunk return one item with the same index and these fields:

- `start`: the earliest date among the facts the chunk states (events, positions held, stints, life dates, and every dated entry of a list).
- `reason_domain`: ONE short sentence naming the words or facts in the chunk that make you choose these labels. Write it before `domain`.
- `domain`: 0 to 3 topic labels for what the chunk is about, dominant topic first, ONLY from this closed list (add a second or third label only if the chunk really covers that topic; a chunk with no real content, such as a citation line, gets an empty list):
{domains}
- `reason_end_date`: ONE short sentence saying why `end` and `ongoing` get the values you return: quote the words that show the situation stopped ("left in 2007"), continues ("since 2010"), or say that nothing tells either way. Name the chunk if the evidence comes from another one. Write it first, then set `end` and `ongoing` to agree with it: if the sentence says nothing tells whether it stopped, `end` must be null; if it names a later date that the chunk's facts reach, `end` must be that date
- `end`: see "What `end` means" below.
- `ongoing_evidence`: ONLY when `ongoing` is true: copy, word for word, the phrase from the chunks that shows the situation still continues ("since 2012", "is still at the club", "to date"). It must appear exactly in the text above. It may come from another chunk of this document, but only if that chunk is about the SAME fact or episode as this one. If you cannot copy such a phrase, `ongoing` is false and this field is empty.
- `ongoing`: true ONLY when the text itself says the situation continues up to the present ("since 2010", "currently", "to date", "incumbent", "present", "still", or a later chunk says it still continues). A missing end date is NOT evidence of continuing. Then set `end` to null.

## What `end` means: decide in this order

1. Is every fact in the chunk a ONE-OFF fact? One-off facts happen at one moment and do not "continue": a birth, a death, an award or title received, a publication or release of a work, a single match, battle or ceremony, an election day. Then `start` and `end` are the same value.
2. Does the chunk state a date RANGE or SEVERAL dated facts? This covers lists (office holders, hosts, honours, commanders) and also ordinary history or season-by-season narrative that mentions two or more dates. A range written in the text ("1963–64", "from 1990 to 1994", "the 2012–13 season", "2012–2017") states its own end: use it. Then `start` is the earliest date mentioned for the chunk's facts and `end` is the latest date or range end mentioned for them (a known end, never null while the chunk itself shows later dates). If the last entry is open ("2019 – present"), use the ongoing rules below. Two cases:
   - The dated facts are separate periods: seasons, years of a history, entries of a list. Use only the dates inside this chunk. A story that merely goes on in the next chunk does NOT extend this chunk: the next chunk is another period, not the same fact.
   - The dated facts are parts of ONE episode that is still running in this chunk (one stint, one job, one marriage, one stay in a place) and another chunk says it ended. Then `end` is that later end date, as in the examples with several chunks below.
3. Does the chunk introduce the subject of the document (usually the first chunk: "X ( born 1961 ) is a ...", "X was founded in 1950 ...")? It covers the subject's whole life or existence. `start` is the birth or founding date. `end` is the death or dissolution date if ANY chunk of the document gives it; otherwise state 3. Never turn a birth or founding date into a one-day validity: it is NOT a one-off fact when the chunk is about the person or thing as a whole.
4. Otherwise the chunk gives ONE date (or one range start) that begins a situation, such as an appointment or a move (see how to tell, below). Then use one of the three states:
   - Known: the situation stopped on a known date. Set `end` to that date.
   - Ongoing: it still continues. Set `end` = null and `ongoing` = true.
   - Unknown: nothing says when it stopped and nothing says it continues. Set `end` = null, `ongoing` = false and `ongoing_evidence` empty. Do NOT guess, and do NOT mark it ongoing just because no end is given or because the thing probably still exists today. Do NOT copy the start date into `end`. Choose it whenever you cannot copy a continuation phrase.

How to tell a one-off fact from one that opens a situation: ask whether it is still true the next day. A birth or an award received is finished at once. But when something is appointed, set up, entered or started, the date only BEGINS a situation that lasts until something ends it. Judge by meaning, not by the verb; these are examples, not a complete list:
- "was appointed head coach on 3 March 1996": the stint lasts until he leaves or is replaced.
- "moved to a city in 1962": he lives there until he moves away.
- "the company opened a factory in 1980": it runs until it is closed.
- "she married in 1990": the marriage lasts until a divorce or a death.
- "the bridge was opened to traffic in 1932": it stays open until closed.
In each case nothing ends the situation until the text (this chunk or another) says so, so `end` is NOT the date of the verb.

## Rules

- Format: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. Keep exactly the precision the text gives; never invent a month or a day.
- Dates may come from the chunk itself, the document title, or OTHER CHUNKS OF THIS DOCUMENT. Do NOT add dates from your own knowledge or from outside the document.
- Start of a chunk without its own date: if it clearly continues the same episode as a neighbouring chunk (same stint, same job, same marriage), reuse that episode's start. If it is about something unrelated, leave it null.
- End of a situation: set `end` only when the text shows it stopped ("left", "moved to", "was replaced by", "resigned", "until", "retired", "divorced", "dissolved", "died"). A later event ends an earlier one only when the two cannot hold at the same time (one team, one office, one spouse at a time). Facts that can overlap (several employers, several memberships, several awards) are not ended by a later one: use state 3.
- If the situation lasted until the person's death and the document gives the death date, `end` = the death date.
- Ignore dates that do not describe the facts themselves, such as years of cited books or articles.
- Dates before year 1 (BC/BCE) -> treat as no date.
- If no date can be derived even from the other chunks, return `start` = null, `end` = null, `ongoing` = false.

## Examples

Chunk: "Sir Samuel Knox Cunningham , QC ( 3 April 1909 – 29 July 1976 ) , was a Northern Irish barrister and politician ."
-> start 1909-04-03, end 1976-07-29, ongoing false (introduces the person, both life dates given)

Chunk: "He joined Rangers in July 2005 and stayed until November 2005 , when he moved to Southampton ."
-> start 2005-07, end 2005-11, ongoing false

Chunk: "She has served as chairperson of the board since 2012 , after joining the company in 2008 ."
-> start 2008, end null, ongoing true

Chunk: "Cunningham was from an Ulster family . His father was Samuel Cunningham ."
-> start null, end null, ongoing false

Chunk: "The Harbor Prize was awarded to her in 2001 ."
-> start 2001, end 2001, ongoing false (a one-off fact)

Chunk: "The club won the league in 1988–89 and reached the cup final in 1990 ."
-> start 1988, end 1990, ongoing false (several dates and a range: earliest and latest; the story goes on in the next chunk but this chunk's own facts end in 1990)

Chunks of one document (a team history): [0] "In 1991–92 the team won the league ." [1] "In 1996 it moved to a new stadium ." -> [0] start 1991, end 1992 (a separate season: chunk 1 is another period and does not extend chunk 0)

Chunks of one document (a town's history): [0] "The town grew quickly between 1850 and 1870 ." [1] "A fire destroyed the centre in 1881 ." -> [0] start 1850, end 1870 (its own range; the fire in chunk 1 is another period), [1] start 1881, end 1881

Chunks of one document (a stint): [0] "Tobias Reed was appointed director in 2004 and opened two branches in 2005 ." [1] "He resigned in March 2009 ." -> [0] start 2004, end 2009-03 (one stint; chunk 1 says it ended), [1] start 2009-03, end 2009-03

Chunks of one document (a marriage): [0] "Ines Costa married Paul Ward in 1988 , and their daughter was born in 1990 ." [1] "The couple divorced in 1997 ." -> [0] start 1988, end 1997 (one marriage that was still running; chunk 1 says it ended), [1] start 1997, end 1997

Chunk: "Mara Voss was appointed head coach of the Lakeside Lions on 3 March 1996 and signed three new players ."
-> start 1996-03-03, end null, ongoing false (an opening verb starts a stint; nothing says it ended: state 3, so `end` is NOT 1996-03-03)

Chunk: "Directors of the institute : - Ana Pires , 1991–1997 - Tomas Weil , 1997–2004 - Lena Ortiz , 2004–2011 ."
-> start 1991, end 2011, ongoing false (a list: earliest and latest date of any entry)

Chunk: "Rosa Almeida ( born 9 May 1971 ) is a novelist and teacher ." (no death date anywhere in the document)
-> start 1971-05-09, end null, ongoing false (introduces the person, whole life, no end known: state 3, so `end` is NOT the birth date)

Chunk: "Delta Freight was founded in 1982 as a regional trucking company ." (another chunk says "the company was dissolved in 1999")
-> start 1982, end 1999, ongoing false (the end comes from the other chunk)

## Examples using the other chunks

The text in parentheses is the kind of sentence to put in `reason_end_date`.

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

Document title: Elena Marsh
[0] Marsh moved to Lisbon in 1958 and worked there as a translator .
[1] She taught part time at a language school in 1962 .
[2] In 1974 she moved to Madrid , where she lived until her death .
-> [0] start 1958, end 1974, ongoing false (a person lives in one city at a time, so 'moved to Madrid' in chunk 2 ends the Lisbon stay; the end comes from chunk 2)
-> [1] start 1962, end 1962, ongoing false (a single dated stint of teaching, one-off)
-> [2] start 1974, end null, ongoing false (nothing gives a death date, so state 3)

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

## Output format

Return one item per chunk, in this JSON shape (`domain` is a list of 0 to 3 labels):

```json
{"items": [
  {"index": 0, "start": "2001",
   "reason_domain": "Mentions captain and club, so it is about sport.", "domain": ["sports"],
   "reason_end_date": "'moved to United' in chunk 1 ends the Rovers stint (one club at a time).",
   "ongoing_evidence": "", "end": "2005", "ongoing": false},
  {"index": 1, "start": "2012",
   "reason_domain": "Company and political office are both named.", "domain": ["business", "politics"],
   "reason_end_date": "'since 2012' with no end date, so it still continues.",
   "ongoing_evidence": "since 2012", "end": null, "ongoing": true},
  {"index": 2, "start": "2003",
   "reason_domain": "Only a family event is described.", "domain": ["person"],
   "reason_end_date": "'Moved to the city in 2003' opens a situation; nothing says whether it stopped or continues.",
   "ongoing_evidence": "", "end": null, "ongoing": false},
  {"index": 3, "start": null,
   "reason_domain": "A citation line with no real content.", "domain": [],
   "reason_end_date": "No date anywhere in the document for this fact.",
   "ongoing_evidence": "", "end": null, "ongoing": false}
]}
```

## Examples of assigning `domain` (invented chunks, only to show the judgement)

- "He scored 12 goals for the club in the 2004 season." -> `["sports"]`
- "She was elected to the national assembly in 1998 as a member of the Green Party." -> `["politics"]`
- "He studied law at a university and then worked for a firm in the city for six years." -> `["career"]`
- "He married a nurse in 1985 and they had two children; the family lived in a village near the coast." -> `["person"]`
- "The company was founded in 1950, is owned by a holding group and is headed by a new chief executive." -> `["business"]`
- "He served as a captain in the army, commanding an infantry battalion, and later entered parliament." -> `["military", "politics"]` (dominant topic first)
- "The bridge crosses the river and connects the two districts; it opened in 1932." -> `["place"]`
- "The band signed to a record label and released its first album, which was broadcast on national radio." -> `["media_arts"]`
- "References: Smith, J. (2001). A History of the Region. Oxford Press." -> `[]` (citation line, no real content)
- A chunk about an event that fits none of the labels, for example a lawsuit over an unrelated matter -> `["other"]`
- A chunk that mentions a team only in passing while mostly describing family life -> `["person"]`, not `sports`: label what the chunk is mainly about.
