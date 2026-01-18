# Kaobook Compilation Fixes and Known Issues

This document captures workarounds for known kaobook template issues encountered during dissertation compilation.

## Fast Compilation Options

For faster iteration while working on specific chapters, use one of these approaches:

### Option 1: Focus Mode (Recommended)

Uncomment the `\FOCUSMODE` line near the top of main.tex:

```latex
% Option 2: Focus mode - only compile specific chapters (set below)
\newcommand{\FOCUSMODE}{}  % <-- Uncomment this line
```

This compiles only:
- Chapter 1 (Introduction)
- EIT Communities Intermezzo

To change which chapters are included in focus mode, edit the `\ifdefined\FOCUSMODE` block starting around line 209.

**Compilation time**: ~15-30 seconds vs ~2-3 minutes for full compilation

### Option 2: Draft Mode (Fastest)

Add `draft` to the document class options:

```latex
\documentclass[
    fontsize=10pt,
    a4paper,
    twoside=false,
    open=any,
    secnumdepth=1,
    numbers=noenddot,
    draft,  % <-- Uncomment this line
]{kaobook}
```

This shows placeholder boxes instead of images - fastest compilation but no graphics.

### Option 3: Compile Individual Chapter

Each chapter can be compiled standalone using subfiles. From the chapter directory:

```bash
lualatex 01-introduction.tex
```

Note: Cross-references to other chapters won't work in standalone mode.

---

## 1. Caption Recursion Error (TeX capacity exceeded)

**Symptom:** `TeX capacity exceeded, sorry [parameter stack size=20000]` when using `\caption{}` inside table/figure environments.

**Cause:** The kao.sty caption hooks cause infinite recursion with some packages when `\caption` is called inside table/figure environments.

**Solution 1:** Use `\captionof{table}{...}` or `\captionof{figure}{...}` instead of `\caption{}`:

```latex
% Instead of:
\begin{table}
\caption{My table caption}  % <-- Can cause recursion error
\begin{tabular}{...}
...
\end{tabular}
\end{table}

% Use:
\begin{table}
\centering
\begin{tabular}{...}
...
\end{tabular}
\captionof{table}{My table caption}  % <-- Works reliably
\label{tab:my-label}
\end{table}
```

**Solution 2 (in main.tex):** The main.tex includes a patch that tries to reset the caption command:

```latex
\makeatletter
\AtBeginDocument{%
    \let\kaociOrigCaption\caption%
    \pretocmd{\figure}{\let\caption\kaociOrigCaption}{}{}%
    \pretocmd{\table}{\let\caption\kaociOrigCaption}{}{}%
}
\makeatother
```

However, this patch doesn't always work, so prefer Solution 1.

## 2. Intermezzo TOC Entries

**Goal:** Intermezzo chapters should appear in TOC, but their sections/subsections should NOT.

**Solution:** Use unnumbered section commands:

```latex
\section*{Section Title}     % NOT \section{...}
\subsection*{Subsection}     % NOT \subsection{...}
```

Also remove `\margintoc` from intermezzos since it can add extra TOC entries.

## 3. tcolorbox Text Color Issues

**Symptom:** White text on light backgrounds (especially in `criticalbox` environment).

**Solution:** In kaoci-rolebox.sty, ensure:

```latex
\newtcolorbox{criticalbox}[1][]{%
    ...
    colbacktitle=AccentCoral!10,  % Light background
    coltitle=black,               % Black title text
    coltext=black,                % Black body text
    ...
}
```

## 4. Float Placement

**Symptom:** Figures/tables appearing far from where they're defined.

**Solutions:**
- Use `[htbp]` placement specifier for flexibility
- Use `[H]` from float package to force "here" (but can cause underfull pages)
- Convert margin figures to body figures using `figure*` for important visuals

## 5. Latexmk Configuration

The `.latexmkrc` file configures:
- LuaLaTeX as default (`$pdf_mode = 4`)
- Shell escape enabled for tikz externalize, minted, etc.
- Output directory: `dissertation/`
- Biber for bibliography

**Clean rebuild command:**
```bash
latexmk -C dissertation/main.tex && latexmk -lualatex dissertation/main.tex
```

## 6. Bibliography Issues

**Symptom:** Undefined citations after first compile.

**Solution:** Run full build sequence:
```bash
latexmk -lualatex dissertation/main.tex  # Runs multiple passes + biber automatically
```

Or manually:
```bash
lualatex main.tex
biber main
lualatex main.tex
lualatex main.tex
```

## 7. Subfiles with Relative Paths

When using `\subfile{}`, paths must be relative to main.tex location:

```latex
\subfile{dissertation/chapters/01-introduction}  % Correct
\subfile{chapters/01-introduction}               % Wrong if main.tex is in root
```

## 8. Figure Scale Issues

**Symptom:** TikZ figures appearing too small or cut off.

**Solution:** Adjust scale and node sizes together:

```latex
\begin{tikzpicture}[scale=1.1]  % Increase overall scale
    % Also increase font sizes proportionally:
    \node[font=\scriptsize] ...  % Instead of \tiny
```

## 9. Table Width Issues

**Symptom:** Tables extending into margins or appearing warped.

**Solutions:**
- Use `\textwidth` or `0.95\textwidth` for table width
- Use `tabularx` with `X` columns for flexible widths
- Use `\scriptsize` or `\small` for dense tables

```latex
\begin{table*}  % Full width
\scriptsize
\begin{tabularx}{0.95\textwidth}{@{}lXXXX@{}}
...
\end{tabularx}
\end{table*}
```

---

## Compilation Checklist

Before final submission:
1. Clean build: `latexmk -C dissertation/main.tex`
2. Full compile: `latexmk -lualatex dissertation/main.tex`
3. Check for undefined references in log
4. Verify TOC has correct entries
5. Review all figures are properly placed
6. Check all boxes have readable text colors
