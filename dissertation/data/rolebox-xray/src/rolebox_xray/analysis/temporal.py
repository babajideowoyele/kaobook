"""
Temporal trend analysis for topics.

Classifies topics into temporal patterns: hot, cold, evergreen, reviving, wallflower.
Adapted from METAFRASIA/role_xray for standalone use.
"""

from __future__ import annotations

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TrendCategory(Enum):
    """Temporal trend categories for topics."""
    HOT = "hot"               # Increasing trend
    COLD = "cold"             # Decreasing trend
    EVERGREEN = "evergreen"   # Stable high activity
    REVIVING = "reviving"     # Recent increase after decline
    WALLFLOWER = "wallflower" # Low but stable activity


@dataclass
class TemporalConfig:
    """Configuration for temporal analysis."""
    polynomial_degree: int = 2
    hot_threshold: float = 0.5
    cold_threshold: float = -0.5
    evergreen_tolerance: float = 0.1
    min_documents: int = 5
    significance_level: float = 0.05


class TemporalAnalyzer:
    """
    Analyze temporal trends in topic distributions.

    Fits polynomial models to topic frequencies over time and
    classifies topics into trend categories.

    Example:
        >>> analyzer = TemporalAnalyzer()
        >>> trends = analyzer.analyze(topics, years)
        >>> hot_topics = analyzer.get_topics_by_category(TrendCategory.HOT)
    """

    def __init__(self, config: Optional[TemporalConfig] = None):
        self.config = config or TemporalConfig()
        self._results = None
        self._topic_years = None

    def analyze(
        self,
        topics: List[int],
        years: List[int],
        topic_labels: Optional[Dict[int, str]] = None
    ) -> pd.DataFrame:
        """
        Analyze temporal trends for all topics.

        Args:
            topics: List of topic assignments
            years: List of publication years (parallel to topics)
            topic_labels: Optional topic labels

        Returns:
            DataFrame with temporal statistics per topic
        """
        logger.info("Analyzing temporal trends...")

        # Build topic-year distribution
        topic_years = {}
        for topic, year in zip(topics, years):
            if topic == -1:  # Skip outliers
                continue
            if topic not in topic_years:
                topic_years[topic] = []
            topic_years[topic].append(year)

        self._topic_years = topic_years

        # Analyze each topic
        results = []
        for topic, years_list in topic_years.items():
            if len(years_list) < self.config.min_documents:
                continue

            result = self._analyze_topic(topic, years_list)
            if topic_labels:
                result['label'] = topic_labels.get(topic, f"Topic_{topic}")
            results.append(result)

        self._results = pd.DataFrame(results)

        # Classify trends
        self._results['trend_category'] = self._results.apply(
            self._classify_trend, axis=1
        )

        logger.info(f"Analyzed {len(self._results)} topics")
        return self._results

    def _analyze_topic(self, topic: int, years: List[int]) -> dict:
        """Analyze temporal trend for a single topic."""
        years = np.array(years)

        result = {
            'topic': topic,
            'count': len(years),
            'year_mean': np.mean(years),
            'year_std': np.std(years),
            'year_min': np.min(years),
            'year_max': np.max(years),
        }

        year_min, year_max = years.min(), years.max()

        try:
            unique_years, counts = np.unique(years, return_counts=True)
            years_for_fit = (unique_years - year_min) / max(year_max - year_min, 1)
            counts_norm = counts / counts.sum()

            if len(unique_years) >= 3:
                coeffs = np.polyfit(
                    years_for_fit,
                    counts_norm,
                    min(self.config.polynomial_degree, len(unique_years) - 1)
                )

                result['coeff_linear'] = coeffs[-2] if len(coeffs) >= 2 else 0
                result['coeff_quadratic'] = coeffs[-3] if len(coeffs) >= 3 else 0
            else:
                result['coeff_linear'] = 0
                result['coeff_quadratic'] = 0

            # Recent trend
            recent_threshold = year_max - 3
            recent_count = sum(1 for y in years if y >= recent_threshold)
            earlier_count = len(years) - recent_count
            result['recent_ratio'] = recent_count / earlier_count if earlier_count > 0 else 1.0

        except Exception as e:
            logger.warning(f"Error fitting trend for topic {topic}: {e}")
            result['coeff_linear'] = 0
            result['coeff_quadratic'] = 0
            result['recent_ratio'] = 1.0

        return result

    def _classify_trend(self, row: pd.Series) -> str:
        """Classify a topic's temporal trend."""
        linear = row.get('coeff_linear', 0)
        quadratic = row.get('coeff_quadratic', 0)
        recent_ratio = row.get('recent_ratio', 1.0)

        if linear > self.config.hot_threshold:
            return TrendCategory.HOT.value
        if linear < self.config.cold_threshold:
            return TrendCategory.COLD.value
        if quadratic > 0.1 and linear < 0 and recent_ratio > 1.5:
            return TrendCategory.REVIVING.value
        if abs(linear) < self.config.evergreen_tolerance:
            return TrendCategory.EVERGREEN.value
        return TrendCategory.WALLFLOWER.value

    def get_topics_by_category(self, category: TrendCategory) -> pd.DataFrame:
        """Get topics in a specific trend category."""
        if self._results is None:
            raise ValueError("Must call analyze() first")
        return self._results[
            self._results['trend_category'] == category.value
        ].copy()

    def get_trend_summary(self) -> dict:
        """Get summary of trend categories."""
        if self._results is None:
            raise ValueError("Must call analyze() first")

        counts = self._results['trend_category'].value_counts().to_dict()
        return {
            'total_topics': len(self._results),
            'hot': counts.get(TrendCategory.HOT.value, 0),
            'cold': counts.get(TrendCategory.COLD.value, 0),
            'evergreen': counts.get(TrendCategory.EVERGREEN.value, 0),
            'reviving': counts.get(TrendCategory.REVIVING.value, 0),
            'wallflower': counts.get(TrendCategory.WALLFLOWER.value, 0),
        }
