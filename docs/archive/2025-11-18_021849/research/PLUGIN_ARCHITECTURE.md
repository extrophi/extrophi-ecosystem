# Plugin Architecture Research for BrainDump v3.0

**Date**: November 16, 2025
**Status**: Research Complete
**Scope**: Extensible architecture patterns, security models, and marketplace design for BrainDump voice journaling app

---

## Executive Summary

This research examines plugin architectures from leading applications (VSCode, Obsidian, Raycast, Notion, Alfred) and proposes an extensible plugin system for BrainDump. Key findings:

1. **Multi-layer architecture** with process isolation (extension host pattern) is the industry standard
2. **Permission-based security model** (declarative capabilities) provides both flexibility and safety
3. **Hot-reload capability** enhances developer experience during plugin development
4. **Lightweight SDK** with clear API boundaries reduces friction for plugin developers
5. **Marketplace infrastructure** (automated installation, version management, security review) drives ecosystem adoption

**Recommendation**: Implement a two-phase plugin system starting with **Simple Plugin Model** (Phase 1: Custom prompt templates, export formats) before advancing to **Full Extension Host** (Phase 2: Third-party AI providers, data visualization).

---

## 1. Plugin System Architecture Patterns

### 1.1 Extension Host Pattern (Industry Standard)

**Pattern Leader**: Visual Studio Code
**Benefits**: Process isolation, fault tolerance, startup time protection

```
┌──────────────────────────────────────┐
│  Main Application Process             │
│  (Tauri + Svelte Frontend)           │
│  - Audio recording                   │
│  - UI rendering                      │
│  - Core database operations          │
└───────────────────────┬──────────────┘
                        │ IPC (Message Passing)
                        ▼
┌──────────────────────────────────────┐
│  Extension Host Process (Node.js)    │
│  - Plugin sandboxing                 │
│  - Lifecycle management              │
│  - Command execution                 │
│  ┌─────────────┐  ┌─────────────┐   │
│  │  Plugin A   │  │  Plugin B   │   │
│  │  (Prompt)   │  │  (Export)   │   │
│  └─────────────┘  └─────────────┘   │
└──────────────────────────────────────┘
```

**How It Works**:
1. Main process manages application lifecycle and UI
2. Extension host runs as separate Node.js child process
3. Plugins load into extension host (isolated from main process)
4. IPC messaging handles cross-process communication
5. Misbehaving plugin cannot crash main app

**BrainDump Implementation**:
- Extension host spawned at app startup
- Managed by Tauri's `spawn_command` or Child Process module
- Communicate via Tauri's `invoke()` with extension proxy commands
- Plugins disabled on errors; user notified in UI

### 1.2 Single-Process Plugin Pattern (Lighter Alternative)

**Pattern Leaders**: Obsidian (TypeScript plugins), Raycast (React components)
**Trade-off**: Simpler architecture but requires stricter plugin validation

```
Application Memory Space
├── Core Module
├── Plugin: Custom Templates
├── Plugin: Export Formats
└── Plugin: Analytics
```

**Advantages**:
- Lower resource overhead (single V8 instance in Raycast)
- Faster startup time
- Simpler IPC (direct function calls)
- Suitable for trusted plugins

**Disadvantages**:
- Plugin crash can crash entire app
- Harder to sandbox (enforce via code review)
- No process-level resource limits

**When to Use**: Early phases, pre-marketplace validation period.

### 1.3 Hot-Reload Architecture

**Pattern Leaders**: Raycast (`npm run dev`), VSCode extensions
**Benefits**: Rapid iteration without app restart

**Implementation**:
```javascript
// Extension host watches plugin directory
const chokidar = require('chokidar');

const watcher = chokidar.watch('./plugins/**/*.js');

watcher.on('change', (filePath) => {
  // 1. Clear module cache
  delete require.cache[require.resolve(filePath)];

  // 2. Unload plugin hooks
  unloadPluginHooks(pluginId);

  // 3. Reload plugin
  const plugin = require(filePath);
  loadPluginHooks(plugin);

  // 4. Notify UI of reload
  mainWindow.webContents.send('plugin:reloaded', { pluginId, version: plugin.version });
});
```

**BrainDump Integration**:
- Development mode: Watch `./plugins/` directory
- Production mode: Disable hot-reload (locked-down plugins)
- Clear npm require cache before reload
- Notify UI to refresh plugin list

---

## 2. BrainDump Plugin Opportunities

