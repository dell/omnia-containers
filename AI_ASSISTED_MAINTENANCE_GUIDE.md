# AI-Assisted Documentation Maintenance Guide

This guide explains how the content engineering team can use AI coding assistants (Devin or Windsurf) to maintain the Dell Omnia v2.1 documentation while preserving its structure, formatting, and branding conventions.

---

## What's Included

The documentation ships with built-in rules that AI assistants automatically follow:

| File | Purpose | Auto-loaded? |
|------|---------|-------------|
| `MAINTAINER_GUIDE.md` | Complete conventions reference (human-readable) | No -- read manually or referenced by AI |
| `.devin/skills/omnia-docs-maintainer/SKILL.md` | Devin skill with all rules and workflows | Yes, when invoked in Devin |
| `.windsurfrules` | Windsurf rules with all conventions | Yes, auto-loaded by Windsurf IDE |

All three files encode the same guidelines. `MAINTAINER_GUIDE.md` is the single source of truth.

---

## Option A: Using Devin

### Initial Setup

1. Open the project directory in Devin (CLI or browser)
2. The `.devin/skills/omnia-docs-maintainer/` skill is available automatically

### Before Each Task

Invoke the skill at the start of your session:

```
Use the omnia-docs-maintainer skill
```

Devin will load all the documentation rules -- Diataxis classification, formatting conventions, page templates, file naming, build commands, and prohibited actions.

### Example Tasks

**Adding a new how-to page:**

```
Using the omnia-docs-maintainer skill, add a new how-to guide for configuring
BeeGFS parallel storage. It should go in HowTo/Storage/. Follow the how-to
page template. Add it to the nav tree in mkdocs.yml. Build and verify.
```

**Editing an existing page:**

```
Using the omnia-docs-maintainer skill, update the NFS configuration guide
at docs/HowTo/Storage/configure_nfs.md to add a section on NFSv4
Kerberos authentication. Preserve the existing structure and formatting.
Build and verify.
```

**Adding a new troubleshooting entry:**

```
Using the omnia-docs-maintainer skill, add a new troubleshooting entry to
docs/Troubleshooting/slurm.md for the issue where slurmctld fails
to start after a node reboot. Use the Symptom/Cause/Resolution format with
collapsible sections. Build and verify.
```

**Moving a page:**

```
Using the omnia-docs-maintainer skill, move configure_roce.md from
HowTo/Networking/ to HowTo/Storage/. Update the nav tree and fix all
cross-reference links across the documentation. Build and verify.
```

**Checking convention compliance:**

```
Using the omnia-docs-maintainer skill, review all pages in HowTo/Setup/
and report any violations of the formatting conventions (missing code block
titles, wrong heading levels, incorrect list syntax, etc.).
```

### What Devin Will Do Automatically (When Skill Is Active)

- Read `MAINTAINER_GUIDE.md` before making changes
- Use the correct page template based on Diataxis type
- Follow file naming conventions
- Add `title` attributes to all code blocks
- Use relative paths with `.md` extension for links
- Add new pages to the `nav:` tree in `mkdocs.yml`
- Build the site and check for errors after changes
- Refuse to modify protected branding files

---

## Option B: Using Windsurf IDE

### Initial Setup

1. Open the project root directory in Windsurf IDE
2. The `.windsurfrules` file is auto-loaded -- no manual step needed
3. Windsurf's AI (Cascade) will automatically follow the rules for every task

### Before Each Task

No explicit invocation needed. Windsurf reads `.windsurfrules` automatically when the project is open. However, for complex tasks, you can remind the AI:

```
Follow the documentation conventions in MAINTAINER_GUIDE.md
```

### Example Tasks

The same task descriptions work in Windsurf. Open the Cascade chat and type:

**Adding a new how-to page:**

```
Add a new how-to guide for configuring BeeGFS parallel storage.
Place it in docs/HowTo/Storage/configure_beegfs.md.
Follow the how-to page template from MAINTAINER_GUIDE.md.
Add it to the nav tree. Build and verify.
```

**Editing an existing page:**

```
Update docs/HowTo/Storage/configure_nfs.md to add a section
on NFSv4 Kerberos authentication. Preserve the existing structure.
Build and verify.
```

**Bulk convention check:**

```
Review all .md files in docs/Reference/Configuration/ and
list any formatting violations based on our documentation conventions.
```

### What Windsurf Will Do Automatically

Same as Devin -- the `.windsurfrules` file contains all the same rules. Windsurf will:

- Follow Diataxis classification
- Use correct page templates
- Apply formatting conventions (code block titles, heading levels, list syntax)
- Use relative paths for links
- Update `mkdocs.yml` nav when adding pages
- Build and verify
- Refuse to modify protected files

---

## Option C: Manual Maintenance (Without AI)

If maintaining documentation without an AI assistant:

1. Read `MAINTAINER_GUIDE.md` thoroughly before starting
2. Use the page templates in Section 5 as starting points
3. Follow the verification checklist at the end of the Maintainer Guide after every change
4. Always build and check for errors:

