import gc
gc.collect()

import math
import time
import network
import urequests
from machine import Pin, I2C

gc.collect()

# ---------------- CONFIGURATION ----------------
WIFI_SSID = "WIFI_SSID"
WIFI_PASS = "WIFI_PASS"
TELEGRAM_BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "TELEGRAM_CHAT_ID"
PATIENT_LOCATION = "PATIENT_LOCATION"

TARGET_HZ = 100
WIN_SAMPLES = 50
FREEFALL_G = 0.6
IMPACT_TH_G = 2.8
COUNTDOWN_S = 20
AI_THRESHOLD = 0.55

CAL_OFFSET_X = 0.00
CAL_OFFSET_Y = 0.00
CAL_OFFSET_Z = 0.00

# ---------------- HARDWARE SETUP ----------------
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)
btn_cancel = Pin(14, Pin.IN, Pin.PULL_UP)
buzzer = Pin(15, Pin.OUT)
buzzer.value(0)

MPU_ADDR = 0x68
MAX_ADDR = 0x57


def init_mpu6050():
    i2c.writeto_mem(MPU_ADDR, 0x6B, b"\x00")
    i2c.writeto_mem(MPU_ADDR, 0x1A, b"\x03")
    i2c.writeto_mem(MPU_ADDR, 0x1C, b"\x18")
    i2c.writeto_mem(MPU_ADDR, 0x1B, b"\x08")


def sleep_max30102():
    try:
        i2c.writeto_mem(MAX_ADDR, 0x09, b"\x80")
    except Exception:
        pass


def read_max30102_bpm(duration_s=6):
    try:
        i2c.writeto_mem(MAX_ADDR, 0x09, b"\x40")
        time.sleep_ms(50)
        i2c.writeto_mem(MAX_ADDR, 0x04, b"\x00")
        i2c.writeto_mem(MAX_ADDR, 0x05, b"\x00")
        i2c.writeto_mem(MAX_ADDR, 0x06, b"\x00")

        i2c.writeto_mem(MAX_ADDR, 0x08, b"\x4F")
        i2c.writeto_mem(MAX_ADDR, 0x0A, b"\x27")
        i2c.writeto_mem(MAX_ADDR, 0x0C, b"\x24")
        i2c.writeto_mem(MAX_ADDR, 0x0D, b"\x24")
        i2c.writeto_mem(MAX_ADDR, 0x09, b"\x03")
        print("MAX30102 ON: Measuring heart rate...")

        samples = []
        times = []
        t_start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), t_start) < duration_s * 1000:
            data = i2c.readfrom_mem(MAX_ADDR, 0x07, 6)
            ir = ((data[3] << 16) | (data[4] << 8) | data[5]) & 0x3FFFF
            samples.append(ir)
            times.append(time.ticks_ms())
            time.sleep_ms(20)

        if len(samples) > 60:
            samples = samples[50:]
            times = times[50:]

        if not samples or max(samples) < 30000:
            print("MAX30102: No skin contact detected.")
            return "No Contact"

        beat_times = []
        last_beat = 0
        for i in range(10, len(samples) - 1):
            baseline = sum(samples[i - 10:i]) / 10.0
            ac_curr = samples[i] - baseline
            ac_prev = samples[i - 1] - baseline
            ac_next = samples[i + 1] - baseline

            if ac_curr > 40 and ac_curr > ac_prev and ac_curr >= ac_next:
                if time.ticks_diff(times[i], last_beat) > 350:
                    beat_times.append(times[i])
                    last_beat = times[i]

        if len(beat_times) >= 2:
            intervals = [
                time.ticks_diff(beat_times[i], beat_times[i - 1])
                for i in range(1, len(beat_times))
            ]
            avg_ms = sum(intervals) / len(intervals)
            bpm = int(60000 / avg_ms)
            if 40 <= bpm <= 180:
                print("MAX30102 Measured BPM:", bpm)
                return bpm

        print("MAX30102: Unstable pulse signal.")
        return "Unstable"

    except Exception as e:
        print("MAX30102 error:", e)
        return "Sensor Error"
    finally:
        sleep_max30102()
        print("MAX30102 OFF.")


def read_mpu6050():
    data = i2c.readfrom_mem(MPU_ADDR, 0x3B, 14)

    def to_int16(h, l):
        v = (h << 8) | l
        return v - 65536 if v & 0x8000 else v

    ax = (to_int16(data[0], data[1]) / 2048.0) - CAL_OFFSET_X
    ay = (to_int16(data[2], data[3]) / 2048.0) - CAL_OFFSET_Y
    az = (to_int16(data[4], data[5]) / 2048.0) - CAL_OFFSET_Z
    gx = to_int16(data[8], data[9]) / 65.5
    gy = to_int16(data[10], data[11]) / 65.5
    gz = to_int16(data[12], data[13]) / 65.5
    return (ax, ay, az, gx, gy, gz)


# ---------------- FEATURE EXTRACTION & AI ----------------
def mean_std(arr):
    n = len(arr)
    if n == 0:
        return 0.0, 0.0
    m = sum(arr) / n
    if n < 2:
        return m, 0.0
    var = sum((x - m) ** 2 for x in arr) / n
    return m, math.sqrt(var)