### 2.1 Phase 1: Custom Prompt Templates (Simple Plugins)

**Complexity**: Low | **Priority**: P1 | **Time**: 20-40 hours

#### Use Cases
1. **Custom Therapy Templates**
   - Cognitive behavioral therapy (CBT) framework
   - Mindfulness prompts
   - Journaling structured templates
   - Grief/trauma processing guides

2. **Domain-Specific Prompts**
   - Academic research journaling
   - Technical learning logs
   - Fitness/health tracking
   - Relationship documentation

3. **User-Created Templates**
   - Import/export prompt YAML files
   - Community template marketplace
   - Fork existing templates

#### Plugin Interface
```javascript
// plugins/therapy-cbt/plugin.js
module.exports = {
  name: 'CBT Therapy Templates',
  version: '1.0.0',
  author: 'BrainDump Team',

  templates: [
    {
      id: 'cbt-thought-record',
      title: 'CBT Thought Record',
      description: 'Identify and challenge unhelpful thoughts',
      systemPrompt: `You are a therapist using CBT techniques...`,
      userPrompt: `{journal_transcript}`,
      icon: 'brain-icon',
    },
    {
      id: 'cbt-behavioral-activation',
      title: 'Behavioral Activation',
      description: 'Plan meaningful activities',
      systemPrompt: `...`
    }
  ],

  manifest: {
    permissions: ['read:transcripts', 'read:templates', 'write:sessions'],
    minAppVersion: '3.0.0'
  }
};
```

#### Storage
```sql
-- New table for community plugins
plugins
├── id (primary key)
├── plugin_id (name)
├── version
├── author
├── manifest (JSON)
├── enabled
├── installed_at
└── enabled_at

-- New table for plugin-contributed templates
plugin_templates
├── id (primary key)
├── plugin_id (FK plugins)
├── template_id
├── template_data (JSON)
└── created_at
```

### 2.2 Phase 2: Export Format Plugins

**Complexity**: Low-Medium | **Priority**: P2 | **Time**: 15-25 hours

#### Export Formats
- **Markdown**: Blog post format
- **PDF with cover**: Printable journal
- **DOCX**: Microsoft Word format
- **Notion**: Export sessions to Notion API
- **Obsidian**: Vault-compatible format
- **Email**: Self-send compiled journal entries

#### Plugin Interface
```javascript
// plugins/export-notion/plugin.js
module.exports = {
  name: 'Notion Exporter',
  version: '1.0.0',

  exporters: [
    {
      id: 'notion-database',
      format: 'notion',
      label: 'Export to Notion Database',
      handler: async (sessions, options) => {
        const notion = new NotionClient(options.notionToken);
        // Implementation
        return { success: true, url: '...' };
      },
      configUI: {
        fields: [
          { name: 'notionToken', type: 'password', label: 'Notion Integration Token' },
          { name: 'databaseId', type: 'text', label: 'Database ID' }
        ]
      }
    }
  ],

  permissions: ['read:sessions', 'read:messages', 'network:https://api.notion.com']
};
```

### 2.3 Phase 3: Third-Party AI Provider Plugins

**Complexity**: Medium-High | **Priority**: P2 | **Time**: 40-60 hours

#### Supported Providers
- **Anthropic Claude** (currently hardcoded - needs plugin-ification)
- **OpenAI GPT-4/3.5** (already in codebase)
- **Google Gemini API**
- **Meta Llama (via Replicate/Groq)**
- **Local LLMs** (Ollama, LM Studio)
- **Custom API endpoints**

#### Plugin Interface
```javascript
// plugins/provider-openai/plugin.js
module.exports = {
  name: 'OpenAI Provider',
  version: '2.0.0',

  provider: {
    id: 'openai',
    label: 'OpenAI GPT',
    models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    configUI: {
      fields: [
        { name: 'apiKey', type: 'password', label: 'API Key' },
        { name: 'model', type: 'select', options: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
        { name: 'temperature', type: 'slider', min: 0, max: 1, step: 0.1 }
      ]
    },
    handler: async (message, options) => {
      const openai = new OpenAI({ apiKey: options.apiKey });
      const response = await openai.chat.completions.create({
        model: options.model,
        temperature: options.temperature,
        messages: [{ role: 'user', content: message }]
      });
      return { text: response.choices[0].message.content };
    }
  },

  permissions: ['read:sessions', 'network:https://api.openai.com', 'read:config:apiKeys'],
  minAppVersion: '3.1.0'
};
```