```bash
python -c "
from mkdocs.commands.build import build
from mkdocs.config import load_config
cfg = load_config('mkdocs.yml')
build(cfg)
"
```

---

## Common Maintenance Scenarios

### 1. New Omnia Feature Added

| Step | Action |
|------|--------|
| 1 | Add overview content to relevant `Overview/` page (or create new page) |
| 2 | Add how-to guide(s) in `HowTo/<Category>/` |
| 3 | Add configuration reference in `Reference/Configuration/` |
| 4 | Update support matrices in `Reference/SupportMatrix/` if applicable |
| 5 | Add troubleshooting entries in `Troubleshooting/` |
| 6 | Update `GetStarted/` tutorials if the feature affects deployment paths |
| 7 | Add all new pages to `nav:` in `mkdocs.yml` |
| 8 | Build and verify |

### 2. Configuration Parameter Changed

| Step | Action |
|------|--------|
| 1 | Update the parameter table in the relevant `Reference/Configuration/` page |
| 2 | Update any how-to guides that reference the parameter |
| 3 | Update sample files in `Reference/SampleFiles/` if applicable |
| 4 | Build and verify |

### 3. New OS or Hardware Added to Support Matrix

| Step | Action |
|------|--------|
| 1 | Update the relevant table in `Reference/SupportMatrix/` |
| 2 | Update prerequisites in affected `GetStarted/` tutorials |
| 3 | Update any how-to guides with OS-specific instructions |
| 4 | Build and verify |

### 4. Bug Fix with Known Workaround

| Step | Action |
|------|--------|
| 1 | Add Symptom/Cause/Resolution entry to relevant `Troubleshooting/` page |
| 2 | Link from the related how-to guide's Troubleshooting section |
| 3 | Build and verify |

### 5. Omnia Version Update

| Step | Action |
|------|--------|
| 1 | Update version references across all pages |
| 2 | Update `Overview/release_notes.md` |
| 3 | Update support matrices |
| 4 | Update `copyright` in `mkdocs.yml` if the year changed |
| 5 | Review and update all configuration reference pages |
| 6 | Build, verify, and package new zip |

---

## Build, Preview, and Package

### Install dependencies (one-time)

```bash
pip install mkdocs-material
```

### Build the site

```bash
python -c "
from mkdocs.commands.build import build
from mkdocs.config import load_config
cfg = load_config('mkdocs.yml')
build(cfg)
"
```

Required: 0 errors, 0 warnings.

### Local preview

```bash
python -m mkdocs serve
```

Opens at http://127.0.0.1:8000

### Package for sharing

```bash
python -c "
from mkdocs.commands.build import build
from mkdocs.config import load_config
import shutil, os
cfg = load_config('mkdocs.yml')
build(cfg)
zip_name = 'Dell_Omnia_Docs_v2.1'
if os.path.exists(zip_name + '.zip'):
    os.remove(zip_name + '.zip')
shutil.make_archive(zip_name, 'zip', 'site')
"
```

---

## Quick Reference Card

| I want to... | AI prompt |
|--------------|-----------|
| Add a how-to page | "Add a how-to guide for [topic] in HowTo/[Category]/. Use the how-to template. Add to nav. Build." |
| Add a config reference | "Add a config reference for [file].yml in Reference/Configuration/. Use the config reference template with 5-column parameter table. Add to nav. Build." |
| Add a troubleshooting entry | "Add a troubleshooting entry to Troubleshooting/[topic].md for [issue]. Use Symptom/Cause/Resolution collapsible format. Build." |
| Update a support matrix | "Update Reference/SupportMatrix/[page].md to add [item] to the matrix table. Build." |
| Move/rename a page | "Move [old path] to [new path]. Update nav tree and fix all cross-reference links. Build." |
| Check for convention violations | "Review all pages in [directory] for formatting violations per MAINTAINER_GUIDE.md." |
| Update for new version | "Update all version references from [old] to [new]. Update release notes, support matrices, and config references. Build." |

---

## Troubleshooting This Guide

**AI is not following conventions:**
- Devin: Make sure you invoked the skill (`Use the omnia-docs-maintainer skill`)
- Windsurf: Verify `.windsurfrules` exists in the project root and the project is open in Windsurf
- Either tool: Explicitly reference `MAINTAINER_GUIDE.md` in your prompt

**Build fails after AI changes:**
- Run the build command manually and read the error output
- Common issues: missing nav entry, broken link path, syntax error in admonition indentation
- Ask the AI: "The build failed with [error]. Fix it following the documentation conventions."

**AI modified a protected file:**
- Check `dell-brand.css`, `home.html`, and `palette-fallback.js` with `git diff`
- Revert any changes to these files
- Remind the AI: "Do not modify branding files."

**Page appears in wrong section:**
- Review the Diataxis classification table in `MAINTAINER_GUIDE.md` Section 2
- Ask the AI: "Reclassify [page] according to Diataxis and move it to the correct section."
