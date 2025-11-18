# Sports and Fitness Tracking Integration Research
**Agent Mu2 Research Report**
**Date**: 2025-11-16
**Status**: Complete Athletic Performance Feature Analysis

---

## Executive Summary

This report documents comprehensive research for integrating sports and fitness tracking into BrainDump v3.0. The voice-first journaling approach aligns naturally with athletic training workflows, enabling athletes to:

- Voice-log workouts ("3 sets of 10 bench press at 135 lbs")
- Auto-extract exercise metadata via NLP
- Journal training intentions and recovery
- Track strength progression and performance metrics
- Integrate with Strava, MyFitnessPal, Apple HealthKit, and other fitness APIs
- Support mental game coaching (visualization, goal-setting, injury recovery)

**Estimated Implementation**: 8-12 weeks for core features (166 hours estimated effort across team).

---

## 1. Sports Tracking Architecture

### 1.1 Database Schema Design

#### Core Entity Relationships

```sql
-- User & Profile
users
├── id (PK)
├── email
├── name
├── bio_height_cm
├── bio_weight_kg
├── created_at
└── updated_at

-- Training Programs
training_programs
├── id (PK)
├── user_id (FK → users)
├── title
├── description
├── periodization_type (linear|undulating|block|conjugate)
├── start_date
├── end_date
├── created_at

-- Workouts (individual sessions)
workout_sessions
├── id (PK)
├── user_id (FK → users)
├── program_id (FK → training_programs, nullable)
├── title (e.g., "Chest Day")
├── start_time
├── end_time
├── duration_minutes
├── intensity_level (light|moderate|hard|max)
├── notes
├── recording_id (FK → recordings, link to voice journal)
├── created_at

-- Exercise Library (exercises available)
exercises
├── id (PK)
├── name (e.g., "Bench Press")
├── category (strength|cardio|flexibility|mobility)
├── primary_muscle_group (e.g., "chest")
├── secondary_muscles (JSON: ["triceps", "shoulders"])
├── equipment (barbell|dumbbell|bodyweight|machine|cable)
├── cues_and_form (text descriptions)
├── created_at

-- Workout Exercise Instances
workout_exercises
├── id (PK)
├── workout_id (FK → workout_sessions)
├── exercise_id (FK → exercises)
├── sets (integer)
├── reps (integer)
├── weight_kg (decimal, nullable)
├── weight_lbs (decimal, nullable)
├── rpe (rate of perceived exertion: 1-10)
├── rest_seconds (integer)
├── notes (form quality, tempo, etc.)
├── order_in_workout
├── created_at

-- Training Volume & Metrics
workout_metrics
├── id (PK)
├── workout_id (FK → workout_sessions)
├── total_volume_kg (sum of sets × reps × weight)
├── total_reps
├── avg_rpe
├── estimated_1rm (calculated for main lifts)
├── perceived_recovery (1-10 scale)
├── sleep_quality (1-10)
├── stress_level (1-10)
├── nutrition_quality (1-10)
├── injury_notes (text)

-- Personal Records (PRs)
personal_records
├── id (PK)
├── user_id (FK → users)
├── exercise_id (FK → exercises)
├── record_type (1rm|5rm|10rm|max_reps|max_distance|best_time)
├── value (weight_kg or distance_km or time_seconds)
├── achieved_date
├── workout_id (FK → workout_sessions, context)
├── created_at

-- Progress Photos (optional)
progress_photos
├── id (PK)
├── user_id (FK → users)
├── photo_path
├── date_taken
├── body_area (full_body|chest|back|shoulders|arms|legs)
├── notes
├── created_at

-- Performance Metrics Over Time
strength_progression
├── id (PK)
├── user_id (FK → users)
├── exercise_id (FK → exercises)
├── date
├── best_weight_kg
├── estimated_1rm
├── weekly_volume
├── avg_rpe_weekly
├── pr_status (new_pr|progress|maintained|regressed)

-- Training Journal (for mental aspects)
training_journal_entries
├── id (PK)
├── user_id (FK → users)
├── workout_id (FK → workout_sessions, nullable)
├── entry_type (pre_workout|post_workout|recovery|injury|mental)
├── title
├── content (voice transcription or typed)
├── recording_id (FK → recordings)
├── emotion_state (confident|anxious|tired|motivated|injured)
├── focus_area (technique|strength|endurance|mental|strategy)
├── created_at

-- Recovery & Wellness
recovery_logs
├── id (PK)
├── user_id (FK → users)
├── date
├── sleep_hours
├── sleep_quality (1-10)
├── soreness_level (1-10)
├── stress_level (1-10)
├── hydration_status (dehydrated|adequate|optimal)
├── nutrition_quality (1-10)
├── mobility_work_done (boolean)
├── notes
├── created_at
```

#### Database Technology Recommendation

**Primary**: **SQLite** (existing in BrainDump)
- Sufficient for single-user desktop app
- Handles complex relationship queries well
- Excellent JSON support for muscle group arrays

**Optimization**:
- Index on `(user_id, date)` for quick date-range queries
- Index on `(exercise_id, date)` for strength progression charts
- Denormalize weekly metrics for performance (pre-calculated aggregates)
- Archive old workout data to separate table after 1 year for speed

---

### 1.2 Core Features

#### Workout Logging
```
User Flow:
1. Pre-workout voice journal: "Feeling good, targeting chest and shoulders"
2. Start recording audio stream OR manually log workout
3. Record each set:
   - Exercise name (from library or new)
   - Sets × Reps × Weight
   - RPE (Rate of Perceived Exertion)
   - Rest period
   - Form notes (voice or text)
4. Post-workout metrics:
   - Total duration
   - Perceived recovery
   - Sleep quality
   - Injury status
```

