# Quick Start - CI/CD Setup in 10 Minutes

**For**: New projects needing automation
**Time**: 10-15 minutes
**Difficulty**: Easy (copy & paste)

---

## Step 1: Copy Workflows (2 min)

```bash
# In your new project root
cd /path/to/your/new/project

# Create workflows directory
mkdir -p .github/workflows

# Copy all workflow files from this package
cp /path/to/braindump/docs/templates/new-project-setup/workflows/*.yml .github/workflows/
```

**Result**: 6 workflow files copied

---

## Step 2: Minimal Customization (5 min)

### Edit `ci.yml`

Find and replace:
- `braindump` → Your project name
- Adjust build commands for your stack

**Node.js**:
```yaml
- run: npm ci
- run: npm test
- run: npm run build
```

**Python**:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
- run: pip install -r requirements.txt
- run: pytest
```

**Rust** (already configured):
```yaml
- run: cargo test
- run: cargo build --release
```

### Edit `handoff-notification.yml`

Change branch pattern (line 6):
```yaml
branches:
  - 'your-prefix/**'  # Change from 'claude/**'
```

---

## Step 3: Push & Test (2 min)

```bash
git add .github/workflows/
git commit -m "ci: Add automation pipeline"
git push
```

**Check**: Go to Actions tab → Should see workflows listed

---

## Step 4: Enable Branch Protection (3 min)

1. GitHub → Your Repo → Settings → Branches
2. Click "Add rule"
3. Branch name pattern: `main`
4. Check:
   - ✅ Require status checks before merging
   - ✅ Require branches to be up to date
5. Select CI jobs to require:
   - CI / Rust Check & Test (or your equivalent)
   - CI / Frontend Check & Test
   - CI / Security Audit
6. Save changes

---

## Step 5: Test It Works (3 min)

```bash
# Create a test branch
git checkout -b test/automation

# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "test: Verify CI automation"
git push -u origin test/automation

# Create PR
gh pr create --title "Test: CI Automation" --body "Testing automated workflows"
```

**Expected**:
- ✅ CI runs automatically
- ✅ Status checks appear on PR
- ✅ Handoff notification issue created
- ✅ QA checklist posted as comment

---

## Done!

Your project now has:
- ✅ Automated CI/CD pipeline
- ✅ Test enforcement (blocks merge if tests fail)
- ✅ QA checklists on every PR
- ✅ Team notifications on push
- ✅ Integration tests

**Next**: See `README.md` for full customization options

---

## Common Stacks - Copy/Paste Configs

### Node.js/TypeScript/React

**`ci.yml`** job:
```yaml
frontend-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
    - run: npm ci
    - run: npm run type-check
    - run: npm test
    - run: npm run lint
    - run: npm run build
```

### Python/Django

**`ci.yml`** job:
```yaml
python-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - run: pip install -r requirements.txt
    - run: pytest --cov
    - run: flake8 .
    - run: black --check .
    - run: python manage.py check
```

### Go

**`ci.yml`** job:
```yaml
go-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-go@v5
      with:
        go-version: '1.21'
    - run: go test ./...
    - run: go vet ./...
    - run: golangci-lint run
    - run: go build ./...
```

### Rust/Cargo (Already Configured!)

Just update project name in `ci.yml`

---

## Troubleshooting

**CI not running?**
- Check: Workflow file syntax (use yamllint)
- Check: GitHub Actions enabled in repo settings
- Check: Branch name matches trigger pattern

**Workflows failing?**
- View logs: Actions tab → Click failed run
- Common: Missing dependencies, wrong paths
- Fix: Update build commands in `ci.yml`

---

**Need more help?** See `README.md` for full documentation
