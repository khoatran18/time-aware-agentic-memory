"""Tóm tắt hiệu năng LLM từ llm_calls.jsonl của một lần chạy.

Chạy: python3 scripts/llm_stats.py output/<YYYYMMDD_HHMMSS>/llm_calls.jsonl   (hoặc file đặt bằng TAM_LLM_METRICS_FILE)
In JSON: p50/p90/p99 của E2E (từng lần gọi và từng lần invoke_structured), tokens/s, TTFT/TPOT (nếu có dòng `stream`),
throughput, RPM/TPM trung bình và đỉnh (cửa sổ 60 giây), số lỗi theo mã HTTP, số lần thử lại, số cache hit.
"""
import json
import sys
from pathlib import Path

from tam.llm.metrics import summarize

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(json.dumps(summarize(Path(sys.argv[1])), ensure_ascii=False, indent=2))