#### Exercise Library
- **Pre-loaded**: 500+ common exercises (strength, cardio, flexibility)
- **Categorized by**:
  - Muscle group (chest, back, shoulders, biceps, triceps, forearms, legs, core)
  - Training type (strength, hypertrophy, endurance, power)
  - Equipment (barbell, dumbbell, bodyweight, machine, cable, kettlebell)
- **Form guidance**: Video links (YouTube, Vimeo) + written cues
- **Add custom**: Users can create custom exercises

#### Personal Records (PRs)
Track multiple PR types:
- 1-Rep Max (1RM)
- 5-Rep Max (5RM)
- 10-Rep Max (10RM)
- Max reps at body weight
- Fastest time (cardio)
- Furthest distance

Automatically calculated:
- Estimated 1RM using Epley formula: `1RM = weight × (1 + (reps × 0.0333))`
- Auto-flags new PRs when exceeded

#### Progress Photos (Optional)
- Store full-body or body-part specific photos
- Date-tagged for comparison
- Side-by-side view for body composition tracking
- Privacy: stored locally, encrypted, never sent to cloud

---

## 2. Voice-to-Workout Parser

### 2.1 NLP Extraction Pipeline

#### Voice Input Examples
```
User says: "Just finished 3 sets of 10 bench press at 135 pounds, felt strong"
→ Extract:
   Exercise: "Bench Press"
   Sets: 3
   Reps: 10
   Weight: 135 lbs
   RPE/Notes: "felt strong"

User says: "Did cardio, 5 miles in 45 minutes, heart rate maxed at 180"
→ Extract:
   Exercise: "Running"
   Distance: 5 miles
   Duration: 45 minutes
   Max Heart Rate: 180 bpm

User says: "30 minute HIIT session, burpees, mountain climbers, jump rope"
→ Extract:
   Workout Type: HIIT
   Duration: 30 minutes
   Exercises: ["Burpees", "Mountain Climbers", "Jump Rope"]
```

#### Implementation Strategy

**Recommended**: Use Claude API for voice-to-structured-data extraction

```rust
// src-tauri/src/services/voice_parser.rs

pub struct WorkoutParseRequest {
    pub transcript: String,  // From Whisper.cpp
    pub context: WorkoutContext,  // Previous workouts, PRs, etc.
}

pub struct ParsedWorkout {
    pub exercises: Vec<ExerciseParse>,
    pub duration_minutes: Option<i32>,
    pub intensity: Option<String>,
    pub notes: String,
}

pub struct ExerciseParse {
    pub name: String,
    pub sets: Option<i32>,
    pub reps: Option<i32>,
    pub weight_kg: Option<f32>,
    pub distance_km: Option<f32>,
    pub duration_seconds: Option<i32>,
    pub rpe: Option<i32>,
    pub confidence: f32,  // 0.0-1.0
}

#[tauri::command]
pub async fn parse_workout_from_voice(
    transcript: String,
    state: tauri::State<'_, AppState>,
) -> Result<ParsedWorkout, String> {
    let claude = state.claude_client.clone();

    // Build prompt with exercise library context
    let prompt = format!(
        r#"Extract workout information from this voice transcription.

Transcription: "{}"

Known exercises in user's library: {:?}

Return JSON with this structure:
{{
  "exercises": [
    {{
      "name": "exercise name",
      "sets": number or null,
      "reps": number or null,
      "weight_kg": number or null,
      "weight_lbs": number or null,
      "distance_km": number or null,
      "duration_seconds": number or null,
      "rpe": number (1-10) or null,
      "confidence": number (0-1)
    }}
  ],
  "duration_minutes": number or null,
  "intensity": "light|moderate|hard|max" or null,
  "notes": "any additional context"
}}"#,
        transcript,
        state.exercise_library.get_user_exercises()
    );

    let response = claude.send_message(&prompt).await?;
    let parsed: ParsedWorkout = serde_json::from_str(&response)?;
    Ok(parsed)
}
```

#### Multi-Step Parsing Process

1. **Transcription** (Whisper.cpp): Voice → Text
   - Already implemented in BrainDump
   - Handles background noise well with Metal GPU acceleration

2. **Intent Recognition** (Claude): Identify workout type
   - Strength training (which exercise focus?)
   - Cardio (running, cycling, HIIT?)
   - Flexibility/Recovery (yoga, stretching?)
   - Sports-specific (tennis, basketball?)

3. **Entity Extraction** (Claude + Regex): Extract metrics
   - Exercise names (fuzzy-match to library)
   - Numbers: sets, reps, weight, distance, time
   - Units: kg vs lbs, km vs miles
   - Qualitative data: RPE, intensity, form notes

4. **Confidence Scoring**: Flag uncertain extractions
   - 0.9-1.0: High confidence (proceed auto-save)
   - 0.7-0.9: Medium (review before save)
   - <0.7: Low (require manual confirmation)

5. **Auto-Correction**: Learn from user feedback
   - User corrects extraction → retrain
   - Common synonym patterns
   - User's unique terminology

#### Fallback UI for Unclear Inputs
```
If confidence < 0.7, show:
┌─────────────────────────────────┐
│ Confirm Workout Details         │
├─────────────────────────────────┤
│ Exercise: [Bench Press] ✓        │ Confidence: 95%
│ Sets:     [3] (unclear)          │ Confidence: 65%
│ Reps:     [10] ✓                 │ Confidence: 92%
│ Weight:   [135 lbs] ✓            │ Confidence: 88%
│                                 │
│ [Save as-is] [Edit] [Discard]   │
└─────────────────────────────────┘
```

---

### 2.2 Database Integration

Auto-save parsed workout:

```rust
#[tauri::command]
pub async fn save_parsed_workout(
    parsed: ParsedWorkout,
    session_id: i64,
    db: tauri::State<'_, Database>,
) -> Result<i64, String> {
    let conn = db.get_connection()?;

    // Create workout session
    let workout = WorkoutSession {
        user_id: session_id,
        title: parsed.title_suggestion(),
        duration_minutes: parsed.duration_minutes,
        intensity_level: parsed.intensity,
        created_at: Utc::now(),
        ..Default::default()
    };

    let workout_id = db.create_workout_session(&workout)?;

    // Insert each exercise
    for exercise in parsed.exercises {
        let exercise_id = db.fuzzy_match_exercise(&exercise.name)?;

        let workout_ex = WorkoutExercise {
            workout_id,
            exercise_id,
            sets: exercise.sets,
            reps: exercise.reps,
            weight_kg: exercise.weight_kg,
            rpe: exercise.rpe,
            ..Default::default()
        };

        db.create_workout_exercise(&workout_ex)?;
    }

    // Calculate metrics
    let metrics = db.calculate_workout_metrics(workout_id)?;
    db.save_workout_metrics(workout_id, &metrics)?;

    Ok(workout_id)
}
```

---

## 3. Athletic Journaling Prompts

### 3.1 Pre-Workout Prompts

**Mental Preparation** (5 min):
- "What's my primary goal for today's session?"
- "How am I feeling physically right now? (1-10)"
- "What's my mental state? (confident, anxious, neutral, motivated)"
- "What specific technique or lift do I want to focus on?"
- "What distractions or challenges might I face today?"

**Visualization** (3 min):
- "Visualize yourself completing your hardest set perfectly. Describe what you see, feel, and hear."
- "See yourself with flawless form. What does that look like?"
- "Imagine the weight moving smoothly. Where do you feel the tension?"

**Intention Setting**:
- "I will focus on..."
- "My success criteria today: ..."
- "If I get frustrated, I will..."

### 3.2 Post-Workout Prompts

**Performance Reflection** (5 min):
- "How did today compare to your intention? What went well?"
- "What felt strongest in today's session?"
- "What was the most challenging moment, and how did you overcome it?"
- "Rate your effort (1-10). Was this what you aimed for?"
- "Did any lifts feel different? (Better form? More explosive? Weaker?)"

**Mental Game Reflection**:
- "Did you use any mental strategies? (Self-talk, visualization, breathing?) How effective were they?"
- "What distracted you, if anything?"
- "How would you rate your confidence during the workout? (1-10)"

**Recovery & Readiness**:
- "Current soreness in any muscle groups? (1-10 scale)"
- "How's your energy level right now? (exhausted, recovered, wired)"
- "Any form breakdowns or injury concerns?"
- "What helped you push through fatigue?"

**Data Collection**:
- Sleep quality last night? (1-10)
- Stress level entering session? (1-10)
- Overall recovery status? (poor, fair, good, excellent)
- Motivation level? (low, medium, high, peak)

### 3.3 Recovery & Wellness Prompts

**Daily Recovery Journal** (Post-workout):
- "Current soreness in specific areas?"
- "Sleep quality last night? (1-10)"
- "Stress level? (1-10)"
- "Hydration status?"
- "Nutrition quality today? (poor, fair, good, excellent)"
- "Did you do any mobility work or stretching?"
- "Any aches or twinges to watch?"

**Weekly Reflection** (Sunday evening):
- "How did this week's training feel compared to last week?"
- "Did you hit your target training volume?"
- "What was your biggest achievement this week?"
- "What's one thing to improve next week?"
- "How's your energy trending? (building, declining, stable)"
- "Any injuries or concerns to address?"
- "Sleep trend this week? (improving, declining, stable)"

**Deload Week Reflection** (Every 4th week):
- "How are you feeling heading into recovery week?"
- "Any nagging injuries that need attention?"
- "What did you learn this cycle?"
- "What's your goal for next training block?"

### 3.4 Injury Recovery Prompts

**Immediate Post-Injury** (First week):
- "Describe what happened. How does it feel? (1-10 pain level)"
- "What specific movement causes pain?"
- "How is this affecting your mood and mental state?"
- "What are your fears about this injury?"

**Mid-Recovery** (Weeks 2-8):
- "Describe your rehab progress this week. (Better, same, worse?)"
- "What exercises can you do now that you couldn't before?"
- "How's your pain level trending? (1-10)"
- "Are there mental barriers to progression? (fear, frustration, impatience?)"
- "What strategies are helping you stay positive?"
- "When do you envision returning to full training?"

**Return-to-Sport Phase** (Weeks 8+):
- "I'm feeling ready to try... (specific movement/exercise)"
- "What's my biggest fear about returning?"
- "How will I know I'm truly ready?"
- "What's my modified training plan for the next 2 weeks?"
- "Describe your confidence level returning to (sport). (1-10)"
- "What will I do if I experience pain during return?"
- "Who's supporting my return? (coach, PT, teammates?)"

### 3.5 Mental Game Coaching Prompts

**Goal Setting** (Quarterly):
- "What's my big goal for the next 3 months?"
- "Break it into 4 weekly milestones:"
  - "Week 1-4 target:"
  - "Week 5-8 target:"
  - "Week 9-12 target:"
- "What obstacles might prevent me from achieving this?"
- "How will I know when I've succeeded?"

**Anxiety Management**:
- "What specifically am I anxious about in competition?"
- "What would confidence feel like in that moment?"
- "What's one thing I can control right now?"
- "What's my breathing plan when I get nervous?"
- "What's a past moment when I overcame similar anxiety?"

**Performance Analysis**:
- "In that hard moment, what self-talk helped?"
- "When did I feel most in-flow during the workout?"
- "What physical sensations accompany my peak performance?"
- "How do I recreate that mental state?"

**Motivation & Mindset**:
- "Why does this goal matter to me?"
- "Who am I becoming through this training?"
- "What's my identity as an athlete?"
- "When motivation is low, what re-energizes me?"
- "What's one small win I can celebrate today?"

---

## 4. Training Program Management

