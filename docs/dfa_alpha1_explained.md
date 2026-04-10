# I Built an App That Detects Both Ventilatory Thresholds in Real Time. Here's How.

**Subtitle:** Heart rate zones are educated guesses. DFA alpha1 from a $60 chest strap gives you VT1 and VT2 — live, personalised, no lab required.

---

Last summer I was doing what I thought was a solid Zone 2 ride. 220 watts, heart rate sitting at 145, two hours into a long base session. Everything looked fine on paper.

Except it wasn't fine. When I later ran the RR interval data through a DFA alpha1 analysis, my alpha was sitting below 0.75 for most of that ride. I wasn't in Zone 2. I was above my aerobic threshold, accumulating fatigue, burning through glycogen — all while my heart rate said "easy."

That ride is why I built AlphaZone.

---

## Heart rate zones don't know your threshold

Here's the thing about heart rate zones: they're derived from either a percentage of your max HR or from a lab test you did months ago. Either way, they're static. Your actual aerobic threshold isn't.

My VT1 sits around 300 watts and 166 bpm on a fresh day. After a hard training block? It might be closer to 280 watts and 158 bpm. On a hot day after bad sleep? Lower still. The formula that says my Zone 2 ceiling is at 150 bpm doesn't know any of this.

If you're doing polarised training — and you should be, the evidence is pretty clear at this point — the whole model depends on keeping most of your volume below VT1. But if your zone boundaries are wrong by even 5-8 beats, you're constantly drifting into no man's land. Not hard enough to be a real interval, not easy enough to build your aerobic base. Just... medium. The worst intensity for long-term adaptation.

I wanted to stop guessing.

---

## The signal your watch is throwing away

Your chest strap transmits the exact millisecond timing between each heartbeat. It's called the RR interval. Your watch takes those intervals, calculates a heart rate from them, and throws the rest away.

That's a mistake, because those intervals contain something your heart rate doesn't: information about how your autonomic nervous system is regulating your heart.

DFA alpha1 — the scaling exponent from Detrended Fluctuation Analysis — measures the complexity of your beat-to-beat variation. Below your aerobic threshold, the pattern is fractal-like, complex, variable. Your parasympathetic system is actively modulating each beat. Alpha1 sits above roughly 0.75.

Cross VT1, and that complexity collapses. The intervals become more regular, more constrained. Alpha1 drops below 0.75. Push harder — into the territory above your anaerobic threshold — and alpha1 drops further, below 0.50. That's VT2. The point where lactate accumulation accelerates and you're on borrowed time.

So the same signal gives you both thresholds. VT1 at ~0.75, VT2 at ~0.50. This has been validated in study after study (Gronwald, Rogers, Schaffarczyk — the references are solid). It's a real physiological signal, not a statistical trick.

One thing worth clarifying: DFA alpha1 correlates with the **ventilatory** thresholds (VT1/VT2), not directly with lactate thresholds (LT1/LT2). The distinction matters. Rogers et al. coined the term HRVT — heart rate variability threshold — and validated it specifically against gas exchange data from spirometry, not against blood lactate. The correlation between HRVT and VT1 is strong (r ~0.95 across multiple studies).

Why? Because both share the same root cause. When you cross the aerobic threshold, your autonomic nervous system shifts from parasympathetic to sympathetic dominance. That shift drives two things simultaneously: your breathing rate increases (the ventilatory response) and your beat-to-beat heart rate complexity collapses (the DFA response). DFA alpha1 and ventilatory breakpoints are two readouts of the same underlying autonomic event.

Lactate threshold is a metabolic marker — it tells you when lactate production outpaces clearance. LT1 and VT1 are related and often sit close together, but in some athletes they can diverge by 5-15 watts. AlphaZone detects the autonomic/ventilatory breakpoint, not the metabolic one. For practical training purposes, the difference is small. For scientific accuracy, it matters — so throughout this article, I use VT1 and VT2, not "lactate threshold."

