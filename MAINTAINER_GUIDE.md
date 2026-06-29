# Omnia Documentation -- Maintainer Guide

This document is the single source of truth for maintaining the Dell Omnia v2.1 documentation. Every convention described here must be followed when adding, editing, or reorganizing content. AI-assisted tools (Devin, Windsurf, etc.) should treat this file as their authoritative ruleset.

---

## 1. Project Overview

| Item | Value |
|------|-------|
| **Product** | Dell Omnia v2.1 |
| **Toolchain** | MkDocs Material |
| **Framework** | Diataxis (tutorials, how-to, reference, explanation) |
| **Source files** | `docs/` (107 Markdown files) |
| **Built site** | `site/` (HTML output) |
| **Config** | `mkdocs.yml` |
| **Branding CSS** | `docs/stylesheets/dell-brand.css` |
| **Theme overrides** | `docs/overrides/home.html` |
| **Dark mode JS** | `docs/javascripts/palette-fallback.js` |
| **Offline support** | `offline` plugin enabled for `file://` browsing |

---

## 2. Information Architecture (Diataxis)

The documentation follows the [Diataxis framework](https://diataxis.fr/). Every page must belong to exactly one of these categories:

| Section | Diataxis Type | Purpose | Question It Answers |
|---------|--------------|---------|---------------------|
| **Overview/** | Explanation | Architecture, concepts, mental models | "How does this work?" |
| **GetStarted/** | Tutorial | End-to-end guided deployment paths | "How do I get started?" |
| **HowTo/** | How-to guide | Task-oriented procedures for specific goals | "How do I do X?" |
| **Reference/** | Reference | Configuration specs, support matrices, samples | "What are the exact values?" |
| **Operations/** | How-to guide | Day-2 operational tasks (add nodes, cleanup, logs) | "How do I maintain this?" |
| **Troubleshooting/** | How-to guide | Symptom/Cause/Resolution for known issues | "Something broke -- how do I fix it?" |
| **Contributing/** | How-to guide | PR guidelines, DCO | "How do I contribute?" |

### Classification rules

- **If it teaches through a complete journey** -> GetStarted/ (tutorial)
- **If it solves a specific task** -> HowTo/ or Operations/
- **If it lists specifications, parameters, or supported values** -> Reference/
- **If it explains architecture or concepts** -> Overview/
- **If it diagnoses a problem** -> Troubleshooting/
- **Never mix types**: a how-to page must not include lengthy conceptual explanations. Link to the relevant Overview/ page instead.

---

## 3. Directory Structure

```
mkdocs.yml                            # Site config and nav tree
MAINTAINER_GUIDE.md                   # THIS FILE -- conventions reference
AI_ASSISTED_MAINTENANCE_GUIDE.md      # Step-by-step guide for content engineering team
docs/
  index.md                            # Landing page with hero + card grid
  assets/
    omnia-logo.png                    # Logo
    favicon.png
    images/                           # All images (original PNGs/JPGs only)
  stylesheets/
    dell-brand.css                    # Dell branding (~623 lines) -- do not modify branding/theme rules; diagram dark-mode selectors may be extended
  javascripts/
    palette-fallback.js              # Dark mode fallback -- DO NOT MODIFY
  overrides/
    home.html                        # Hero section override -- DO NOT MODIFY
  Overview/
    index.md                         # Section landing page
    architecture.md
    components.md
    network_topologies.md
    composable_roles.md
    telemetry_architecture.md
    security_model.md
    release_notes.md
    blogs.md
    glossary.md
  GetStarted/
    index.md
    prerequisites_checklist.md
    slurm_quickstart.md
    full_deployment.md
    k8s_telemetry_only.md
    buildstream_deployment.md
  HowTo/
    index.md
    Setup/                           # 11 files
    Slurm/                           # 7 files
    Kubernetes/                      # 3 files
    Storage/                         # 2 files
    Networking/                      # 2 files
    Authentication/                  # 4 files
    Telemetry/                       # 6 files
    Containers/                      # 2 files
    BuildStreaM/                     # 3 files
  Reference/
    index.md
    SupportMatrix/                   # 7 files
    Configuration/                   # 10 files
    SampleFiles/                     # 4 files
    ClusterRequirements/             # 3 files
    Playbooks/                       # 1 file
    Metrics/                         # 3 files
    Appendices/                      # 3 files
  Operations/
    index.md
    add_remove_nodes.md
    reprovision_cluster.md
    oim_cleanup.md
    log_management.md
    security_hardening.md
    best_practices_checklist.md
  Troubleshooting/
    index.md
    general.md
    provisioning.md
    slurm.md
    kubernetes.md
    telemetry.md
    authentication.md
    buildstream.md
    known_limitations.md
  Contributing/
    index.md
    pull_requests.md
site/                                # Built HTML output (DO NOT EDIT)
```

### Directory depth

Maximum depth is 3 levels: `docs/<Section>/<Subcategory>/<page>.md`. Do not create deeper nesting.

---

## 4. File Naming Conventions

| Rule | Example |
|------|---------|
| All lowercase | `configure_nfs.md`, not `Configure_NFS.md` |
| Underscores for word separation | `pxe_boot_nodes.md`, not `pxe-boot-nodes.md` |
| `.md` extension always | Never `.markdown` or `.txt` |
| Section landing pages | Always `index.md` |
| Verb-first for how-to files | `configure_`, `setup_`, `deploy_`, `verify_`, `create_`, `build_`, `add_`, `remove_` |
| Noun-first for reference files | `omnia_config.md`, `provision_config.md`, `servers.md` |
| Noun-first for troubleshooting | `provisioning.md`, `slurm.md`, `kubernetes.md` |

---

## 5. Page Templates

### 5.1 How-to Guide (HowTo/, Operations/)

```markdown
# Page Title

Brief 1-2 sentence description of what this guide accomplishes.

## Overview

Detailed explanation of what happens during this procedure and why it matters.

## Prerequisites

- Prerequisite one
- Prerequisite two
- [Link to related prerequisite guide](../path/to/guide.md)

## Procedure

1. **Step one description**

    Explanation of what this step does.

    ```bash title="Run on: OIM host"
    command here
    ```

2. **Step two description**

    ```yaml title="File: /opt/omnia/input/project_default/config.yml"
    parameter: value
    ```

    !!! note
        Important note about this step.

## Verification

1. Verify step one:

    ```bash title="Run on: OIM host"
    verification command
    ```

    Expected output (all nodes `Ready`):

    ```text title="Expected output"
    expected output here
    ```

## Next Steps

- [Next logical guide](../path/to/next.md)
- [Related guide](../path/to/related.md)

## Troubleshooting

- **Problem description**: Resolution summary. See [Troubleshooting page](../../Troubleshooting/topic.md) for details.
```

### 5.2 Reference -- Configuration Page

```markdown
# config_file.yml Reference

File path: `/opt/omnia/input/project_default/config_file.yml`

Brief description of what this configuration file controls.

## Parameter reference

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `param_name` | String | Yes | `(none)` | Description of the parameter |
| `nested.param` | Integer | No | `10` | Description with `inline code` examples |

## Usage example

```yaml
param_name: "value"
nested:
  param: 10
```

!!! note
    Security-sensitive values are stored in Ansible Vault.

!!! info "Related configuration"
    - [Related Config](../Configuration/related_config.md)
    - [Sample File](../SampleFiles/sample.md)
```

### 5.3 Reference -- Support Matrix Page

```markdown
# Supported Category Name

Brief description of what this matrix covers.

## Category matrix

| Column A | Column B | Column C | Notes |
|----------|----------|----------|-------|
| Value | Value | Value | Description |

## Additional details heading

Explanatory content with tables or lists as needed.

!!! info "Related references"
    - [Related Matrix](related_page.md)
    - [Configuration](../Configuration/config.md)
```

### 5.4 Troubleshooting Page

```markdown
# Subsystem Issues

Brief description of common issues covered on this page.

## Issue Category Heading

### Specific Issue Title

???+ note "Symptom"
    Description of what the user observes.
    Error messages in `inline code` or code blocks.

??? note "Cause"
    - Possible cause one
    - Possible cause two

??? note "Resolution"
    1. First resolution step:

        ```bash
        command here
        ```

    2. Second resolution step.

    3. Verify the fix:

        ```bash
        verification command
        ```

## Another Issue Category

### Another Specific Issue

???+ note "Symptom"
    ...

??? note "Cause"
    ...

??? note "Resolution"
    ...

!!! info "Related resources"
    - [Related How-to Guide](../HowTo/path/to/guide.md)
    - [Operations Guide](../Operations/guide.md)
```

### 5.5 Overview / Explanation Page

```markdown
# Concept Title

Introductory paragraph explaining the concept and its relevance to Omnia.

## Major concept section

Explanatory content. Use images where they add clarity:

![Descriptive alt text](../assets/images/image_name.png)

## Another section

Content with links to related how-to guides for practical application:
see [How to configure X](../HowTo/Category/configure_x.md).

## Key takeaways or summary (optional)

- Summary point one
- Summary point two
```

### 5.6 Section Index Page

```markdown
# Section Title

Brief 1-3 sentence description of what this section contains and who it is for.

!!! tip
    Contextual tip or guidance for the reader.
```

Index pages are intentionally minimal. The sidebar navigation (driven by `mkdocs.yml`) handles page discovery. Do not duplicate the nav tree in index pages.

Exception: `docs/index.md` (the landing page) uses grid cards and a hero section -- do not change its structure.

### 5.7 Get Started Tutorial Page

```markdown
# Tutorial Title

Brief description of the deployment path and what the reader will achieve.

![Relevant deployment flow image](../assets/images/image.jpg)

!!! note
    Important prerequisites or context.

## What you will deploy

Description of end-state after completing this tutorial.

## Prerequisites

- Prerequisite with link
- Hardware/software requirement

## Step 1: First Major Phase

Detailed instructions with code blocks.

```bash title="Run on: OIM host"
command
```

## Step 2: Next Major Phase

...

## Step N: Verify Your Deployment

Verification steps.

## What's next

- [Advanced configuration](../HowTo/path.md)
- [Operations guide](../Operations/guide.md)
```

---

## 6. Formatting Conventions

### 6.1 Headings

| Rule | Detail |
|------|--------|
| **H1 (`#`)** | Exactly one per page, always on line 1 or 2. This is the page title. |
| **H2 (`##`)** | Major section divisions. Typically 2-6 per page. |
| **H3 (`###`)** | Subsections within H2. Use sparingly -- only in detailed procedures or troubleshooting. |
| **H4+ (`####`)** | Avoid. If you need H4, consider restructuring into a separate page. |
| **Blank lines** | Always one blank line before and after every heading. |

### 6.2 Admonitions

**Static admonitions** (always visible):

```markdown
!!! note
    Content indented by 4 spaces.

!!! tip
    Helpful hint.

!!! warning
    Something that could cause problems.

!!! danger
    Something that will cause data loss or security issues.

!!! info "Custom title"
    Content with a custom title.
```

**Collapsible admonitions** (expandable):

```markdown
??? note "Collapsed by default"
    Content hidden until clicked.

???+ note "Expanded by default"
    Content visible, but can be collapsed.
```

**Usage rules:**
- Use `note` for general information, prerequisites, important clarifications
- Use `tip` for best practices, shortcuts, helpful hints
- Use `warning` for actions that could cause problems
- Use `danger` for actions that could cause data loss or security issues
- Use `info` for cross-reference blocks linking to related pages (typically at the end of a page)
- Use `???+ note "Symptom"` / `??? note "Cause"` / `??? note "Resolution"` exclusively in Troubleshooting pages
- 1-3 admonitions per page is typical. Do not overuse.
- Always a blank line before and after the admonition block.

### 6.3 Code Blocks

**Always specify a language tag and a `title` attribute for context:**

```markdown
```bash title="Run on: OIM host"
ansible-playbook prepare_oim.yml
```

```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
admin_network:
  nic_name: eno1
```

```text title="Expected output"
PLAY RECAP *****
oim : ok=45  changed=12
```
```

**Supported language tags:** `bash`, `yaml`, `json`, `text`, `ini`, `python`, `sql`

**Title conventions:**
- Shell commands: `title="Run on: OIM host"` or `title="Run on: compute node"`
- Config files: `title="File: /full/path/to/file.yml"`
- Expected output: `title="Expected output"`
- Sample content: `title="Example"`

**Rules:**
- Always include the `title` attribute -- this is a distinguishing convention of this project
- Blank line before and after every code block
- When code blocks appear inside numbered lists or admonitions, indent them by 4 spaces to maintain nesting

### 6.4 Tables

**Standard format:**

```markdown
| Column A | Column B | Column C |
|----------|----------|----------|
| Value | Value | Value |
```

**Rules:**
- Always include the header separator row (`| --- | --- |`)
- Use backticks for parameter names, commands, file paths, package names inside table cells
- Use bold for emphasis inside cells where needed
- Use links inside cells for cross-references
- Keep cells concise -- if a cell needs more than 2 lines, consider moving to a list or subsection

**Parameter reference tables** (Configuration pages) use exactly 5 columns:

```markdown
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
```

### 6.5 Lists

| Type | Syntax | Usage |
|------|--------|-------|
| Unordered | `- item` (hyphen) | Feature lists, prerequisites, bullet points |
| Ordered | `1. item` | Procedural steps, resolution steps |
| Definition | `**Term**` + indented description | Decision guides, Q&A |

- Use hyphens (`-`) for unordered lists, never asterisks (`*`)
- Use numbered lists (`1.`, `2.`, `3.`) for sequential procedures
- Indent continuation content by 4 spaces to maintain list nesting

### 6.6 Cross-References / Links

**Always use relative paths with `.md` extension:**

```markdown
[Link Text](../Section/page.md)
[Same directory](page.md)
[Subdirectory](Subcategory/page.md)
[Parent section](../../Section/page.md)
```

**Rules:**
- Always include the `.md` extension
- Use relative paths (not absolute `/HowTo/Setup/page.md`)
- Place cross-reference links contextually within the text, not as bare URLs
- For end-of-page "related resources" links, use an `!!! info` admonition block
- Never use anchor links (`#section-heading`) for cross-page references -- link to the page and let the reader find the section via the TOC

### 6.7 Images

**Format:**

```markdown
![Descriptive alt text](../assets/images/filename.png)
```

**Rules:**
- All images go in `docs/assets/images/`
- Use original PNG/JPG images only -- no Mermaid diagrams, no generated diagrams
- Always provide descriptive alt text
- Use relative paths from the current file
- For custom-styled images (e.g., logos in landing page), inline HTML is acceptable:
  ```html
  <img src="assets/images/logo.png" alt="Description" style="height: 60px;">
  ```

### 6.8 Inline Formatting

| Element | Syntax | When to use |
|---------|--------|-------------|
| **Bold** | `**text**` | Key terms, emphasis, step descriptions in procedures |
| *Italic* | `*text*` | Rarely -- only for introducing a term for the first time |
| `Inline code` | `` `text` `` | Commands, file paths, parameter names, service names, package names, variable names |
| Links | `[text](url)` | Cross-references, external links |

### 6.9 Horizontal Rules

```markdown
---
```

Use sparingly. Acceptable inside grid cards as visual separators. Do not use between regular content sections -- headings already provide visual separation.

### 6.10 Grid Cards (Landing Page Only)

Grid cards are used on `docs/index.md` for the section navigation cards. Format:

```markdown
<div class="grid cards" markdown>

-   :material-icon-name: **[Card Title](path/to/section/index.md)**

    ---

    Brief description of this section.

</div>
```

Do not use grid cards on other pages unless creating a new section landing page that requires visual navigation.

---

## 7. Navigation (mkdocs.yml)

The `nav:` tree in `mkdocs.yml` defines the sidebar and tab navigation. Every content page must appear in the nav tree.

### Adding a new page

1. Create the `.md` file in the correct section directory
2. Add an entry to the `nav:` tree in `mkdocs.yml` in the correct position
3. Format: `- "Display Name": Section/Subcategory/filename.md`

### Adding a new subcategory under HowTo/ or Reference/

1. Create the subdirectory: `docs/HowTo/NewCategory/`
2. Create pages inside it
3. Add to `mkdocs.yml` nav under the parent section:
   ```yaml
   - NewCategory:
     - Page Title: HowTo/NewCategory/page.md
   ```

### Rules

- Nav display names should be short (2-4 words)
- The order in the nav tree determines sidebar ordering -- keep it logical
- Section index pages use the `index.md` convention: `- Overview/index.md`
- Do not create sections with only one page -- either add more pages or place the content in the parent section

---

## 8. Dell Branding

The following files control Dell branding and must not be modified unless explicitly requested by Dell brand or design teams. The exception is `dell-brand.css`, where **diagram dark-mode selectors** may be extended to cover new images (follow the existing `img[alt*="..."]` pattern).

| File | Purpose |
|------|---------|
| `docs/stylesheets/dell-brand.css` | Dell color palette, typography, component styling (~623 lines). Diagram dark-mode selectors may be extended. |
| `docs/overrides/home.html` | Hero section with gradient, buttons, feature grid |
| `docs/javascripts/palette-fallback.js` | Dark mode toggle fallback for `file://` browsing |

### Brand colors (reference only)

| Token | Hex | Usage |
|-------|-----|-------|
| Dell Blue | `#0076CE` | Primary -- headers, links, navigation |
| Dell Dark | `#003566` | Tabs, footer, H1 borders |
| Dell Navy | `#001d3d` | Header/footer backgrounds |
| Dell Teal | `#00857C` | Accent -- hover states |
| Dell Light | `#4DA3E0` | Light blue variant |
| Dell Sky | `#00a8e8` | Sky blue gradient endpoint |

### Font

- Text: Roboto (Google Fonts)
- Code: Roboto Mono

### Dark mode

Dark mode is fully supported with automatic detection and a manual toggle. The following ensure it works offline (from a zip via `file://`):

- `offline` plugin in `mkdocs.yml`
- CSS fallback in `dell-brand.css` (sibling selectors for toggle labels)
- JS fallback in `palette-fallback.js` (manual scheme switching)
- `home.html` inherits the active scheme -- no hardcoded `data-md-color-scheme`

Do not add `data-md-color-scheme` attributes to any template or page.

---

## 9. Tone and Voice

| Aspect | Guideline |
|--------|-----------|
| **Audience** | Technical practitioners -- DevOps engineers, HPC admins, cluster engineers |
| **Formality** | Professional but approachable. Avoid unnecessary jargon. |
| **Voice** | Active, imperative. "Run the playbook", "Verify the service", "Check the logs" |
| **Clarity** | Direct and concise. One idea per sentence. Avoid filler words. |
| **Context** | Always specify where a command runs (via `title` on code blocks) |
| **Assumptions** | Assume technical competency with Linux, Ansible, and cluster management |
| **Pronouns** | Use "you" when addressing the reader. Avoid "we" and "I". |
| **Tense** | Present tense for descriptions. Imperative for instructions. |

**Examples:**

- Good: "Run the playbook on the OIM host."
- Bad: "You should now go ahead and run the playbook on the OIM host."
- Good: "This playbook configures NFS mounts on all compute nodes."
- Bad: "What this playbook does is it goes ahead and configures NFS mounts on all compute nodes."

---

## 10. Build, Preview, and Package

### Install dependencies

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

The Python API method avoids a CLI version warning. Build output goes to `site/`.

### Local preview

```bash
python -m mkdocs serve
```

Opens at `http://127.0.0.1:8000`.

### Package for sharing (zip)

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

### Build targets

- **0 errors, 0 warnings** is the required build status
- Always build after making changes and verify no errors before committing

---

## 11. Workflows

### Adding a new page

1. Determine the correct Diataxis section (see Section 2)
2. Determine the correct subcategory directory (see Section 3)
3. Create the file using the correct naming convention (see Section 4)
4. Write content using the appropriate page template (see Section 5)
5. Add the page to the `nav:` tree in `mkdocs.yml` (see Section 7)
6. Add any images to `docs/assets/images/`
7. Add cross-reference links from related pages
8. Build the site and verify 0 errors, 0 warnings
9. Open the built page in a browser and verify rendering

### Editing an existing page

1. Read the existing page fully before making changes
2. Preserve existing headings, section order, and formatting conventions
3. Do not remove or rewrite cross-reference links unless the target has moved
4. Do not remove admonitions unless the information is no longer accurate
5. Build and verify after changes

### Moving or renaming a page

1. Move/rename the file
2. Update the `nav:` tree in `mkdocs.yml`
3. Search all `.md` files for links pointing to the old path and update them
4. Build and verify no broken links

### Adding a new section

This should be rare. Before creating a new top-level section, verify it does not fit in an existing section.

1. Create the directory under `docs/`
2. Create an `index.md` using the Section Index template (Section 5.6)
3. Add pages to the directory
4. Add the section to the `nav:` tree in `mkdocs.yml`
5. Add a grid card to `docs/index.md` if the section should appear on the landing page
6. Build and verify

---

## 12. Things to NEVER Do

1. **Never modify `dell-brand.css`, `home.html`, or `palette-fallback.js`** without explicit design team approval
2. **Never add Mermaid diagrams or auto-generated diagrams** -- use original PNG/JPG images only
3. **Never create pages deeper than 3 levels** (`Section/Subcategory/page.md`)
4. **Never add a page without adding it to the `nav:` tree** in `mkdocs.yml`
5. **Never use absolute paths** in cross-reference links -- always use relative paths with `.md` extension
6. **Never mix Diataxis types** on a single page (e.g., don't put reference tables in a how-to guide)
7. **Never commit with build errors or warnings**
8. **Never edit files in `site/`** -- this is generated output
9. **Never use asterisks (`*`) for unordered lists** -- use hyphens (`-`)
10. **Never omit the `title` attribute on code blocks**
11. **Never add `data-md-color-scheme` attributes** to templates or pages
12. **Never use H4 or deeper headings** -- restructure into separate pages instead

---

## 13. MkDocs Material Features Reference

These features are enabled in `mkdocs.yml` and available for use in content:

| Feature | Usage |
|---------|-------|
| `content.code.copy` | Copy button appears automatically on all code blocks |
| `content.code.annotate` | Add annotations to code blocks with `(1)` markers |
| `content.tabs.link` | Tabbed content blocks stay in sync across the page |
| `pymdownx.details` | Collapsible admonitions (`???` / `???+`) |
| `pymdownx.superfences` | Fenced code blocks with language highlighting |
| `pymdownx.tabbed` | Tabbed content with `=== "Tab Name"` syntax |
| `pymdownx.tasklist` | Checkbox lists with `- [x]` / `- [ ]` |
| `navigation.tabs` | Top-level sections appear as tabs |
| `navigation.indexes` | Section index pages (`index.md`) |
| `search.suggest` | Search autocomplete |
| `toc.follow` | TOC auto-scrolls to current section |
| `tags` | Tag pages with metadata (available but not widely used yet) |

---

## 14. mkdocs.yml -- Key Settings to Preserve

Do not change these settings unless there is a specific, documented reason:

```yaml
use_directory_urls: false          # Required for file:// offline browsing
plugins:
  - offline                        # Required for file:// offline browsing
  - search
  - tags
theme:
  name: material
  custom_dir: docs/overrides       # Hero section override
  logo: assets/omnia-logo.png
  favicon: assets/favicon.png
  font:
    text: Roboto
    code: Roboto Mono
extra:
  generator: false                 # Hides "Made with MkDocs" footer
copyright: "Copyright &copy; 2025 Dell Technologies. All rights reserved."
```

The `nav:` tree, `markdown_extensions:`, and `extra_css:`/`extra_javascript:` entries are the only sections that should be routinely updated.
