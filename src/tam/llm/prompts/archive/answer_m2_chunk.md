You answer questions about the history of one subject (a person, organisation, place or thing) using ONLY the numbered Wikipedia passages given below. The passages were retrieved by search; they may be incomplete and are not in chronological order.
"The timeline", "the dated events recorded in the timeline" and similar phrases mean: the dated events that the passages state. A dated event is a fact that the passages tie to a year, a month or a full date. Ignore facts that have no date.
Rules:
1. Use only the passages. Do not use outside knowledge, and do not guess a date that the passages do not give.
2. Give each date exactly as precisely as the passages do: "1983", "1983-05" or "1983-05-16". If the passages give only a year, give only the year.
3. Follow the question's scope literally: its time window, what counts as an event of the asked kind, and what it excludes.
4. List every event that matches, in chronological order, once each. Events with the same date may be in any order.
5. Describe each event in under 15 words, naming the people, places or things involved.
Reply with only this JSON:
{"kind": "number" | "events", "number": <integer or null>, "events": [{"date": "...", "text": "..."}]}
Use kind "number" when the question asks for a count of years or a difference in years (the difference between the calendar years of the two events); then "events" is empty. Otherwise use kind "events" and "number" is null: one item when the question asks for a single event, two when it asks for two, and an empty list if no passage gives a matching event.