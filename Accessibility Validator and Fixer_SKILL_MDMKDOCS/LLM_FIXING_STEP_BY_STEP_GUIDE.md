# Step-by-Step Guide: LLM-Enhanced Accessibility Fixing

## 🎯 Quick Start Guide

This guide walks you through the complete process of using the LLM-enhanced automation to fix accessibility errors in your RST documentation.

---

## 📋 Prerequisites

- Python 3.6 or higher installed
- RST documentation files ready for validation
- Accessibility Validator & Fixer skill files
- (Optional) LLM API key for enhanced fixing

---

## 🚀 Step-by-Step Process

### Step 1: Prepare Your Documentation

**Action**: Ensure your RST files are ready for processing.

```bash
# Navigate to your documentation directory
cd path/to/your/documentation

# Verify files exist
ls *.rst
```

**What to check**:
- Files are in RST format (.rst extension)
- Files are accessible and readable
- You have write permissions for the files

---

### Step 2: Configure LLM Settings

**Action**: Set up the LLM configuration for your needs.

**Option A: Local Rule-Based (Recommended for Start)**

Edit `llm_config.json`:
```json
{
  "enabled": true,
  "provider": "local",
  "model": "local-rules"
}
```

**Benefits**:
- No API key required
- Works offline
- Fast processing
- Good for common patterns

**Option B: API-Based (For Complex Content)**

Edit `llm_config.json`:
```json
{
  "enabled": true,
  "provider": "openai",
  "api_key": "your-openai-api-key",
  "model": "gpt-4"
}
```

**Benefits**:
- Better context understanding
- Higher accuracy for complex content
- More sophisticated fixes

---

### Step 3: Run Initial Validation

**Action**: Generate an accessibility report to identify issues.

```bash
# Navigate to the skill directory
cd "Accessibility Validator and Fixer_SKILL_MDMKDOCS"

# Run validation
python run_omnia_accessibility.py path/to/docs --skip-fixes
```

**What happens**:
- Scans all RST files
- Identifies accessibility issues
- Generates JSON report
- Creates visual HTML report

**Output locations**:
- JSON report: `reports/baseline_validation/accessibility_report.json`
- HTML report: `reports/accessibility_visual_report.html`

---

### Step 4: Review the Validation Report

**Action**: Understand what issues need fixing.

```bash
# Open the HTML report in your browser
start reports/accessibility_visual_report.html
```

**Key information to review**:
- Total issues by severity (ERROR, WARNING, SUGGESTION)
- Issues by type (missing alt text, insecure links, etc.)
- Files affected
- Specific line numbers and context

---

### Step 5: Run LLM-Enhanced Fixing

**Action**: Apply intelligent fixes using the LLM automation.

```bash
# Run LLM-enhanced fixes
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json
```

**What happens**:
1. Categorizes issues into auto-fixable, LLM-fixable, manual-only
2. Applies intelligent fixes to LLM-fixable issues
3. Creates backup of original files
4. Re-validates after fixes
5. Generates updated reports

**Output locations**:
- LLM fix report: `reports/llm_fix_report.txt`
- Updated report: `reports/current_status/accessibility_report_llm_fixed.json`
- Backup files: `.llm_backup/` directory

---

### Step 6: Review the LLM Fix Report

**Action**: Check what was fixed and what needs attention.

```bash
# View the LLM fix report
type reports\llm_fix_report.txt
```

**What to look for**:
- Total LLM-fixable issues found
- Successfully fixed count
- Failed fixes count
- Skipped issues count
- Specific fixes applied with file locations

**Example output**:
```
SUMMARY:
  Total LLM-fixable issues: 15
  Successfully fixed: 12
  Failed: 1
  Skipped: 2
```

---

### Step 7: Review Backup Files (Optional)

**Action**: Check original files if needed for rollback.

```bash
# Navigate to backup directory
cd .llm_backup

# View backup files
dir
```

**When to use backups**:
- If a fix was incorrect
- If you need to compare before/after
- If you want to rollback changes

---

### Step 8: Re-validate After LLM Fixes

**Action**: Run validation again to measure improvement.

```bash
# Run validation to see remaining issues
python run_omnia_accessibility.py path/to/docs --skip-fixes
```

