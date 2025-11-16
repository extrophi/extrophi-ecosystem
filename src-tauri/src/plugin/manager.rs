//! Plugin manager for registration and lifecycle management
//!
//! The `PluginManager` provides centralized control over transcription plugins,
//! allowing registration, switching, and invocation of the active plugin.

use super::types::PluginResult;
use super::{AudioData, PluginError, Transcript, TranscriptionPlugin};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

/// Information about a registered plugin
#[derive(Clone, Debug)]
pub struct PluginInfo {
    /// Plugin name
    pub name: String,
    /// Plugin version
    pub version: String,
    /// Whether this plugin is currently active
    pub is_active: bool,
    /// Whether the plugin is initialized
    pub is_initialized: bool,
}

/// Manages a collection of transcription plugins
///
/// The `PluginManager` maintains a registry of plugins and ensures only
/// one plugin is active at a time. It provides thread-safe access to plugins
/// via interior mutability.
///
/// # Example
///
/// ```rust
/// use braindump::plugin::{PluginManager, TranscriptionPlugin};
///
/// let mut manager = PluginManager::new();
///
/// // Register plugins
/// manager.register(Box::new(plugin1))?;
/// manager.register(Box::new(plugin2))?;
///
/// // Switch active plugin
/// manager.switch_plugin("plugin2")?;
///
/// // Use active plugin
/// let transcript = manager.transcribe(&audio)?;
/// ```
pub struct PluginManager {
    /// Map of plugin name to plugin instance
    plugins: HashMap<String, Arc<Mutex<Box<dyn TranscriptionPlugin>>>>,
    /// Name of the currently active plugin
    active_plugin: Option<String>,
}

impl PluginManager {
    /// Create a new empty plugin manager
    pub fn new() -> Self {
        Self {
            plugins: HashMap::new(),
            active_plugin: None,
        }
    }

    /// Register a new plugin
    ///
    /// If this is the first plugin registered, it automatically becomes active.
    ///
    /// # Arguments
    ///
    /// * `plugin` - Boxed trait object implementing `TranscriptionPlugin`
    ///
    /// # Errors
    ///
    /// Returns an error if a plugin with the same name is already registered.
    ///
    /// # Example
    ///
    /// ```rust
    /// manager.register(Box::new(WhisperCppPlugin::new(model_path)))?;
    /// ```
    pub fn register(&mut self, plugin: Box<dyn TranscriptionPlugin>) -> PluginResult<()> {
        let name = plugin.name().to_string();

        if self.plugins.contains_key(&name) {
            return Err(PluginError::InitializationFailed(format!(
                "Plugin '{}' is already registered",
                name
            )));
        }

        self.plugins
            .insert(name.clone(), Arc::new(Mutex::new(plugin)));

        // Set as active if first plugin
        if self.active_plugin.is_none() {
            self.active_plugin = Some(name);
        }

        Ok(())
    }

    /// Switch to a different plugin
    ///
    /// Changes the active plugin to the specified name. The plugin must
    /// already be registered.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the plugin to activate
    ///
    /// # Errors
    ///
    /// Returns `PluginError::NotFound` if the plugin isn't registered.
    ///
    /// # Example
    ///
    /// ```rust
    /// manager.switch_plugin("candle")?;
    /// ```
    pub fn switch_plugin(&mut self, name: &str) -> PluginResult<()> {
        if !self.plugins.contains_key(name) {
            return Err(PluginError::NotFound(name.to_string()));
        }
        self.active_plugin = Some(name.to_string());
        Ok(())
    }

    /// Get the currently active plugin
    ///
    /// Returns an `Arc<Mutex<>>` to the active plugin for thread-safe access.
    ///
    /// # Errors
    ///
    /// Returns `PluginError::NotFound` if no plugin is active.
    pub fn get_active(&self) -> PluginResult<Arc<Mutex<Box<dyn TranscriptionPlugin>>>> {
        let name = self
            .active_plugin
            .as_ref()
            .ok_or_else(|| PluginError::NotFound("No active plugin".to_string()))?;

        self.plugins
            .get(name)
            .cloned()
            .ok_or_else(|| PluginError::NotFound(name.clone()))
    }

