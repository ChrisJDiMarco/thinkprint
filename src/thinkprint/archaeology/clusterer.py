"""Topic clustering using TF-IDF + KMeans.

The spec calls for embedding-based clustering. For the MVP we deliberately use TF-IDF
to avoid the torch/sentence-transformers dependency — installs in seconds instead of
minutes, and works well enough on chat history where vocabulary signal is strong.
Swappable later for sentence-transformers without changing the public API.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from thinkprint.models import Cluster, Message

_STOPWORDS_EXTRA = frozenset(
    {"like", "just", "really", "would", "could", "want", "need", "try", "make", "say", "thing"}
)


def _suggest_k(n_messages: int) -> int:
    """Sqrt heuristic capped to a sensible range."""
    if n_messages < 20:
        return max(2, n_messages // 5)
    return max(4, min(20, int(math.sqrt(n_messages / 2))))


def _label_cluster(top_keywords: list[str]) -> str:
    """Build a short human-readable cluster label from keywords."""
    if not top_keywords:
        return "general"
    return ", ".join(top_keywords[:3])


def cluster_messages(
    messages: list[Message],
    k: int | None = None,
    random_state: int = 42,
) -> list[Cluster]:
    """Cluster messages into topical groups.

    Args:
        messages: messages to cluster (typically post-filter)
        k: explicit cluster count, or None to autoselect
        random_state: deterministic seed
    """
    if not messages:
        return []
    if len(messages) < 4:
        # Not enough signal to cluster meaningfully — single bucket.
        return [
            Cluster(
                id=0,
                label="general",
                message_ids=[m.id for m in messages],
                keywords=[],
            )
        ]

    texts = [m.content for m in messages]
    k = k or _suggest_k(len(texts))

    vectorizer = TfidfVectorizer(
        max_features=2000,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2 if len(texts) >= 10 else 1,
        max_df=0.85,
    )
    try:
        X = vectorizer.fit_transform(texts)
    except ValueError:
        # All inputs are stopwords or empty after vectorization
        return [
            Cluster(id=0, label="general", message_ids=[m.id for m in messages], keywords=[])
        ]

    if X.shape[1] == 0:
        return [
            Cluster(id=0, label="general", message_ids=[m.id for m in messages], keywords=[])
        ]

    k = min(k, X.shape[0])
    model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
    labels = model.fit_predict(X)

    feature_names = np.array(vectorizer.get_feature_names_out())
    centers = model.cluster_centers_

    clusters: list[Cluster] = []
    for cid in range(k):
        idxs = [i for i, lab in enumerate(labels) if lab == cid]
        if not idxs:
            continue
        center = centers[cid]
        top_indices = center.argsort()[::-1][:8]
        keywords = [
            kw
            for kw in feature_names[top_indices].tolist()
            if kw not in _STOPWORDS_EXTRA and len(kw) > 2
        ][:5]
        clusters.append(
            Cluster(
                id=cid,
                label=_label_cluster(keywords),
                message_ids=[messages[i].id for i in idxs],
                keywords=keywords,
            )
        )
    return clusters


def top_terms_in_messages(messages: list[Message], n: int = 5) -> list[str]:
    """Quick heuristic top-terms helper used by signal detection."""
    word_re = re.compile(r"[A-Za-z][A-Za-z\-]{2,}")
    counter: Counter[str] = Counter()
    for m in messages:
        for w in word_re.findall(m.content.lower()):
            if w not in _STOPWORDS_EXTRA:
                counter[w] += 1
    return [w for w, _ in counter.most_common(n)]
