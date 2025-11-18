<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Terminal } from '@xterm/xterm';
  import { FitAddon } from '@xterm/addon-fit';
  import { WebLinksAddon } from '@xterm/addon-web-links';
  import '@xterm/xterm/css/xterm.css';
  import { Command } from '@tauri-apps/plugin-shell';

  // Props using Svelte 5 runes
  let {
    visible = $bindable(true),
    initialCwd = '~',
  }: {
    visible?: boolean;
    initialCwd?: string;
  } = $props();

  // State using Svelte 5 runes
  let terminalContainer: HTMLDivElement | undefined;
  let terminal: Terminal | null = null;
  let fitAddon: FitAddon | null = null;
  let currentLine = $state('');
  let currentCwd = $state(initialCwd);
  let commandHistory = $state<string[]>([]);
  let historyIndex = $state(-1);
  let isExecuting = $state(false);

  // Constants
  const HISTORY_KEY = 'braindump_terminal_history';
  const MAX_HISTORY = 100;
  const PROMPT = '$ ';

  /**
   * Load command history from localStorage
   */
  function loadHistory(): void {
    try {
      const stored = localStorage.getItem(HISTORY_KEY);
      if (stored) {
        commandHistory = JSON.parse(stored);
      }
    } catch (e) {
      console.error('Failed to load command history:', e);
      commandHistory = [];
    }
  }

  /**
   * Save command history to localStorage
   */
  function saveHistory(): void {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(commandHistory));
    } catch (e) {
      console.error('Failed to save command history:', e);
    }
  }

  /**
   * Add command to history
   */
  function addToHistory(cmd: string): void {
    if (cmd.trim() === '') return;

    // Remove duplicates
    commandHistory = commandHistory.filter(c => c !== cmd);

    // Add to beginning
    commandHistory.unshift(cmd);

    // Limit size
    if (commandHistory.length > MAX_HISTORY) {
      commandHistory = commandHistory.slice(0, MAX_HISTORY);
    }

    saveHistory();
    historyIndex = -1;
  }

  /**
   * Execute shell command via Tauri
   */
  async function executeCommand(cmd: string): Promise<void> {
    if (!terminal || cmd.trim() === '') return;

    isExecuting = true;
    addToHistory(cmd);

    try {
      // Handle built-in commands
      if (cmd.trim() === 'clear') {
        terminal.clear();
        writePrompt();
        isExecuting = false;
        return;
      }

      if (cmd.trim().startsWith('cd ')) {
        const newDir = cmd.trim().substring(3).trim();
        currentCwd = newDir || '~';
        terminal.writeln('');
        writePrompt();
        isExecuting = false;
        return;
      }

      // Execute via Tauri shell plugin
      const command = Command.create('sh', ['-c', cmd], {
        cwd: currentCwd === '~' ? undefined : currentCwd,
      });

      // Execute and capture output
      const output = await command.execute();

      terminal.writeln('');

      // Write stdout
      if (output.stdout) {
        const lines = output.stdout.trim().split('\n');
        lines.forEach(line => terminal!.writeln(line));
      }

      // Write stderr (in red)
      if (output.stderr) {
        const lines = output.stderr.trim().split('\n');
        lines.forEach(line => terminal!.writeln(`\x1b[31m${line}\x1b[0m`));
      }

      // Show exit code if non-zero
      if (output.code !== 0) {
        terminal.writeln(`\x1b[31mExit code: ${output.code}\x1b[0m`);
      }

    } catch (error) {
      terminal.writeln('');
      terminal.writeln(`\x1b[31mError: ${error instanceof Error ? error.message : 'Unknown error'}\x1b[0m`);
    } finally {
      writePrompt();
      isExecuting = false;
    }
  }

  /**
   * Write the prompt to terminal
   */
  function writePrompt(): void {
    if (!terminal) return;
    terminal.write(`\r\n${PROMPT}`);
    currentLine = '';
  }

  /**
   * Handle keyboard input
   */
  function handleData(data: string): void {
    if (!terminal || isExecuting) return;

    const code = data.charCodeAt(0);

    // Enter key
    if (code === 13) {
      const cmd = currentLine.trim();
      terminal.writeln('');
      if (cmd) {
        executeCommand(cmd);
      } else {
        writePrompt();
      }
      return;
    }

    // Backspace
    if (code === 127 || code === 8) {
      if (currentLine.length > 0) {
        currentLine = currentLine.slice(0, -1);
        terminal.write('\b \b');
      }
      return;
    }

    // Ctrl+C
    if (code === 3) {
      terminal.writeln('^C');
      currentLine = '';
      writePrompt();
      return;
    }

    // Ctrl+L (clear)
    if (code === 12) {
      terminal.clear();
      writePrompt();
      return;
    }

    // Ctrl+U (clear line)
    if (code === 21) {
      // Clear current line
      terminal.write('\r' + PROMPT + ' '.repeat(currentLine.length));
      terminal.write('\r' + PROMPT);
      currentLine = '';
      return;
    }

    // Arrow up (previous command)
    if (data === '\x1b[A') {
      if (historyIndex < commandHistory.length - 1) {
        historyIndex++;
        const cmd = commandHistory[historyIndex];
        // Clear current line
        terminal.write('\r' + PROMPT + ' '.repeat(currentLine.length));
        terminal.write('\r' + PROMPT + cmd);
        currentLine = cmd;
      }
      return;
    }

    // Arrow down (next command)
    if (data === '\x1b[B') {
      if (historyIndex > 0) {
        historyIndex--;
        const cmd = commandHistory[historyIndex];
        // Clear current line
        terminal.write('\r' + PROMPT + ' '.repeat(currentLine.length));
        terminal.write('\r' + PROMPT + cmd);
        currentLine = cmd;
      } else if (historyIndex === 0) {
        historyIndex = -1;
        // Clear current line
        terminal.write('\r' + PROMPT + ' '.repeat(currentLine.length));
        terminal.write('\r' + PROMPT);
        currentLine = '';
      }
      return;
    }

    // Ignore other escape sequences
    if (data.startsWith('\x1b')) {
      return;
    }

    // Regular character input
    if (code >= 32 && code < 127) {
      currentLine += data;
      terminal.write(data);
    }
  }

  /**
   * Handle window resize
   */
  function handleResize(): void {
    if (fitAddon && terminal) {
      try {
        fitAddon.fit();
      } catch (e) {
        console.error('Failed to fit terminal:', e);
      }
    }
  }

  /**
   * Initialize xterm.js terminal
   */
  function initializeTerminal(): void {
    if (!terminalContainer) return;

    // Create terminal with dark theme
    terminal = new Terminal({
      cursorBlink: true,
      cursorStyle: 'block',
      fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", "Consolas", monospace',
      fontSize: 14,
      lineHeight: 1.2,
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#d4d4d4',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#ffffff',
      },
      allowProposedApi: true,
    });

    // Add addons
    fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.loadAddon(new WebLinksAddon());

    // Open terminal in container
    terminal.open(terminalContainer);

    // Fit to container
    fitAddon.fit();

    // Handle input
    terminal.onData(handleData);

    // Load command history
    loadHistory();

    // Welcome message
    terminal.writeln('\x1b[1;32mBrainDump Terminal\x1b[0m');
    terminal.writeln('Type commands and press Enter to execute.');
    terminal.writeln('Use ↑/↓ for command history, Ctrl+L to clear, Ctrl+C to cancel.');
    terminal.writeln('');

    // Write initial prompt
    writePrompt();

    // Handle resize
    window.addEventListener('resize', handleResize);
  }

  /**
   * Cleanup terminal on destroy
   */
  function destroyTerminal(): void {
    if (terminal) {
      terminal.dispose();
      terminal = null;
    }
    if (fitAddon) {
      fitAddon.dispose();
      fitAddon = null;
    }
    window.removeEventListener('resize', handleResize);
  }

  // Lifecycle: Initialize terminal on mount
  onMount(() => {
    initializeTerminal();
  });

  // Lifecycle: Cleanup on destroy
  onDestroy(() => {
    destroyTerminal();
  });

  // Re-fit terminal when visibility changes
  $effect(() => {
    if (visible && fitAddon && terminal) {
      // Small delay to ensure container is visible
      setTimeout(() => {
        handleResize();
      }, 100);
    }
  });