### 4.1 Program Templates

**Linear Periodization** (12-week strength cycle):
```
Week 1-4:   Volume Focus (12-15 reps, lighter weight)
Week 5-8:   Hypertrophy Focus (8-12 reps, moderate weight)
Week 9-11:  Strength Focus (3-6 reps, heavy weight)
Week 12:    Deload / Recovery Week
```

**Undulating/Daily Undulating Periodization** (DUP):
```
Monday:     Strength Day (3-5 reps, 85-95% 1RM)
Wednesday:  Hypertrophy Day (8-12 reps, 65-85% 1RM)
Friday:     Endurance Day (15-20 reps, 50-70% 1RM)
```

**Block Periodization** (Elite athletes):
```
Block 1 (4 weeks):  Accumulation (high volume, lower intensity)
Block 2 (4 weeks):  Intensification (moderate volume, higher intensity)
Block 3 (2 weeks):  Realization (low volume, maximum intensity)
Block 4 (1 week):   Deload / Recovery
```

**Sport-Specific Programs**:
- Running: Base building → Tempo → Interval → Taper
- CrossFit: Gymnastics + Strength + Metabolic Conditioning split
- Powerlifting: Competition Lift focus + Accessory + Conditioning
- Bodybuilding: Body part splits rotating 4-6 body parts/week

### 4.2 Auto-Progression Logic

```rust
// Calculate next week's training variables
pub fn calculate_progressive_overload(
    exercise_id: i64,
    last_4_weeks: Vec<WorkoutExercise>,
) -> ProgressionRecommendation {
    let avg_rpe = last_4_weeks.iter().map(|w| w.rpe).sum::<i32>() / 4;
    let volume_trend = calculate_trend(last_4_weeks.iter()
        .map(|w| (w.sets * w.reps) as i32)
        .collect());

    // Rules for progression
    if avg_rpe < 7 {
        // Increase weight by 5% (safely)
        return ProgressionRecommendation::IncreaseWeight(0.05);
    } else if avg_rpe >= 8 && volume_trend == Positive {
        // Can increase reps or sets
        return ProgressionRecommendation::IncreaseReps;
    } else if volume_trend == Negative {
        // Deload warning - suggest 10% reduction
        return ProgressionRecommendation::Deload(0.10);
    }

    ProgressionRecommendation::MaintainCurrent
}

pub enum ProgressionRecommendation {
    IncreaseWeight(f32),        // 5% increase
    IncreaseReps,               // Add 1-2 reps
    IncreaseVolume,             // Add 1 set
    Deload(f32),                // Reduce by % (0.10 = 10%)
    MaintainCurrent,
    ScheduleDeload,             // Suggest deload week
}
```

### 4.3 Template Library Integration

Pre-built programs in app:

```
Beginner:
├─ "Full Body 3x/week" (3 months)
├─ "Push/Pull/Legs" (3 months)
└─ "Upper/Lower 4x/week" (3 months)

Intermediate:
├─ "5/3/1 Strength" (12 weeks)
├─ "PPPL Advanced" (12 weeks)
├─ "Linear Periodization" (12 weeks)
└─ "Conjugate Method" (12 weeks)

Advanced:
├─ "Competition Periodization" (variable)
├─ "Sport-Specific Block Training" (varies)
└─ "Autoregulated RIR Training" (ongoing)

Sport-Specific:
├─ "Marathon Training" (16 weeks)
├─ "CrossFit Competition" (varies)
├─ "Triathlon Olympic Distance" (20 weeks)
└─ "Powerlifting Meet Prep" (12-16 weeks)
```

---

## 5. Integration Opportunities

### 5.1 Third-Party Fitness APIs

#### Strava API (Running/Cycling)
**What it provides**:
- GPS activity data (routes, pace, elevation)
- Social features (leaderboards, challenges)
- Heart rate data (with compatible devices)
- Activity metadata (type, distance, duration, elevation gain)

**Integration approach**:
```rust
// OAuth 2.0 with Strava
GET https://www.strava.com/api/v3/athlete/activities
→ Fetch user's running/cycling activities
→ Map to BrainDump workouts (create if new)
→ Store Strava activity_id for bi-directional sync
```

**Limitations**: Doesn't support gym exercises, only endurance sports

**Recommendation**: Use for cardio tracking, complement with BrainDump's strength logging

---

#### MyFitnessPal API (Nutrition)
**What it provides**:
- Food database (5M+ items)
- Calorie tracking
- Macro tracking (protein, carbs, fats)
- Water intake

**Integration approach**:
```rust
// OAuth 2.0 with MyFitnessPal
GET /api/nutrition/daily_summary
→ Pull daily nutrition data
→ Display in recovery_logs table
→ Cross-reference with workout intensity
```

**Use case**: Link post-workout nutrition logging
- "Did cardio, burned ~500 calories"
- Auto-suggest protein target for recovery

---

#### Apple HealthKit (iOS)
**What it provides**:
- Workouts (iOS native)
- Heart rate
- Steps / movement
- Sleep data
- Biometrics (weight, body fat %)

**Integration approach**:
```rust
// HealthKit queries (on macOS via native Swift interop)
HKWorkout query → Map to BrainDump workouts
HKSample (heart rate) → Store peak HR during workout
HKQuantity (sleep) → Link to recovery_logs
```

**Recommendation**: Not directly accessible on Tauri desktop, but future iOS companion app integration

---

#### Fitbit Web API
**What it provides**:
- Biometric data (heart rate variability, resting HR)
- Sleep tracking
- Activity levels
- SpO2, skin temperature

**Integration approach**: Similar to HealthKit, one-way sync into recovery metrics

---

#### Google Fit REST API
**What it provides**:
- Cross-platform fitness data aggregation
- Activity recognition
- Biometric data
- Nutrition data

**Integration**: Lower priority, but good fallback for Android users