**Implementation Details**:
- Provider selection persisted to database (not just Settings)
- Fall back to Claude if provider plugin unavailable
- API key stored in Keychain with provider namespace
- Error handling with user-friendly fallback messages

### 2.4 Phase 4: Data Visualization & Analytics Plugins

**Complexity**: High | **Priority**: P3 | **Time**: 50-80 hours

#### Plugin Examples
- **Emotion Timeline**: Chart mood trends over time
- **Word Cloud**: Visualize frequently mentioned concepts
- **Theme Analysis**: Categorize journal entries by topic
- **Writing Metrics**: Streak counters, entry statistics
- **Privacy Heatmap**: Visual PII detection dashboard

#### Plugin Interface
```javascript
// plugins/viz-emotion-timeline/plugin.js
module.exports = {
  name: 'Emotion Timeline',
  version: '1.0.0',

  widget: {
    id: 'emotion-timeline',
    label: 'Emotion Timeline',
    component: './EmotionTimeline.svelte',
    width: 'full',  // 'small', 'half', 'full'
    height: 300,
    dataRequest: {
      type: 'session-analysis',
      startDate: '${startDate}',
      endDate: '${endDate}'
    },
    handler: async (sessions) => {
      // Extract emotions from transcripts
      // Return: { dates: [...], emotions: [...], colors: [...] }
    }
  },

  permissions: ['read:sessions', 'read:messages'],
  minAppVersion: '3.2.0'
};
```

---

## 3. Plugin Security Model

### 3.1 Permission System (Declarative Capabilities)

**Pattern**: Browser Extension model (Chrome, Firefox)

#### Permission Categories

| Category | Examples | Risk Level |
|----------|----------|-----------|
| **Data Read** | `read:transcripts`, `read:sessions`, `read:messages` | Medium |
| **Data Write** | `write:sessions`, `write:prompts`, `delete:sessions` | High |
| **System** | `read:config`, `read:keychain`, `system:clipboard` | High |
| **Network** | `network:https://api.example.com`, `network:*` | Very High |
| **UI** | `ui:sidebar`, `ui:modal`, `ui:settings` | Low |
| **Filesystem** | `fs:read`, `fs:write` | Very High |

**Manifest Example**:
```json
{
  "name": "Custom Templates Plugin",
  "version": "1.0.0",
  "permissions": [
    "read:templates",
    "read:sessions",
    "ui:sidebar"
  ],
  "optionalPermissions": [
    "network:https://api.example.com"
  ],
  "requiredMinVersion": "3.0.0"
}
```

### 3.2 Permission Verification & Enforcement

**At Load Time**:
```rust
// src-tauri/src/plugins/validator.rs
pub fn validate_plugin_manifest(manifest: &PluginManifest) -> Result<(), PluginError> {
    // 1. Check app version compatibility
    if manifest.required_min_version > APP_VERSION {
        return Err(PluginError::IncompatibleVersion);
    }

    // 2. Validate permission format
    for perm in &manifest.permissions {
        validate_permission(perm)?;
    }

    // 3. Warn on high-risk permissions
    if contains_high_risk_permissions(manifest) {
        warn!("Plugin requests high-risk permissions: {:?}", manifest.permissions);
    }

    Ok(())
}

pub fn check_permission(plugin_id: &str, permission: &str) -> Result<(), PermissionError> {
    let plugin = get_plugin_manifest(plugin_id)?;

    if !plugin.permissions.contains(&permission.to_string()) {
        return Err(PermissionError::PermissionDenied(permission.to_string()));
    }

    Ok(())
}
```

**At Runtime**:
```javascript
// Extension host validates all plugin calls
class ExtensionHost {
  registerCommand(pluginId, command, handler) {
    return async (...args) => {
      const plugin = this.plugins[pluginId];
      const requiredPerm = this.getPermissionForCommand(command);

      // Check permission before execution
      if (!plugin.manifest.permissions.includes(requiredPerm)) {
        throw new Error(`Plugin ${pluginId} lacks permission: ${requiredPerm}`);
      }

      // Execute with audit logging
      console.log(`[AUDIT] Plugin ${pluginId} executed: ${command}`);
      return handler(...args);
    };
  }
}
```

### 3.3 Sandboxing Strategy

#### Execution Model
1. **Process Isolation**: Extension host in separate Node.js process
2. **Context Isolation**: Plugins cannot access main process variables
3. **API Whitelist**: Only approved Tauri commands accessible
4. **Code Review**: All marketplace plugins reviewed before listing