This also explains an advantage that isn't immediately obvious: **DFA alpha1 is harder to fool than ventilation-based metrics.**

If you've ever used a device that estimates your threshold from respiratory rate or breathing patterns — and there are a few on the market — you know the problem. Conscious or unconscious changes in your breathing pattern (talking, drinking, a hill that makes you breathe harder mechanically, deliberately trying to "breathe calm" during an effort) can all distort the signal. Ventilation-based detection measures the output of your respiratory muscles, which is partly under voluntary control.

DFA alpha1 doesn't have this problem. It measures the autonomic regulation of your heart — something you can't consciously override. You can't "breathe your way" to a different alpha1 value. You can't trick it by nasal breathing or controlling your cadence. The signal comes from a layer of your nervous system that operates below conscious control. It's measuring what your body is actually doing, not what you're telling it to do.

There's also a mathematical reason why breathing patterns wash out. Respiratory sinus arrhythmia — the natural coupling between breathing and heart rate — operates at a cycle length of roughly 3 to 5 seconds (12-20 breaths per minute). DFA works by analysing fluctuation patterns across multiple timescales. AlphaZone's deep engine uses a 500 to 1280-beat buffer with segment factor 5, which means the smallest scale it evaluates already spans 25 beats — roughly 15 to 20 seconds of data. At that timescale, individual breath cycles average out. You'd need to sustain an artificially altered breathing pattern for minutes at a constant rate to even begin to influence the result, and even then the effect would be small compared to the autonomic shift that happens at the threshold. Short-term breathing artefacts simply don't survive the averaging that DFA performs across its scale range.

And it happens beat by beat. In real time. On a phone.

---

## DFA is the science. AlphaZone is what makes it usable.

Let me be clear about the distinction, because the naming can be confusing.

**DFA** — Detrended Fluctuation Analysis — is a well-established mathematical method from the 1990s. You take a time series, detrend it at multiple scales, measure how the fluctuations scale, and get an exponent. Applied to RR intervals during exercise, it produces alpha1, which crosses 0.75 at VT1 and 0.50 at VT2. The science is solid. Gronwald, Rogers, Schaffarczyk and others have validated this extensively.

But DFA as published in the literature is a post-hoc analysis. You record a workout, export the RR data, run it through MATLAB or Python, wait for the result, and find out where your threshold was — past tense. That's useful for research. It's not useful on a Tuesday afternoon ride when you're trying to stay in Zone 2.

**AlphaZone** — what I built — is the engineering layer that turns DFA from a lab tool into something you can glance at on your handlebars.

That gap between "works in a paper" and "works on your bike" is bigger than it looks.

### The noise problem

The papers that validate DFA alpha1 use carefully recorded, artifact-cleaned RR data from controlled lab settings. Chest strap perfectly positioned, subject sitting on an ergometer, no road vibration, no sweat-induced contact issues, no Bluetooth interference from passing cars.

Out on the road, none of that applies. One ectopic beat, one Bluetooth hiccup, one moment where the strap shifts on your chest — and the number jumps. If you just display raw alpha1, you get a jittery mess that makes athletes more anxious, not more informed.

So I spent a lot of time on what I call the stabilisation layer. AlphaZone doesn't run a single DFA computation — it runs two engines in parallel. A fast one (segment factor 1, scales 4-16, 200-beat buffer) for responsive VT1 detection, and a deep one (segment factor 5, scales 5-64, up to 1280 beats) for stable autonomic tracking. The deep engine computes alpha at each scale independently, then takes the median across all of them — much more robust against outlier scales than the single OLS slope you'd find in a textbook implementation.

On top of that, an RMSSD plausibility gate catches physiologically impossible data — frozen sensor, severe artefacts — and holds the last good value instead of propagating garbage. And there's a maturity tracker that tells you whether the signal is still in warmup (don't trust it yet), transition (getting there), or mature (this number is real). It's based on how many beats the deep engine has accumulated: below 400, you're warming up. Above 1280, every scale is active and the output is reliable.

