You answer a question about one subject using ONLY a dated timeline. Each line is "[id] date | text".
Return in `selected_ids` the ids of the timeline events that answer the question:
- a question asking to list or summarize: every event needed, in chronological order;
- a question asking which event came first, last or next: that single event (or all events sharing the same date if the question allows it);
- a question asking how many years (or months, days) passed between two events: the two events, in order.
Use only ids that appear in the timeline. Do not invent events. Answer only with the schema.