def extract_features(win):
    n = len(win)
    dt = 1.0 / TARGET_HZ
    svm = []
    gmag = []
    for s in win:
        svm.append(math.sqrt(s[0]*s[0] + s[1]*s[1] + s[2]*s[2]))
        gmag.append(math.sqrt(s[3]*s[3] + s[4]*s[4] + s[5]*s[5]))

    svm_max = max(svm)
    svm_min = min(svm)
    svm_mean, svm_std = mean_std(svm)
    p = svm.index(svm_max)

    freefall_s = sum(1 for v in svm if v < FREEFALL_G) * dt
    jerk_max = max(abs(svm[i+1] - svm[i]) / dt for i in range(n - 1))

    pre_s = max(0, p - 15)
    pre_e = max(pre_s + 1, p - 3)
    pre_len = pre_e - pre_s
    pre = [sum(win[i][k] for i in range(pre_s, pre_e)) / pre_len for k in range(3)]

    if p + 10 < n:
        post_len = n - (p + 10)
        post = [sum(win[i][k] for i in range(p + 10, n)) / post_len for k in range(3)]
    else:
        post = [win[-1][0], win[-1][1], win[-1][2]]

    dot = pre[0]*post[0] + pre[1]*post[1] + pre[2]*post[2]
    n_pre = math.sqrt(pre[0]**2 + pre[1]**2 + pre[2]**2)
    n_post = math.sqrt(post[0]**2 + post[1]**2 + post[2]**2)
    cosang = max(-1.0, min(1.0, dot / (n_pre * n_post + 1e-9)))
    tilt_change = math.degrees(math.acos(cosang))

    after_slice = svm[min(n - 1, p + 5):]
    _, post_std = mean_std(after_slice)
    gyro_max = max(gmag)
    gyro_mean = sum(gmag) / n

    return [
        svm_max, svm_min, svm_mean, svm_std, freefall_s,
        jerk_max, tilt_change, post_std, gyro_max, gyro_mean
    ]


def predict_fall_prob(feats):
    svm_max = feats[0]
    svm_min = feats[1]
    freefall_s = feats[4]
    jerk_max = feats[5]
    tilt_change = feats[6]
    post_std = feats[7]
    gyro_max = feats[8]

    if svm_max < 2.8:
        return 0.05

    score = 0.0
    if svm_max >= 3.5:
        score += 0.35
    elif svm_max >= 2.8:
        score += 0.20

    if freefall_s >= 0.06 or svm_min < 0.45:
        score += 0.25

    if tilt_change >= 55.0 and gyro_max >= 180.0:
        score += 0.25
    elif tilt_change >= 45.0:
        score += 0.15

    if jerk_max >= 35.0:
        score += 0.15

    if post_std > 0.45:
        score -= 0.25
    elif post_std < 0.22:
        score += 0.10

    return max(0.0, min(1.0, score))


# ---------------- LOCAL DATABASE & CLOUD ALERTS ----------------
def log_event_db(event_type, prob, hr_bpm):
    try:
        with open("events_db.csv", "a") as f:
            f.write(f"{time.time()},{event_type},{prob:.3f},{hr_bpm}\n")
    except Exception as e:
        print("DB log error:", e)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        for _ in range(15):
            if wlan.isconnected():
                break
            time.sleep(0.5)
    return wlan.isconnected()


def send_telegram_alert(prob, hr_bpm):
    if not connect_wifi():
        log_event_db("QUEUED_NO_WIFI", prob, hr_bpm)
        return False
    hr_text = f"{hr_bpm} BPM" if isinstance(hr_bpm, int) else str(hr_bpm)
    msg = (f"EMERGENCY: Fall Detected!\n"
           f"AI Confidence: {prob*100:.1f}%\n"
           f"Heart Rate: {hr_text}\n"
           f"Location: {PATIENT_LOCATION}\n"
           f"No cancel response after {COUNTDOWN_S}s.")
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = urequests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        r.close()
        return True
    except Exception as e:
        print("Telegram error:", e)
        return False


# ---------------- MAIN REAL-TIME LOOP ----------------
def main():
    init_mpu6050()
    sleep_max30102()
    connect_wifi()

    ring_buf = []
    post_impact_countdown = -1
    print("Pico 2 W Fall Detector Running at 100 Hz...")

    while True:
        t0 = time.ticks_ms()
        sample = read_mpu6050()
        ring_buf.append(sample)
        if len(ring_buf) > WIN_SAMPLES:
            ring_buf.pop(0)

        svm_now = math.sqrt(sample[0]**2 + sample[1]**2 + sample[2]**2)

        if svm_now >= IMPACT_TH_G and post_impact_countdown < 0 and len(ring_buf) >= 25:
            post_impact_countdown = 25

        if post_impact_countdown > 0:
            post_impact_countdown -= 1
        elif post_impact_countdown == 0:
            post_impact_countdown = -1
            if len(ring_buf) >= WIN_SAMPLES // 2:
                feats = extract_features(ring_buf)
                prob = predict_fall_prob(feats)
                print(f"Trigger evaluated -> Fall probability: {prob:.3f}")

                if prob >= AI_THRESHOLD:
                    print("FALL DETECTED! Starting 20s cancel countdown...")
                    cancelled = False
                    for _ in range(COUNTDOWN_S * 10):
                        buzzer.value(1)
                        if btn_cancel.value() == 0:
                            cancelled = True
                            break
                        time.sleep(0.1)
                    buzzer.value(0)

                    if cancelled:
                        print("Alert cancelled by user.")
                        log_event_db("CANCELLED", prob, "N/A")
                    else:
                        hr_bpm = read_max30102_bpm(duration_s=6)
                        print("Sending emergency alert!")
                        sent = send_telegram_alert(prob, hr_bpm)
                        log_event_db("FALL_ALERT_SENT" if sent else "FALL_ALERT_FAILED", prob, hr_bpm)
                        gc.collect()

                    ring_buf.clear()

        elapsed = time.ticks_diff(time.ticks_ms(), t0)
        if elapsed < 10:
            time.sleep_ms(10 - elapsed)


if __name__ == "__main__":
    main()