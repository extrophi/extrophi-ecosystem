// src-tauri/src/logging.rs
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;

/// Log levels matching our philosophy
#[derive(Debug, Clone, Copy)]
pub enum LogLevel {
    Info,
    Warn,
    Error,
    Critical,
}

impl LogLevel {
    fn as_str(&self) -> &str {
        match self {
            LogLevel::Info => "INFO",
            LogLevel::Warn => "WARN",
            LogLevel::Error => "ERROR",
            LogLevel::Critical => "CRITICAL",
        }
    }
}

/// Global logger instance
static LOGGER: Mutex<Option<Logger>> = Mutex::new(None);

/// Simple file logger for BrainDump
pub struct Logger {
    log_path: PathBuf,
}

impl Logger {
    /// Initialize the logger (call once at startup)
    pub fn init() -> Result<(), std::io::Error> {
        let log_dir = Self::get_log_dir()?;
        fs::create_dir_all(&log_dir)?;
        
        let log_path = log_dir.join("app.log");
        
        // Save display string before moving log_path
        let log_path_str = log_path.display().to_string();
        
        let logger = Logger { log_path };
        
        {
            let mut global = LOGGER.lock().unwrap();
            *global = Some(logger);
        }  // Lock dropped here - critical to prevent deadlock!
        
        // Write startup marker (safe now that lock is released)
        Self::log_internal(LogLevel::Info, "Startup", "=== BrainDump Started ===")?;
        Self::log_internal(LogLevel::Info, "Startup", "Version: 3.0.0")?;
        Self::log_internal(LogLevel::Info, "Startup", &format!("Log file: {}", log_path_str))?;
        
        Ok(())
    }
    
    /// Get platform-specific log directory
    fn get_log_dir() -> Result<PathBuf, std::io::Error> {
        let home = dirs::home_dir()
            .ok_or_else(|| std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "Could not find home directory"
            ))?;
        
        Ok(home.join(".braindump").join("logs"))
    }
    
    /// Internal logging function
    fn log_internal(level: LogLevel, component: &str, message: &str) -> Result<(), std::io::Error> {
        let global = LOGGER.lock().unwrap();
        
        if let Some(logger) = global.as_ref() {
            let timestamp = chrono::Local::now().format("%Y-%m-%d %H:%M:%S");
            let log_line = format!(
                "[{}] {:8} {}: {}\n",
                timestamp,
                level.as_str(),
                component,
                message
            );
            
            let mut file = OpenOptions::new()
                .create(true)
                .append(true)
                .open(&logger.log_path)?;
            
            file.write_all(log_line.as_bytes())?;
            file.flush()?;
            
            // Also print to stderr in debug mode
            if cfg!(debug_assertions) {
                eprint!("{}", log_line);
            }
        }
        
        Ok(())
    }
    
    /// Get the current log file path
    pub fn get_log_path() -> Option<PathBuf> {
        let global = LOGGER.lock().unwrap();
        global.as_ref().map(|logger| logger.log_path.clone())
    }
}

/// Public logging functions
pub fn info(component: &str, message: &str) {
    let _ = Logger::log_internal(LogLevel::Info, component, message);
}

pub fn warn(component: &str, message: &str) {
    let _ = Logger::log_internal(LogLevel::Warn, component, message);
}

pub fn error(component: &str, message: &str) {
    let _ = Logger::log_internal(LogLevel::Error, component, message);
}

pub fn critical(component: &str, message: &str) {
    let _ = Logger::log_internal(LogLevel::Critical, component, message);
}

/// Convenience macro for logging with automatic component name
#[macro_export]
macro_rules! log_info {
    ($msg:expr) => {
        $crate::logging::info(module_path!(), $msg)
    };
}

#[macro_export]
macro_rules! log_error {
    ($msg:expr) => {
        $crate::logging::error(module_path!(), $msg)
    };
}