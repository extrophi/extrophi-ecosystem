# Tutorial Outline: Vim Text Editor

**Category**: Tools
**Level**: 0 (Seed)
**Estimated Time**: 10-12 hours

## Learning Objectives

- Master Vim's modal editing philosophy and navigation
- Edit text efficiently using Vim motions and commands
- Customize Vim with plugins and configuration
- Integrate Vim into development workflow
- Achieve proficiency for daily text editing tasks

## Section 1: Vim Philosophy and Modes

**Concepts**:
- Modal editing: Normal, Insert, Visual, Command
- Why Vim exists and its design principles
- Composability of Vim commands
- Vim vs other editors (when to use Vim)

**Skills**:
- Switch between modes confidently
- Enter and exit Vim properly (:q, :wq, :q!)
- Understand mode indicators

## Section 2: Navigation and Movement

**Concepts**:
- Character movement: h, j, k, l
- Word-level movement: w, b, e
- Line movement: 0, ^, $, gg, G
- Search-based movement: f, t, /, ?

**Skills**:
- Navigate files without arrow keys
- Jump to specific lines and positions
- Search and navigate to text patterns

## Section 3: Basic Editing Operations

**Concepts**:
- Insert mode variants: i, I, a, A, o, O
- Deletion: x, d, dd, D
- Change: c, C, s, S
- Undo and redo: u, Ctrl+r

**Skills**:
- Insert text at various positions
- Delete text using motions (dw, d$, d3j)
- Change text efficiently (ciw, ct,)

## Section 4: Operators and Text Objects

**Concepts**:
- Vim grammar: operator + motion/text object
- Text objects: iw, aw, i", a(, it (tags)
- Repetition with . (dot command)
- Counts: 3dw, 5j, 10x

**Skills**:
- Use text objects for precise edits
- Combine operators with motions
- Repeat commands efficiently with .

## Section 5: Visual Mode and Registers

**Concepts**:
- Visual mode types: v, V, Ctrl+v
- Selection and operations
- Registers and clipboard
- Named registers for clipboard history

**Skills**:
- Select text visually for operations
- Yank (copy) and paste: y, p, P
- Use named registers ("ay, "ap)

## Section 6: Search and Replace

**Concepts**:
- Search with / and ?
- Search navigation: n, N
- Substitute command: :s and :%s
- Regular expressions in Vim

**Skills**:
- Search for patterns efficiently
- Perform find and replace operations
- Use regex for complex substitutions

## Section 7: Configuration and Customization

**Concepts**:
- .vimrc file structure
- Setting options (set, setlocal)
- Key mappings (map, noremap, imap)
- Leader key concept

**Skills**:
- Create and maintain .vimrc
- Customize settings for preferences
- Create useful key mappings

## Section 8: Plugins and Modern Vim

**Concepts**:
- Plugin managers (vim-plug, Vundle, Packer)
- Essential plugins (NERDTree, fzf.vim, ale)
- Language-specific plugins
- Neovim vs Vim

**Skills**:
- Install and configure plugin manager
- Add and manage plugins
- Configure LSP for code intelligence

## Capstone Project

**Vim Development Environment Setup**

Build complete Vim/Neovim setup for coding:

1. **Configuration File** (.vimrc or init.vim):
   - Sensible defaults (line numbers, syntax, etc.)
   - Custom keybindings and leader mappings
   - Theme and visual customization
   - Split and tab management settings

2. **Plugin Suite**:
   - File explorer (NERDTree or netrw)
   - Fuzzy finder (fzf.vim or telescope)
   - Git integration (fugitive)
   - Linting/formatting (ALE or null-ls)
   - Status line (airline or lualine)
   - Auto-completion (coc.nvim or nvim-cmp)

3. **Language Support**:
   - Configure for 2-3 languages (JS, Python, etc.)
   - LSP integration for code intelligence
   - Syntax highlighting and indentation
   - Snippets and templates

4. **Workflow Demonstrations**:
   - Refactoring a code file
   - Git workflow within Vim
   - Multi-file search and replace
   - Split windows and buffer management

5. **Documentation**:
   - Personal Vim cheat sheet
   - Plugin usage guide
   - Workflow documentation
   - Troubleshooting common issues

**Deliverables**:
- Fully configured .vimrc (200+ lines)
- Documented plugin list with usage
- Video/GIF demonstrating 5 common workflows
- Personal cheat sheet (markdown)
- Blog post about Vim journey

## Prerequisites

- Terminal Basics (command line comfort)
- Typing proficiency (touch typing recommended)
- Programming experience helpful
- Patience and growth mindset (Vim has learning curve)

## Next Steps

After completing this tutorial, you should be ready for:
- **Advanced Vim**: Macros, complex regex, advanced motions
- **Neovim Lua Configuration**: Modern Neovim setup
- **Vim as IDE**: Complete IDE replacement for development
- **Vim + Tmux**: Terminal-based development environment
- **Vim Scripting**: Custom plugins and Vimscript
- **Modal Editing Elsewhere**: Browser (Vimium), IDE (IdeaVim)

## Resources

- Vim Tutor (vimtutor command)
- Practical Vim by Drew Neil
- Vim Adventures (game for learning)
- Vim Casts (video tutorials)
- r/vim subreddit
- Vim Tips Wiki
- ThePrimeagen's Vim tutorials

## Assessment Criteria

Students should be able to:
- [ ] Navigate files efficiently without mouse
- [ ] Edit text using Vim grammar (operator + motion)
- [ ] Use visual mode for selections
- [ ] Perform search and replace operations
- [ ] Configure Vim via .vimrc
- [ ] Install and use essential plugins
- [ ] Complete coding tasks entirely within Vim
- [ ] Demonstrate 10+ productivity-boosting workflows