None of this is in the DFA literature. It's the gap between the math and a product.

### The 0.75 problem — and why AlphaZone recalculates your threshold every single session

This is the core innovation, and it's worth explaining in detail, because it's what separates AlphaZone from every other DFA tool I'm aware of.

In the literature, the threshold is fixed: alpha1 crosses 0.75 at VT1, crosses 0.50 at VT2. Done. Every app that implements DFA alpha1 uses these numbers as constants. And for a population average derived from controlled lab conditions, they're reasonable.

But your threshold isn't a constant. It shifts. My alpha1 at VT1 sits around 0.78-0.80 on fresh legs. After a hard training block, it might be closer to 0.73. On a hot day, different again. Using a fixed 0.75 for me would sometimes overestimate and sometimes underestimate my threshold — depending on the day, my fatigue, my hydration, how well I slept. The error is small on any given ride, maybe 5-10 watts. But if you're trying to nail Zone 2, 5-10 watts of systematic error accumulated over weeks is the difference between building your base and quietly eroding it.

AlphaZone throws out the fixed numbers entirely. Here's what happens instead:

**Before the workout — baseline calibration.** When you start a session, the app collects a brief baseline during your warmup: low-intensity pedalling for the first few minutes while your autonomic system settles. During this phase, AlphaZone measures your current resting-state alpha1 and compares it to your cross-session average. This tells the system two things: where your alpha1 starts today (which varies day to day), and whether you're fresher or more fatigued than usual. That's the readiness score — but it also calibrates the detection for this specific session. If your baseline alpha is lower than normal today, the system knows your threshold will sit lower too.

**During the workout — live threshold updates.** AlphaZone doesn't detect VT1 once and lock it for the rest of the ride. It continuously tracks where your threshold sits, because your threshold moves during a session.

As fatigue accumulates — and it always does on a long ride — your aerobic threshold drifts downward. The power you could sustain below VT1 at minute 20 is higher than what you can sustain at minute 90. AlphaZone's adaptive drift detector picks this up in real time. It monitors the relationship between your power, heart rate, and alpha1, and classifies what kind of drift is happening: cardiac drift (heart rate creeping up at constant power — your cardiovascular system is working harder for the same output), muscular drift (power dropping at constant heart rate — your muscles are fatiguing), or both. The VT1 estimate on your gauge updates accordingly — not every beat, that would be noisy, but when the TriGate confirms a new lock based on converging evidence from all three signals.

This means two rides that look identical on paper (same average power, same average HR, same duration) can produce completely different threshold trajectories. One might show a stable VT1 throughout — you were fresh, well-fuelled, the ride was within your capacity. The other might show VT1 drifting down by 15 watts over the last 30 minutes — same external load, but your body was handling it differently. That information is invisible with fixed thresholds. With AlphaZone, you see it happening.

**Across sessions — the system learns you.** Each workout feeds back into a cross-session baseline tracker. Over multiple rides, AlphaZone builds a model of where your personal alpha threshold sits, how it varies with fatigue and conditions, and how your body typically drifts during extended efforts. Session 1 uses conservative defaults. By session 5 or 10, the system has a personalised profile that's tighter than most lab retests — because it's based on your actual data from your actual rides, not a single controlled test from months ago.

The same applies to VT2. The fixed 0.50 from the literature is a starting point. A cross-session Kalman filter refines your personal VT2 estimate with every workout that pushes you above the anaerobic threshold.

**Why this matters practically:** On a Tuesday evening ride, I don't care what the literature says my threshold should be. I care what it is today, right now, 45 minutes into this specific ride, after the training I did this week. That's what AlphaZone gives me. Not a static number from a paper, not a zone boundary from a formula — a live, personalised, fatigue-adjusted threshold that moves with me.

### The false positive problem

Standard DFA gives you a number. If it drops below threshold, you've crossed VT1. Simple.

