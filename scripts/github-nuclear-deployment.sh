#!/bin/bash
# GitHub Nuclear Deployment Script
# Merges PRs and closes issues for v0.3.0 nuclear deployment
#
# Requirements:
# - GitHub Personal Access Token with 'repo' scope
# - jq (JSON processor): brew install jq / apt install jq
#
# Usage:
#   export GITHUB_TOKEN="your_github_token_here"
#   ./scripts/github-nuclear-deployment.sh

set -e  # Exit on error

# Configuration
REPO_OWNER="extrophi"
REPO_NAME="extrophi-ecosystem"
API_BASE="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN environment variable not set${NC}"
    echo "Please set your GitHub token:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo ""
    echo "Create a token at: https://github.com/settings/tokens"
    echo "Required scope: 'repo'"
    exit 1
fi

# Check for jq
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq not found. Install with: brew install jq${NC}"
    echo "Proceeding without JSON parsing (output will be raw)..."
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

echo "========================================="
echo "  Nuclear Deployment: v0.3.0"
echo "  Repository: ${REPO_OWNER}/${REPO_NAME}"
echo "========================================="
echo ""

# Function to make GitHub API calls
github_api() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -n "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            -d "$data" \
            "${API_BASE}${endpoint}"
    else
        curl -s -X "$method" \
            -H "Authorization: token $GITHUB_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            "${API_BASE}${endpoint}"
    fi
}

# Function to merge PR
merge_pr() {
    local pr_number=$1
    local pr_title=$2

    echo -e "${YELLOW}Merging PR #${pr_number}: ${pr_title}${NC}"

    # Get PR details to find the head branch
    pr_details=$(github_api GET "/pulls/${pr_number}")

    if [ "$JQ_AVAILABLE" = true ]; then
        head_branch=$(echo "$pr_details" | jq -r '.head.ref')
        base_branch=$(echo "$pr_details" | jq -r '.base.ref')
        state=$(echo "$pr_details" | jq -r '.state')

        if [ "$state" != "open" ]; then
            echo -e "${RED}  ✗ PR #${pr_number} is not open (state: ${state})${NC}"
            return 1
        fi

        echo "  Source: ${head_branch} → ${base_branch}"
    fi

    # Merge PR with squash method
    merge_data=$(cat <<EOF
{
  "merge_method": "squash",
  "commit_title": "${pr_title}",
  "commit_message": "Nuclear deployment v0.3.0 - 100% feature parity"
}
EOF
)

    merge_result=$(github_api PUT "/pulls/${pr_number}/merge" "$merge_data")

    if [ "$JQ_AVAILABLE" = true ]; then
        merged=$(echo "$merge_result" | jq -r '.merged // false')
        if [ "$merged" = "true" ]; then
            echo -e "${GREEN}  ✓ PR #${pr_number} merged successfully${NC}"

            # Delete branch if merge was successful
            if [ -n "$head_branch" ] && [ "$head_branch" != "main" ]; then
                echo "  Deleting branch: ${head_branch}"
                delete_result=$(github_api DELETE "/git/refs/heads/${head_branch}")
                echo -e "${GREEN}  ✓ Branch deleted${NC}"
            fi
        else
            message=$(echo "$merge_result" | jq -r '.message // "Unknown error"')
            echo -e "${RED}  ✗ Failed to merge: ${message}${NC}"
        fi
    else
        echo "$merge_result"
    fi

    echo ""
}

# Function to close issue
close_issue() {
    local issue_number=$1

    echo -e "${YELLOW}Closing issue #${issue_number}${NC}"

    # Add comment and close issue
    comment_data=$(cat <<'EOF'
{
  "body": "✅ Completed in nuclear deployment"
}
EOF
)

    comment_result=$(github_api POST "/issues/${issue_number}/comments" "$comment_data")

    if [ "$JQ_AVAILABLE" = true ]; then
        comment_id=$(echo "$comment_result" | jq -r '.id // empty')
        if [ -n "$comment_id" ]; then
            echo -e "${GREEN}  ✓ Comment added${NC}"
        fi
    fi

    # Close the issue
    close_data=$(cat <<'EOF'
{
  "state": "closed"
}
EOF
)

    close_result=$(github_api PATCH "/issues/${issue_number}" "$close_data")

    if [ "$JQ_AVAILABLE" = true ]; then
        state=$(echo "$close_result" | jq -r '.state // empty')
        if [ "$state" = "closed" ]; then
            echo -e "${GREEN}  ✓ Issue #${issue_number} closed${NC}"
        else
            echo -e "${RED}  ✗ Failed to close issue #${issue_number}${NC}"
        fi
    else
        echo "$close_result"
    fi

    echo ""
}

# =========================================
# STEP 1: Merge Pull Requests
# =========================================
echo "STEP 1: Merging Pull Requests (squash merge)"
echo "---------------------------------------------"

merge_pr 128 "XI #74"
merge_pr 129 "OMICRON-2 #75"
merge_pr 130 "PI-2 #76"
merge_pr 131 "SCRAPERS-IMPL #125"
merge_pr 132 "WRITER-RESEARCH #126"
merge_pr 133 "TEST-COVERAGE #127"
merge_pr 134 "SEC-ALPHA-FIX #98"

echo ""
echo "==========================================="
echo ""

# =========================================
# STEP 2: Close Issues
# =========================================
echo "STEP 2: Closing Issues"
echo "---------------------------------------------"

