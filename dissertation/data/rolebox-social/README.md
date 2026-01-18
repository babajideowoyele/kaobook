# RoleBox-Social: Social Media Pipeline

Social media presence and discourse for EIT ecosystem organizations.

## Overview

This modality captures the **relational roles** dimension of multimodal cartography - how organizations position themselves in network discourse and communicate with stakeholders. Social media reveals communicative identity, audience engagement, and inter-organizational relationships.

## Data Sources

| Source | Description | Access |
|--------|-------------|--------|
| Twitter/X | Microblogging platform | Academic API (v2) |
| LinkedIn | Professional network | Limited API |
| Bluesky | Decentralized social | Public API |

## Directory Structure

```
rolebox-social/
├── data/
│   ├── raw/                    # Original API responses
│   └── processed/              # Cleaned/structured data
├── docs/                       # Methodology documentation
├── notebooks/                  # Jupyter analysis notebooks
├── outputs/
│   ├── figures/               # Generated visualizations
│   └── tables/                # Summary statistics
└── scripts/
    ├── collect/               # API collection scripts
    └── analyze/               # Network/text analysis
```

## Data Schema

### Tweet/Post Data Fields

| Field | Type | Description |
|-------|------|-------------|
| post_id | str | Unique post identifier |
| author_id | str | Account identifier |
| author_handle | str | Username/handle |
| created_at | datetime | Post timestamp |
| text | str | Post content |
| retweet_count | int | Repost count |
| like_count | int | Like/favorite count |
| reply_count | int | Reply count |
| mentions | list | @mentioned accounts |
| hashtags | list | #hashtags used |
| urls | list | Embedded links |

### Network Data Fields

| Field | Type | Description |
|-------|------|-------------|
| source | str | Source account |
| target | str | Target account |
| edge_type | str | follow/mention/retweet |
| weight | int | Interaction count |
| timestamp | datetime | First/last interaction |

## Usage

### Key Analyses

1. **Follower Networks**: Who follows whom
2. **Mention Networks**: Communication patterns
3. **Hashtag Co-occurrence**: Topical alignment
4. **Discourse Analysis**: How organizations discuss roles

### Network Construction

```python
import networkx as nx

# Build mention network
G = nx.DiGraph()
for tweet in tweets:
    for mention in tweet['mentions']:
        G.add_edge(tweet['author'], mention)
```

## Related Chapters

- **Chapter 5: Interstitial Pluralism** - Relational configurations
- **Chapter 10: Synthesis** - Relational vs. claimed role gaps

## Data Collection Notes

- Platform: Twitter Academic Research API v2
- Query: Organization handles + EIT hashtags
- Time range: 2020-2024
- Rate limits: 10M tweets/month
- Ethics: Compliant with Twitter TOS and academic research guidelines

## Ethical Considerations

- No collection of private accounts
- Aggregated analysis only (no individual-level reporting)
- Compliance with platform terms of service
- GDPR considerations for EU accounts

## API Access

```python
import tweepy

# Academic Research access
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    wait_on_rate_limit=True
)

# Search tweets
tweets = client.search_all_tweets(
    query="EIT Climate-KIC OR @EITClimateKIC",
    tweet_fields=['author_id', 'created_at', 'public_metrics']
)
```

## Citation

```bibtex
@misc{rolebox2025social,
  title = {EIT Ecosystem Social Media Dataset},
  author = {Owoyele, Babajide Alamu},
  year = {2025},
  note = {Twitter/X data collected via Academic Research API}
}
```