#### Threat Scenarios Mitigated

| Threat | Mitigation |
|--------|-----------|
| **Keylogging** | No keyboard event access in plugin API |
| **Data Exfiltration** | Network permissions required; monitored requests |
| **Privilege Escalation** | Runs with app permissions (user level) |
| **Infinite Loops** | Worker timeout (5 min); user can force kill |
| **Memory Exhaustion** | Node.js heap limits; monitor in extension host |
| **Disk DoS** | File size limits on plugin temp directories |

### 3.4 Code Signing & Integrity

**Approach**: HMAC-SHA256 signatures for marketplace plugins

```rust
// src-tauri/src/plugins/signing.rs
pub fn sign_plugin(plugin_path: &Path, private_key: &str) -> Result<String> {
    let plugin_bytes = fs::read(plugin_path)?;
    let signature = hmac_sha256(&plugin_bytes, private_key);
    Ok(hex::encode(signature))
}

pub fn verify_plugin(plugin_path: &Path, signature: &str, public_key: &str) -> Result<()> {
    let plugin_bytes = fs::read(plugin_path)?;
    let expected_sig = hmac_sha256(&plugin_bytes, public_key);

    if hex::encode(expected_sig) != signature {
        return Err(PluginError::InvalidSignature);
    }
    Ok(())
}
```

---

## 4. Plugin Marketplace Architecture

### 4.1 Marketplace Infrastructure

#### Registry Structure
```
braindump-plugin-registry/
├── plugins/
│   ├── prompt-templates/
│   │   ├── manifest.json
│   │   ├── index.js
│   │   ├── package.json
│   │   └── README.md
│   ├── export-markdown/
│   ├── provider-openai/
│   └── viz-emotions/
├── registry.json  # Searchable index
├── SECURITY.md    # Code review checklist
└── PUBLISHING.md  # Developer guide
```

#### Registry Index (`registry.json`)
```json
{
  "version": "1.0",
  "lastUpdated": "2025-11-16T10:00:00Z",
  "plugins": [
    {
      "id": "prompt-templates-cbt",
      "name": "CBT Therapy Templates",
      "author": "BrainDump Team",
      "version": "1.0.0",
      "description": "Cognitive Behavioral Therapy templates for journaling",
      "category": "templates",
      "downloadUrl": "https://registry.braindump.app/plugins/prompt-templates-cbt/v1.0.0/plugin.zip",
      "checksum": "sha256:abc123...",
      "signature": "hmac:def456...",
      "downloads": 1240,
      "rating": 4.8,
      "reviews": 89,
      "minAppVersion": "3.0.0",
      "tags": ["therapy", "templates", "cbt"],
      "publishedDate": "2025-06-01T00:00:00Z"
    }
  ]
}
```

### 4.2 Installation Flow (Client-Side)

**UI Component: Plugin Browser**
```svelte
<!-- src/components/PluginBrowser.svelte -->
<script>
  import { invoke } from '@tauri-apps/api/core';

  let plugins = $state([]);
  let installing = $state(new Set());

  async function fetchPlugins() {
    const response = await fetch('https://registry.braindump.app/registry.json');
    plugins = await response.json();
  }

  async function installPlugin(pluginId, version) {
    installing.add(pluginId);
    try {
      const result = await invoke('plugin:install', { pluginId, version });
      plugins = plugins.map(p => p.id === pluginId ? { ...p, installed: true } : p);
    } catch (error) {
      console.error('Installation failed:', error);
    } finally {
      installing.delete(pluginId);
    }
  }
</script>

<div class="plugin-browser">
  {#each plugins as plugin}
    <div class="plugin-card">
      <h3>{plugin.name}</h3>
      <p>{plugin.description}</p>
      <div class="meta">
        <span class="rating">★ {plugin.rating}</span>
        <span class="downloads">{plugin.downloads} downloads</span>
      </div>
      <button onclick={() => installPlugin(plugin.id, plugin.version)}>
        {installing.has(plugin.id) ? 'Installing...' : 'Install'}
      </button>
    </div>
  {/each}
</div>
```

