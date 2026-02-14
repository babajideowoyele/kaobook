# Dissertation Correction Plan
**Date**: 2025-02-14
**Purpose**: Systematic plan to align chapter text with verified pipeline outputs

---

## Priority Classification

🔴 **CRITICAL**: Breaks scientific credibility (wrong n, wrong results)
🟡 **HIGH**: Notable errors affecting interpretation
🟢 **MEDIUM**: Refinements for accuracy
⚪ **LOW**: Optional improvements for future work

---

## 🔴 CRITICAL Priority (Do First)

### Visual Abstract (`chapters/00-visual-abstract.tex`)

| Line | Current | Should Be | Reason |
|------|---------|-----------|--------|
| 82-86 | Ch5: 675 sites, 5 Sociotypes | 2,190 sites OR 675*, 3 sociotypes* | Actual crawl was 2,190; reanalysis found 3 sociotypes |
| 112-115 | Ch7: 6,393 ventures, 23 Communities | 7,341 ventures, 23 Communities | venture_analysis.json has 7,341 |

**Proposed Changes:**

```latex
% Option 1: Report actual numbers with footnote
\node[curation] (ch5-c) at (3.5, 10.2) {\faSpider\ Web crawl\\2,190 sites};
\node[output] (ch5-o) at (3.5, 7.2) {\faUsers\ 3 Sociotypes*\\KT profiles};

% Bottom note
\node[font=\scriptsize, text=Slate] at (8.5, 0.5) {
    *Louvain analysis on 3,774 triplets; differs from exploratory 5-cluster prototype in early drafts
};

% Ch7 fix
\node[curation] (ch7-c) at (8.5, 10.2) {\faDatabase\ Crunchbase\\7,341 ventures};
```

**OR Option 2: Keep strategic framing**
- If "675 sites" refers to target list (not actual crawl), add note
- If "5 sociotypes" is theoretical target, mark as exploratory finding

---

### Ch5: `chapters/05-interstitial-pluralism.tex`

#### 🔴 Replace Demo Analysis Results Throughout

**Global Search & Replace:**

| Find | Replace | Occurrences |
|------|---------|-------------|
| 156 triplets | 3,774 triplets | Multiple |
| D = 0.64 | D = 0.00 | Line ~553 |
| I = 0.38 | I = 0.56 | Line ~553 |
| five sociotypes | three sociotypes | Multiple |
| 3,500 documents | 2,190 websites | Line 107 |
| 1.2 million words | 583,000 words | Line 107 |

#### 🔴 Sociotype Permeability Values (Lines 567-692)

**Current (Demo):**
```latex
\item[Connective Configuration] Permeability: 0.54
\item[Acceleration Configuration] Permeability: 0.39
\item[Development Configuration] Permeability: 0.32
\item[Knowledge Configuration] Permeability: 0.28
\item[Accountability Configuration] Permeability: 0.21
```

**Replace With (Actual):**
```latex
\item[Knowledge Configuration] Permeability: 0.70, Density: 0.38
    Core roles: enabler, knowledge producer, change agent, voice, broker
    Size: 133 documents

\item[Acceleration Configuration 1] Permeability: 0.51, Density: 0.59
    Core roles: enabler, collaborator, catalyst, anchor
    Size: 187 documents

\item[Acceleration Configuration 2] Permeability: 0.47, Density: 0.85
    Core roles: enabler, catalyst, broker, knowledge producer
    Size: 178 documents
```

**Note**: Only 3 sociotypes detected (not 5). Two are acceleration-focused with different structural properties.

#### 🔴 Remove Placeholder Statistics (Lines 509-518)

**Current:**
- "94% precision and 89% recall" — PLACEHOLDER, never validated
- "Cohen's kappa=0.78" — PLACEHOLDER, no IRR study conducted
- "Modularity Q=0.42 (95% CI: [0.38, 0.46])" — PLACEHOLDER

**Action**: Either remove these claims OR add note: "Validation study pending; preliminary analysis only."

---

### Ch8: `chapters/08-visual-registers.tex`

#### 🔴 Corpus Size (Throughout)

| Line | Find | Replace |
|------|------|---------|
| 125 | 9,500 visuals | 2,003 manually coded visuals (plus 31,508 automated BLIP analysis) |
| 207 | stratified sample of 480 visuals | [verify or remove claim] |
| 920 | analyzed 9,500 visual artifacts | dual workflow: 31,508 automated + 2,003 theory-driven coding |

#### 🔴 Table Corrections

**Line 46-64: Visual Corpus Overview**
- Current total: 9,500
- Should be: 2,003
- Recalculate all KIC rows using `kic_visual_profiles.csv`

