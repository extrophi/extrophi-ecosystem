//! WAV file writer using hound

use super::RecorderError;
use hound::{WavSpec, WavWriter as HoundWriter};
use std::path::Path;

pub struct WavWriter;

impl WavWriter {
    /// Write samples to WAV file (16-bit PCM, 16kHz mono)
    pub fn write<P: AsRef<Path>>(path: P, samples: &[f32]) -> Result<(), RecorderError> {
        Self::write_with_rate(path, samples, 16000)
    }

    /// Resample audio from input_rate to target_rate using linear interpolation
    pub fn resample_public(samples: &[f32], input_rate: u32, target_rate: u32) -> Vec<f32> {
        Self::resample(samples, input_rate, target_rate)
    }

    /// Resample audio from input_rate to target_rate using linear interpolation
    fn resample(samples: &[f32], input_rate: u32, target_rate: u32) -> Vec<f32> {
        if input_rate == target_rate {
            return samples.to_vec();
        }

        let ratio = input_rate as f64 / target_rate as f64;
        let output_len = (samples.len() as f64 / ratio) as usize;
        let mut resampled = Vec::with_capacity(output_len);

        for i in 0..output_len {
            let src_index = i as f64 * ratio;
            let index_floor = src_index.floor() as usize;
            let index_ceil = (index_floor + 1).min(samples.len() - 1);
            let fract = src_index - index_floor as f64;

            // Linear interpolation between adjacent samples
            let sample = samples[index_floor] * (1.0 - fract) as f32
                       + samples[index_ceil] * fract as f32;
            resampled.push(sample);
        }

        resampled
    }

    /// Write samples to WAV file, resampling from input_rate to 16kHz (16-bit PCM, mono)
    pub fn write_resampled<P: AsRef<Path>>(path: P, samples: &[f32], input_rate: u32) -> Result<(), RecorderError> {
        let resampled = Self::resample(samples, input_rate, 16000);
        Self::write_with_rate(path, &resampled, 16000)
    }

    /// Write samples to WAV file with custom sample rate (16-bit PCM, mono)
    pub fn write_with_rate<P: AsRef<Path>>(path: P, samples: &[f32], sample_rate: u32) -> Result<(), RecorderError> {
        let spec = WavSpec {
            channels: 1,
            sample_rate,
            bits_per_sample: 16,
            sample_format: hound::SampleFormat::Int,
        };
        
        let mut writer = HoundWriter::create(path, spec)
            .map_err(|e| RecorderError::Io(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
        
        for sample in samples {
            // Convert f32 [-1.0, 1.0] to i16 [-32768, 32767]
            let sample_i16 = (*sample * i16::MAX as f32) as i16;
            writer.write_sample(sample_i16)
                .map_err(|e| RecorderError::Io(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
        }
        
        writer.finalize()
            .map_err(|e| RecorderError::Io(std::io::Error::new(std::io::ErrorKind::Other, e)))?;
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    
    #[test]
    fn test_wav_write() {
        let samples = vec![0.0; 16000]; // 1 second of silence
        let path = "/tmp/test_recorder.wav";
        
        WavWriter::write(path, &samples).unwrap();
        
        // Verify file exists
        assert!(std::path::Path::new(path).exists());
        
        // Verify file size (~32KB for 1s 16kHz mono 16-bit)
        let metadata = fs::metadata(path).unwrap();
        assert!(metadata.len() > 30000 && metadata.len() < 35000);
        
        // Cleanup
        fs::remove_file(path).unwrap();
    }
}
