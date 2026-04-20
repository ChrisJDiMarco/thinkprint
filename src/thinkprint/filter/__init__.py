"""Filters strip noise and flag injection candidates before archaeology."""

from thinkprint.filter.injection import flag_injection_candidates
from thinkprint.filter.noise import is_noise, strip_noise

__all__ = ["is_noise", "strip_noise", "flag_injection_candidates"]