**What to compare**:
- Total issues before vs after
- Issues by severity
- Issues by type
- Files still with issues

---

### Step 9: Manual Fixing for Remaining Issues

**Action**: Fix issues that require manual intervention.

**Common manual fixes**:

**Missing Image Alt Text**:
```rst
.. image:: screenshot.png
   :alt: Descriptive text showing the interface elements
```

**Empty Section Title**:
```rst
Configuration
============

Content here...
```

**Non-Descriptive Links**:
```rst
`View the configuration guide <https://docs.example.com/config>`_
```

**Process**:
1. Open the file in your IDE
2. Navigate to the line number from the report
3. Apply the fix manually
4. Save the file

---

### Step 10: Final Validation

**Action**: Confirm all issues are resolved.

```bash
# Run final validation
python run_omnia_accessibility.py path/to/docs --skip-fixes
```

**Success criteria**:
- No ERROR level issues
- Minimal WARNING level issues
- Only SUGGESTION level issues remaining (optional)

---

### Step 11: Commit Changes

**Action**: Save your work to version control.

```bash
# Review changes
git diff

# Add files
git add .

# Commit
git commit -m "Fix accessibility issues using LLM-enhanced automation"

# Push
git push
```

---

## 🔄 Alternative Workflows

### Workflow A: Dry Run First

**Use when**: You want to see what would be fixed without applying changes.

```bash
# Dry run mode
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json --dry-run
```

**Benefits**:
- No changes applied to files
- See what fixes would be generated
- Test configuration settings

---

### Workflow B: Standalone LLM Fixer

**Use when**: You already have a validation report and want to apply LLM fixes only.

```bash
# Run standalone LLM fixer
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json
```

**Benefits**:
- Faster processing
- No re-validation
- Direct control over fixing process

---

### Workflow C: Combined Auto + LLM

**Use when**: You want to apply both automatic and LLM fixes in sequence.

```bash
# First run auto fixes
python run_omnia_accessibility.py path/to/docs

# Then run LLM fixes on remaining issues
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json
```

**Benefits**:
- Maximum automation
- Handles both simple and complex issues
- Reduces manual work significantly

---

## 🛠️ Troubleshooting Steps

### Problem: No LLM fixes applied

**Step 1**: Check configuration
```bash
# Verify LLM config exists
type llm_config.json
```

**Step 2**: Check if LLM is enabled
```json
{
  "enabled": true  // Should be true
}
```

**Step 3**: Check for LLM-fixable issues
```bash
# Review the validation report
type reports/baseline_validation/accessibility_report.json
```

**Step 4**: Verify fix strategies are enabled
```json
{
  "fix_strategies": {
    "MISSING_IMAGE_ALT": {
      "enabled": true  // Should be true for types you want to fix
    }
  }
}
```

---

### Problem: Fixes are not appropriate

**Step 1**: Review the LLM fix report
```bash
type reports\llm_fix_report.txt
```

**Step 2**: Check backup files
```bash
cd .llm_backup
dir
```

**Step 3**: Restore from backup if needed
```bash
# Copy backup file to original location
copy .llm_backup\filename_YYYYMMDD_HHMMSS.bak original_file.rst
```

**Step 4**: Customize local rules in config
```json
{
  "local_rules": {
    "image_alt_patterns": {
      "screenshot": "Custom description for"
    }
  }
}
```

---

### Problem: API integration not working

**Step 1**: Check API key
```bash
# Verify API key in config
type llm_config.json
```

**Step 2**: Test API connectivity
```bash
# Test with curl or similar tool
curl https://api.openai.com/v1/models
```

**Step 3**: Switch to local provider
```json
{
  "provider": "local"  // Use local rules instead
}
```

---

## 📊 Measuring Success

### Before LLM Fixes

Run validation and note:
- Total issues: ___
- ERROR level: ___
- WARNING level: ___
- SUGGESTION level: ___

### After LLM Fixes

Run validation again and note:
- Total issues: ___
- ERROR level: ___
- WARNING level: ___
- SUGGESTION level: ___

### Calculate Improvement

```
Improvement % = (Before - After) / Before * 100
```

**Example**:
- Before: 50 issues
- After: 15 issues
- Improvement: (50-15)/50 * 100 = 70%

---

## 🎯 Best Practices

### 1. Always Start with Dry Run

```bash
python llm_enhanced_fixer.py report.json --dry-run
```

### 2. Review Before Applying

- Check the LLM fix report
- Review a few sample fixes manually
- Verify configuration matches your needs

### 3. Use Backups

- Keep backups enabled
- Know how to restore if needed
- Review backup directory location

### 4. Re-validate After Fixes

- Always run validation after LLM fixes
- Compare before/after metrics
- Track improvement over time

### 5. Manual Review Required

- Some issues still need manual intervention
- Review all LLM fixes in your IDE
- Make corrections as needed

---

## ⚡ Quick Reference Commands

```bash
# Navigate to skill directory
cd "Accessibility Validator and Fixer_SKILL_MDMKDOCS"