**Backend Installation Command**:
```rust
// src-tauri/src/commands.rs
#[tauri::command]
pub async fn plugin_install(
    plugin_id: String,
    version: String,
    state: tauri::State<'_, AppState>,
) -> Result<PluginInstallResult, String> {
    // 1. Download plugin from registry
    let download_url = format!("https://registry.braindump.app/plugins/{}/{}/plugin.zip",
                               plugin_id, version);
    let response = reqwest::get(&download_url).await.map_err(|e| e.to_string())?;
    let plugin_bytes = response.bytes().await.map_err(|e| e.to_string())?;

    // 2. Verify signature
    let registry_entry = fetch_registry_entry(&plugin_id, &version).await?;
    verify_plugin_signature(&plugin_bytes, &registry_entry.signature)?;

    // 3. Extract to plugins directory
    let plugins_dir = app_data_dir().join("plugins");
    let plugin_dir = plugins_dir.join(&plugin_id);
    extract_zip(&plugin_bytes, &plugin_dir)?;

    // 4. Validate manifest
    let manifest = PluginManifest::from_file(plugin_dir.join("plugin.json"))?;
    validate_plugin_manifest(&manifest)?;

    // 5. Load plugin into extension host
    invoke_extension_host("plugin:load", json!({
        "pluginId": plugin_id,
        "manifestPath": plugin_dir.join("plugin.json")
    }))?;

    // 6. Save installation metadata
    db.record_plugin_installation(&PluginInstallation {
        plugin_id: plugin_id.clone(),
        version: version.clone(),
        installed_at: now(),
        enabled: true,
    })?;

    Ok(PluginInstallResult {
        pluginId: plugin_id,
        version,
        success: true,
    })
}
```

### 4.3 Security Review Process

**Before Listing in Marketplace**:

1. **Automated Checks** (5 min)
   - Verify signatures
   - Validate manifest
   - Check permissions against declared functionality
   - Scan for known vulnerabilities
   - Test compatibility with current app version

2. **Manual Code Review** (1-2 days)
   - Inspect plugin source code
   - Verify network permissions actually needed
   - Check for hardcoded credentials
   - Test functionality on multiple OS versions
   - Validate error handling

3. **Community Rating** (Ongoing)
   - Users rate plugins (1-5 stars)
   - Flag malicious or low-quality plugins
   - Developers respond to reviews
   - Community moderation (reputation-based)

**Checklist Template** (`docs/SECURITY.md`):
```markdown
# Plugin Security Review Checklist

## Automated Checks
- [ ] Manifest validates against schema
- [ ] Permissions declared match functionality
- [ ] No hardcoded API keys or credentials found
- [ ] No known vulnerabilities in dependencies
- [ ] Signature verification passes

## Code Review
- [ ] Source code available (not obfuscated)
- [ ] Network calls to declared domains only
- [ ] File I/O scoped to plugin directory
- [ ] No system command execution
- [ ] Proper error handling and logging

## Functionality Testing
- [ ] Plugin loads without errors
- [ ] Expected features work as documented
- [ ] No memory leaks (heap usage stable)
- [ ] Handles graceful shutdown
- [ ] Compatible with min/max app versions

## Approval
- [ ] Reviewed by: [maintainer name]
- [ ] Date: [YYYY-MM-DD]
- [ ] Rating: [APPROVED/NEEDS_REVISION/REJECTED]
```

### 4.4 Versioning & Compatibility

**Semantic Versioning (SemVer)**:
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- MAJOR: Breaking API changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Compatibility Matrix**:
```javascript
// In plugin manifest.json
{
  "name": "Example Plugin",
  "version": "2.0.0",
  "engines": {
    "braindump": ">=3.0.0 <4.0.0"
  },
  "compatibility": {
    "schemas": {
      "minVersion": 2,  // Database schema version
      "migrations": ["./migrations/v2.sql"]
    },
    "permissions": {
      "minApiVersion": "1.0"
    }
  }
}
```

**Compatibility Checking**:
```rust
pub fn check_compatibility(
    plugin: &PluginManifest,
    app_version: &semver::Version,
) -> Result<(), IncompatibilityError> {
    let required_version = semver::VersionReq::parse(&plugin.engines.braindump)?;

    if !required_version.matches(app_version) {
        return Err(IncompatibilityError::VersionMismatch {
            required: plugin.engines.braindump.clone(),
            actual: app_version.to_string(),
        });
    }

    Ok(())
}
```

---

## 5. SDK & Developer Experience

### 5.1 Plugin SDK Structure