    /// Get a specific plugin by name
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the plugin to retrieve
    ///
    /// # Errors
    ///
    /// Returns `PluginError::NotFound` if the plugin doesn't exist.
    pub fn get_plugin(&self, name: &str) -> PluginResult<Arc<Mutex<Box<dyn TranscriptionPlugin>>>> {
        self.plugins
            .get(name)
            .cloned()
            .ok_or_else(|| PluginError::NotFound(name.to_string()))
    }

    /// List all registered plugins with their metadata
    ///
    /// Returns a vector of `PluginInfo` containing details about each plugin.
    pub fn list_plugins(&self) -> Vec<PluginInfo> {
        self.plugins
            .iter()
            .filter_map(|(name, plugin)| {
                // Recover from poisoned mutex by extracting the inner data
                let plugin_guard = plugin
                    .lock()
                    .unwrap_or_else(|poisoned| poisoned.into_inner());
                Some(PluginInfo {
                    name: name.clone(),
                    version: plugin_guard.version().to_string(),
                    is_active: self.active_plugin.as_ref() == Some(name),
                    is_initialized: plugin_guard.is_initialized(),
                })
            })
            .collect()
    }

    /// Transcribe audio using the active plugin
    ///
    /// This is a convenience method that gets the active plugin and calls
    /// its `transcribe()` method.
    ///
    /// # Arguments
    ///
    /// * `audio` - Audio data to transcribe
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - No plugin is active
    /// - The active plugin is not initialized
    /// - Transcription fails
    ///
    /// # Example
    ///
    /// ```rust
    /// let audio = AudioData { /* ... */ };
    /// let transcript = manager.transcribe(&audio)?;
    /// println!("Transcript: {}", transcript.text);
    /// ```
    pub fn transcribe(&self, audio: &AudioData) -> PluginResult<Transcript> {
        let plugin = self.get_active()?;
        // Recover from poisoned mutex by extracting the inner data
        let plugin_guard = plugin
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        plugin_guard.transcribe(audio)
    }

    /// Get the name of the active plugin
    ///
    /// Returns `None` if no plugin is active.
    pub fn active_plugin_name(&self) -> Option<&str> {
        self.active_plugin.as_deref()
    }

    /// Initialize all registered plugins
    ///
    /// Calls `initialize()` on each plugin. Continues even if some fail.
    ///
    /// # Returns
    ///
    /// A vector of tuples containing (plugin_name, Result) for each plugin.
    pub fn initialize_all(&self) -> Vec<(String, PluginResult<()>)> {
        self.plugins
            .iter()
            .map(|(name, plugin)| {
                // Recover from poisoned mutex by extracting the inner data
                let mut plugin_guard = plugin
                    .lock()
                    .unwrap_or_else(|poisoned| poisoned.into_inner());
                let result = plugin_guard.initialize();
                (name.clone(), result)
            })
            .collect()
    }

    /// Shutdown all registered plugins
    ///
    /// Calls `shutdown()` on each plugin. Continues even if some fail.
    ///
    /// # Returns
    ///
    /// A vector of tuples containing (plugin_name, Result) for each plugin.
    pub fn shutdown_all(&self) -> Vec<(String, PluginResult<()>)> {
        self.plugins
            .iter()
            .map(|(name, plugin)| {
                // Recover from poisoned mutex by extracting the inner data
                let mut plugin_guard = plugin
                    .lock()
                    .unwrap_or_else(|poisoned| poisoned.into_inner());
                let result = plugin_guard.shutdown();
                (name.clone(), result)
            })
            .collect()
    }

    /// Get the number of registered plugins
    pub fn plugin_count(&self) -> usize {
        self.plugins.len()
    }

    /// Check if a plugin with the given name is registered
    pub fn has_plugin(&self, name: &str) -> bool {
        self.plugins.contains_key(name)
    }
}

