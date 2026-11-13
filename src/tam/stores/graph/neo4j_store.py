"""Neo4jStore: graph sự kiện của Cơ chế 2 (docs/decisions/10). File duy nhất biết cú pháp Cypher.

Mô hình: (:Page)-[:HAS_CELL]->(:Cell {page, track})<-[:IN_CELL]-(:Event {node_id, date, ...})-[:FROM_CHUNK]->(:Chunk {chunk_id}).
Ô = (trang, track). Cạnh TIẾP_THEO không lưu: dựng lúc truy vấn bằng cách sắp Event của ô theo date (và phase).
Chunk là con trỏ sang VectorDB (Boomerang): chunk_id trùng payload `chunk_id` trong Qdrant.
"""
from __future__ import annotations

from typing import Any

from neo4j import GraphDatabase


class Neo4jStore:
    def __init__(self, driver) -> None:
        self._d = driver

    @classmethod
    def from_config(cls, cfg) -> Neo4jStore:
        g = cfg.graph_store
        return cls(GraphDatabase.driver(g.url, auth=(g.user, g.password)))

    def close(self) -> None:
        self._d.close()

    def _run(self, q: str, **p: Any) -> list[dict]:
        with self._d.session() as s:
            return [dict(r) for r in s.run(q, **p)]

    def ensure_schema(self) -> None:
        for q in (
            "CREATE CONSTRAINT ev_id IF NOT EXISTS FOR (e:Event) REQUIRE e.node_id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
            "CREATE CONSTRAINT page_id IF NOT EXISTS FOR (p:Page) REQUIRE p.page IS UNIQUE",
            "CREATE INDEX cell_key IF NOT EXISTS FOR (c:Cell) ON (c.key)",
            "CREATE INDEX ev_date IF NOT EXISTS FOR (e:Event) ON (e.date)",
        ):
            self._run(q)

    def clear_page(self, page: str) -> None:
        self._run("MATCH (e:Event {page:$p}) DETACH DELETE e", p=page)
        self._run("MATCH (c:Cell {page:$p}) DETACH DELETE c", p=page)

    def upsert_page(self, page: str, nodes: list[dict]) -> int:
        """Ghi lại toàn bộ nút của một trang (xóa cũ trước); trả số nút."""
        self.clear_page(page)
        self._run("MERGE (:Page {page:$p})", p=page)
        rows = [{**n, "key": f"{page}|{n['track']}", "merged_from": len(n.get("merged_from", [])), "flags": ",".join(n.get("flags", []))} for n in nodes]
        self._run(
            """
            UNWIND $rows AS r
            MATCH (p:Page {page: r.page})
            MERGE (c:Cell {key: r.key}) ON CREATE SET c.page = r.page, c.track = r.track
            MERGE (p)-[:HAS_CELL]->(c)
            CREATE (e:Event {node_id: r.node_id, page: r.page, track: r.track, date: r.date, phase: r.phase, kind: r.kind,
                             subject: r.subject, object: r.object, text: r.text, quote: r.quote, tier: r.tier,
                             is_lead: r.is_lead, approximate: r.approximate, flags: r.flags, merged: r.merged_from})
            CREATE (e)-[:IN_CELL]->(c)
            WITH e, r
            UNWIND r.cids AS cid
            MERGE (k:Chunk {chunk_id: cid})
            MERGE (e)-[:FROM_CHUNK]->(k)
            """,
            rows=rows,
        )
        return len(nodes)

    def count(self) -> dict[str, int]:
        return {r["l"]: r["n"] for r in self._run("MATCH (n) UNWIND labels(n) AS l RETURN l, count(*) AS n")}

    # ---- truy vấn ----
    def events_of_chunks(self, chunk_ids: list[str]) -> list[dict]:
        """Chunk -> nút (tra ngược qua :FROM_CHUNK)."""
        return self._run(
            "MATCH (e:Event)-[:FROM_CHUNK]->(c:Chunk) WHERE c.chunk_id IN $ids "
            "RETURN DISTINCT e.node_id AS node_id, e.page AS page, e.track AS track", ids=chunk_ids)

    def cell_events(self, page: str, tracks: list[str] | None = None, date_from: str | None = None, date_to: str | None = None,
                    max_tier: int = 2) -> list[dict]:
        """Đi dọc các ô của trang theo thời gian (TIẾP_THEO = thứ tự date); lọc track, khoảng năm, tier."""
        q = ("MATCH (e:Event {page:$p})-[:IN_CELL]->(c:Cell) WHERE e.tier <= $t "
             "AND ($tracks IS NULL OR e.track IN $tracks) AND ($f IS NULL OR substring(e.date,0,4) >= $f) AND ($to IS NULL OR substring(e.date,0,4) <= $to) "
             "OPTIONAL MATCH (e)-[:FROM_CHUNK]->(k:Chunk) "
             "RETURN e.node_id AS node_id, e.date AS date, e.phase AS phase, e.track AS track, e.kind AS kind, e.subject AS subject, "
             "e.tier AS tier, e.text AS text, e.quote AS quote, collect(k.chunk_id) AS cids ORDER BY e.date, e.phase")
        return self._run(q, p=page, tracks=tracks, f=date_from, to=date_to, t=max_tier)
