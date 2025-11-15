fn main() {
    // Run Tauri build process to generate capabilities context
    tauri_build::build();

    // Platform-specific whisper.cpp linking
    #[cfg(target_os = "macos")]
    {
        // macOS: Use @executable_path rpath for dynamic library loading
        println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path");
        println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path/../Frameworks");

        // Link whisper.cpp dynamically
        println!("cargo:rustc-link-lib=dylib=whisper");

        // Try Homebrew location (both Intel and ARM)
        if std::path::Path::new("/opt/homebrew/lib").exists() {
            println!("cargo:rustc-link-search=native=/opt/homebrew/lib");
        } else if std::path::Path::new("/usr/local/lib").exists() {
            println!("cargo:rustc-link-search=native=/usr/local/lib");
        }
    }

    #[cfg(target_os = "linux")]
    {
        // Linux: Use $ORIGIN rpath for bundled libraries
        println!("cargo:rustc-link-arg=-Wl,-rpath,$ORIGIN");
        println!("cargo:rustc-link-arg=-Wl,-rpath,$ORIGIN/../lib");

        // Link whisper.cpp dynamically
        println!("cargo:rustc-link-lib=dylib=whisper");

        // Check common Linux library locations
        let search_paths = [
            "/usr/local/lib",
            "/usr/lib",
            "/usr/lib/x86_64-linux-gnu",
        ];

        for path in &search_paths {
            if std::path::Path::new(path).exists() {
                println!("cargo:rustc-link-search=native={}", path);
            }
        }
    }

    #[cfg(target_os = "windows")]
    {
        // Windows: Link whisper.dll
        println!("cargo:rustc-link-lib=dylib=whisper");

        // Check common Windows library locations
        if let Ok(vcpkg_root) = std::env::var("VCPKG_ROOT") {
            let lib_path = format!("{}\\installed\\x64-windows\\lib", vcpkg_root);
            if std::path::Path::new(&lib_path).exists() {
                println!("cargo:rustc-link-search=native={}", lib_path);
            }
        }

        // Also check local build directory
        if std::path::Path::new("whisper.cpp/build/Release").exists() {
            println!("cargo:rustc-link-search=native=whisper.cpp/build/Release");
        }
    }
}
