You update a knowledge graph of dated events after ONE chunk of a Wikipedia page was revised.

Page title: {title}
Section: {section}

You receive:
1. The revised chunk, as OLD text and NEW text. The NEW text is the truth now.
2. The other chunks of the same window, marked "(context only)". Use them only to understand the text; never change anything because of them.
3. The EXISTING NODES: events already stored for this page, taken from the old text. Each node has an id (N1, N2, ...), `date`, `phase`, `track`, `kind`, `text`, `quote`, and `chunks` (the chunk numbers it comes from; "revised" marks the revised chunk). Nodes that come from a chunk other than the revised one are shown only so you can see the timeline around the change.

Compare OLD and NEW first. Find what the NEW text says differently. Then decide, for each existing node that the change touches:
- keep: the node is still correct. Do NOT list it. Most nodes are kept. This includes a node whose wording differs from the NEW text but whose dates, numbers, names, places and organisations are all the same: a paraphrase changes nothing, leave it.
- `close`: the NEW text says the state, role, name or relationship in the node WAS true but has ended. Give `end_date` (the date the NEW text gives for the end). The node stays true for the past.
- `invalidate`: the NEW text states a different value for the same fact (another year, date, name, number or person), so the node's claim was wrong from the start. Do not use `close` for this: invalidate the node and put the corrected event in `add`. Changing even one date, number, name, place or organisation (a network, a person, a street) is an `invalidate` plus an `add`.
- `add` (in `add`, not in `changes`): an event the NEW text states that no existing node covers: the corrected event after an `invalidate`, the end event after a `close`, or any new dated event. Use the same fields as in extraction (below).

Rules:
- Use only the NEW text for new facts. Do NOT add dates, numbers or facts from your own knowledge. Every number in a `text` must appear in the NEW text.
- Only touch nodes that the OLD to NEW difference concerns. If the difference is only wording and no node is affected, return empty lists.
- A node that comes from several chunks (`chunks` lists more than one) is still true if another chunk supports it: do not invalidate or close it unless the NEW text itself contradicts it.
- `evidence`: a verbatim excerpt (under 25 words) copied exactly from the NEW text that supports your decision. Required for every change and every `add`.
- After you have handled the existing nodes, read the NEW text once more. Every dated event that the NEW text states and that no existing node covers goes in `add`, even when no existing node is affected (for example a changed name or value inside a sentence that has no node yet).
- `phase` of an `add` item: use "end" when the event is an ending (resigned, left, ended, was fired, was succeeded, "until <date>", the last year of "from X to Y"); "start" for the beginning of a period; "point" otherwise.
- One decision per node. Never both `close` and `invalidate` the same node.

Fields of an `add` item (same as extraction): `text` (one short sentence, only words and numbers from the NEW text), `date_text` (the time expression exactly as written, or null), `date` (`YYYY`, `YYYY-MM` or `YYYY-MM-DD` with exactly the precision the text gives, never invented; null if no year can be found), `approximate`, `track` (role | affiliation | location | ownership_structure | work | naming | family | education | other), `phase` ("start" | "end" | "point"; a period is two items; an event where something ended or was replaced at a date, such as "until 1954" or "was succeeded by", is an "end" item), `kind` (change | occurrence | state | result | statement), `subject` (self | part_of_self | other), `object` (main named thing copied from the text, or null), `quote` (verbatim excerpt under 25 words from the NEW text; must contain `date_text` when it is not null).