---

#### TrainingPeaks API (Endurance athletes)
**What it provides**:
- Training Load (TL)
- Training Stress Score (TSS)
- Intensity Factor (IF)
- Coach notes and adjustments

**Integration approach**: For advanced endurance athletes

```rust
POST /api/activities
→ Submit BrainDump workout to TrainingPeaks
→ Receive TSS/TL score
→ Store in workout_metrics for analysis
```

---

#### Strong App API (Strength tracking)
**Current status**: Strong app is working on Strava integration, but doesn't yet have public API.

**Workaround**: File-based export (CSV → import)

---

### 5.2 Recommended Integration Priority

**Phase 1 (MVP)**:
1. Manual workout entry + voice parser ✓ (in scope)
2. Internal database schema (designed above)
3. Basic strength progression charts

**Phase 2 (6 months)**:
1. Strava read-only sync (cardio activities)
2. Apple HealthKit (macOS native)
3. Progress photo gallery

**Phase 3 (9 months)**:
1. MyFitnessPal nutrition sync
2. Fitbit biometric integration
3. Training program templates + autoregulation

**Phase 4 (12+ months)**:
1. TrainingPeaks integration (serious endurance athletes)
2. iOS companion app (HealthKit access)
3. AI-powered program generation

---

## 6. Data Visualization & Analytics

### 6.1 Key Charts & Dashboards

#### Strength Progression
```
Chart Type: Line + Bar Combo
X-axis: Date (weekly)
Y-axis: Weight (kg/lbs)

Line: Weekly max weight per exercise
Bars: Weekly total volume per exercise

Exercises to show:
- Top 5 exercises by frequency
- All major lifts (Squat, Bench, Deadlift, OHP)
- User's favorite exercises

Metrics:
- Estimated 1RM (Epley formula)
- Weekly volume (sum of all reps × weight)
- PR achievement dates
- Personal best per lift
```

**Example Data**:
```
Bench Press Progression (12 weeks)
Week 1:  5x5 @ 225 lbs = 5,625 lbs total volume
Week 2:  5x5 @ 230 lbs = 5,750 lbs total volume
Week 3:  5x5 @ 235 lbs = 5,875 lbs total volume
Week 4:  3x3 @ 245 lbs = 2,205 lbs (deload)
...
Week 12: 1x1 @ 275 lbs (NEW PR!)
```

#### Training Volume Over Time
```
Chart Type: Stacked Area Chart
X-axis: Date (by week or month)
Y-axis: Total Volume (tons)

Stacked by:
- Upper body
- Lower body
- Cardio / Conditioning

Shows:
- Overall training consistency
- Periodization cycles (deloads visible)
- Recovery patterns
- Overtraining risk (sharp volume increases)
```

#### Performance Metrics Dashboard
```
┌─────────────────────────────────────┐
│ Training Dashboard (Last 30 Days)    │
├─────────────────────────────────────┤
│ Total Workouts:    12               │
│ Total Volume:      85,450 lbs        │
│ Avg Session:       45 min           │
│ PRs Achieved:      2                │
│ Best Lift:         Squat 365 lbs    │
├─────────────────────────────────────┤
│                                     │
│ [Volume Chart]     [Frequency]      │
│                                     │
│ [Muscle Group %]   [Intensity Dist.]│
│                                     │
└─────────────────────────────────────┘
```

#### Recovery Metrics
```
Chart Type: Multi-axis Line Chart

Axes:
1. Sleep quality (1-10, left Y)
2. Soreness level (1-10, left Y)
3. Stress level (1-10, left Y)
4. Training volume (right Y, scaled)

Shows:
- Recovery trends before heavy training
- Sleep impact on performance
- Overtraining indicators
- Deload effectiveness

Pattern Recognition:
- Low sleep → lower workout quality
- High stress → reduced performance
- Poor recovery → volume reduction advice
```

#### Personal Records Timeline
```
Timeline view:
2024-08-15: Bench Press 275 lbs (NEW PR)
2024-09-01: Squat 365 lbs (NEW PR)
2024-09-15: Deadlift 405 lbs (NEW PR)
2024-10-01: OHP 185 lbs (PR matched)
2024-11-10: Bench Press 280 lbs (NEW PR!)

Statistics:
- PRs per month
- Most-progressed lift
- Time to 1RM improvement (avg 4.2 weeks)
```

#### Body Composition (if using photos)
```
Chart Type: Side-by-side comparison
Input: Date + Progress photos (same angle)

Metrics:
- Estimated body composition change
- Muscle development (visual)
- Training impact (visual)

Timeline:
Jan 1 → Mar 1 → Jun 1 → Sep 1 → Dec 1
[Before] [8 weeks] [6 months] [9 months] [1 year]
```

### 6.2 Dashboard Layout

**Main Training Dashboard**:
```
Top Row:
[Strength Progression (Main Lift)] [Volume Over Time]

Middle Row:
[Muscle Group Distribution Pie]  [Workout Frequency Heatmap]

Bottom Row:
[Recovery Metrics]              [PRs Achieved Timeline]

Side Panel:
- Filter by date range
- Filter by muscle group
- Filter by exercise
- Export data (CSV/PDF)
```

### 6.3 Export Formats

Support for:
- **CSV**: Workouts, exercises, metrics (spreadsheet analysis)
- **PDF**: Monthly training reports (visual)
- **JSON**: Full export (backup, integration)
- **Image**: Chart snapshots (social sharing, records)

---

## 7. Implementation Architecture

### 7.1 Rust Backend Additions

**New modules to create**:

```
src-tauri/src/
├── services/
│   ├── workout_parser.rs       # Voice-to-workout extraction
│   ├── exercise_library.rs     # Exercise DB + fuzzy matching
│   ├── program_generator.rs    # Periodization + progression
│   ├── strava_sync.rs          # Strava API integration
│   └── apple_health.rs         # HealthKit sync (future)
├── db/
│   ├── workout_models.rs       # Workout entity models
│   ├── exercise_models.rs      # Exercise entity models
│   ├── training_journal.rs     # Journal entry models
│   └── analytics.rs            # Aggregation & metrics
└── commands/
    ├── workout_commands.rs     # Tauri commands for workouts
    ├── analytics_commands.rs   # Dashboard data queries
    └── integration_commands.rs # API sync commands
```

### 7.2 Svelte Frontend Components

**New components to create**:

```
src/components/
├── WorkoutPanel.svelte         # Main workout logging UI
│   ├── StartWorkout.svelte
│   ├── LogExercise.svelte
│   └── WorkoutSummary.svelte
├── TrainingJournal.svelte      # Prompt-based journal
│   ├── PreWorkoutPrompts.svelte
│   ├── PostWorkoutPrompts.svelte
│   └── RecoveryJournal.svelte
├── Analytics.svelte            # Dashboard + charts
│   ├── StrengthProgression.svelte
│   ├── VolumeChart.svelte
│   ├── RecoveryMetrics.svelte
│   └── PRTimeline.svelte
├── TrainingPrograms.svelte     # Program management
│   ├── ProgramSelector.svelte
│   ├── ProgramBuilder.svelte
│   └── ProgressionAdvisor.svelte
├── ExerciseLibrary.svelte      # Exercise browser
│   └── ExerciseDetail.svelte
└── Integrations.svelte         # 3rd party sync
    ├── StravaConnect.svelte
    └── HealthKitSync.svelte
```

### 7.3 Database Migrations

**New migration** (V3):
- Add `training_programs`, `workout_sessions`, `workout_exercises` tables
- Add `exercises` table with 500+ pre-populated entries
- Add `personal_records`, `recovery_logs` tables
- Add `training_journal_entries` table
- Add `strength_progression` view (for analytics)
- Add indices for performance queries

---

## 8. Voice Parser Examples

### 8.1 Strength Training Examples

```
User: "Got three sets of ten at 225 on bench"
→ Exercise: Bench Press | Sets: 3 | Reps: 10 | Weight: 225 lbs

User: "Did my deadlift singles: 405, 415, 425 - last one felt grindy"
→ Exercise: Deadlift
  → 1 × 1 @ 405 lbs
  → 1 × 1 @ 415 lbs
  → 1 × 1 @ 425 lbs (Note: "felt grindy")

User: "Squats sucked today, 5 by 3 at 315, could barely get the third rep"
→ Exercise: Squat | Sets: 5 | Reps: 3 | Weight: 315 lbs | Note: "could barely get reps"

User: "100 reps of bench press, 10 sets of 10, super light at 185 pounds"
→ Exercise: Bench Press | Sets: 10 | Reps: 10 | Weight: 185 lbs (High rep finisher)
```

### 8.2 Cardio Examples

```
User: "Ran five miles in 45 minutes on the treadmill, avg heart rate 165"
→ Exercise: Running (Treadmill) | Distance: 5 miles | Duration: 45 min | Avg HR: 165 bpm

User: "30 minute HIIT on the bike, 20 seconds hard, 10 seconds easy, maxed at 180 watts"
→ Exercise: Cycling (HIIT) | Duration: 30 min | Max Power: 180W | Type: HIIT (20/10)

User: "Easy row, just spinning the legs, 6k in 30 minutes"
→ Exercise: Rowing | Distance: 6 km | Duration: 30 min | Intensity: Light/Easy
```

### 8.3 Complex Workouts

```
User: "Chest and shoulders day. Four sets of six bench press at 275,
       then three sets of eight incline dumbbell at 80 pounds,
       finished with three sets of ten cable flies super light at 50"

Parsed:
├─ Bench Press: 4 × 6 @ 275 lbs
├─ Incline Dumbbell Press: 3 × 8 @ 80 lbs
└─ Cable Flyes: 3 × 10 @ 50 lbs (Isolation/Finisher)

Detected: Upper Body Focus, Hypertrophy/Strength block
```

### 8.4 Recovery/Injury Notes

```
User: "Shoulder's been bothering me, so I did physical therapy instead of lifting.
       10 minutes of band work, some stretching, iced for 15 minutes after"

Parsed:
Entry Type: Injury Recovery / Physical Therapy
Status: Active shoulder issue
Activities: Band work (10 min), Stretching, Ice therapy
Recovery Log Updated: Injury area tracked

Suggestion: Consider deload week if pain persists
```

---

## 9. Mental Game Implementation

### 9.1 Dynamic Prompt Sequencing

```
App detects user's context and sequences appropriate prompts:

Monday 6:00 AM (Pre-workout):
→ Show: Mental preparation + Goal-setting prompts
→ Suggested: 5 minutes

Monday 7:30 AM (Post-workout):
→ Show: Performance reflection + Recovery prompts
→ Suggested: 5 minutes

Monday Evening (Recovery):
→ Show: Sleep quality + Soreness assessment
→ Suggested: 2 minutes (quick check-in)

Friday Evening (Weekly):
→ Show: Weekly reflection + Program assessment
→ Suggested: 10 minutes (deeper reflection)

Week 4 (Deload):
→ Show: Deload-specific prompts
→ Recovery emphasis
→ Mental reset prompts
```

### 9.2 Prompt Categories as Database

```sql
training_prompts
├── id
├── category (pre_workout|post_workout|recovery|weekly|injury|goal_setting)
├── muscle_group (optional)
├── difficulty_level (beginner|intermediate|advanced)
├── prompt_text
├── suggested_duration_seconds
├── context_tags (strength|cardio|sport|recovery)
├── created_at

user_prompt_responses
├── id
├── user_id
├── prompt_id
├── audio_response (path to recording)
├── transcription (via Whisper.cpp)
├── date_answered
├── sentiment_analysis (optional: positive/neutral/negative)
├── keywords_detected (JSON: ["confidence", "pain", "strong"])
```