**Lines 325-327: Embodied Positions (Contact)**
```latex
% WRONG (from synthetic gaze_analysis.json):
Strong contact & 2,478 & 25.0\% \\
Weak contact & 3,567 & 36.0\% \\
No contact & 3,867 & 39.0\% \\

% CORRECT (from visual_statistics.csv):
Strong contact (demand) & 623 & 31.1\% \\
Weak contact (offer) & 1,156 & 57.7\% \\
No contact & 224 & 11.2\% \\
```

**Line 548: Eye Level Angle**
```latex
% WRONG:
Equality & 8,923 & 90.0\% \\

% CORRECT:
Equality (eye level) & 1,234 & 61.6\% \\
```

**Lines 537-540: Gaze Summary**
```latex
% WRONG (n=9,912 synthetic):
Partnership & Weak/Strong & 3,567 & 36\% \\
Impact & None & 2,876 & 29\% \\
Talent & Strong & 2,478 & 25\% \\

% CORRECT (from kic_visual_profiles.csv weighted avg):
Partnership & Weak/Strong & ~788 & 39.3\% \\
Impact & None & ~719 & 35.9\% \\
Talent & Strong & ~496 & 24.8\% \\
```

**Line 237: People Proportion**
```latex
% WRONG:
People are the dominant participants (61.2\% of visuals)

% CORRECT:
People are the dominant participants (42.3\% of visuals)
```

**Line 243: Gender**
```latex
% WRONG:
male adults appear individually 42\% more often than female adults (18.5\% vs. 13.0\%)

% CORRECT:
male adults appear individually 33\% more often than female adults (15.6\% vs. 11.7\%)
```

---

### Ch7: `chapters/07-venture-positioning.tex`

#### 🔴 Corpus Size Consistency

**Lines throughout:**
- Find: "6,393 ventures"
- Replace with: "7,341 ventures" (from `venture_analysis.json`)

**OR** if 6,393 is after specific filtering:
- Create and save filtered dataset as `eit_ventures_6393.csv`
- Document filtering criteria in replication box

#### 🔴 Cluster Count Consistency

| Line | Current | Issue | Fix |
|------|---------|-------|-----|
| 441 | 23 communities | Correct (TF-IDF Louvain) | Keep ✓ |
| 461 | 22 clusters (table) | Inconsistent | Change to 23 |
| 620 | 27 clusters (embedding) | Wrong (actual: 25) | Change to 25 |
| 626 | 8.3% noise | Wrong (actual: 39.6%) | Change to 39.6% OR use venture_analysis.json (5.0%) |

**Recommendation**: Use `venture_analysis.json` consistently (23 for both methods, 5.0% noise).

#### 🔴 Method Comparison Metrics (Table 7.6, Line 648)

```latex
% WRONG (hardcoded):
ARI & 0.412 \\
NMI & 0.534 \\
Correlation & 0.623 \\

% CORRECT (from embedding_analysis.json):
ARI & 0.042 \\
NMI & 0.210 \\
Correlation & 0.254 \\
```

---

## 🟡 HIGH Priority

### Ch5: Field Positions Table (Lines 214-233)

**Issue**: KIC-level E/R/B percentages don't match `field_positions_full_summary.json`

**Current aggregate**: E=25%, R=32%, B=43%
**Actual aggregate**: E=14%, R=37%, B=49%

**Action**: Regenerate table from `outputs/full_analysis/field_positions_full_summary.json`

### Ch6: Clarify Two Analyses

**Lines 1-300**: Describes Schiffer co-classification (10 sub-regions, 12,847 actors)
**Lines 301-600**: Describes mention network (96 communities, 65K actors)

**Problem**: First half describes analysis that was NOT run (field_analysis.json is hand-crafted).

**Options**:
1. Add note: "The co-classification analysis represents planned methodology; actual results based on mention network (Section X)"
2. Rewrite first half to focus exclusively on mention network
3. Run Schiffer pipeline if Twitter list data can be obtained

### Ch8: Methodology Claims

**Line 368**: "n = 2,500 visual-verbal comparison" — No evidence
**Line 372**: "random sample of 500 visuals" for ICR — No evidence

**Action**: Either remove claims OR mark as "planned but not completed in current scope"

### Ch7: Placeholder Figures

**Lines 445-448**: `[AGGREGATE SIMILARITY NETWORK VISUALIZATION]`
**Lines 618-621**: `[UMAP EMBEDDING VISUALIZATION]`

**Issue**: Figures exist but for wrong corpus (654 ventures not 7,341)

**Action**:
1. Re-run visualization scripts on full corpus
2. OR use existing 654-venture figures with note about subset
3. OR generate from `similarity_network.gexf` (exists for full corpus)

---

## 🟢 MEDIUM Priority

### Ch5: Terminology Alignment

