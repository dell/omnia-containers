# 🎯 Accessibility Validator & Fixer - Quick Start Guide

---

## 🚀 The Big Picture

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  START  │───▶│VALIDATE │───▶│   FIX   │───▶│ REVIEW  │───▶│  COMMIT │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                    │              │              │
                    ▼              ▼              ▼
              📋 Report      🔧 Auto/       ✅ Check
              Generated      Manual        Changes
```

---

## 📝 Step-by-Step Guide

### 🔍 STEP 1: Validate Your Documentation

```
┌─────────────────────────────────────────────────────────┐
│  🖥️  Open terminal and run:                              │
│                                                          │
│  python run_omnia_accessibility.py path/to/docs          │
│                                                          │
│  ✅ This will:                                           │
│     • Scan all your Markdown files                      │
│     • Find accessibility issues                         │
│     • Auto-fix what it can                              │
│     • Generate reports                                 │
└─────────────────────────────────────────────────────────┘
```

**Or if you want to review first:**
```bash
python run_omnia_accessibility.py path/to/docs --skip-fixes
```

**Or use checkpoint mode to review baseline reports before fixing, then review rendered output before publishing:**
```bash
# Phase 1: Validation + baseline reports
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase1

# Phase 2: Fixer + all reports (after reviewing baseline)
python run_omnia_accessibility.py path/to/docs --checkpoint-mode phase2

# Phase 3: Render + preview (manual steps)
cd path/to/docs && mkdocs build
# The HTML report uses file:// URLs and works directly from the built site
# When satisfied, publish to ReadTheDocs: https://your-project.readthedocs.io/
```

---

### 📊 STEP 2: Check the Report

```
┌─────────────────────────────────────────────────────────┐
│  📁 Look in the reports/ folder:                         │
│                                                          │
│  📄 COMPREHENSIVE_ACCESSIBILITY_REPORT.txt               │
│     → Simplified summary with all issues                  │
│                                                          │
│  📊 category_report.txt                                 │
│     → Issues grouped by category (Images, Links, etc.)   │
│                                                          │
│  🌐 accessibility_visual_report.html                    │
│     → Open in browser for colorful charts                │
│                                                          │
│  📈 comparison_visual_report.html                       │
│     → HTML comparison with summary statistics            │
│                                                          │
│  📊 comparison_report.csv                               │
│     → Before/after comparison data                       │
└─────────────────────────────────────────────────────────┘
```

**What to look for:**
- 🔴 **ERROR** = Must fix (critical)
- 🟡 **WARNING** = Should fix (important)
- 🟢 **SUGGESTION** = Nice to fix (optional)

---

### 🔧 STEP 3: Fix the Issues

```
┌─────────────────────────────────────────────────────────┐
│  Choose your fix mode:                                   │
│                                                          │
│  🤖 AUTO MODE (Recommended)                             │
│     python run_omnia_accessibility.py path/to/docs       │
│     → Fixes errors & warnings automatically              │
│                                                          │
│  👤 CHECKPOINT MODE (Review first)                      │
│     python run_omnia_accessibility.py path/to/docs \    │
│            --checkpoint-mode phase1                      │
│     → Generate baseline reports for review             │
│     → Then run phase2 to apply fixes                    │
│                                                          │
│  🔍 VALIDATE ONLY                                       │
│     python run_omnia_accessibility.py path/to/docs \    │
│            --skip-fixes                                 │
│     → Just validate, don't fix                          │
└─────────────────────────────────────────────────────────┘
```

---

### ✏️ STEP 4: Manual Fixes (If Needed)

```
┌─────────────────────────────────────────────────────────┐
│  Some issues need human help:                            │
│                                                          │
│  🖼️  Missing Alt Text                                   │
│     Add description to images:                           │
│     .. image:: photo.png                                 │
│        :alt: A screenshot showing the settings panel     │
│                                                          │
│  📝 Empty Section Titles                                 │
│     Add meaningful text:                                 │
│     Configuration                                        │
│     =============                                        │
│                                                          │
│  🔗 Non-Descriptive Links                                │
│     Change "click here" to descriptive text:             │
│     `View the configuration guide <link>`_               │
│                                                          │
  ⚙️  Missing Directive Options                           │
│     Add required options:                                │
│     .. code-block:: python                               │
│        :linenos:                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 🔄 STEP 5: Re-Validate (After Manual Fixes)

```
┌─────────────────────────────────────────────────────────┐
│  Check if you fixed everything:                          │
│                                                          │
│  python run_omnia_accessibility.py path/to/docs \       │
│         --skip-fixes                                    │
│                                                          │
│  ✅ Compare with the first report to see progress!       │
└─────────────────────────────────────────────────────────┘
```

---

### 💾 STEP 6: Save Your Work

```
┌─────────────────────────────────────────────────────────┐
│  Commit your changes to Git:                             │
│                                                          │
│  git add .                                               │
│  git commit -m "Fix accessibility issues"                │
│  git push                                                │
│                                                          │
│  🎉 Your documentation is now more accessible!           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 Fix Modes at a Glance

```
┌──────────────────┬──────────────────────┬─────────────────┐
│      MODE        │     DESCRIPTION      │   WHEN TO USE   │
├──────────────────┼──────────────────────┼─────────────────┤
│ 🔍 skip-fixes    │ Just check, don't fix│ First time scan │
│                  │                      │ Review first    │
├──────────────────┼──────────────────────┼─────────────────┤
│ 🤖 auto          │ Auto-fix errors &   │ Quick fixes     │
│                  │ warnings             │ Standard workflow│
├──────────────────┼──────────────────────┼─────────────────┤
│ 🎯 checkpoint    │ Two-phase execution  │ Review baseline │
│                  │ Review before fixing │ Large docs      │
│                  │                      │ Team workflow   │
└──────────────────┴──────────────────────┴─────────────────┘
```

---

## 📋 Quick Command Reference

```
┌─────────────────────────────────────────────────────────┐
│  🚀 Most Common Command:                                │
│                                                          │
│  python run_omnia_accessibility.py path/to/docs          │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  🔍 Validate Only:                                      │
│  python run_omnia_accessibility.py path/to/docs \       │
│         --skip-fixes                                    │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  🎯 Checkpoint Mode (Review first):                      │
│  python run_omnia_accessibility.py path/to/docs \       │
│         --checkpoint-mode phase1                         │
│  python run_omnia_accessibility.py path/to/docs \       │
│         --checkpoint-mode phase2                         │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  💾 No Backup (Testing):                                │
│  python run_omnia_accessibility.py path/to/docs \       │
│         --no-backup                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 What Reports Will You Get?

