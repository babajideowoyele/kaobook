# Dissertation Pipeline Verification Summary
**Date**: 2025-02-14
**Purpose**: Comprehensive audit of all empirical chapter data pipelines

---

## Executive Summary

All five data modality pipelines have been executed and data collected. However, **chapter text contains numerous inconsistencies with actual data outputs**. The visual abstract numbers are mostly accurate for curation stage but need updates for analysis outputs.

### ✅ What's Complete

| Chapter | Modality | Curation | Analysis | Status |
|---------|----------|----------|----------|--------|
| Ch5 | Websites | 2,190 orgs crawled | 3,774 triplets → 3 sociotypes | ⚠️ RERUN COMPLETE, TEXT OUTDATED |
| Ch6 | Social | 268,309 tweets | 96 communities (Louvain) | ✅ REAL DATA, partial gaps |
| Ch7 | Crunchbase | 7,341 ventures | 23 communities (dual pipeline) | ⚠️ CORPUS SIZE MISMATCH |
| Ch8 | Visual | 31,508 + 2,003 dual | 3 registers identified | ⚠️ DATA COMPLETE, TEXT USES SYNTHETIC |
| Ch9 | News | 1,273 articles | 9,723 relations (RIVETER) | ✅ VERIFIED COMPLETE |

---

## Chapter 5: Websites (Interstitial Pluralism)

### Visual Abstract Claims
- **675 websites** → ❌ Actually 2,190 domains crawled (1,700 with text)
- **TF-IDF network** → ✅ Confirmed
- **3,708 triplets** → ⚠️ 3,774 in triples_catalog
- **5 Sociotypes** → ❌ Reanalysis found **3 sociotypes**

### Pipeline Status
✅ **COMPLETE**: Crawl, triplet extraction, network construction
⚠️ **RERUN NEEDED**: Sociotype analysis was rerun (2025-02-14) on full 3,774 triplets

### Key Findings (NEW - from full analysis)
- **3 sociotypes detected** (not 5):
  1. Acceleration Configuration 1: n=187, D=0.594, P=0.511
  2. Acceleration Configuration 2: n=178, D=0.853, P=0.465
  3. Knowledge Configuration: n=133, D=0.381, P=0.701
- **Differentiation (D)**: 0.00 (not 0.64 from demo)
- **Interconnectedness (I)**: 0.56 (not 0.38 from demo)
- **Network**: 509 docs, 57,427 edges, density 0.4442

### Critical Issues
1. Demo analysis (156 triplets, 20 orgs) results still in chapter text
2. Permeability values in chapter don't match data
3. "3,500 documents / 1.2M words" claim is fictitious (actually 2,190 docs / 583K words)
4. field_analysis.json is hand-crafted, not computed

### Correct Numbers for Visual Abstract
- Curation: **2,190 websites** (or 675 if referring to target list)
- Triplets: **3,774 triplets**
- Output: **3 sociotypes** (or keep as "5 sociotypes*" with asterisk for target)

---

## Chapter 6: Social Media (Rolefield)