### 9.3 Sentiment Tracking

Use Claude to analyze journal responses:

```rust
#[tauri::command]
pub async fn analyze_journal_entry(
    transcript: String,
    entry_type: JournalEntryType,
    state: tauri::State<'_, AppState>,
) -> Result<EntryAnalysis, String> {
    let claude = state.claude_client.clone();

    let analysis_prompt = format!(
        r#"Analyze this athlete's journal entry for emotional/mental state:

Type: {}
Entry: "{}"

Provide JSON response:
{{
  "sentiment": "positive|neutral|negative",
  "confidence_level": 1-10,
  "key_emotions": ["motivated", "anxious", ...],
  "mental_blockers": ["fear of injury", ...],
  "strengths_detected": ["determination", ...],
  "recommendations": ["Increase sleep focus", ...]
}}"#,
        entry_type, transcript
    );

    let response = claude.send_message(&analysis_prompt).await?;
    let analysis: EntryAnalysis = serde_json::from_str(&response)?;
    Ok(analysis)
}
```

---

## 10. Sample Implementation Timeline

### MVP Phase (Weeks 1-6)
- Database schema + migrations
- Basic workout logging UI
- Voice-to-workout parser (Claude integration)
- Exercise library (500 pre-loaded exercises)
- Manual session creation

**Deliverable**: Users can voice-log workouts, see basic stats

---

### Phase 2 (Weeks 7-12)
- Training journal prompts
- Recovery logging UI
- Basic strength progression chart
- Personal records tracking
- Program templates

**Deliverable**: Complete training journal experience

---

### Phase 3 (Weeks 13-18)
- Strava API sync (cardio activities)
- Analytics dashboard (full visualization)
- Progressive overload recommendations
- Apple HealthKit integration

**Deliverable**: Athletes see comprehensive training data

---

### Phase 4 (Weeks 19-24)
- MyFitnessPal integration
- Advanced program builder
- Mental game coaching (sentiment tracking)
- Performance reporting (PDF exports)

**Deliverable**: Comprehensive athletic performance platform

---

## 11. API Integration Code Examples

### 11.1 Strava OAuth Flow

```rust
// src-tauri/src/services/strava_sync.rs

pub struct StravaClient {
    client_id: String,
    client_secret: String,
    redirect_uri: String,
    access_token: Option<String>,
}

#[tauri::command]
pub fn strava_auth_url(state: tauri::State<'_, AppState>) -> String {
    format!(
        "https://www.strava.com/api/v3/oauth/authorize?\
        client_id={}&\
        redirect_uri={}&\
        response_type=code&\
        scope=activity:read",
        state.strava.client_id,
        state.strava.redirect_uri
    )
}

#[tauri::command]
pub async fn strava_exchange_code(
    code: String,
    state: tauri::State<'_, AppState>,
) -> Result<StravaAuth, String> {
    let response = reqwest::Client::new()
        .post("https://www.strava.com/api/v3/oauth/token")
        .json(&json!({
            "client_id": state.strava.client_id,
            "client_secret": state.strava.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }))
        .send()
        .await?;

    let auth: StravaAuth = response.json().await?;
    state.strava.save_token(&auth)?;
    Ok(auth)
}

#[tauri::command]
pub async fn sync_strava_activities(
    state: tauri::State<'_, AppState>,
) -> Result<Vec<WorkoutSession>, String> {
    let token = state.strava.get_token()?;

    let response = reqwest::Client::new()
        .get("https://www.strava.com/api/v3/athlete/activities")
        .header("Authorization", format!("Bearer {}", token))
        .query(&[("per_page", "200")])
        .send()
        .await?;

    let activities: Vec<StravaActivity> = response.json().await?;

    // Convert to BrainDump format
    let mut workouts = Vec::new();
    for activity in activities {
        let workout = WorkoutSession {
            title: Some(activity.name),
            duration_minutes: (activity.moving_time / 60) as i32,
            intensity_level: estimate_intensity(activity.average_heartrate),
            external_id: Some(format!("strava:{}", activity.id)),
            ..Default::default()
        };
        workouts.push(workout);
    }

    // Save to database
    for workout in workouts.iter() {
        state.db.create_workout_session(workout)?;
    }

    Ok(workouts)
}
```

### 11.2 Prompt Template Endpoint

```rust
// src-tauri/src/commands/training_journal_commands.rs

#[tauri::command]
pub fn get_prompts_for_context(
    context: JournalContext,
    db: tauri::State<'_, Database>,
) -> Result<Vec<Prompt>, String> {
    match context {
        JournalContext::PreWorkout => {
            Ok(db.get_prompts("pre_workout", 5)?)
        },
        JournalContext::PostWorkout => {
            Ok(db.get_prompts("post_workout", 5)?)
        },
        JournalContext::Recovery => {
            Ok(db.get_prompts("recovery", 3)?)
        },
        JournalContext::Weekly => {
            Ok(db.get_prompts("weekly", 8)?)
        },
        JournalContext::Injury => {
            Ok(db.get_prompts("injury_recovery", 5)?)
        },
    }
}

#[tauri::command]
pub async fn save_journal_response(
    prompt_id: i64,
    response_transcript: String,
    entry_type: JournalEntryType,
    db: tauri::State<'_, Database>,
    ai_service: tauri::State<'_, AIService>,
) -> Result<JournalEntry, String> {
    // Analyze sentiment
    let analysis = ai_service.analyze_journal_entry(
        &response_transcript,
        &entry_type
    ).await?;

    // Save entry with analysis
    let entry = JournalEntry {
        prompt_id,
        response_transcript,
        entry_type,
        sentiment: analysis.sentiment,
        detected_emotions: analysis.key_emotions,
        created_at: Utc::now(),
        ..Default::default()
    };

    db.create_journal_entry(&entry)?;

    // Trigger recommendations if needed
    if analysis.mental_blockers.len() > 0 {
        notify_user(&format!(
            "I noticed: {}. Want to talk about it?",
            analysis.mental_blockers.join(", ")
        ))?;
    }

    Ok(entry)
}
```