</script>

{#if visible}
  <div class="terminal-island">
    <div class="terminal-header">
      <div class="terminal-info">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="4 17 10 11 4 5"></polyline>
          <line x1="12" y1="19" x2="20" y2="19"></line>
        </svg>
        <span class="terminal-title">Terminal</span>
        <span class="terminal-cwd">{currentCwd}</span>
      </div>
      <div class="terminal-actions">
        {#if isExecuting}
          <span class="terminal-status executing">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
            </svg>
            Executing...
          </span>
        {/if}
        <button
          class="terminal-close"
          onclick={() => (visible = false)}
          title="Close terminal (Ctrl+`)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    </div>

    <div class="terminal-container" bind:this={terminalContainer}></div>

    <div class="terminal-footer">
      <span class="terminal-hint">
        <kbd>↑</kbd><kbd>↓</kbd> History
        <span class="separator">•</span>
        <kbd>Ctrl+L</kbd> Clear
        <span class="separator">•</span>
        <kbd>Ctrl+C</kbd> Cancel
        <span class="separator">•</span>
        <kbd>Ctrl+`</kbd> Toggle
      </span>
      <span class="terminal-count">{commandHistory.length} commands in history</span>
    </div>
  </div>
{/if}

<style>
  .terminal-island {
    display: flex;
    flex-direction: column;
    height: 400px;
    background: #1e1e1e;
    border: 1px solid #333;
    border-radius: 8px;
    overflow: hidden;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  }

  .terminal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #252526;
    border-bottom: 1px solid #333;
  }

  .terminal-info {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #d4d4d4;
  }

  .terminal-info svg {
    color: #0dbc79;
  }

  .terminal-title {
    font-size: 13px;
    font-weight: 600;
    color: #d4d4d4;
  }

  .terminal-cwd {
    font-size: 11px;
    color: #888;
    padding: 2px 6px;
    background: #333;
    border-radius: 4px;
  }

  .terminal-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .terminal-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #d4d4d4;
  }

  .terminal-status.executing svg {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .terminal-close {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s;
  }

  .terminal-close:hover {
    background: #333;
    color: #d4d4d4;
  }

  .terminal-container {
    flex: 1;
    overflow: hidden;
    padding: 8px;
  }

  .terminal-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px;
    background: #252526;
    border-top: 1px solid #333;
    font-size: 11px;
    color: #888;
  }

  .terminal-hint {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .terminal-hint kbd {
    padding: 2px 6px;
    background: #333;
    border-radius: 3px;
    font-size: 10px;
    font-family: inherit;
    color: #d4d4d4;
  }

  .separator {
    color: #555;
  }

  .terminal-count {
    font-size: 10px;
    color: #666;
  }

  /* Global styles for xterm */
  :global(.xterm) {
    height: 100%;
    padding: 4px;
  }

  :global(.xterm .xterm-viewport) {
    overflow-y: auto;
  }

  :global(.xterm .xterm-screen) {
    height: 100%;
  }
</style>
