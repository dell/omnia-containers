# Omnia Documentation Maintainer Skill

## Description

This skill provides all rules, conventions, and workflows for maintaining the Dell Omnia v2.1 documentation built with MkDocs Material. Invoke this skill before adding, editing, moving, or reorganizing any documentation page.

## When to Use

- Adding a new documentation page
- Editing an existing page
- Moving or renaming a page
- Adding a new section or subcategory
- Updating the navigation tree
- Adding images
- Fixing broken links
- Reviewing documentation for convention compliance

## Authoritative Reference

The single source of truth for all conventions is:

```
MAINTAINER_GUIDE.md
```

**You MUST read this file at the start of every task.** It contains the complete specification for structure, formatting, templates, branding, and workflows.

## Quick Reference -- Core Rules

The following is a summary. When in doubt, defer to `MAINTAINER_GUIDE.md`.

---

### Project Layout

- **Config**: `mkdocs.yml` -- site config and nav tree
- **Content**: `docs/` -- all Markdown source files (107 pages)
- **Built site**: `site/` -- generated HTML output (NEVER edit)
- **Branding**: `docs/stylesheets/dell-brand.css` (do not modify branding/theme rules; diagram dark-mode selectors may be extended)
- **Theme overrides**: `docs/overrides/home.html` (DO NOT MODIFY)
- **Dark mode JS**: `docs/javascripts/palette-fallback.js` (DO NOT MODIFY)
- **Images**: `docs/assets/images/` -- original PNGs/JPGs only

### Diataxis Classification

Every page belongs to exactly one type. Use this decision tree:

1. **Teaches through a complete journey** -> `GetStarted/` (tutorial)
2. **Solves a specific task** -> `HowTo/` or `Operations/`
3. **Lists specifications, parameters, or supported values** -> `Reference/`
4. **Explains architecture or concepts** -> `Overview/`
5. **Diagnoses a problem** -> `Troubleshooting/`
6. **Describes contribution process** -> `Contributing/`

Never mix types on a single page. Link to other sections instead.

### Directory Structure (max depth: 3)

```
docs/<Section>/<Subcategory>/<page>.md
```

Sections: `Overview/`, `GetStarted/`, `HowTo/`, `Reference/`, `Operations/`, `Troubleshooting/`, `Contributing/`

HowTo subcategories: `Setup/`, `Slurm/`, `Kubernetes/`, `Storage/`, `Networking/`, `Authentication/`, `Telemetry/`, `Containers/`, `BuildStreaM/`

Reference subcategories: `SupportMatrix/`, `Configuration/`, `SampleFiles/`, `ClusterRequirements/`, `Playbooks/`, `Metrics/`, `Appendices/`

### File Naming

- All lowercase with underscores: `configure_nfs.md`
- `.md` extension always
- Section landing pages: always `index.md`
- HowTo/Operations files: verb-first (`configure_`, `setup_`, `deploy_`, `verify_`, `create_`, `build_`, `add_`, `remove_`)
- Reference files: noun-first (`omnia_config.md`, `servers.md`)
- Troubleshooting files: noun-first (`provisioning.md`, `slurm.md`)

### Headings

- **H1 (`#`)**: Exactly ONE per page, always first line. This is the page title.
- **H2 (`##`)**: Major section divisions (2-6 per page)
- **H3 (`###`)**: Subsections, used sparingly (detailed procedures, troubleshooting sub-issues)
- **H4+ (`####`)**: NEVER use. Restructure into separate pages instead.
- Always one blank line before and after every heading.

### Code Blocks -- ALWAYS Include Title Attribute

This is a distinguishing convention of this project. Every code block MUST have a `title`:

```
```bash title="Run on: OIM host"
ansible-playbook prepare_oim.yml
```
```

```
```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
admin_network:
  nic_name: eno1
```
```

```
```text title="Expected output"
PLAY RECAP *****
oim : ok=45  changed=12
```
```

Title conventions:
- Shell commands: `title="Run on: OIM host"` or `title="Run on: compute node"`
- Config files: `title="File: /full/path/to/file.yml"`
- Output: `title="Expected output"`
- Samples: `title="Example"`

Language tags: `bash`, `yaml`, `json`, `text`, `ini`, `python`, `sql`

### Admonitions