Too simple. In noisy real-world data, alpha1 dips below threshold all the time for reasons that have nothing to do with your metabolism — a few ectopic beats, a momentary artefact burst, a BLE packet arriving late. A naive implementation would flash "above VT1!" every few minutes and destroy your trust in the system within one ride.

AlphaZone uses what I call a TriGate: VT1 only fires when power, heart rate, AND alpha1 all agree within 10% of your known values. All three signals must converge. A noise spike in one channel gets caught by the other two. It sounds overly conservative, but it's the difference between a research tool and something you'd actually use in training.

If it's your very first session and there's no baseline yet? The system shows nothing rather than something wrong. No hidden fallback to 0.75. I'd rather give you no number than a wrong number.

### The gauge

Nobody wants to stare at "alpha1 = 0.73" during a ride. So I built an intensity gauge — four colour zones, a needle, smoothed with a 10-second moving average. Green means you're well below VT1. Yellow means you're approaching. Orange is between VT1 and VT2. Red means you're deep in the pain cave.

The score behind the gauge weights power at 50%, heart rate at 30%, and alpha1 at 20%. VT1 and VT2 are both marked on the gauge, so you can see whether you're in the aerobic zone, the threshold zone, or above VT2. If you don't have a power meter, it adapts. If there's no personal baseline, it goes grey instead of guessing.

### It gets smarter over time

Every ride feeds a 3D bin history — power, heart rate, alpha1 combinations from your training. When the TriGate can't lock in the current session (maybe you're still warming up, maybe conditions are weird), the system extrapolates from your history using nearest-neighbour lookup. Session 10 benefits from everything sessions 1 through 9 taught about your body.

### Fatigue tracking beyond the threshold

The threshold drift I described above is one piece of the fatigue picture. AlphaZone goes further.

For intervals, it tracks carryover between efforts. Not just "I did 6x5 minutes" but "by rep 4, I wasn't recovering between efforts anymore — my alpha1 wasn't bouncing back to baseline between sets." That's the kind of information that changes how you structure a session, and it's completely invisible if you're only looking at power and heart rate.

### VT2 — the other threshold

Most DFA implementations stop at VT1, if they even get that far. AlphaZone detects VT2 as well.

In the literature, VT2 at alpha1 ~0.50 is mentioned almost as an afterthought — "and alpha1 also crosses 0.50 near VT2." Making that work reliably in real time is a different story. The signal-to-noise ratio is worse at high intensities (shorter RR intervals, more artefacts, less data per window), and the transition is less sharp than VT1. AlphaZone uses hysteresis to avoid flickering around the boundary and requires a minimum regression quality (R^2) before it'll commit to a VT2 call.

Across sessions, a Kalman filter smooths your VT2 estimate. One ride might put it at 350 watts, the next at 355. The filter converges on where your VT2 actually sits right now, accounting for noise in individual sessions. The intensity gauge shows both thresholds — green below VT1, orange between VT1 and VT2, red above VT2 — so you always know exactly where you are relative to both.

Having both thresholds live on the same screen changes how you do intervals. You can see in real time whether you're actually hitting the target zone or just drifting in no-man's land between VT1 and VT2 where the training stimulus is ambiguous.

### Recovery and readiness

After each session, the app estimates recovery time based on the actual autonomic stress pattern — not just "you rode for 90 minutes at 200 watts average." It classifies how your body responds (some people recover fast, some slow) and adjusts over time. Before your next workout, a readiness score during warmup tells you whether to push or back off.

There's also a full training load chart (CTL/ATL/TSB) and a fitness trend tracker that shows whether your VT1 power is going up, down, or sideways over weeks.

### Garmin on your wrist

The phone does all the computation, but you probably don't want to look at your phone while riding. AlphaZone streams the results to your Garmin watch via Connect IQ every 2.5 seconds. Phone = brain, watch = display.

### Export everything

CSV with beat-by-beat data. FIT files that work with Garmin Connect, Strava, TrainingPeaks. The FIT export includes native RR intervals, so you can re-analyse everything in any tool you want. PDF summaries for coaches.

---

