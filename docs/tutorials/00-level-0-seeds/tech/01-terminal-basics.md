# Tutorial Outline: Terminal Basics

**Category**: Tech
**Level**: 0 (Seed)
**Estimated Time**: 4-6 hours

## Learning Objectives

- Navigate file systems confidently using command-line interface
- Execute basic file operations (create, read, update, delete) via terminal
- Understand shell environments and command structure
- Compose commands using pipes, redirects, and basic shell scripting
- Troubleshoot common terminal errors and understand exit codes

## Section 1: Terminal Fundamentals

**Concepts**:
- What is a terminal vs shell vs console
- Command structure: program, arguments, flags
- File system hierarchy and paths (absolute vs relative)
- Standard streams: stdin, stdout, stderr

**Skills**:
- Open and configure terminal application
- Execute basic commands with proper syntax
- Read and interpret command output

## Section 2: Navigation and Exploration

**Concepts**:
- Working directory vs home directory
- Directory tree structure
- Hidden files and dotfiles
- Path expansion and wildcards

**Skills**:
- Navigate directories using cd, pwd, ls
- List files with various options (ls -la, ls -lh)
- Find files using basic patterns

## Section 3: File Operations

**Concepts**:
- File permissions and ownership
- File types (regular, directory, symlink)
- Text vs binary files
- File metadata (size, timestamps)

**Skills**:
- Create, copy, move, rename files and directories
- Remove files safely (rm, rm -r, rm -i)
- View file contents (cat, less, head, tail)

## Section 4: Text Processing Basics

**Concepts**:
- Pipes and command chaining
- Output redirection (>, >>, <)
- Filtering and searching text
- Command substitution

**Skills**:
- Chain commands with pipes (|)
- Redirect output to files
- Search text using grep basics

## Section 5: Process Management

**Concepts**:
- What is a process
- Foreground vs background processes
- Process signals (SIGINT, SIGTERM, SIGKILL)
- Exit codes and command success/failure

**Skills**:
- View running processes (ps, top)
- Stop processes (Ctrl+C, kill)
- Run processes in background (&)

## Section 6: Environment and Configuration

**Concepts**:
- Environment variables
- Shell configuration files (.bashrc, .zshrc)
- PATH variable and command lookup
- Aliases and shell functions

**Skills**:
- View and set environment variables
- Create simple aliases
- Modify PATH variable

## Section 7: Help Systems and Debugging

**Concepts**:
- Man pages structure
- Command help options (--help, -h)
- Command history
- Tab completion

**Skills**:
- Read man pages effectively
- Use command history (history, Ctrl+R)
- Debug commands using verbose/debug flags

## Section 8: Safety and Best Practices

**Concepts**:
- Dangerous commands (rm -rf, sudo)
- Backing up before destructive operations
- Testing commands safely
- Security considerations

**Skills**:
- Use confirmation flags (-i)
- Test with echo before execution
- Recognize and avoid common pitfalls

## Capstone Project

**Build a File Organization System**

Create a shell script that:
1. Scans a downloads directory
2. Categorizes files by type (documents, images, videos, code)
3. Creates organized subdirectories
4. Moves files to appropriate locations
5. Generates a summary report of actions taken
6. Includes safety checks and dry-run mode

**Deliverables**:
- Working shell script (organize_files.sh)
- Documentation of how to use the script
- Example output showing categorization
- Error handling for edge cases

## Prerequisites

- Basic computer literacy
- Ability to install software
- Willingness to make mistakes and learn from errors
- Access to Unix-like terminal (macOS, Linux, or WSL on Windows)

## Next Steps

After completing this tutorial, you should be ready for:
- **Git Fundamentals**: Version control using terminal
- **Bash Scripting**: Advanced shell scripting
- **Vim Basics**: Terminal-based text editing
- **System Administration Basics**: User management, services, networking
- **DevOps Tools**: Docker, package managers, deployment scripts

## Resources

- Official documentation: GNU Bash manual
- Interactive learning: Learn Enough Command Line to Be Dangerous
- Practice environment: Set up a dedicated practice directory
- Cheat sheet: Common Unix commands reference

## Assessment Criteria

Students should be able to:
- [ ] Navigate any directory structure without GUI
- [ ] Perform file operations confidently
- [ ] Chain commands to solve multi-step problems
- [ ] Read and understand basic shell scripts
- [ ] Troubleshoot common terminal errors independently
- [ ] Complete capstone project with all requirements met
