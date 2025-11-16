fn main() {
    // Run Tauri build process to generate capabilities context
    tauri_build::build();

    // Only link whisper.cpp if feature is enabled
    #[cfg(feature = "whisper")]
    link_whisper();
}

#[cfg(feature = "whisper")]
fn link_whisper() {
    // Try to use pkg-config first (works on macOS with Homebrew and Linux)
    if let Ok(lib) = pkg_config::Config::new().probe("whisper") {
        // pkg-config found whisper - it will automatically set link paths
        for path in &lib.link_paths {
            println!("cargo:rustc-link-search=native={}", path.display());
        }
        return;
    }

    // Fallback: Platform-specific manual linking if pkg-config fails
    eprintln!("Warning: pkg-config could not find whisper.cpp");
    eprintln!("Please install whisper.cpp:");
    eprintln!("  macOS: brew install whisper-cpp");
    eprintln!("  Linux: Install whisper.cpp from source or package manager");

    #[cfg(target_os = "macos")]
    {
        println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path");
        println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path/../Frameworks");
        println!("cargo:rustc-link-lib=dylib=whisper");
    }

    #[cfg(target_os = "linux")]
    {
        println!("cargo:rustc-link-arg=-Wl,-rpath,$ORIGIN");
        println!("cargo:rustc-link-arg=-Wl,-rpath,$ORIGIN/../lib");
        println!("cargo:rustc-link-lib=dylib=whisper");
    }
}