- Chapter describes "Stochastic Block Models (SBMs)" but actual analysis used "Louvain"
- Either change chapter to "Louvain" OR re-run analysis with SBM

### Ch6: Complete Sub-Region Characterization

- `sub_regions_detailed.json` has all zeros (density, ties, top_terms)
- Either compute from data OR remove detailed structural claims

### Ch8: Dual Workflow Emphasis

**Add to methodology section**:
```latex
Our analysis employed a dual workflow combining automated vision analysis
with theory-driven manual coding. We processed 31,508 images using BLIP
(caption generation) and DINOv2 (embeddings) to identify broad visual patterns.
From this, we selected a stratified sample of 2,003 images for intensive manual
coding using Kress \& van Leeuwen's social semiotics framework.
```

---

## ⚪ LOW Priority (Future Work)

### Ch5: Run Full Validation Study
- Implement precision/recall evaluation on held-out set
- Conduct inter-rater reliability study for triplet extraction
- Replace placeholder statistics with actual validation metrics

### Ch6: Implement Schiffer Pipeline
- Collect Twitter list data (if API access permits)
- Run 6-step co-classification procedure
- Generate field_analysis.json from actual computation

### Ch8: Generate Complete Raw Coding File
- Currently only 25 exemplar rows in `eit_visual_coding.csv`
- Full 2,003 exists only as aggregates in `visual_statistics.csv`
- Create per-image coding file for replication

### Ch7: Generate Full-Corpus Visualizations
- Re-render UMAP and network plots for 7,341 ventures (not 654)
- Export at 300 DPI for dissertation figures
- Update figure references in chapter

---

## Implementation Sequence

### Phase 1: Visual Abstract + Critical Errors (1-2 hours)
1. Update visual abstract (Ch5: 3 sociotypes, Ch7: 7,341)
2. Ch5: Replace all demo values (D, I, permeability, n)
3. Ch8: Replace all n=9,912 with n=2,003
4. Ch7: Standardize corpus size to 7,341

### Phase 2: Table Corrections (2-3 hours)
5. Ch8: Regenerate all tables from visual_statistics.csv
6. Ch5: Update field positions table from actual data
7. Ch7: Fix cluster counts and metrics tables

### Phase 3: Methodology Clarifications (1 hour)
8. Ch5: Add note about demo vs. full analysis
9. Ch6: Clarify mention network vs. co-classification
10. Ch8: Emphasize dual workflow structure

### Phase 4: Figures (Optional, 2-4 hours)
11. Ch7: Generate visualizations for full corpus
12. Ch8: Verify all figure references use correct data
13. Ch5: Add sociotype network visualization if desired

---

## Verification Checklist

After corrections, verify:
- [ ] Visual abstract numbers match PIPELINE_VERIFICATION_SUMMARY.md
- [ ] All n= values reference actual data files
- [ ] No synthetic/placeholder data (gaze_analysis.json, field_analysis.json demo)
- [ ] Replication boxes cite correct output files
- [ ] Figure captions reference correct corpus sizes
- [ ] Consistent terminology (e.g., Louvain not SBM if Louvain was used)

---

## Data Source Reference

**Authoritative files to use:**

```
Ch5: data/rolebox-websites/
  - outputs/triples_catalog/all_triples.csv (3,774 triplets)
  - data/outputs/sociotype_analysis.json (NEW - 2025-02-14)
  - outputs/full_analysis/field_positions_full_summary.json

Ch6: data/rolebox-social/
  - data/processed/twitter_consolidated.parquet (268,309)
  - data/processed/mention_network_stats.json
  - data/processed/community_structure.json

Ch7: data/rolebox-crunchbase/
  - data/outputs/venture_analysis.json (7,341)
  - data/outputs/cluster_profiles.json (23 clusters)
  - data/outputs/embedding_analysis.json

Ch8: data/rolebox-visual/
  - data/processed/visual_statistics.csv (2,003 manual)
  - data/processed/kic_visual_profiles.csv
  - data/processed/dinov2/blip_captions.json (31,508 auto)
  - data/processed/dinov2/corpus_statistics.json

Ch9: data/rolebox-news/
  - data/outputs/corpus_consolidated.json (1,273)
  - data/outputs/riveter_output.json
```

---

## Questions for Review

1. **Ch5 sociotypes**: Accept 3 sociotypes as final, or explore different clustering parameters?
2. **Ch7 corpus**: Use 7,341 consistently, or create 6,393 filtered dataset?
3. **Ch8 dual workflow**: Emphasize both pipelines equally, or focus on manual coding?
4. **Placeholder figures**: Generate new ones, or note as "not shown due to space"?
5. **Ch6 co-classification**: Acknowledge as planned future work, or rewrite chapter?

---

**Ready to proceed?** Indicate which phase(s) to implement, or request modifications to this plan.
