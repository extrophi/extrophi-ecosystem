# Tutorial Outline: Tmux Terminal Multiplexer

**Category**: Tools
**Level**: 0 (Seed)
**Estimated Time**: 4-6 hours

## Learning Objectives

- Master tmux sessions, windows, and panes for efficient terminal use
- Customize tmux configuration for personal workflow
- Use tmux for persistent remote sessions
- Integrate tmux into development workflow
- Navigate and control tmux entirely via keyboard

## Section 1: Tmux Fundamentals

**Concepts**:
- What is terminal multiplexing
- Sessions, windows, and panes hierarchy
- Client-server architecture
- Prefix key and command mode

**Skills**:
- Start and attach tmux sessions
- Understand prefix key concept (Ctrl+b)
- Execute basic tmux commands

## Section 2: Session Management

**Concepts**:
- Sessions as workspaces
- Named vs unnamed sessions
- Detaching and reattaching
- Session persistence across disconnects

**Skills**:
- Create named sessions (tmux new -s name)
- List and switch sessions (tmux ls, tmux attach)
- Detach from sessions (prefix + d)

## Section 3: Windows and Navigation

**Concepts**:
- Windows as tabs in browser
- Window naming and numbering
- Window navigation strategies
- Moving windows and reordering

**Skills**:
- Create and close windows (prefix + c, prefix + &)
- Navigate between windows (prefix + n/p/number)
- Rename windows (prefix + ,)

## Section 4: Panes and Layouts

**Concepts**:
- Panes for side-by-side work
- Horizontal vs vertical splits
- Pane resizing and zooming
- Predefined layouts

**Skills**:
- Split panes (prefix + % and prefix + ")
- Navigate panes (prefix + arrow keys)
- Resize and zoom panes (prefix + z)

## Section 5: Copy Mode and Scrollback

**Concepts**:
- Copy mode vs normal mode
- Scrollback buffer
- Vi vs Emacs keybindings
- Copying and pasting in tmux

**Skills**:
- Enter copy mode (prefix + [)
- Navigate and search in copy mode
- Copy text and paste (prefix + ])

## Section 6: Configuration and Customization

**Concepts**:
- .tmux.conf file structure
- Key rebinding
- Status bar customization
- Color schemes and themes

**Skills**:
- Create and edit .tmux.conf
- Customize prefix key (Ctrl+a common)
- Configure status bar display

## Section 7: Advanced Features

**Concepts**:
- Synchronize panes
- Command mode and tmux CLI
- Scripting tmux commands
- Plugins and TPM (Tmux Plugin Manager)

**Skills**:
- Broadcast commands to multiple panes
- Use command mode (prefix + :)
- Install and configure plugins

## Section 8: Workflow Integration

**Concepts**:
- Tmux for development environments
- Remote work with tmux
- Pairing tmux with Vim
- Project-specific session layouts

**Skills**:
- Create project-based session scripts
- Work efficiently in remote tmux sessions
- Integrate with other terminal tools

## Capstone Project

**Development Environment Setup Script**

Create automated tmux workspace setup:

1. **Project Session Script**:
   - Create named session for each project
   - Window 1: Code editor (Vim/Neovim)
   - Window 2: Git operations (3 panes: status, log, working)
   - Window 3: Server/tests (2 panes: dev server, test runner)
   - Window 4: Database/logs (2 panes: DB client, log tail)

2. **Configuration File**:
   - Custom prefix key
   - Mouse support configuration
   - Status bar with useful info
   - Vi-mode copy keybindings
   - Custom theme/colors

3. **Workflow Enhancements**:
   - Quick session switcher
   - Common window layouts saved
   - Keybindings for frequent tasks
   - Plugin integration (tmux-resurrect)

4. **Documentation**:
   - Personal tmux cheat sheet
   - Session management workflow
   - Keyboard shortcuts reference
   - Troubleshooting guide

**Deliverables**:
- Tmux configuration file (.tmux.conf)
- Session startup scripts for 2-3 projects
- Personal cheat sheet (markdown)
- Screen recording demonstrating workflow

## Prerequisites

- Terminal Basics (command line comfort)
- Text editor skills for config editing
- SSH knowledge (for remote sessions)
- Basic shell scripting helpful but not required

## Next Steps

After completing this tutorial, you should be ready for:
- **Vim + Tmux Workflow**: Integrated development environment
- **Remote Development**: SSH + tmux for cloud/server work
- **DevOps Workflows**: Monitoring multiple services
- **Terminal Productivity**: Combining tmux, Vim, shell scripts
- **Advanced Tmux**: Custom plugins, complex layouts
- **Alternative Tools**: Screen, Zellij comparison

## Resources

- Tmux Manual (man tmux)
- The Tao of tmux (free book)
- Tmux Plugin Manager (TPM) GitHub
- Oh My Tmux (popular config framework)
- Awesome Tmux (curated list)
- Tmux Cheat Sheet (visual reference)

## Assessment Criteria

Students should be able to:
- [ ] Create and manage sessions effortlessly
- [ ] Navigate windows and panes without mouse
- [ ] Configure tmux via .tmux.conf
- [ ] Use copy mode for scrollback and text selection
- [ ] Set up project-specific tmux sessions
- [ ] Work productively in remote tmux sessions
- [ ] Complete capstone with automated workspace setup