impl Default for PluginManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Mock plugin for testing
    struct MockPlugin {
        name: String,
        initialized: bool,
    }

    impl MockPlugin {
        fn new(name: &str) -> Self {
            Self {
                name: name.to_string(),
                initialized: false,
            }
        }
    }

    impl TranscriptionPlugin for MockPlugin {
        fn name(&self) -> &str {
            &self.name
        }

        fn version(&self) -> &str {
            "1.0.0"
        }

        fn initialize(&mut self) -> PluginResult<()> {
            self.initialized = true;
            Ok(())
        }

        fn transcribe(&self, audio: &AudioData) -> PluginResult<Transcript> {
            if !self.initialized {
                return Err(PluginError::NotInitialized(self.name.clone()));
            }

            Ok(Transcript {
                text: format!("Mock from {}", self.name),
                language: Some("en".to_string()),
                segments: vec![],
            })
        }

        fn shutdown(&mut self) -> PluginResult<()> {
            self.initialized = false;
            Ok(())
        }

        fn is_initialized(&self) -> bool {
            self.initialized
        }
    }

    #[test]
    fn test_new_manager() {
        let manager = PluginManager::new();
        assert_eq!(manager.plugin_count(), 0);
        assert!(manager.active_plugin_name().is_none());
    }

    #[test]
    fn test_register_plugin() {
        let mut manager = PluginManager::new();
        let plugin = Box::new(MockPlugin::new("test"));

        manager.register(plugin).expect("Failed to register plugin");

        assert_eq!(manager.plugin_count(), 1);
        assert!(manager.has_plugin("test"));
        assert_eq!(manager.active_plugin_name(), Some("test"));
    }

    #[test]
    fn test_register_duplicate_plugin() {
        let mut manager = PluginManager::new();

        manager
            .register(Box::new(MockPlugin::new("test")))
            .expect("Failed to register first plugin");
        let result = manager.register(Box::new(MockPlugin::new("test")));

        assert!(matches!(result, Err(PluginError::InitializationFailed(_))));
    }

    #[test]
    fn test_register_multiple_plugins() {
        let mut manager = PluginManager::new();

        manager
            .register(Box::new(MockPlugin::new("plugin1")))
            .expect("Failed to register plugin1");
        manager
            .register(Box::new(MockPlugin::new("plugin2")))
            .expect("Failed to register plugin2");
        manager
            .register(Box::new(MockPlugin::new("plugin3")))
            .expect("Failed to register plugin3");

        assert_eq!(manager.plugin_count(), 3);
        // First plugin should be active
        assert_eq!(manager.active_plugin_name(), Some("plugin1"));
    }

    #[test]
    fn test_switch_plugin() {
        let mut manager = PluginManager::new();

        manager
            .register(Box::new(MockPlugin::new("plugin1")))
            .expect("Failed to register plugin1");
        manager
            .register(Box::new(MockPlugin::new("plugin2")))
            .expect("Failed to register plugin2");

        assert_eq!(manager.active_plugin_name(), Some("plugin1"));

        manager
            .switch_plugin("plugin2")
            .expect("Failed to switch plugin");
        assert_eq!(manager.active_plugin_name(), Some("plugin2"));
    }

    #[test]
    fn test_switch_to_nonexistent_plugin() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("plugin1")))
            .expect("Failed to register plugin");

        let result = manager.switch_plugin("nonexistent");
        assert!(matches!(result, Err(PluginError::NotFound(_))));
    }

    #[test]
    fn test_get_active_plugin() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("test")))
            .expect("Failed to register plugin");

        let plugin = manager.get_active().expect("Failed to get active plugin");
        let plugin_guard = plugin.lock().expect("Failed to lock plugin mutex");

        assert_eq!(plugin_guard.name(), "test");
    }

    #[test]
    fn test_get_active_no_plugins() {
        let manager = PluginManager::new();
        let result = manager.get_active();

        assert!(matches!(result, Err(PluginError::NotFound(_))));
    }

    #[test]
    fn test_get_plugin_by_name() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("plugin1")))
            .expect("Failed to register plugin1");
        manager
            .register(Box::new(MockPlugin::new("plugin2")))
            .expect("Failed to register plugin2");

        let plugin = manager
            .get_plugin("plugin2")
            .expect("Failed to get plugin by name");
        let plugin_guard = plugin.lock().expect("Failed to lock plugin mutex");

        assert_eq!(plugin_guard.name(), "plugin2");
    }

    #[test]
    fn test_list_plugins() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("plugin1")))
            .expect("Failed to register plugin1");
        manager
            .register(Box::new(MockPlugin::new("plugin2")))
            .expect("Failed to register plugin2");

        let plugins = manager.list_plugins();
        assert_eq!(plugins.len(), 2);

        // Check that one is marked as active
        let active_count = plugins.iter().filter(|p| p.is_active).count();
        assert_eq!(active_count, 1);
    }

    #[test]
    fn test_transcribe_with_active_plugin() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("test")))
            .expect("Failed to register plugin");

        // Initialize the plugin
        let plugin = manager.get_active().expect("Failed to get active plugin");
        plugin
            .lock()
            .expect("Failed to lock plugin mutex")
            .initialize()
            .expect("Failed to initialize plugin");

        let audio = AudioData {
            samples: vec![0.0; 100],
            sample_rate: 16000,
            channels: 1,
        };

        let transcript = manager
            .transcribe(&audio)
            .expect("Failed to transcribe audio");
        assert!(transcript.text.contains("Mock from test"));
    }

    #[test]
    fn test_initialize_all() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("plugin1")))
            .expect("Failed to register plugin1");
        manager
            .register(Box::new(MockPlugin::new("plugin2")))
            .expect("Failed to register plugin2");

        let results = manager.initialize_all();
        assert_eq!(results.len(), 2);

        // All should succeed
        for (_, result) in results {
            assert!(result.is_ok());
        }

        // Verify all are initialized
        let plugins = manager.list_plugins();
        for plugin in plugins {
            assert!(plugin.is_initialized);
        }
    }

    #[test]
    fn test_shutdown_all() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("plugin1")))
            .expect("Failed to register plugin1");
        manager
            .register(Box::new(MockPlugin::new("plugin2")))
            .expect("Failed to register plugin2");

        // Initialize first
        manager.initialize_all();

        // Then shutdown
        let results = manager.shutdown_all();
        assert_eq!(results.len(), 2);

        // All should succeed
        for (_, result) in results {
            assert!(result.is_ok());
        }

        // Verify all are shutdown
        let plugins = manager.list_plugins();
        for plugin in plugins {
            assert!(!plugin.is_initialized);
        }
    }

    #[test]
    fn test_has_plugin() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("test")))
            .expect("Failed to register plugin");

        assert!(manager.has_plugin("test"));
        assert!(!manager.has_plugin("nonexistent"));
    }

    #[test]
    fn test_plugin_info_structure() {
        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("test")))
            .expect("Failed to register plugin");

        let plugins = manager.list_plugins();
        assert_eq!(plugins.len(), 1);

        let info = &plugins[0];
        assert_eq!(info.name, "test");
        assert_eq!(info.version, "1.0.0");
        assert!(info.is_active);
        assert!(!info.is_initialized);
    }

    #[test]
    fn test_thread_safety() {
        use std::sync::Arc;
        use std::thread;

        let mut manager = PluginManager::new();
        manager
            .register(Box::new(MockPlugin::new("test")))
            .expect("Failed to register plugin");

        // Initialize plugin
        let plugin = manager.get_active().expect("Failed to get active plugin");
        plugin
            .lock()
            .expect("Failed to lock plugin mutex")
            .initialize()
            .expect("Failed to initialize plugin");

        let manager = Arc::new(manager);
        let mut handles = vec![];

        // Spawn multiple threads transcribing
        for _ in 0..5 {
            let manager_clone = Arc::clone(&manager);
            let handle = thread::spawn(move || {
                let audio = AudioData {
                    samples: vec![0.0; 100],
                    sample_rate: 16000,
                    channels: 1,
                };
                manager_clone.transcribe(&audio)
            });
            handles.push(handle);
        }

        // Wait for all threads
        for handle in handles {
            let result = handle.join().expect("Thread panicked");
            assert!(result.is_ok());
        }
    }
}