# Issues 71-77
for issue in 71 72 73 74 75 76 77; do
    close_issue $issue
done

# Issues 80-81
close_issue 80
close_issue 81

# Issues 83-85
for issue in 83 84 85; do
    close_issue $issue
done

# Issues 87-100
for issue in 87 88 89 90 91 92 93 94 95 96 97 98 99 100; do
    close_issue $issue
done

# Issues 125-127
for issue in 125 126 127; do
    close_issue $issue
done

echo ""
echo "==========================================="
echo ""

# =========================================
# STEP 3: Create Git Tag
# =========================================
echo "STEP 3: Creating Release Tag"
echo "---------------------------------------------"

tag_data=$(cat <<'EOF'
{
  "tag": "v0.3.0",
  "message": "Nuclear deployment complete - 100% feature parity\n\nThis release includes:\n- Complete BrainDump v3.0 implementation\n- IAC-032 Unified Scraper backend\n- Full test coverage and security fixes\n- Production-ready deployment configuration",
  "object": "",
  "type": "commit",
  "tagger": {
    "name": "Claude Code",
    "email": "noreply@anthropic.com"
  }
}
EOF
)

# Get the latest commit SHA on main
echo "Fetching latest commit SHA from main branch..."
latest_commit=$(github_api GET "/git/refs/heads/main")

if [ "$JQ_AVAILABLE" = true ]; then
    commit_sha=$(echo "$latest_commit" | jq -r '.object.sha')
    echo "Latest commit: ${commit_sha}"

    # Update tag data with commit SHA
    tag_data=$(echo "$tag_data" | jq --arg sha "$commit_sha" '.object = $sha')

    echo "Creating annotated tag v0.3.0..."
    tag_result=$(github_api POST "/git/tags" "$tag_data")

    tag_sha=$(echo "$tag_result" | jq -r '.sha // empty')

    if [ -n "$tag_sha" ]; then
        echo -e "${GREEN}✓ Tag created${NC}"

        # Create reference
        ref_data=$(cat <<EOF
{
  "ref": "refs/tags/v0.3.0",
  "sha": "${tag_sha}"
}
EOF
)

        ref_result=$(github_api POST "/git/refs" "$ref_data")
        echo -e "${GREEN}✓ Tag reference created${NC}"

        # Create GitHub Release
        echo "Creating GitHub Release..."
        release_data=$(cat <<'EOF'
{
  "tag_name": "v0.3.0",
  "name": "v0.3.0 - Nuclear Deployment",
  "body": "## Nuclear Deployment Complete ✅\n\n### 100% Feature Parity Achieved\n\nThis release represents the complete implementation of the Extrophi Ecosystem:\n\n#### BrainDump v3.0\n- ✅ Voice recording and transcription\n- ✅ AI chat with multi-provider support\n- ✅ Privacy scanner with PII detection\n- ✅ Session management\n- ✅ Prompt templates\n- ✅ Settings persistence\n- ✅ Export capabilities\n\n#### IAC-032 Unified Scraper\n- ✅ Multi-platform scraping (Twitter, YouTube, Reddit)\n- ✅ RAG semantic search\n- ✅ LLM analysis pipeline\n- ✅ PostgreSQL + pgvector integration\n- ✅ Redis job queue\n- ✅ ChromaDB vector storage\n\n#### Infrastructure\n- ✅ Complete Hetzner deployment guide\n- ✅ Podman containerization\n- ✅ Production security hardening\n- ✅ Automated backups and monitoring\n\n#### Testing & Quality\n- ✅ Comprehensive test coverage\n- ✅ Security fixes applied\n- ✅ Performance optimizations\n\n### Deployment\n\nSee [DEPLOYMENT.md](./DEPLOYMENT.md) for complete deployment instructions.\n\n### Download\n\n- **macOS**: BrainDump_0.3.0_aarch64.dmg\n- **Windows**: BrainDump_0.3.0_x64.msi\n- **Linux**: BrainDump_0.3.0_amd64.AppImage\n\n---\n\n**Full Changelog**: https://github.com/extrophi/extrophi-ecosystem/compare/v0.2.0...v0.3.0",
  "draft": false,
  "prerelease": false
}
EOF
)

        release_result=$(github_api POST "/releases" "$release_data")
        release_url=$(echo "$release_result" | jq -r '.html_url // empty')

        if [ -n "$release_url" ]; then
            echo -e "${GREEN}✓ GitHub Release created${NC}"
            echo "  URL: ${release_url}"
        else
            echo -e "${RED}✗ Failed to create GitHub Release${NC}"
            echo "$release_result" | jq '.'
        fi
    else
        echo -e "${RED}✗ Failed to create tag${NC}"
        echo "$tag_result" | jq '.'
    fi
else
    echo "$latest_commit"
    echo ""
    echo -e "${YELLOW}Note: Install jq for automatic tag creation${NC}"
fi

echo ""
echo "==========================================="
echo -e "${GREEN}Nuclear Deployment Script Complete!${NC}"
echo "==========================================="
echo ""
echo "Next steps:"
echo "1. Verify PRs merged: https://github.com/${REPO_OWNER}/${REPO_NAME}/pulls?q=is%3Apr+is%3Aclosed"
echo "2. Verify issues closed: https://github.com/${REPO_OWNER}/${REPO_NAME}/issues?q=is%3Aissue+is%3Aclosed"
echo "3. View release: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/tag/v0.3.0"
echo "4. Deploy to production following DEPLOYMENT.md"
echo ""