#### SDK Package (`@braindump/plugin-sdk`)
```json
{
  "name": "@braindump/plugin-sdk",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "files": [
    "dist",
    "README.md"
  ],
  "exports": {
    ".": "./dist/index.js",
    "./templates": "./dist/plugin-types/templates.d.ts",
    "./exporters": "./dist/plugin-types/exporters.d.ts",
    "./providers": "./dist/plugin-types/providers.d.ts"
  }
}
```

#### SDK Exports
```typescript
// @braindump/plugin-sdk
export interface PluginContext {
  api: PluginAPI;
  manifest: PluginManifest;
  storage: PluginStorage;
}

export interface PluginAPI {
  // Prompt templates
  registerTemplate(template: Template): void;
  // Export formats
  registerExporter(exporter: Exporter): void;
  // AI providers
  registerProvider(provider: AIProvider): void;
  // Data access
  getSessions(filter?: SessionFilter): Promise<Session[]>;
  getMessages(sessionId: number): Promise<Message[]>;
  // UI components
  showNotification(notification: Notification): Promise<void>;
  openModal(modal: Modal): Promise<any>;
  // Events
  on(event: string, handler: Function): Unsubscribe;
  emit(event: string, data: any): void;
}

export interface PluginStorage {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T): Promise<void>;
  delete(key: string): Promise<void>;
}

export interface Template {
  id: string;
  title: string;
  description: string;
  systemPrompt: string;
  icon?: string;
}

export interface Exporter {
  id: string;
  format: string;
  handler: (sessions: Session[]) => Promise<ExportResult>;
}

export interface AIProvider {
  id: string;
  label: string;
  models: string[];
  handler: (message: string, options: any) => Promise<AIResponse>;
}
```

### 5.2 Developer Documentation & Examples

**Quick Start Template** (`docs/dev/PLUGIN_QUICK_START.md`):
```markdown
# BrainDump Plugin Development Quick Start

## 1. Create Project
\`\`\`bash
npm create @braindump/plugin my-plugin
cd my-plugin
npm install
\`\`\`

## 2. Develop Plugin
\`\`\`typescript
// src/index.ts
import { definePlugin } from '@braindump/plugin-sdk';

export default definePlugin({
  name: 'My Plugin',
  version: '1.0.0',

  async setup(api) {
    // Register components, templates, etc.
    api.registerTemplate({
      id: 'my-template',
      title: 'My Template',
      systemPrompt: 'You are helpful...'
    });
  }
});
\`\`\`

## 3. Test Locally
\`\`\`bash
npm run dev
# This starts BrainDump in dev mode with your plugin
\`\`\`

## 4. Build for Release
\`\`\`bash
npm run build
npm run package
# Creates .zip file for marketplace submission
\`\`\`
\`\`\`

**Code Examples Repository**:
```
braindump-plugin-examples/
├── template-prompt-templates/    # Simple prompt template plugin
├── exporter-markdown/             # Export to Markdown
├── provider-openai/               # OpenAI integration
└── widget-emotion-timeline/       # Data visualization widget
```

### 5.3 Testing & Development Tools

**Local Development Setup**:
```bash
# Plugin development mode
npm run tauri:dev -- --plugin-dir ./my-plugin

# Watch plugin for changes (hot reload)
npm run plugin:watch

# Test plugin in isolation
npm run plugin:test

# Lint & validate plugin
npm run plugin:lint
npm run plugin:validate
```

**Plugin Testing Framework**:
```typescript
// plugin.test.ts
import { createPluginTestContext } from '@braindump/plugin-sdk/testing';

describe('My Plugin', () => {
  let ctx: PluginTestContext;

  beforeEach(async () => {
    ctx = await createPluginTestContext({
      dataDir: './test-data',
      mockAPI: true
    });
  });

  test('should register template', async () => {
    const plugin = await import('./index');
    await plugin.default.setup(ctx.api);

    expect(ctx.api.templates).toContainEqual(
      expect.objectContaining({ id: 'my-template' })
    );
  });

  test('should export sessions', async () => {
    const exporter = ctx.api.exporters[0];
    const result = await exporter.handler([mockSession]);

    expect(result.success).toBe(true);
    expect(result.format).toBe('markdown');
  });
});
```

### 5.4 Publishing Workflow

**Automated Publishing Pipeline**:

```yaml
# .github/workflows/publish-plugin.yml
name: Publish Plugin

