# Tutorial Outline: Git Fundamentals

**Category**: Tech
**Level**: 0 (Seed)
**Estimated Time**: 6-8 hours

## Learning Objectives

- Understand version control concepts and why Git matters
- Create and manage local Git repositories effectively
- Collaborate using remote repositories (GitHub/GitLab)
- Resolve merge conflicts and recover from mistakes
- Follow industry-standard Git workflows and conventions

## Section 1: Version Control Concepts

**Concepts**:
- What is version control and why it exists
- Centralized vs distributed version control
- Git's data model: snapshots, not diffs
- The three states: working directory, staging, committed

**Skills**:
- Explain Git benefits to non-technical stakeholders
- Identify scenarios where version control prevents problems
- Diagram Git's three-tree architecture

## Section 2: Local Repository Basics

**Concepts**:
- Repository initialization
- Commits as snapshots in time
- Commit hashes and SHA-1
- .git directory structure

**Skills**:
- Initialize new repository (git init)
- Check repository status (git status)
- Create meaningful commits (git add, git commit)

## Section 3: Staging and Committing

**Concepts**:
- The staging area (index)
- Atomic commits and commit granularity
- Commit messages: what makes them good
- .gitignore patterns

**Skills**:
- Stage files selectively (git add -p)
- Write clear commit messages
- Configure .gitignore for project types

## Section 4: History and Inspection

**Concepts**:
- Commit history as a DAG
- Branches as pointers to commits
- HEAD and detached HEAD state
- Viewing diffs and changes

**Skills**:
- View commit history (git log, git log --graph)
- Inspect changes (git diff, git show)
- Navigate history (git checkout, git switch)

## Section 5: Branching and Merging

**Concepts**:
- Branches as lightweight movable pointers
- Fast-forward vs three-way merge
- Merge commits and merge strategies
- When to branch: features, fixes, experiments

**Skills**:
- Create and switch branches (git branch, git checkout -b)
- Merge branches (git merge)
- Delete branches (git branch -d)

## Section 6: Remote Collaboration

**Concepts**:
- Remote repositories and origin
- Push, pull, fetch differences
- Tracking branches
- Forking vs cloning

**Skills**:
- Clone remote repository (git clone)
- Push changes to remote (git push)
- Pull updates from remote (git pull, git fetch)

## Section 7: Conflict Resolution

**Concepts**:
- What causes merge conflicts
- Conflict markers (<<<<, ====, >>>>)
- Manual vs tool-assisted resolution
- Preventing conflicts through communication

**Skills**:
- Identify conflicting changes
- Resolve conflicts manually
- Use git mergetool for complex conflicts

## Section 8: Undoing Changes

**Concepts**:
- Difference between reset, revert, restore
- Rewriting history vs creating new commits
- When it's safe to rewrite history
- Recovering "lost" commits with reflog

**Skills**:
- Unstage changes (git restore --staged)
- Undo commits safely (git revert)
- Use reflog to recover work (git reflog)

## Capstone Project

**Collaborative Documentation Website**

Build a small documentation site with a team (or simulate solo):

1. Create repository with README and initial structure
2. Develop on feature branches:
   - Add getting-started guide
   - Add API reference
   - Add FAQ section
   - Add contributing guidelines
3. Create merge conflicts intentionally and resolve them
4. Use proper commit messages following convention
5. Tag releases (v1.0.0)
6. Write comprehensive .gitignore
7. Document Git workflow in CONTRIBUTING.md

**Deliverables**:
- Repository with clean commit history
- At least 3 feature branches merged
- 2 resolved merge conflicts documented
- Semantic versioning tags
- Professional README and CONTRIBUTING.md

## Prerequisites

- Terminal Basics (ability to use command line)
- Text editor familiarity
- Basic understanding of file systems
- GitHub account (free tier)

## Next Steps

After completing this tutorial, you should be ready for:
- **Advanced Git Workflows**: Rebase, cherry-pick, interactive staging
- **CI/CD Basics**: GitHub Actions, automated testing
- **Code Review Practices**: Pull requests, code review etiquette
- **Git Hooks**: Automating tasks with pre-commit, pre-push hooks
- **Team Collaboration**: Gitflow, trunk-based development

## Resources

- Pro Git book (free online)
- GitHub Skills interactive tutorials
- Git Visual Reference (visual diagrams)
- Oh Shit, Git!?! (common problems and fixes)
- Conventional Commits specification

## Assessment Criteria

Students should be able to:
- [ ] Explain Git's value proposition clearly
- [ ] Create repositories and make commits independently
- [ ] Branch, merge, and resolve conflicts confidently
- [ ] Collaborate via GitHub pull requests
- [ ] Recover from common mistakes without data loss
- [ ] Follow commit message conventions
- [ ] Complete capstone project with clean Git history
