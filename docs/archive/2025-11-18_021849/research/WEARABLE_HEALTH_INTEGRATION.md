# Wearable Health Data Integration Research

**Date:** 2025-11-16
**Agent:** Iota2
**Purpose:** Research health data integration opportunities for BrainDump voice journaling context

---

## Executive Summary

This report analyzes the feasibility and implementation pathways for integrating wearable health data into BrainDump's voice journaling experience. The research covers major health platforms (Apple HealthKit, Fitbit, Oura, Garmin, Whoop), privacy regulations, data correlation opportunities, and technical implementation patterns for Tauri/Swift integration.

**Key Findings:**
- Apple HealthKit is the most comprehensive option for macOS/iOS integration
- Strong research evidence supports HRV-mood correlations (83% classification accuracy)
- HIPAA generally does NOT apply to consumer wearable apps (but state laws may)
- Tauri can bridge to Swift via `swift-bridge` crate for native HealthKit access
- Multiple REST APIs available for cross-platform support (Fitbit, Oura, Garmin)

---

## Table of Contents

1. [API Comparison Matrix](#api-comparison-matrix)
2. [Platform Deep Dives](#platform-deep-dives)
3. [Privacy and Consent Requirements](#privacy-and-consent-requirements)
4. [Health-Journaling Correlation Research](#health-journaling-correlation-research)
5. [Data Schema for Health Metrics](#data-schema-for-health-metrics)
6. [Visualization Recommendations](#visualization-recommendations)
7. [Implementation Roadmap for Tauri/Swift](#implementation-roadmap-for-tauriswift)
8. [Use Cases and AI Integration](#use-cases-and-ai-integration)
9. [Recommendations](#recommendations)

---

## API Comparison Matrix

| Platform | Auth Method | Data Types | Rate Limits | Platform Support | Status |
|----------|-------------|-----------|-------------|-----------------|--------|
| **Apple HealthKit** | Native iOS/macOS | HR, HRV, Sleep, Steps, SpO2, ECG | Device-based | iOS/macOS only | Active |
| **Fitbit Web API** | OAuth 2.0 | HR, Sleep Stages, HRV, SpO2, Stress | 150 req/hour/user | Cross-platform | Active |
| **Oura Ring API** | OAuth 2.0 / PAT | Sleep, HRV, Readiness, Temp | Not published | Cross-platform | Active (V2) |
| **Garmin Health API** | OAuth 2.0 | HR, Sleep, Stress, Steps | By agreement | Cross-platform | Active |
| **WHOOP API** | OAuth 2.0 | Recovery, Strain, Sleep, HRV | Free tier | Cross-platform | Active |
| **Google Fit** | OAuth 2.0 | HR, Sleep, Steps, Weight | Standard GCP | Cross-platform | **DEPRECATED 2026** |
| **Samsung Health** | SDK Partnership | HR, Sleep, Steps | By agreement | Android only | Active (new SDK) |

### Integration Complexity

1. **Easiest:** Fitbit, Oura (REST APIs with good documentation)
2. **Moderate:** Apple HealthKit (native but requires Swift bridge), Garmin, WHOOP
3. **Complex:** Samsung Health (partnership required), Google Fit (deprecated)

---

## Platform Deep Dives

### Apple HealthKit (Priority: HIGH)

**Why Prioritize:**
- Native integration with macOS (target platform)
- Richest data set (300+ health data types)
- Real-time heart rate from Apple Watch
- No API rate limits (device-based)
- Privacy-first architecture (user controls all permissions)

**Key Data Types for Journaling:**

```swift
// Quantity Types
HKQuantityTypeIdentifier.heartRate           // BPM
HKQuantityTypeIdentifier.heartRateVariabilitySDNN  // HRV in ms
HKQuantityTypeIdentifier.restingHeartRate    // Baseline
HKQuantityTypeIdentifier.oxygenSaturation    // SpO2 %
HKQuantityTypeIdentifier.respiratoryRate     // Breaths/min

// Category Types
HKCategoryTypeIdentifier.sleepAnalysis       // Sleep stages
HKCategoryTypeIdentifier.mindfulSession      // Meditation time

// Correlation Types (advanced)
HKCorrelationTypeIdentifier.bloodPressure    // Systolic/Diastolic
```

**Real-Time Limitations:**
- Heart rate: Every few seconds during workouts
- Other metrics: Up to 30-minute delay from Apple Watch
- Background delivery available but limited

**Setup Requirements:**
1. Add HealthKit capability in Xcode
2. Request specific permissions in Info.plist
3. User must grant explicit consent per data type
4. Data stays on device (privacy-first)

---

### Fitbit Web API (Priority: HIGH)

**Why Consider:**
- Large user base (30M+ active users)
- Well-documented REST API
- Sleep stages with 30-second granularity
- HRV intraday data available
- Cross-platform web access

**Key Endpoints:**

```http
# Heart Rate Time Series
GET /1/user/-/activities/heart/date/{date}/1d/1min.json

# Sleep Log with Stages
GET /1.2/user/-/sleep/date/{date}.json

# HRV Intraday
GET /1/user/-/hrv/date/{date}/all.json
```

**OAuth 2.0 Scopes:**
- `heartrate` - Heart rate data
- `sleep` - Sleep logs
- `activity` - Steps, calories
- `oxygen_saturation` - SpO2
- `respiratory_rate` - Breathing
- `temperature` - Skin temp

**Rate Limits:**
- 150 API requests per hour per user
- Token expires in 28,800 seconds (8 hours)
- Refresh tokens available

**Sleep Stages Data:**

```json
{
  "levels": {
    "data": [
      {
        "dateTime": "2025-11-16T00:00:00.000",
        "level": "deep",
        "seconds": 1800
      },
      {
        "level": "light",
        "seconds": 3600
      },
      {
        "level": "rem",
        "seconds": 2400
      },
      {
        "level": "wake",
        "seconds": 300
      }
    ]
  }
}
```

---

### Oura Ring API (Priority: MEDIUM)

**Unique Value:**
- Highest accuracy HRV measurement (clinical-grade)
- Readiness score combines multiple metrics
- Temperature tracking (baseline deviation)
- Sleep efficiency scoring
- V2 API (V1 removed January 2024)

**Key Data Types:**

```json
// Sleep Endpoint Response
{
  "average_hrv": 45,
  "average_heart_rate": 52,
  "deep_sleep_duration": 5400,
  "rem_sleep_duration": 7200,
  "light_sleep_duration": 14400,
  "efficiency": 92
}

// Readiness Endpoint Response
{
  "score": 85,
  "contributors": {
    "hrv_balance": 90,
    "sleep_balance": 88,
    "resting_heart_rate": 85,
    "body_temperature": 95,
    "recovery_index": 78
  }
}
```

**Access Methods:**
1. Personal Access Token (PAT) - Single user, quick setup
2. OAuth 2.0 Application - Multi-user, production apps

---

### Garmin Health API (Priority: MEDIUM)

**Architecture:**
- **Ping/Pull:** Poll for new data
- **Push:** Real-time webhooks when data available
- JSON format responses

**Data Available:**
- All-day heart rate
- Sleep analysis with stages
- Stress levels (proprietary algorithm)
- Body battery (energy level)
- Respiration rate
- Pulse Ox

**Access Requirements:**
- Must apply via Garmin Developer Portal
- Focus on Corporate Wellness, Population Health
- Developer web tools for testing
- Customized data feeds

---

### WHOOP API (Priority: LOW-MEDIUM)

**Unique Metrics:**
- **Strain Score:** 0-21 scale (daily exertion)
- **Recovery Score:** Based on HRV, sleep, RHR
- **Sleep Performance:** Efficiency and consistency

**Limitations:**
- Summary data only (no continuous HR)
- Requires WHOOP membership ($30/month)
- Focus on performance athletes

**API Data:**
```json
{
  "recovery": {
    "score": 85,
    "hrv_rmssd": 45.2,
    "resting_heart_rate": 52
  },
  "strain": {
    "score": 12.5,
    "day_strain": 10.2,
    "workout_strain": 2.3
  }
}
```

---

### Samsung Health (Priority: LOW)

**Important Notes:**
- Old SDK deprecated July 31, 2025
- New Samsung Health Data SDK required
- Partnership agreement mandatory
- Android only (not macOS)
- Galaxy Watch/Ring data available

**Not Recommended** for BrainDump due to:
- Platform mismatch (Android vs macOS/iOS)
- Partnership overhead
- Limited to Samsung ecosystem

---

### Google Fit API (Priority: NONE)

**CRITICAL: DEPRECATED**
- No new sign-ups as of May 1, 2024
- Full deprecation in 2026
- Migrate to Android Health Connect
- Not viable for new development

---

## Privacy and Consent Requirements

### HIPAA Applicability

**Generally Does NOT Apply to Consumer Wearables:**
- HIPAA covers "covered entities" (hospitals, insurers, healthcare providers)
- Consumer health apps typically fall outside HIPAA scope
- Exception: If app interfaces with provider's EHR system

**When HIPAA Applies:**
- Data shared with healthcare providers
- Integration with Electronic Health Records
- Used in clinical treatment context

### GDPR Requirements (EU Users)

**Consent Requirements:**
- Explicit, granular consent for sensitive health data
- Must be: freely given, specific, informed, unambiguous
- User can withdraw consent at any time
- Right to data portability and deletion
- Clear purpose limitation

**Implementation:**
```javascript
// Geofenced consent example
const consentModal = {
  EU: {
    type: 'explicit_opt_in',
    granularity: 'per_data_type',
    withdrawable: true,
    dataPortability: true
  },
  US: {
    type: 'opt_out',
    notice: 'privacy_policy',
    stateSpecific: true
  }
};
```

### State-Level Regulations (US)

**California (CCPA/CPRA):**
- Wearable metrics classified as "sensitive personal information"
- Opt-out rights required
- Data minimization principles

**Washington (My Health My Data Act):**
- Opt-in consent required for health data
- Geofencing restrictions near health facilities
- Private right of action

**Other States (19 total as of 2025):**
- Colorado, Virginia, Connecticut have comprehensive privacy laws
- Many include health data provisions
- Check individual state requirements

### New Federal Legislation (2025)

**Health Information Privacy Reform Act (HIPRA):**
- Introduced November 4, 2025 by Senator Cassidy
- Requires disclosure that wellness data is NOT HIPAA-protected
- Mandatory opt-out mechanism for wellness data generation
- May become law - monitor closely

### BrainDump-Specific Recommendations

1. **Clear Disclosure:**
   ```
   "Health data from your wearable is stored locally on your device.
   This data is NOT protected by HIPAA. You control all sharing."
   ```

2. **Granular Permissions:**
   - Heart rate: Separate consent
   - Sleep data: Separate consent
   - HRV: Separate consent
   - Each for specific use (AI context, visualization, etc.)

3. **Local-First Architecture:**
   - Store health data locally (SQLite)
   - Never transmit to cloud without explicit consent
   - Option to send anonymized summaries only

4. **Data Minimization:**
   - Only collect what's used
   - Aggregate metrics preferred over raw data
   - Auto-purge after configurable retention period

5. **Audit Trail:**
   - Log all health data access
   - User can review what data was used when
   - Export/delete functionality

---

## Health-Journaling Correlation Research

### Scientific Evidence

**HRV and Mental Health (2024-2025 Research):**

1. **Classification Accuracy:**
   - 83% accuracy for mental health state prediction with 5-min HRV data
   - 73% accuracy with just 2-min HRV data
   - Higher than previously thought possible with consumer devices

2. **Key HRV Metrics:**
   - **RMSSD:** Root mean square of successive differences
   - **SDNN:** Standard deviation of NN intervals
   - **HF (High Frequency):** Parasympathetic activity
   - **LF/HF Ratio:** Sympathetic/parasympathetic balance

3. **Significant Correlations Found:**
   - RMSSD ↔ PHQ-9 depression scores
   - HRV during sleep ↔ daytime stress levels
   - Oura ring HRV ↔ anxiety from stress (strong positive correlation)

**Bipolar Disorder Monitoring:**
- Up to 95.81% accuracy in mood state recognition
- Using personalized HRV baselines
- Long-term trend analysis critical

**Limitations to Consider:**
- Individual variation (age, sex, BMI)
- HRV alone insufficient for diagnosis
- Should be "component of complex phenomenon"
- Not a proxy for perceived stress

### Practical Correlations for BrainDump

**High-Value Correlations:**

1. **Stress Level During Recording:**
   ```
   Recording at 2:30 PM
   Real-time HR: 85 bpm (↑ from baseline 72)
   HRV: 35ms (↓ from average 45ms)

   AI Context: "User appears stressed during this recording.
               Consider themes of anxiety or pressure."
   ```

2. **Sleep Quality → Mood:**
   ```
   Last night: 62% sleep efficiency, 3.2 hours deep sleep
   Morning journal tone: Negative sentiment, frustration

   Pattern: Poor sleep correlates with negative journaling
   ```

3. **Recovery State:**
   ```
   Oura Readiness: 58 (low)
   WHOOP Recovery: 45%

   AI Insight: "Low recovery may affect cognitive function.
               Today might benefit from lighter reflection prompts."
   ```

4. **Activity Level:**
   ```
   Steps today: 12,450 (above average)
   Calories: 2,800
   Last journal: Energetic, positive, future-focused

   Trend: Higher activity days = more optimistic journaling
   ```

### Data Model for Correlations

```sql
-- Health context for each journal entry
CREATE TABLE health_context (
    id INTEGER PRIMARY KEY,
    recording_id INTEGER REFERENCES recordings(id),
    recorded_at TIMESTAMP NOT NULL,

    -- Heart metrics at recording time
    heart_rate_bpm INTEGER,
    heart_rate_baseline INTEGER,
    hrv_ms REAL,
    hrv_baseline REAL,

    -- Sleep from previous night
    sleep_duration_minutes INTEGER,
    sleep_efficiency_percent REAL,
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,

    -- Daily metrics
    readiness_score INTEGER,
    recovery_percent INTEGER,
    stress_level INTEGER,

    -- Computed flags
    elevated_stress BOOLEAN,
    poor_sleep BOOLEAN,
    high_recovery BOOLEAN,

    -- Source tracking
    data_source TEXT,  -- 'healthkit', 'fitbit', 'oura'
    sync_timestamp TIMESTAMP
);
```

---

## Data Schema for Health Metrics

### Unified Health Data Schema

```sql
-- Core health metrics table (platform-agnostic)
CREATE TABLE health_metrics (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'local',
    metric_type TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    source_platform TEXT NOT NULL,
    source_device TEXT,
    metadata TEXT,  -- JSON for platform-specific data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_health_metrics_type_time
    ON health_metrics(metric_type, recorded_at DESC);
CREATE INDEX idx_health_metrics_source
    ON health_metrics(source_platform);

-- Metric type constants
-- 'heart_rate' | 'hrv' | 'resting_hr' | 'sleep_duration' |
-- 'deep_sleep' | 'rem_sleep' | 'light_sleep' | 'awake_time' |
-- 'sleep_efficiency' | 'readiness' | 'recovery' | 'strain' |
-- 'stress_level' | 'steps' | 'calories' | 'spo2' |
-- 'respiratory_rate' | 'body_temperature'
```

### Sleep Session Schema

```sql
CREATE TABLE sleep_sessions (
    id INTEGER PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    total_duration_minutes INTEGER,

    -- Stage durations (minutes)
    deep_sleep_minutes INTEGER,
    light_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,
    awake_minutes INTEGER,

    -- Quality metrics
    efficiency_percent REAL,
    latency_minutes INTEGER,
    awakenings_count INTEGER,

    -- Biometrics during sleep
    avg_heart_rate INTEGER,
    min_heart_rate INTEGER,
    avg_hrv REAL,
    avg_respiratory_rate REAL,
    avg_spo2 REAL,

    -- Scores
    sleep_score INTEGER,

    -- Source
    source_platform TEXT,
    raw_data TEXT,  -- JSON backup
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Daily Summary Schema

```sql
CREATE TABLE daily_health_summary (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Activity
    total_steps INTEGER,
    total_calories INTEGER,
    active_minutes INTEGER,

    -- Heart
    resting_heart_rate INTEGER,
    avg_hrv REAL,
    max_hrv REAL,
    min_hrv REAL,

    -- Recovery/Readiness
    readiness_score INTEGER,
    recovery_percent INTEGER,
    strain_score REAL,
    stress_score INTEGER,

    -- Sleep (from previous night)
    sleep_session_id INTEGER REFERENCES sleep_sessions(id),

    -- Wellness
    body_battery INTEGER,
    mood_score INTEGER,  -- User input

    -- Journaling correlation
    journal_entries_count INTEGER,
    avg_sentiment_score REAL,
    total_recording_minutes INTEGER,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Platform-Specific Metadata

```json
// Apple HealthKit metadata
{
  "source_bundle_id": "com.apple.health",
  "device_name": "Apple Watch Series 9",
  "was_user_entered": false,
  "metadata": {
    "HKMetadataKeyHeartRateMotionContext": 1
  }
}

// Fitbit metadata
{
  "tracker_id": "abc123",
  "log_type": "auto_detected",
  "confidence_level": "FINAL",
  "time_in_bed": 480
}

// Oura metadata
{
  "ring_firmware": "2.0.1",
  "bedtime_start": "2025-11-16T22:30:00Z",
  "temperature_deviation": -0.2
}
```

---

## Visualization Recommendations

### JavaScript Libraries for Health Data

**1. Open mHealth Web Visualizations (Recommended)**
- Purpose-built for health data
- Heart rate: 30-150 BPM range built-in
- Sleep patterns visualization
- Data quantization for performance
- Open source (Apache 2.0)

```javascript
import { HeartRateChart } from 'openmhealth-web-visualizations';

<HeartRateChart
  data={heartRateData}
  yDomain={[40, 160]}
  quantization="hour"
/>
```

**2. hGraph (MITRE Corporation)**
- Designed for health metrics
- Fitness index visualization
- Sleep, nutrition, activity categories
- Apache 2.0 license
- Clear health score representation

**3. LightningChart (High Performance)**
- 500M+ data points for time series
- Real-time ECG/HRV visualization
- Medical-grade precision
- Commercial license

**4. General Purpose Options**
- **D3.js:** Most flexible, steeper learning curve
- **Chart.js:** Easy setup, good for basic charts
- **Plotly.js:** Interactive, scientific charts

### Visualization Components for BrainDump

**1. Heart Rate During Recording (Real-time)**
```svelte
<script>
  let heartRateHistory = $state([]);
  let currentHR = $derived(heartRateHistory[heartRateHistory.length - 1]);

  // SVG line chart with real-time updates
</script>

<div class="recording-vitals">
  <span class="current-hr">{currentHR} BPM</span>
  <svg class="hr-timeline">
    <!-- Smooth line showing HR during recording -->
  </svg>
</div>
```

**2. Sleep Quality Sparkline (Dashboard)**
```svelte
<div class="sleep-week">
  {#each weekSleep as night}
    <div
      class="sleep-bar"
      style:height="{night.efficiency}%"
      style:--deep="{night.deepPercent}%"
      style:--rem="{night.remPercent}%"
      style:--light="{night.lightPercent}%"
    >
      <div class="deep" />
      <div class="rem" />
      <div class="light" />
    </div>
  {/each}
</div>
```

**3. HRV Trend Chart (Mental Wellness)**
```javascript
// 30-day HRV trend with journaling sentiment overlay
const hrvTrend = {
  labels: dates,
  datasets: [
    {
      label: 'HRV (ms)',
      data: hrvValues,
      borderColor: '#10B981',
      yAxisID: 'hrv'
    },
    {
      label: 'Journal Sentiment',
      data: sentimentScores,
      borderColor: '#6366F1',
      yAxisID: 'sentiment'
    }
  ]
};
```

**4. Readiness/Recovery Gauge**
```svelte
<div class="readiness-gauge">
  <svg viewBox="0 0 100 50">
    <path
      d="M 10,50 A 40,40 0 0,1 90,50"
      stroke="#E5E7EB"
      stroke-width="8"
      fill="none"
    />
    <path
      d="M 10,50 A 40,40 0 0,1 90,50"
      stroke="#10B981"
      stroke-width="8"
      stroke-dasharray="{readinessScore * 1.26} 126"
      fill="none"
    />
  </svg>
  <span class="score">{readinessScore}</span>
</div>
```

**5. Health Context Panel (Chat Interface)**
```svelte
<div class="health-context-badge">
  <div class="metric">
    <Icon name="heart" />
    <span>{heartRate} BPM</span>
    {#if heartRate > baseline}
      <span class="elevated">↑</span>
    {/if}
  </div>
  <div class="metric">
    <Icon name="moon" />
    <span>{sleepEfficiency}% sleep</span>
  </div>
  <div class="metric">
    <Icon name="battery" />
    <span>{readiness}/100</span>
  </div>
</div>
```

### Color Schemes for Health States

```css
:root {
  /* Recovery/Readiness */
  --health-excellent: #10B981;  /* Green: 80-100 */
  --health-good: #84CC16;       /* Lime: 60-79 */
  --health-fair: #F59E0B;       /* Amber: 40-59 */
  --health-poor: #EF4444;       /* Red: 0-39 */

  /* Sleep Stages */
  --sleep-deep: #1E40AF;        /* Dark blue */
  --sleep-rem: #7C3AED;         /* Purple */
  --sleep-light: #60A5FA;       /* Light blue */
  --sleep-awake: #FCA5A5;       /* Light red */

  /* Heart Rate */
  --hr-resting: #10B981;
  --hr-elevated: #F59E0B;
  --hr-high: #EF4444;
}
```

---

## Implementation Roadmap for Tauri/Swift

### Phase 1: Foundation (2-3 weeks)

**1.1 Swift Bridge Setup**

Use `swift-bridge` crate for Rust-Swift FFI:

```toml
# src-tauri/Cargo.toml
[build-dependencies]
swift-bridge-build = "0.1"

[dependencies]
swift-bridge = "0.1"
```

```rust
// src-tauri/src/healthkit_bridge.rs
#[swift_bridge::bridge]
mod ffi {
    extern "Swift" {
        type HealthKitManager;

        #[swift_bridge(init)]
        fn new() -> HealthKitManager;

        async fn request_authorization(&self) -> bool;
        async fn get_heart_rate(&self) -> Option<f64>;
        async fn get_hrv(&self) -> Option<f64>;
        async fn get_sleep_data(&self, date: String) -> String; // JSON
    }
}
```

```swift
// Sources/HealthKitManager.swift
import HealthKit

public class HealthKitManager {
    private let healthStore = HKHealthStore()

    public init() {}

    public func requestAuthorization() async -> Bool {
        let types: Set<HKSampleType> = [
            HKQuantityType(.heartRate),
            HKQuantityType(.heartRateVariabilitySDNN),
            HKCategoryType(.sleepAnalysis)
        ]

        do {
            try await healthStore.requestAuthorization(
                toShare: [],
                read: types
            )
            return true
        } catch {
            return false
        }
    }

    public func getHeartRate() async -> Double? {
        // Query latest heart rate sample
        // Return BPM value
    }
}
```

**1.2 Database Schema Migration**

Add tables from [Data Schema](#data-schema-for-health-metrics) section.

**1.3 Basic UI Components**

- Health permission request dialog
- Connected device indicator
- Simple heart rate display

### Phase 2: Apple HealthKit Integration (3-4 weeks)

**2.1 Core HealthKit Features**

- Heart rate reading (latest + time series)
- HRV queries (SDNN)
- Sleep analysis data
- Resting heart rate

**2.2 Tauri Commands**

```rust
// src-tauri/src/commands.rs
#[tauri::command]
pub async fn connect_healthkit(
    state: tauri::State<'_, AppState>
) -> Result<bool, String> {
    let manager = HealthKitManager::new();
    let authorized = manager.request_authorization().await;

    if authorized {
        state.health_source.lock().unwrap().insert(
            "healthkit".to_string(),
            Box::new(manager)
        );
    }

    Ok(authorized)
}

#[tauri::command]
pub async fn get_current_vitals(
    state: tauri::State<'_, AppState>
) -> Result<VitalsData, String> {
    // Query HealthKit for current metrics
    // Return heart rate, HRV, etc.
}

#[tauri::command]
pub async fn get_sleep_summary(
    date: String,
    state: tauri::State<'_, AppState>
) -> Result<SleepData, String> {
    // Query last night's sleep
}
```

**2.3 Background Sync**

```rust
// Periodic sync task
async fn health_sync_task(state: AppState) {
    loop {
        if let Some(hk) = state.health_source.get("healthkit") {
            let hr = hk.get_heart_rate().await;
            let hrv = hk.get_hrv().await;

            // Store in SQLite
            state.db.insert_health_metric(
                "heart_rate", hr, "bpm", "healthkit"
            )?;
        }

        sleep(Duration::from_secs(300)).await; // 5 minutes
    }
}
```

### Phase 3: Web API Integrations (2-3 weeks)

**3.1 Fitbit OAuth Flow**

```rust
// src-tauri/src/services/fitbit_api.rs
pub struct FitbitClient {
    access_token: String,
    refresh_token: String,
    base_url: String,
}

impl FitbitClient {
    pub async fn get_heart_rate(&self, date: &str) -> Result<HeartRateData> {
        let url = format!(
            "{}/1/user/-/activities/heart/date/{}/1d.json",
            self.base_url, date
        );

        let response = self.client
            .get(&url)
            .bearer_auth(&self.access_token)
            .send()
            .await?;

        response.json().await
    }

    pub async fn get_sleep(&self, date: &str) -> Result<SleepData> {
        let url = format!(
            "{}/1.2/user/-/sleep/date/{}.json",
            self.base_url, date
        );
        // ...
    }
}
```

**3.2 Oura Ring Integration**

```rust
// src-tauri/src/services/oura_api.rs
pub struct OuraClient {
    personal_access_token: String,
}

impl OuraClient {
    pub async fn get_readiness(&self, date: &str) -> Result<ReadinessData> {
        let url = format!(
            "https://api.ouraring.com/v2/usercollection/daily_readiness?start_date={}&end_date={}",
            date, date
        );
        // ...
    }
}
```

**3.3 Unified Health Provider Interface**

```rust
// src-tauri/src/services/health_provider.rs
pub trait HealthProvider: Send + Sync {
    async fn get_heart_rate(&self) -> Result<Option<f64>>;
    async fn get_hrv(&self) -> Result<Option<f64>>;
    async fn get_sleep_data(&self, date: &str) -> Result<SleepData>;
    async fn get_readiness(&self) -> Result<Option<i32>>;
}

// Implement for each platform
impl HealthProvider for HealthKitManager { ... }
impl HealthProvider for FitbitClient { ... }
impl HealthProvider for OuraClient { ... }
```

### Phase 4: AI Context Integration (2 weeks)

**4.1 Health Context for Claude/OpenAI**

```rust
// src-tauri/src/services/ai_context.rs
pub fn build_health_context(db: &Repository, session_id: i64) -> String {
    let summary = db.get_daily_health_summary(today())?;
    let recording_vitals = db.get_recording_vitals(session_id)?;

    format!(r#"
    Health Context for this conversation:
    - Current heart rate: {} BPM (baseline: {})
    - HRV: {}ms (average: {}ms)
    - Last night's sleep: {}% efficiency, {} hours
    - Readiness score: {}/100
    - Stress indicator: {}

    Consider this physiological context when responding to the user's journal entry.
    "#,
    recording_vitals.heart_rate,
    summary.resting_heart_rate,
    recording_vitals.hrv,
    summary.avg_hrv,
    summary.sleep_efficiency,
    summary.sleep_hours,
    summary.readiness_score,
    if recording_vitals.hrv < summary.avg_hrv * 0.8 { "elevated" } else { "normal" }
    )
}
```

**4.2 Insight Generation**

```rust
#[tauri::command]
pub async fn generate_health_insights(
    session_id: i64,
    state: tauri::State<'_, AppState>
) -> Result<Vec<Insight>, String> {
    let health_data = state.db.get_health_trends(30)?; // 30 days
    let journal_data = state.db.get_journal_sentiments(30)?;

    let insights = correlate_health_journal(health_data, journal_data);

    // Example insights:
    // "Your journaling tone is 40% more positive on days after 7+ hours of sleep"
    // "High HRV days correlate with more future-focused journal entries"
    // "You recorded 3x more when your readiness score was above 70"

    Ok(insights)
}
```

### Phase 5: Visualization Dashboard (2-3 weeks)

**5.1 Health Dashboard Component**

```svelte
<!-- src/components/HealthDashboard.svelte -->
<script>
  import { invoke } from '@tauri-apps/api/core';

  let healthSummary = $state(null);
  let sleepTrend = $state([]);
  let hrvTrend = $state([]);

  $effect(() => {
    loadHealthData();
  });

  async function loadHealthData() {
    healthSummary = await invoke('get_daily_health_summary');
    sleepTrend = await invoke('get_sleep_trend', { days: 7 });
    hrvTrend = await invoke('get_hrv_trend', { days: 30 });
  }
</script>

<div class="health-dashboard">
  <section class="today-summary">
    <ReadinessGauge score={healthSummary?.readiness_score} />
    <SleepQualityCard data={healthSummary?.sleep} />
    <HeartMetricsCard
      rhr={healthSummary?.resting_heart_rate}
      hrv={healthSummary?.avg_hrv}
    />
  </section>

  <section class="trends">
    <HRVTrendChart data={hrvTrend} />
    <SleepTrendChart data={sleepTrend} />
  </section>
</div>
```

**5.2 Recording Context Display**

```svelte
<!-- Show health context during/after recording -->
<div class="recording-health-context">
  {#if isRecording}
    <RealTimeHeartRate />
  {:else}
    <RecordingVitalsSummary {sessionId} />
  {/if}
</div>
```

### Phase 6: Polish & Testing (2 weeks)

- Unit tests for health providers
- Integration tests for data sync
- UI/UX testing
- Privacy compliance audit
- Performance optimization
- Error handling and offline support

### Total Estimated Timeline: 13-17 weeks

---

## Use Cases and AI Integration

### 1. Real-Time Recording Context

**Scenario:** User records a brain dump during stressful moment

```
User starts recording at 3:45 PM
System detects:
- Heart rate: 92 BPM (baseline: 68 BPM) ↑35%
- HRV: 28ms (average: 42ms) ↓33%

AI Response includes:
"I notice you're recording during what appears to be a high-stress
moment based on your elevated heart rate. Would you like to start
with some breathing exercises, or would you prefer to dive into
what's on your mind?"
```

### 2. Sleep-Mood Correlation Insights

**Scenario:** Identifying patterns over time

```
Pattern detected over 30 days:
- Poor sleep nights (efficiency < 70%): 8 occurrences
- Following day journal entries: 62% negative sentiment
- Good sleep nights (efficiency > 85%): 12 occurrences
- Following day journal entries: 78% positive sentiment

AI Insight:
"Your sleep quality strongly correlates with your journaling mood.
On days after restful sleep, your entries show more gratitude and
future-oriented thinking. Consider prioritizing sleep hygiene
when you notice negative thought patterns."
```

### 3. Recovery-Based Prompt Selection

**Scenario:** Adaptive journaling prompts

```
User opens app in morning
Oura Readiness Score: 45/100
Recovery: Low
Previous night: 4.5 hours sleep, high stress

System selects gentle prompt:
"Good morning. Your body is still recovering from a tough night.
What's ONE kind thing you can do for yourself today?"

vs. High recovery day:
"You're feeling recharged today! What exciting goal do you want
to make progress on?"
```

### 4. Stress Pattern Recognition

**Scenario:** Identifying triggers

```
Health + Journal Analysis:
- Every Tuesday 2-4 PM: HRV drops 30%, HR spikes
- Journal entries mention "team meetings" and "presentations"
- Pattern consistent for 6 weeks

AI Observation:
"I've noticed your Tuesday afternoon meetings coincide with
significant stress markers. Your heart rate elevates and HRV
drops during this time. Would you like to explore some
pre-meeting grounding techniques?"
```

### 5. Holistic Wellness Dashboard

**Scenario:** Monthly wellness report

```
Dashboard View:

┌─────────────────────────────────────┐
│     November 2025 Wellness Summary  │
├─────────────────────────────────────┤
│ 📊 Journal Entries: 24              │
│ 🎙️ Recording Time: 8.5 hours       │
│ 😴 Avg Sleep: 7.2 hours            │
│ ❤️ Avg HRV: 45ms (↑5% from Oct)    │
│ 🔋 Avg Readiness: 72/100           │
├─────────────────────────────────────┤
│ Key Insights:                       │
│ • Best journaling: after 8+ hrs    │
│   sleep (sentiment +40%)            │
│ • Stress patterns: Mon, Wed PM      │
│ • HRV improving with meditation     │
│   practice (6 sessions tracked)     │
└─────────────────────────────────────┘
```

### 6. Crisis Support Enhancement

**Scenario:** Early warning system

```
System detects (non-clinical, supportive):
- HRV below personal threshold for 3+ days
- Sleep efficiency declining trend
- Journal sentiment increasingly negative
- Decreased recording frequency

Gentle prompt:
"I've noticed you might be going through a difficult time.
Your recent patterns suggest increased stress. Remember, this
app is for reflection, not clinical support. Would you like me
to suggest some self-care resources, or would you prefer to
connect with a mental health professional?"

[Show Resources] [Maybe Later] [I'm Okay]
```

### Important Limitations

1. **NOT Medical Advice:** All insights are observational, not diagnostic
2. **User Controls:** Always optional, user can disable health integration
3. **Privacy First:** Health data never leaves device without explicit consent
4. **Non-Judgmental:** Frame insights positively, not as failures
5. **Professional Support:** Always encourage professional help for serious concerns

---

## Recommendations

### Priority Integration Order

1. **Apple HealthKit** (Highest Priority)
   - Native to macOS (target platform)
   - Richest data set
   - Most private (on-device)
   - Best for real-time features
   - Implementation: 3-4 weeks with swift-bridge

2. **Oura Ring API** (High Priority)
   - Best HRV accuracy
   - Readiness score is invaluable
   - Simple REST API
   - Growing user base
   - Implementation: 1-2 weeks

3. **Fitbit Web API** (Medium Priority)
   - Large user base
   - Good sleep data
   - Well-documented
   - Cross-platform
   - Implementation: 1-2 weeks

4. **WHOOP** (Low Priority, Niche)
   - Strain/recovery metrics
   - Athletic user focus
   - Membership required
   - Implementation: 1 week

5. **Garmin** (Lower Priority)
   - Requires partnership approval
   - Good data but complex access
   - Implementation: 2-3 weeks (with approval)

### Technical Architecture Recommendations

1. **Use Trait-Based Abstraction**
   - Create `HealthProvider` trait
   - Implement for each platform
   - Easy to add new sources
   - Consistent data model

2. **Local-First Storage**
   - SQLite for health metrics
   - Sync periodically (5-15 minutes)
   - Cache for offline access
   - Export functionality

3. **Privacy by Design**
   - Granular permissions
   - Clear disclosure
   - Local processing preferred
   - Anonymization options

4. **Progressive Enhancement**
   - App works without health data
   - Each integration is optional
   - Graceful degradation
   - Feature flags for each provider

### MVP Feature Set

**Version 1.0 (8-10 weeks):**
- Apple HealthKit integration (HR, HRV, Sleep)
- Basic health context in AI prompts
- Simple visualization (gauges, trends)
- Permission management UI
- Data storage and sync

**Version 1.1 (4-6 weeks):**
- Fitbit integration
- Advanced correlations
- Pattern detection
- Wellness dashboard
- Export reports

**Version 2.0 (Future):**
- Multiple provider support
- Predictive insights
- Adaptive prompts based on state
- Long-term trend analysis
- Research-grade features

### Critical Success Factors

1. **User Trust:** Be transparent about data use
2. **Value Demonstration:** Show clear benefit of health context
3. **Performance:** Don't impact app responsiveness
4. **Reliability:** Handle API failures gracefully
5. **Privacy Compliance:** Stay ahead of regulations
6. **User Control:** Always respect user preferences

---

## Conclusion

Wearable health integration represents a significant opportunity for BrainDump to provide contextually-aware journaling experiences. With strong scientific evidence supporting HRV-mood correlations (83% classification accuracy), the technical feasibility via swift-bridge for HealthKit integration, and multiple REST APIs for cross-platform support, this feature set can transform BrainDump from a simple voice journaling tool into a holistic wellness companion.

**Key Takeaways:**

1. **Start with HealthKit:** Native macOS integration provides the richest, most private data source
2. **Privacy is Paramount:** Health data requires careful handling with clear consent
3. **Scientific Backing:** HRV and sleep correlations with mental health are well-researched
4. **User Control:** Always make health features optional and transparent
5. **Incremental Approach:** Build foundation first, then add advanced features

The estimated implementation timeline of 13-17 weeks for full feature set is achievable, with a meaningful MVP deliverable in 8-10 weeks. This positions BrainDump uniquely in the voice journaling market as a biometric-aware mental wellness tool.

---

**Report Prepared By:** Agent Iota2
**Date:** 2025-11-16
**Research Sources:** Apple Developer Documentation, Fitbit API Docs, Oura API V2, Garmin Developer Portal, WHOOP Developer Platform, NIH PubMed, Frontiers in Psychiatry, Legal Analysis of HIPAA/GDPR