on:
  push:
    tags:
      - 'v*'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: volta-cli/action@v4
      - run: npm ci
      - run: npm run lint
      - run: npm run test
      - run: npm run validate-plugin

  publish:
    runs-on: ubuntu-latest
    needs: validate
    steps:
      - uses: actions/checkout@v3
      - run: npm run build
      - run: npm run package
      - name: Create release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/plugin.zip
      - name: Submit to marketplace
        run: npx @braindump/cli plugin:publish
        env:
          BRAINDUMP_REGISTRY_TOKEN: ${{ secrets.REGISTRY_TOKEN }}
```

**CLI Publishing Tool**:
```bash
# Login to registry
braindump plugin:auth --token <token>

# Validate plugin locally
braindump plugin:validate ./plugin.json

# Submit to marketplace
braindump plugin:publish --changelog "Added CBT templates"

# Update existing plugin
braindump plugin:publish --version patch

# View submission status
braindump plugin:status my-plugin
```

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Months 1-2)

**Goal**: Enable simple prompt template plugins

**Deliverables**:
1. Plugin manifest schema & validation
2. Extension host (Node.js process) spawned at startup
3. Basic Tauri IPC commands for plugins
4. Hot-reload for development
5. Simple template plugin loader
6. Filesystem storage for plugin state

**Files to Create**:
```
src-tauri/src/
├── plugins/
│   ├── mod.rs
│   ├── manifest.rs
│   ├── loader.rs
│   ├── validator.rs
│   └── context.rs

src/components/
├── PluginBrowser.svelte
└── PluginManager.svelte

docs/dev/
├── PLUGIN_QUICK_START.md
├── PLUGIN_SDK.md
└── PLUGIN_EXAMPLES.md
```

**Test Requirements**:
- Plugin loads from filesystem
- Manifest validation works
- Hot-reload successfully reloads changes
- Template plugin registers correctly

### Phase 2: Permissions & Security (Months 2-3)

**Goal**: Enforce permission-based access control

**Deliverables**:
1. Permission system (read/write/network)
2. Permission checking in extension host
3. Runtime enforcement via API wrapper
4. Security review checklist
5. Code signing infrastructure

**Files to Create**:
```
src-tauri/src/plugins/
├── permissions.rs
├── signing.rs
└── security.rs