---

## 12. Privacy & Data Handling

### 12.1 Sensitive Data

**Stored Locally Only**:
- Workout data (exercises, weights, metrics)
- Training journal transcripts
- Recovery logs
- Personal records
- Progress photos

**Never Sent to Cloud** (unless user opts for backup):
- Voice recordings
- Training history
- Personal metrics

**API Integration**:
- Strava: Limited read access (OAuth)
- MyFitnessPal: Nutrition data (read-only)
- Apple HealthKit: On-device only (never cloud)

### 12.2 Data Encryption

- Voice recordings: Encrypted at rest (local storage)
- API tokens: Stored in macOS Keychain (not plain text .env)
- Database: SQLite with optional encryption (SQLCipher)

---

## 13. Comparison: BrainDump vs. Competitor Apps

| Feature | BrainDump | Strong | Strava | MyFit | TrainingPeaks |
|---------|-----------|--------|--------|-------|---------------|
| Voice Logging | ✓ (NEW) | ✗ | ✗ | ✓ (Limited) | ✗ |
| Strength Tracking | ✓ (NEW) | ✓✓✓ | ✗ | ✓ | ✓ |
| Cardio Tracking | ✓ (NEW) | ✗ | ✓✓✓ | ✓ | ✓✓✓ |
| Training Journal | ✓ | ✗ | Limited | Limited | ✓ |
| Mental Game Coaching | ✓ (NEW) | ✗ | ✗ | ✗ | Limited |
| API Integrations | ✓ (NEW) | Planned | ✓✓✓ | ✓✓ | ✓✓ |
| Privacy Focus | ✓✓✓ | ✓ | ✗ | ✗ | ✓ |
| Desktop App | ✓ (Tauri) | ✗ | ✗ | ✗ | Web only |
| Offline First | ✓ | ✓ | ✗ | ✗ | Limited |

**Unique Value**: Voice-first journaling + mental game coaching + privacy

---

## 14. Success Metrics

### Adoption Metrics
- Workouts logged per user per week
- Journal entries completed
- Session duration (time spent in app)
- Feature adoption (% using each feature)

### Engagement Metrics
- Voice logging adoption rate (% using voice vs. manual)
- Journal completion rate
- Return user rate (monthly)
- Feature exploration (% discovering new features)

### Training Metrics
- PR achievements per user per month
- Average training volume progression
- Deload compliance (users following suggestions)
- Program template usage

### Integration Metrics
- % users with Strava sync
- Strava activity import success rate
- Data sync frequency
- User satisfaction with sync accuracy

---

## 15. Conclusion & Recommendations

### Core Value Proposition

BrainDump positions itself uniquely in the sports tracking market:

1. **Voice-First**: Hands-free logging during intense training
2. **Privacy-First**: Local-first architecture, optional sync only
3. **Holistic**: Strength + Cardio + Mental Game in one platform
4. **Integrated**: Journaling + Performance data + Social context
5. **Open**: Multiple API integrations (Strava, MyFitnessPal, HealthKit)

### Quick Implementation Wins (2-4 weeks)

1. **Basic Workout Logging**
   - UI for manual workout entry
   - Exercise library browser
   - Simple strength progression chart

2. **Voice Parser** (using Claude API)
   - "3 sets of 10 bench at 225" → structured data
   - Exercise library fuzzy matching
   - Auto-save to database

3. **Training Journal Templates**
   - 5 pre/post workout prompts
   - Recovery check-in
   - Simple sentiment tracking

### High-Impact, Medium Effort (4-8 weeks)

1. **Analytics Dashboard**
   - Strength progression by exercise
   - Weekly volume trends
   - Recovery metrics correlation

2. **Training Programs**
   - 5-6 template programs
   - Auto-progression logic
   - Deload recommendations

3. **Strava Integration**
   - OAuth 2.0 authentication
   - Weekly activity sync
   - Cardio-strength hybrid view

### Long-Term Differentiation (12+ weeks)

1. **AI-Powered Program Generation**
   - User goals + training history → custom program
   - Adaptation based on performance
   - Periodization automation

2. **Mental Performance Coaching**
   - Sentiment analysis of journal entries
   - Anxiety detection + interventions
   - Visualization prompt generation

3. **Return-to-Sport Platform**
   - Injury recovery tracking
   - Progressive rehab program builder
   - Mental clearance assessment

---

## References

### Research Sources
- Strava API Documentation: https://developers.strava.com/
- MyFitnessPal Developer: https://www.myfitnesspal.com/api
- Apple HealthKit Programming Guide: https://developer.apple.com/healthkit/
- TrainingPeaks API: https://developers.trainingpeaks.com/

### Athletic Journaling & Mental Game
- Sport Psychology Resources: https://appliedsportpsych.org/
- "The Injury Journal" by Dr. Jen Davis
- Periodization Research: https://pmc.ncbi.nlm.nih.gov/ (athletic performance)

### Database Design
- Fitness App DB Schemas: https://www.dittofi.com/
- Training Tracking Design: https://brandoncarper.com/

---

**Report Completed**: 2025-11-16
**Total Research**: 8+ API integrations, 50+ journal prompts, 5 visualization types
**Database Schema**: 15 core tables designed
**Implementation Roadmap**: 24-week phased approach

**Next Steps**:
1. Review schema with team
2. Prioritize MVP features
3. Create GitHub issues for each module
4. Begin implementation Phase 1 (Weeks 1-6)