Static (always visible):
```
!!! note
    Content indented by 4 spaces.

!!! tip
    Best practices and hints.

!!! warning
    Could cause problems.

!!! danger
    Could cause data loss or security issues.

!!! info "Custom title"
    Cross-reference blocks at end of page.
```

Collapsible (Troubleshooting pages only):
```
???+ note "Symptom"       # Expanded by default
    What the user observes.

??? note "Cause"           # Collapsed by default
    Root cause list.

??? note "Resolution"      # Collapsed by default
    Numbered fix steps.
```

Rules:
- 1-3 admonitions per page typical
- End-of-page cross-references use `!!! info "Related resources"`
- Blank line before and after every admonition block

### Tables

Standard format with pipe delimiters:
```
| Column A | Column B |
|----------|----------|
| Value    | Value    |
```

Configuration reference tables use exactly 5 columns:
```
| Parameter | Type | Required | Default | Description |
```

Use backticks for parameter names, commands, and file paths in cells.

### Lists

- Unordered: hyphens (`-`), NEVER asterisks (`*`)
- Ordered: `1.`, `2.`, `3.` for sequential procedures
- Indent continuation by 4 spaces to maintain nesting

### Cross-References

Always relative paths with `.md` extension:
```
[Link Text](../Section/page.md)
[Same directory](page.md)
[Subdirectory](Subcategory/page.md)
```

Never use absolute paths. Never omit `.md` extension.

### Images

```
![Descriptive alt text](../assets/images/filename.png)
```

- All images in `docs/assets/images/`
- Original PNG/JPG only -- NO Mermaid, NO generated diagrams
- Always provide descriptive alt text

### Inline Formatting

- **Bold** (`**text**`): key terms, emphasis, step descriptions
- `Inline code` (`` `text` ``): commands, file paths, parameters, services, packages, variables
- Hyphens (`-`) for unordered lists, never asterisks

### Tone and Voice

- Active, imperative: "Run the playbook", "Verify the service"
- Direct and concise. One idea per sentence.
- Address reader as "you"
- Present tense for descriptions, imperative for instructions
- Assume technical competency with Linux, Ansible, cluster management

---

## Page Templates

Before creating any new page, read `MAINTAINER_GUIDE.md` Section 5 for the complete templates. Summary:

| Page Type | Template Location in Guide | Key Sections |
|-----------|--------------------------|--------------|
| How-to Guide | Section 5.1 | Overview, Prerequisites, Procedure, Verification, Next Steps, Troubleshooting |
| Config Reference | Section 5.2 | Parameter reference (5-col table), Usage example, Related config |
| Support Matrix | Section 5.3 | Matrix table, Additional details, Related references |
| Troubleshooting | Section 5.4 | Issue Category > Specific Issue > Symptom/Cause/Resolution |
| Overview/Explanation | Section 5.5 | Concept sections with images, links to how-to guides |
| Section Index | Section 5.6 | Minimal: title, brief description, optional tip admonition |
| Tutorial (GetStarted) | Section 5.7 | What you will deploy, Prerequisites, Numbered steps, What's next |

---

## Workflows

### Adding a New Page

Execute these steps in order:

1. **Classify**: Determine the Diataxis type (tutorial, how-to, reference, explanation, troubleshooting)
2. **Locate**: Identify the correct section and subcategory directory
3. **Name**: Create file with correct naming convention (lowercase, underscores, verb/noun-first)
4. **Template**: Use the correct page template from MAINTAINER_GUIDE.md Section 5
5. **Write**: Author content following all formatting conventions
6. **Nav**: Add the page to the `nav:` tree in `mkdocs.yml`
7. **Images**: Add any new images to `docs/assets/images/`
8. **Links**: Add cross-reference links from related existing pages
9. **Build**: Run the build and verify 0 errors, 0 warnings
10. **Review**: Open the built page in a browser and verify rendering

### Editing an Existing Page

1. **Read**: Read the entire existing page before making any changes
2. **Preserve**: Keep existing heading structure, section order, and formatting
3. **Links**: Do not remove cross-reference links unless the target has been removed
4. **Admonitions**: Do not remove admonitions unless the information is no longer accurate
5. **Build**: Run the build and verify after changes

### Moving or Renaming a Page

1. **Move/Rename**: Move or rename the `.md` file
2. **Nav**: Update the `nav:` tree in `mkdocs.yml`
3. **Links**: Search ALL `.md` files for links to the old path and update them:
   ```bash
   grep -r "old_filename.md" docs/
   ```