## Under the hood

For the technically curious: it's all Swift and SwiftUI, running entirely on-device. No cloud. Your data never leaves your phone.

The pipeline is 75+ modules — and the actual DFA math is maybe 5% of that. The other 95% is everything DFA papers don't have to deal with: BLE connection management, RR preprocessing (ectopic detection, artefact rejection, missing-beat interpolation), the stabilisation layer, cross-session learning, drift detection, fatigue modelling, Kalman filtering, respiratory rate extraction from the RR signal, and making all of it work in under a millisecond per beat.

Dual-engine DFA: a fast α₁ engine (sf=1, scales 4-16, 200 beats) for VT1 detection and a deep α₂ engine (sf=5, scales 5-64, up to 1280 beats) for autonomic tracking. Quadratic detrending, median-over-scales stabilisation. A Levenberg-Marquardt solver for fitting sigmoid curves to the HR-alpha relationship across sessions. The DFA computation itself went through an optimisation from O(n^2) to O(n), which was necessary because the original version took 17 minutes to process a 90-minute ride. Now it's real-time.

I wrote 1200+ automated tests, including synthetic artefact injection — I generate fake ectopic beats, simulate BLE dropouts, inject baseline wander, and verify the pipeline handles all of it without falling over. That test suite is where most of the confidence comes from. The math is proven. The question was always whether the math survives contact with real-world data from a chest strap on a bumpy road.

---

## Where this goes next

The foundation works. I've validated it against my own step test data (VT1 at 300W / 166 bpm), and AlphaZone consistently detects the threshold within about 10 watts across sessions. That's tighter than most lab retests.

Next up: I want to surface RMSSD (a measure of vagal nervous system activity) as a live trend during the workout. The pipeline already computes it as a quality gate. Showing the suppression pattern over time would add a second dimension — DFA alpha1 tells you whether you're above or below threshold, RMSSD tells you how much autonomic stress has accumulated since you started. Together, they'd give you something heart rate never can: a two-dimensional picture of your metabolic state, updating in real time.

But that's the next sprint, not this article.

---

---

## References

The DFA alpha1 methodology that AlphaZone builds on is grounded in peer-reviewed research. If you want to dig into the science behind the signal:

- **Gronwald, T., Rogers, B., Hoos, O. (2020)** — *Fractal correlation properties of heart rate variability: A new biomarker for intensity distribution in endurance exercise and training prescription?* Frontiers in Physiology. The paper that put DFA alpha1 on the map for endurance training — establishes the case for using fractal HRV properties as an intensity marker.

- **Rogers, B. et al. (2021)** — Multiple papers on DFA alpha1 as a marker for the heart rate variability threshold (HRVT), validating the ~0.75 crossover against ventilatory and lactate thresholds across different populations and sports. This is the body of work that makes the VT1 detection in AlphaZone possible.

- **Kanniainen, M. et al. (2023)** — *Estimation of physiological exercise thresholds based on dynamical correlation properties of heart rate variability.* Explores how dynamical correlation properties (including DFA) can estimate both VT1 and VT2 — directly relevant to AlphaZone's dual-threshold approach. Also informs the timescale behaviour of the large-buffer DFA window.

- **Molkkari, M. et al. (2020)** — *Dynamical heart beat correlations during running.* Examines how beat-to-beat correlation structure changes during exercise — foundational for understanding why the DFA signal behaves differently at different intensities and why window size matters.

- **Plews, D. J. et al. (2013)** — *Training adaptation and heart rate variability in elite endurance athletes.* The reference for how HRV metrics (including RMSSD) track training adaptation over time. Informs AlphaZone's cross-session baseline tracking and the upcoming RMSSD suppression feature.

---

**Walter Vath** — endurance athlete, developer. AlphaZone is available for iOS.

---

*Tags: HRV, DFA Alpha1, iOS Development, SwiftUI, BLE, Sports Science, Real-Time Signal Processing, Cycling, Running, Threshold Detection, Endurance Training*
