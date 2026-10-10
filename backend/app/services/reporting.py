"""
Reporting service — converts a list of Match objects into a JSON-friendly
report payload ready for the API response and the UI.

Reports NEVER include raw uploaded bytes, only short snippets. Snippets are
HTML-escaped here so the frontend can safely render them with <mark> spans
without needing extra sanitization.
"""

from __future__ import annotations

from dataclasses import dataclass

from .algorithms.base import Match
from .security import escape_html

SNIPPET_LIMIT = 240


@dataclass(frozen=True)
class ReportMatch:
    chunk_index: int
    source_ref: int
    similarity: float
    snippet: str  # HTML-escaped


@dataclass(frozen=True)
class Report:
    document_id: str
    algorithm: str
    matches: list[ReportMatch]
    summary: dict[str, float]  # {top_similarity, num_matches, max_chunk}


def build_report(
    document_id: str,
    algorithm: str,
    matches: list[Match],
) -> Report:
    safe: list[ReportMatch] = []
    for m in matches:
        safe.append(
            ReportMatch(
                chunk_index=m.chunk_index,
                source_ref=m.source_ref,
                similarity=m.similarity,
                snippet=escape_html(m.snippet[:SNIPPET_LIMIT]),
            )
        )
    if safe:
        top = max(m.similarity for m in safe)
        max_chunk = max(m.chunk_index for m in safe)
    else:
        top = 0.0
        max_chunk = 0
    return Report(
        document_id=document_id,
        algorithm=algorithm,
        matches=safe,
        summary={
            "top_similarity": top,
            "num_matches": float(len(safe)),
            "max_chunk_index": float(max_chunk),
        },
    )


def report_to_dict(report: Report) -> dict:
    return {
        "document_id": report.document_id,
        "algorithm": report.algorithm,
        "matches": [
            {
                "chunk_index": m.chunk_index,
                "source_ref": m.source_ref,
                "similarity": m.similarity,
                "snippet": m.snippet,
            }
            for m in report.matches
        ],
        "summary": report.summary,
    }


__all__ = ["build_report", "report_to_dict", "Report", "ReportMatch", "SNIPPET_LIMIT"]