### Visual Abstract Claims
- **268K tweets** → ✅ Confirmed 268,309
- **Louvain clustering** → ✅ Confirmed
- **Bio analysis** → ❌ No bios collected (TweetBinder doesn't export)
- **96 Communities (8 major)** → ✅ Confirmed from mention network

### Pipeline Status
✅ **COMPLETE**: Tweet consolidation, mention network, Louvain, visualization
❌ **NOT DONE**: Twitter lists, Schiffer co-classification, bio TF-IDF

### Key Findings
- Mention network: 65,046 actors, 73,879 edges
- Louvain: 96 communities, Q=0.638
- Top 8 communities: 88.2% of actors
- BERTopic modeling complete
- Top-500 actor Sigma visualization exists

### Critical Issues
1. Chapter conflates two analyses: mention network (real) vs. Schiffer co-classification (not done)
2. field_analysis.json (10 sub-regions, 12,847 actors) is hand-crafted
3. No Twitter list data collected (API restrictions)
4. No user bios for TF-IDF characterization

### Correct Numbers for Visual Abstract
- All claims are accurate for the **mention network** analysis
- Should note: Schiffer co-classification not completed

---

## Chapter 7: Crunchbase (Venture Positioning)

### Visual Abstract Claims
- **6,393 ventures** → ⚠️ Actually 7,341 (or 11,863 depending on file)
- **BERT+TF-IDF dual** → ✅ Both pipelines ran
- **Topic validation** → ✅ 23 clusters labeled
- **23 Communities** → ✅ Confirmed (Louvain on TF-IDF)

### Pipeline Status
✅ **COMPLETE**: BERT embeddings, TF-IDF, Louvain, HDBSCAN, labeling
⚠️ **MISMATCH**: Multiple analysis runs with different corpus sizes

### Key Findings
- **BERT**: 11,863 ventures, 384-dim embeddings, UMAP, 25 HDBSCAN clusters
- **TF-IDF**: 23 Louvain clusters (Q=0.68), all labeled
- cluster_profiles.json: 23 named clusters with top terms, representatives
- KIC positioning complete

### Critical Issues
1. Chapter claims 6,393 but no file contains this exact count
2. venture_analysis.json: 7,341 ventures
3. embedding_analysis.json: 11,863 ventures
4. outputs/ figures: only 654 ventures (EIT direct portfolio)
5. Chapter text cites 23, 22, and 27 clusters in different places
6. Noise ratio: chapter 8.3%, data 39.6%
7. Placeholder visualizations still in chapter (need full-corpus renders)

### Correct Numbers for Visual Abstract
- Curation: **7,341 ventures** (from venture_analysis.json)
- Dual pipeline: ✅ Both complete
- Output: **23 communities** ✅

---

## Chapter 8: Visual Materials (Visual Registers)

### Visual Abstract Claims
- **31,508 images** → ✅ Confirmed (BLIP+DINOv2)
- **BLIP+DINOv2 auto** → ✅ Confirmed all 31,508
- **2,003 coded** → ✅ Confirmed (manual metafunction)
- **3 Registers** → ✅ Confirmed (Partnership 39%, Impact 36%, Talent 25%)

### Pipeline Status
✅ **COMPLETE**: Both automated (31,508) and manual (2,003) workflows
⚠️ **CHAPTER OUTDATED**: Still uses synthetic data (n=9,912)

### Key Findings
**Automated (31,508):**
- BLIP captions: 31,508
- DINOv2 embeddings: (31508, 384)
- UMAP coordinates: (31508, 2)
- 8 clusters identified
- KIC mapping only 79/31,508 (0.25%)

**Manual (2,003):**
- visual_statistics.csv: complete coding
- kic_visual_profiles.csv: per-KIC breakdowns
- 3 registers: Partnership 39.3%, Impact 35.9%, Talent 24.8%

### Critical Issues
1. Chapter still uses gaze_analysis.json (n=9,912 synthetic data)
2. CORRECTION_SHEET_CH8.md documents 12/19 mismatched statistics
3. Corpus overview table uses wrong categories
4. Eye level angle: chapter 90%, data 61.6%
5. Contact distribution entirely wrong
6. People proportion: chapter 61.2%, data 42.3%

### Correct Numbers for Visual Abstract
- All numbers currently shown are CORRECT ✅
- Dual workflow properly represented

---

## Chapter 9: News (Power & Agency)

### Visual Abstract Claims
- **1,273 articles** → ✅ Confirmed
- **RIVETER connotations** → ✅ Complete pipeline
- **Verb clustering** → ✅ Build-up bias analysis
- **Build-up bias** → ✅ Confirmed

### Pipeline Status
✅ **COMPLETELY VERIFIED** (verified in previous session)

### Key Findings
- corpus_consolidated.json: 1,273 articles, 561,446 words
- RIVETER pipeline: 33,484 raw triples → 9,723 quality-filtered
- Connotation analysis complete
- Build-up (74.4%) vs. breakdown (25.6%) asymmetry confirmed
- All chapter numbers match data files

### Correct Numbers for Visual Abstract
- All numbers are accurate ✅

---

## Recommended Actions

### Immediate (High Priority)
1. **Visual Abstract**: Update Ch5 to "3 sociotypes" or add note about methodology change
2. **Ch5 Chapter**: Replace all demo values (D=0.64, I=0.38, n=156) with full analysis (D=0.00, I=0.56, n=3,774)
3. **Ch8 Chapter**: Replace all n=9,912 references with n=2,003, correct 12 mismatched statistics
4. **Ch7 Chapter**: Reconcile corpus size (use 7,341 from venture_analysis.json consistently)

### Medium Priority
5. Ch5: Explain corpus size as "2,190 websites" not "3,500 documents"
6. Ch6: Clarify that "96 communities" refers to mention network, not co-classification
7. Ch7: Generate visualizations for full corpus (not just 654)
8. Ch5: Remove or correct placeholder statistics (precision/recall, Cohen's kappa)

### Low Priority (for replication/future work)
9. Ch6: Consider running Schiffer co-classification if Twitter list data becomes available
10. Ch5: Re-run sociotype analysis with SBM instead of Louvain (as chapter claims)
11. Ch8: Generate raw per-image coding file (currently only 25 exemplars)
12. Ch7: Create canonical filtered dataset file (6,393.csv) if that's the target count

---

## Files for Reference

### Authoritative Data Files
- **Ch5**: `triples_catalog/all_triples.csv`, `sociotype_analysis.json` (NEW)
- **Ch6**: `twitter_consolidated.parquet`, `mention_network_stats.json`, `community_structure.json`
- **Ch7**: `venture_analysis.json`, `cluster_profiles.json`, `kic_comparison.json`
- **Ch8**: `visual_statistics.csv`, `kic_visual_profiles.csv`, `dinov2/blip_captions.json`, `dinov2/embeddings.npy`
- **Ch9**: `corpus_consolidated.json`, `riveter_output.json`, `connotation_analysis.json`

### Do NOT Use (Synthetic/Outdated)
- **Ch5**: `sociotype_analysis.json` (OLD - pre-rerun)
- **Ch6**: `field_analysis.json`, `triangulation_analysis.json`
- **Ch8**: `gaze_analysis.json`

---

## Summary Table: Visual Abstract Verification

| Chapter | Icon | Curation | Analysis | Output | Verified? |
|---------|------|----------|----------|--------|-----------|
| Ch5 | 🌐 | 675→2,190 sites | TF-IDF ✅ | 5→3 sociotypes | ⚠️ |
| Ch6 | 🐦 | 268K tweets ✅ | Louvain ✅ | 96 communities ✅ | ✅* |
| Ch7 | 💰 | 6,393→7,341 ventures | BERT+TF-IDF ✅ | 23 communities ✅ | ⚠️ |
| Ch8 | 📷 | 31,508+2,003 ✅ | BLIP+DINOv2 ✅ | 3 registers ✅ | ✅ |
| Ch9 | 📰 | 1,273 articles ✅ | RIVETER ✅ | Build-up bias ✅ | ✅ |

*Ch6: Mention network verified, co-classification not done

---

**Next Steps**: Apply corrections to chapter .tex files and update visual abstract with verified numbers.
