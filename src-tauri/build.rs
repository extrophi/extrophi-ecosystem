fn main() {
    // Run Tauri build process to generate capabilities context
    tauri_build::build();
    
    // Set rpath for whisper.cpp libraries
    // @executable_path = where the binary lives
    // @executable_path/../Frameworks = where Tauri bundles frameworks
    println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path");
    println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path/../Frameworks");
    
    // Tell linker to link against whisper.cpp
    println!("cargo:rustc-link-lib=dylib=whisper");
    println!("cargo:rustc-link-search=native=/opt/homebrew/Cellar/whisper-cpp/1.8.2/libexec/lib");
}