4. **Build**: Run the build and verify no broken links

### Adding a New Subcategory

1. Create the subdirectory under the appropriate section
2. Create pages inside it
3. Add to the `nav:` tree under the parent section
4. Build and verify

---

## Build Commands

### Build the site
```bash
python -c "
from mkdocs.commands.build import build
from mkdocs.config import load_config
cfg = load_config('mkdocs.yml')
build(cfg)
"
```

### Local preview
```bash
python -m mkdocs serve
```

### Package as zip
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

### Required build status: 0 errors, 0 warnings

---

## Absolute Prohibitions

1. **NEVER modify** `dell-brand.css` branding/theme rules, `home.html`, or `palette-fallback.js` (diagram dark-mode selectors in `dell-brand.css` may be extended)
2. **NEVER add** Mermaid diagrams or auto-generated diagrams
3. **NEVER create** pages deeper than 3 levels
4. **NEVER add** a page without adding it to the `nav:` tree
5. **NEVER use** absolute paths in cross-reference links
6. **NEVER mix** Diataxis types on a single page
7. **NEVER commit** with build errors or warnings
8. **NEVER edit** files in `site/`
9. **NEVER use** asterisks for unordered lists (use hyphens)
10. **NEVER omit** the `title` attribute on code blocks
11. **NEVER add** `data-md-color-scheme` attributes to templates or pages
12. **NEVER use** H4 or deeper headings
13. **NEVER remove** existing cross-reference links without verifying the target is gone
14. **NEVER change** `use_directory_urls: false` in mkdocs.yml (required for offline browsing)
15. **NEVER remove** the `offline` plugin from mkdocs.yml

---

## mkdocs.yml -- Protected Settings

Do not change these settings:

```yaml
use_directory_urls: false          # Required for file:// offline browsing
plugins:
  - offline                        # Required for file:// offline browsing
  - search
  - tags
theme:
  name: material
  custom_dir: docs/overrides
  logo: assets/omnia-logo.png
  favicon: assets/favicon.png
  font:
    text: Roboto
    code: Roboto Mono
extra:
  generator: false                 # Hides "Made with MkDocs" footer
copyright: "Copyright &copy; 2025 Dell Technologies. All rights reserved."
```

Only these sections should be routinely updated: `nav:`, `markdown_extensions:`, `extra_css:`, `extra_javascript:`.

---

## Dell Branding (Reference Only -- Do Not Modify)

| Token | Hex | Usage |
|-------|-----|-------|
| Dell Blue | `#0076CE` | Primary -- headers, links, navigation |
| Dell Dark | `#003566` | Tabs, footer, H1 borders |
| Dell Navy | `#001d3d` | Header/footer backgrounds |
| Dell Teal | `#00857C` | Accent -- hover states |
| Font: Text | Roboto | Via Google Fonts |
| Font: Code | Roboto Mono | Via Google Fonts |

Dark mode is fully supported. Do not add hardcoded color scheme attributes.

---

## MkDocs Material Features Available

| Feature | How to Use |
|---------|-----------|
| Code copy button | Automatic on all code blocks |
| Code annotations | `(1)` markers inside code blocks |
| Linked tabs | `=== "Tab Name"` syntax |
| Collapsible admonitions | `???` / `???+` syntax |
| Task lists | `- [x]` / `- [ ]` syntax |
| Search autocomplete | Automatic |
| TOC auto-scroll | Automatic |
| Tags | Add `tags:` to page front matter |

---

## Verification Checklist

After any change, verify:

- [ ] File follows the correct page template for its Diataxis type
- [ ] File naming convention is correct (lowercase, underscores, verb/noun-first)
- [ ] H1 is present exactly once, on the first line
- [ ] All code blocks have a `title` attribute
- [ ] All cross-reference links use relative paths with `.md` extension
- [ ] All images are in `docs/assets/images/` and use relative paths
- [ ] Page is added to the `nav:` tree in `mkdocs.yml`
- [ ] Build completes with 0 errors, 0 warnings
- [ ] Page renders correctly in the browser
- [ ] Admonitions use correct types and formatting
- [ ] Lists use hyphens (not asterisks)
- [ ] No H4 or deeper headings
- [ ] No Diataxis type mixing
- [ ] Tone is active, imperative, and concise
