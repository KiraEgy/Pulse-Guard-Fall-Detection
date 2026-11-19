# fall_model_pico.py — Calibrated Multi-Condition Edge AI Classifier

# Require at least two fall indicators (e.g., Impact + Tilt/Free-fall/Stillness)
THRESHOLD = 0.55

def predict_fall_prob(feats):
    """
    feats[0]: svm_max      (Peak impact in g)
    feats[1]: svm_min      (Minimum g during window)
    feats[2]: svm_mean     (Mean g)
    feats[3]: svm_std      (Overall std deviation)
    feats[4]: freefall_s   (Seconds spent below 0.6g)
    feats[5]: jerk_max     (Peak deceleration rate in g/s)
    feats[6]: tilt_change  (Pre-to-post orientation angle in degrees)
    feats[7]: post_std     (Movement variance right after impact)
    feats[8]: gyro_max     (Peak rotation in deg/s)
    feats[9]: gyro_mean    (Mean rotation in deg/s)
    """
    svm_max     = feats[0]
    svm_min     = feats[1]
    freefall_s  = feats[4]
    jerk_max    = feats[5]
    tilt_change = feats[6]
    post_std    = feats[7]
    gyro_max    = feats[8]

    # Hard guard: ignore normal low-G hand movements
    if svm_max < 2.8:
        return 0.05

    score = 0.0

    # 1. Impact Severity (Max +0.35)
    if svm_max >= 3.5:
        score += 0.35
    elif svm_max >= 2.8:
        score += 0.20

    # 2. Pre-Impact Free-Fall / Weightlessness (Max +0.25)
    # Normal arm swings pull outward (high g); true drops briefly dip < 0.6g
    if freefall_s >= 0.06 or svm_min < 0.45:
        score += 0.25

    # 3. Postural Collapse / Orientation Tilt + Rotation (Max +0.25)
    if tilt_change >= 55.0 and gyro_max >= 180.0:
        score += 0.25
    elif tilt_change >= 45.0:
        score += 0.15

    # 4. Impact Sharpness / Jerk (Max +0.15)
    if jerk_max >= 35.0:
        score += 0.15

    # 5. Active-Movement Filter (Crucial for stopping false alarms)
    # If the wrist keeps moving heavily right after the peak (walking/clapping),
    # subtract points. If the person lies relatively still after impact, add points.
    if post_std > 0.45:
        score -= 0.25
    elif post_std < 0.22:
        score += 0.10

    return max(0.0, min(1.0, score))