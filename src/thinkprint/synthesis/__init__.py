"""Synthesis module — builds the final Thinkprint from interview + seed."""

from __future__ import annotations

from .profile import (
    SynthesisResult,
    render_thinkprint_md,
    synthesize_profile,
    write_thinkprint,
)

__all__ = [
    "SynthesisResult",
    "render_thinkprint_md",
    "synthesize_profile",
    "write_thinkprint",
]