# Validate only
python run_omnia_accessibility.py path/to/docs --skip-fixes

# LLM-enhanced fixing
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json

# Dry run
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json --dry-run

# Custom LLM config
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json --llm-config custom_config.json

# View reports
type reports\llm_fix_report.txt
start reports\accessibility_visual_report.html
```

---

## 📈 Expected Results

### Time Savings

- **Traditional workflow**: 2-3 hours for 50 issues
- **LLM-enhanced workflow**: 20-30 minutes for 50 issues
- **Time saved**: ~80%

### Fix Rate

- **Auto-fixable issues**: 100% fixed automatically
- **LLM-fixable issues**: 70-80% fixed successfully
- **Manual-only issues**: 0% automated (require manual work)

### Typical Results

For a documentation set with 50 accessibility issues:
- 15 issues: Auto-fixable (insecure links, bare URLs) → 100% fixed
- 25 issues: LLM-fixable (alt text, links, titles) → 80% fixed (20 issues)
- 10 issues: Manual-only (complex context) → 0% automated

**Total**: 35/50 issues (70%) fixed automatically, 15 require manual work

---

## 🎓 Advanced Usage

### Custom Fix Patterns

Edit `llm_config.json` to add custom patterns:

```json
{
  "local_rules": {
    "image_alt_patterns": {
      "my_custom_pattern": "Custom description for"
    }
  }
}
```

### Selective Issue Type Fixing

Enable/disable specific issue types:

```json
{
  "fix_strategies": {
    "MISSING_IMAGE_ALT": {
      "enabled": true
    },
    "NON_DESCRIPTIVE_LINK": {
      "enabled": false
    }
  }
}
```

### Batch Processing

Process multiple documentation sets:

```bash
# Set 1
python run_omnia_accessibility.py docs/set1
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json

# Set 2
python run_omnia_accessibility.py docs/set2
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json

# Set 3
python run_omnia_accessibility.py docs/set3
python llm_enhanced_fixer.py reports/baseline_validation/accessibility_report.json
```

---

## ✅ Checklist

Before starting:
- [ ] Python 3.6+ installed
- [ ] RST files ready
- [ ] LLM config reviewed
- [ ] Backup enabled
- [ ] Write permissions confirmed

After fixing:
- [ ] LLM fix report reviewed
- [ ] Re-validation completed
- [ ] Manual fixes applied
- [ ] Final validation passed
- [ ] Changes committed to version control

---

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Review the LLM fix report for detailed information
2. **Review configuration**: Verify `llm_config.json` settings
3. **Check backups**: Restore from backup if fixes were incorrect
4. **Consult documentation**: See `LLM_AUTOMATION_GUIDE.md` for detailed information
5. **Manual review**: Some issues may require manual intervention

---

## 📞 Support Resources

- **Main documentation**: `LLM_AUTOMATION_GUIDE.md`
- **Configuration reference**: `llm_config.json`
- **Example reports**: `reports/` directory
- **Backup location**: `.llm_backup/` directory

---

**Summary**: This step-by-step guide provides a complete workflow for using the LLM-enhanced accessibility automation. Start with validation, apply LLM fixes, review results, complete manual fixes, and validate again. The process typically reduces fixing time by 80% while maintaining quality and safety.