docs/
├── PLUGIN_SECURITY.md
└── SECURITY_REVIEW_CHECKLIST.md
```

### Phase 3: Marketplace (Months 3-4)

**Goal**: Full plugin discovery & installation

**Deliverables**:
1. Plugin registry API (JSON endpoint)
2. Plugin browser UI in BrainDump
3. Automated download & installation
4. Signature verification
5. Version management

**Infrastructure**:
- Registry hosted on braindump.app (or GitHub Pages)
- GitHub Actions workflow for security review
- Automated testing on multiple OS versions

### Phase 4: Advanced Features (Months 5+)

**Goal**: Third-party providers, data visualization

**Deliverables**:
1. AI provider plugin system
2. Export format plugins
3. Data visualization widget framework
4. Plugin dependencies system
5. Version migration system

---

## 7. Competitive Analysis

### VSCode Extension Model
**Strengths**:
- Mature marketplace (50k+ extensions)
- Process-isolated extension host
- Rich API surface area
- Strong developer documentation

**For BrainDump**: Adopt extension host pattern + simplified API

### Obsidian Plugin System
**Strengths**:
- Simple TypeScript-based plugins
- Built-in hot-reload
- Large community (700+ plugins)
- Sample plugin template
- Excellent developer docs

**For BrainDump**: Use Obsidian's TypeScript approach + simpler permission model

### Raycast Extensions
**Strengths**:
- React-based UI components
- Fast startup (shared V8 context)
- Simple publishing workflow
- Active community

**For BrainDump**: Consider React components for widgets in Phase 4

### Notion Integrations
**Strengths**:
- OAuth-based auth flow
- Partner program with benefits
- Public API well-documented
- Native integration examples

**For BrainDump**: Model Partner Program structure; publish API docs publicly

---

## 8. Key Decisions

### Decision 1: Single vs. Multi-Process

**Chosen**: Multi-process (Extension Host)

**Rationale**:
- Protects main app from plugin crashes
- Standard industry pattern
- Easier to enforce permissions
- Resource isolation possible

### Decision 2: Sandbox Security

**Chosen**: Permission-based (not full sandbox)

**Rationale**:
- Simpler to implement
- Sufficient for initial plugins
- Can upgrade to full sandbox later
- Trade-off acceptable given plugins are curated

### Decision 3: Plugin Discovery

**Chosen**: Centralized registry with optional GitHub hosting

**Rationale**:
- Single source of truth
- Can implement marketplace features
- Community contribution possible via GitHub PRs
- Can add search, ratings, reviews later

### Decision 4: Development Model

**Chosen**: npm-based packages for plugins

**Rationale**:
- Leverages existing JavaScript ecosystem
- Easy for web developers to contribute
- Standard build tooling (TypeScript, Vite, etc.)
- Familiar to most plugin developers

---

## 9. Success Metrics

**Phase 1 (Foundation)**:
- Ability to load custom prompt templates
- Plugin hot-reload working in dev mode
- Plugin browser UI functional

**Phase 2 (Security)**:
- All plugin API calls checked for permissions
- Security review checklist documented
- No unauthorized data access in tests

**Phase 3 (Marketplace)**:
- 5+ plugins published
- 100+ plugin downloads total
- Positive community feedback (>4.0 stars avg)

**Phase 4 (Advanced)**:
- AI provider plugins working
- Export plugins covering 5+ formats
- 50+ plugins in marketplace
- Strong plugin developer documentation

---

## 10. Open Questions & Future Work

1. **Revenue Sharing**: Should plugin developers be compensated? (Consider premium plugins or marketplace fee splits)
2. **Dependency Management**: How to handle plugin dependencies on other plugins?
3. **Data Migration**: When plugins are disabled/uninstalled, how to handle plugin-specific data?
4. **Rollback Safety**: Can plugins auto-rollback on app crash?
5. **Telemetry**: Should plugins report usage metrics?
6. **Internationalization**: Support for non-English plugin names/descriptions?
7. **Mobile**: Tauri supports iOS/Android - should plugins work on mobile?

---

## 11. References & Resources

### Official Documentation
- [Tauri Plugin Documentation](https://v2.tauri.app/develop/plugins/)
- [VSCode Extension API](https://code.visualstudio.com/api)
- [Obsidian Developer Docs](https://docs.obsidian.md/)
- [Raycast API Docs](https://developers.raycast.com/)
- [Chrome Extensions Manifest](https://developer.chrome.com/docs/extensions/develop/)

### Security
- [OWASP Plugin Security](https://cheatsheetseries.owasp.org/cheatsheets/Extension_Security.html)
- [Chromium Sandbox Architecture](https://chromium.googlesource.com/chromium/src/+/main/docs/design/sandbox.md)

### Patterns & Best Practices
- [API Design Best Practices](https://nordicapis.com/best-practices-building-sdks-for-apis/)
- [Semantic Versioning](https://semver.org/)
- [Plugin Architecture Patterns](https://www.microsoft.com/en-us/research/publication/plugin-architectures-for-extensibility/)

---

## Appendix A: Sample Plugin Project Structure

```
braindump-plugin-cbt-templates/
├── src/
│   ├── index.ts              # Plugin entry point
│   ├── templates/
│   │   ├── cbt-thought.ts
│   │   ├── behavioral-activation.ts
│   │   └── index.ts
│   └── utils/
│       └── prompt-builder.ts
├── tests/
│   ├── plugin.test.ts
│   └── templates.test.ts
├── dist/                      # Build output
│   ├── index.js
│   └── index.d.ts
├── plugin.json               # Plugin manifest
├── package.json
├── tsconfig.json
├── vite.config.ts
├── README.md
├── LICENSE
└── .github/workflows/
    └── publish.yml           # CI/CD workflow
```

---

## Appendix B: Plugin Manifest Schema

```json
{
  "$schema": "https://braindump.app/schemas/plugin-manifest-v1.json",
  "name": "Plugin Display Name",
  "id": "plugin-id-kebab-case",
  "version": "1.0.0",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://example.com"
  },
  "description": "Short description",
  "readme": "README.md",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/user/repo"
  },
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "engines": {
    "braindump": ">=3.0.0 <4.0.0"
  },
  "permissions": [
    "read:templates",
    "read:sessions",
    "ui:sidebar"
  ],
  "optionalPermissions": [
    "network:https://api.example.com"
  ],
  "keywords": [
    "templates",
    "therapy",
    "cbt"
  ],
  "categories": [
    "templates"
  ],
  "icon": "icon.png",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  },
  "dependencies": {
    "@braindump/plugin-sdk": "^1.0.0"
  }
}
```

---

**Document Complete**
**Research Date**: November 16, 2025
**Next Step**: Begin Phase 1 implementation (Plugin foundation & extension host)