```
reports/
├── 📄 COMPREHENSIVE_ACCESSIBILITY_REPORT.txt
│   └── 📋 Main summary with all issues and recommendations
│
├── 🌐 accessibility_visual_report.html
│   └── 📊 Open in browser for colorful charts and graphs
│
├── 📈 accessibility_report.csv
│   └── 📊 Open in Excel for data analysis
│
└── 📋 comparison_report_corrected.txt
    └── 🔄 Before/after comparison of fixes
```

---

## 🚨 Severity Levels Explained

```
┌─────────────────────────────────────────────────────────┐
│  🔴 ERROR (Must Fix)                                     │
│     Critical for accessibility compliance                │
│     Examples: Missing alt text, empty sections          │
│                                                          │
│  🟡 WARNING (Should Fix)                                │
│     Important for user experience                       │
│     Examples: Insecure links, invalid code languages    │
│                                                          │
│  🟢 SUGGESTION (Nice to Fix)                            │
│     Optional improvements                               │
│     Examples: Bare URLs, bare references                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Common Issue Types

```
┌──────────────────────────┬──────────┬─────────────────┐
│        ISSUE TYPE        │ SEVERITY │  AUTO-FIXABLE?  │
├──────────────────────────┼──────────┼─────────────────┤
│ 🖼️  Missing Alt Text    │   🔴     │      ❌ No      │
├──────────────────────────┼──────────┼─────────────────┤
│ 📝 Empty Section Titles  │   🔴     │      ❌ No      │
├──────────────────────────┼──────────┼─────────────────┤
│ 🔗 Non-Descriptive Links │   🔴     │      ❌ No      │
├──────────────────────────┼──────────┼─────────────────┤
│ 🔓 Insecure Links (http) │   🟡     │      ✅ Yes     │
├──────────────────────────┼──────────┼─────────────────┤
│ 💻 Invalid Code Langs    │   🟡     │      ❌ No      │
├──────────────────────────┼──────────┼─────────────────┤
│ 🔗 Bare URLs             │   🟢     │      ✅ Yes     │
├──────────────────────────┼──────────┼─────────────────┤
│ 📄 Bare References       │   🟢     │      ✅ Yes     │
└──────────────────────────┴──────────┴─────────────────┘
```

---

## ✅ Best Practices

```
┌─────────────────────────────────────────────────────────┐
│  1️⃣  Always use backup                                  │
│     Don't use --no-backup (safety first!)               │
│                                                          │
│  2️⃣  Start with auto mode                               │
│     Let automatic fixes run first                       │
│                                                          │
│  3️⃣  Review changes                                    │
│     Check fixes in IDE before committing                │
│                                                          │
│  4️⃣  Fix in phases                                     │
│     ERROR → WARNING → SUGGESTION                       │
│                                                          │
│  5️⃣  Re-validate                                       │
│     Run validation after manual fixes                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🆘 Troubleshooting

```
┌─────────────────────────────────────────────────────────┐
│  ❌ Problem: Python not found                           │
│     ✅ Solution: Install Python 3.6+ from python.org    │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  ❌ Problem: Permission denied                         │
│     ✅ Solution: Run as administrator (Windows)         │
│              or use chmod +x (Linux/Mac)                │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  ❌ Problem: File not found                             │
│     ✅ Solution: Use absolute path or check working     │
│              directory                                  │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  ❌ Problem: No issues found but expected               │
│     ✅ Solution: Check configuration in                 │
│              omnia_config.json                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📂 File Structure

```
Accessibility Validator and Fixer_SKILL_MDMKDOCS/
│
├── 🚀 run_omnia_accessibility.py      ← Main script (use this!)
├── ⚙️  omnia_config.json               ← Configuration
├── 🔍 omnia_rst_accessibility_validator.py  ← Validator
├── 🔧 omnia_rst_accessibility_fixer.py      ← Fixer
│
└── 📁 reports/                        ← Generated reports
    ├── 📄 COMPREHENSIVE_ACCESSIBILITY_REPORT.txt
    ├── 🌐 accessibility_visual_report.html
    └── 📈 accessibility_report.csv
```

---

## 📚 Need More Details?

```
┌─────────────────────────────────────────────────────────┐
│  See WORKFLOW_ROADMAP.md for:                            │
│     • Complete detailed workflow                        │
│     • All checkpoints and options                       │
│     • Advanced features                                 │
│     • CI/CD integration                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🎉 You're Ready!

```
┌─────────────────────────────────────────────────────────┐
│  Just run this command to get started:                  │
│                                                          │
│  python run_omnia_accessibility.py path/to/docs          │
│                                                          │
│  🚀 Your documentation will be more accessible in       │
│     minutes!                                            │
│                                                          │
│  💡 Tip: Use --checkpoint-mode phase1 to review baseline │
│     reports before applying fixes                        │
└─────────────────────────────────────────────────────────┘
```
