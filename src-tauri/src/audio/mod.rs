//! Audio recording module (Rust replacement for C++ recorder)

pub mod recorder;
pub mod wav_writer;

pub use recorder::{Recorder, RecorderError, RecorderResult};
pub use wav_writer::WavWriter;
