# GitHub Commit Workflow for Accessibility Fixes

## Overview
This workflow is designed to review accessibility fixes locally before committing to GitHub and merging to the main staging area.

## Three-Phase Checkpoint Workflow

### Phase 1: Validation & Baseline Assessment
**Purpose**: Review initial accessibility issues before making any changes

```bash
cd "C:\Users\Joned_David\OneDrive - Dell Technologies\Documents\OMNIA_Workfiles\One Last Ride\Accessibility Validator and Fixer_SKILL_MDMKDOCS"
python run_omnia_accessibility.py "..\docs" --checkpoint-mode phase1
```

**What happens**:
- Validates documentation for accessibility issues
- Generates baseline reports showing current state
- Creates checkpoint state for resuming later
- **PAUSES** for your review

**Review Phase 1**:
- Check `reports/baseline_validation/INDEX.txt` for initial assessment
- Review `reports/baseline_validation/ISSUES_BY_CATEGORY.txt` for issue types
- Decide if you want to proceed with fixes

### Phase 2: Fix Application & Local Preview
**Purpose**: Apply fixes and review them locally before committing

```bash
python run_omnia_accessibility.py "..\docs" --checkpoint-mode phase2
```

**What happens**:
- Applies automatic accessibility fixes
- Generates post-fix validation reports
- Creates comparison reports (before/after)
- **Builds documentation locally** with fixes applied
- Generates HTML report with clickable links to local build

**Review Phase 2**:
1. **Build Documentation Locally**:
   ```bash
   python build_local_preview.py "..\docs"
   ```
   *Note: This uses `python -m mkdocs` to avoid Application Control policy issues*

2. **Start Local Server**:
   ```bash
   python build_local_preview.py "..\docs" serve
   ```

3. **Review Fixes**:
   - Open `reports/fixed_issues_with_links.html`
   - Click "👁️ View in Docs" links to see actual fixed content
   - Navigate to `http://127.0.0.1:8000` to browse full documentation
   - Verify all fixes are correct and appropriate

4. **Review Reports**:
   - `reports/comparison_report.txt` - Summary of changes
   - `reports/visual_comparison_with_charts.html` - Visual analysis
   - `reports/current_status/INDEX.txt` - Remaining issues (if any)

**Checkpoint Decision**:
- ✅ **If satisfied**: Proceed to Phase 3 (commit to GitHub)
- ❌ **If issues found**: Manually fix remaining issues, then re-run Phase 2

### Phase 3: Commit to GitHub & Merge to Main Staging
**Purpose**: Commit reviewed changes and merge to main staging area

```bash
# Navigate to your GitHub repository
cd "C:\Users\Joned_David\OneDrive - Dell Technologies\Documents\OMNIA_Workfiles\One Last Ride"

# Stage the fixed documentation files
git add docs/

# Commit with descriptive message
git commit -m "Fix accessibility issues: Update non-descriptive links and image captions

- Applied automatic accessibility fixes via Omnia Validator
- Fixed non-descriptive links with descriptive text
- Enhanced image captions for screen reader compatibility
- Built and validated changes locally before commit
- See reports/ for detailed accessibility analysis"

# Push to your feature branch
git push origin your-feature-branch

# Create Pull Request
# - Reference the accessibility improvements
# - Link to the reports folder for review
# - Request review from documentation team
```

**Merge to Main Staging**:
1. After PR approval, merge to main staging branch
2. ReadTheDocs will automatically rebuild with your changes
3. Verify fixes are live on ReadTheDocs
4. Close the accessibility improvement task

## Alternative: Single-Command Workflow

If you prefer not to use checkpoints, you can run the complete workflow:

```bash
# Complete workflow with local build
python run_omnia_accessibility.py "..\docs"

# Then build locally for review
python build_local_preview.py "..\docs"

# Then serve locally
python build_local_preview.py "..\docs" serve
```

## Validation Before Commit

### Pre-Commit Checklist
- [ ] Reviewed all automatic fixes in `fixed_issues_with_links.html`
- [ ] Verified fixes in local preview at `http://127.0.0.1:8000`
- [ ] Checked `comparison_report.txt` for expected changes
- [ ] Reviewed remaining issues in `current_status/INDEX.txt`
- [ ] Manually fixed any critical remaining issues
- [ ] Tested navigation in local build
- [ ] Confirmed no broken links or formatting issues

### Commit Message Template
```
Fix accessibility issues: [Brief description]

- Applied automatic accessibility fixes via Omnia Validator
- [Specific changes made]
- [Issues addressed]
- Built and validated changes locally before commit
- Accessibility improvement: [X% reduction in errors]

See reports/ for detailed accessibility analysis
```

## Rollback Procedure

If issues are discovered after commit:

```bash
# Revert the commit
git revert HEAD

# Or reset to previous commit (if not yet pushed)
git reset --hard HEAD~1

# Re-run accessibility workflow
cd "Accessibility Validator and Fixer_SKILL_MDMKDOCS"
python run_omnia_accessibility.py "..\docs"
```

## Integration with CI/CD

### GitHub Actions Integration
Add to your `.github/workflows/accessibility.yml`:

```yaml
name: Accessibility Check

on:
  pull_request:
    paths:
      - 'docs/**'

jobs:
  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Accessibility Validator
        run: |
          cd "Accessibility Validator and Fixer_SKILL_MDMKDOCS"
          python run_omnia_accessibility.py "../docs" --skip-fixes
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: accessibility-reports
          path: Accessibility\ Validator\ and\ Fixer_SKILL_MDMKDOCS/reports/
```

## Benefits of This Workflow

1. **Quality Control**: Review changes locally before affecting production
2. **Transparency**: Clear documentation of all accessibility improvements
3. **Rollback Safety**: Easy to revert if issues are discovered
4. **Team Collaboration**: PR process allows team review
5. **Audit Trail**: Reports provide detailed change history
6. **Staging Safety**: Main staging area only receives reviewed changes

## Troubleshooting

### Local Build Fails
```bash
# Check mkdocs installation
pip install mkdocs

# Verify mkdocs configuration
cd docs
python -m mkdocs build --verbose
```

### Server Won't Start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
python -m mkdocs serve -a 127.0.0.1:8001
```

### Changes Not Visible in Local Build
```bash
# Clean and rebuild
cd docs
rm -rf site/
python -m mkdocs build
```

## Next Steps After Main Staging Merge

1. **Monitor ReadTheDocs Build**: Watch for successful deployment
2. **Verify Live Changes**: Check ReadTheDocs for fixes
3. **Update Documentation**: Update any related guides or standards
4. **Team Communication**: Notify team of accessibility improvements
5. **Continuous Monitoring**: Set up regular accessibility checks
