#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/system_properties.h>
#include <android/log.h>

#define LOG_TAG "LHDC_V5_SHIM"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

typedef void* HANDLE_LHDC_BT;
typedef void* HANDLE_LHDCV5_BT;

static void *g_v5_lib = NULL;
static int32_t (*fn_lhdcv5BT_get_handle)(uint32_t version, HANDLE_LHDCV5_BT *handle) = NULL;
static int32_t (*fn_lhdcv5BT_free_handle)(HANDLE_LHDCV5_BT handle) = NULL;
static int32_t (*fn_lhdcv5BT_init_encoder)(HANDLE_LHDCV5_BT handle, uint32_t sample_rate, uint32_t bits, uint32_t bitrate_inx, uint32_t mtu, uint32_t interval, uint32_t lossless) = NULL;
static int32_t (*fn_lhdcv5BT_get_block_Size)(HANDLE_LHDCV5_BT handle, uint32_t *samples) = NULL;
static int32_t (*fn_lhdcv5BT_get_bitrate)(HANDLE_LHDCV5_BT handle, uint32_t *br) = NULL;
static int32_t (*fn_lhdcv5BT_set_bitrate)(HANDLE_LHDCV5_BT handle, uint32_t bitrate_inx) = NULL;
static int32_t (*fn_lhdcv5BT_set_max_bitrate)(HANDLE_LHDCV5_BT handle, uint32_t max_bitrate_inx) = NULL;
static int32_t (*fn_lhdcv5BT_adjust_bitrate)(HANDLE_LHDCV5_BT handle, uint32_t queueLen) = NULL;
static int32_t (*fn_lhdcv5BT_set_ext_func_state)(HANDLE_LHDCV5_BT handle, int field, bool enabled, void *priv, uint32_t len) = NULL;
static int32_t (*fn_lhdcv5BT_get_user_exApiver)(HANDLE_LHDCV5_BT handle, char *userConfig, int clen) = NULL;
static int32_t (*fn_lhdcv5BT_get_user_exconfig)(HANDLE_LHDCV5_BT handle, char *userConfig, int clen) = NULL;
static int32_t (*fn_lhdcv5BT_set_user_exconfig)(HANDLE_LHDCV5_BT handle, const char *userConfig, const int clen) = NULL;
static void (*fn_lhdcv5BT_set_user_exdata)(HANDLE_LHDCV5_BT handle, const char *userConfig, const int clen) = NULL;
static int32_t (*fn_lhdcv5BT_encode)(HANDLE_LHDCV5_BT handle, void *p_in_pcm, uint32_t pcm_bytes, uint8_t *p_out_buf, uint32_t out_buf_bytes, uint32_t *p_out_bytes, uint32_t *p_out_frames) = NULL;

static void *g_v5_dsp_lib = NULL;

static bool init_v5_lib(void) {
    if (g_v5_lib) return true;
    
    // Preload liblhdcv5.so with RTLD_GLOBAL so symbols are resolved
    const char *dsp_paths[] = {
        "/apex/com.android.btservices/lib64/liblhdcv5.so",
        "/data/adb/modules/lhdc_codec_old/apex_lib64/liblhdcv5.so",
        "/data/adb/modules/lhdc_codec_support/apex_lib64/liblhdcv5.so",
        "liblhdcv5.so",
        "/system/lib64/liblhdcv5.so"
    };
    for (int i = 0; i < 5; i++) {
        g_v5_dsp_lib = dlopen(dsp_paths[i], RTLD_NOW | RTLD_GLOBAL);
        if (g_v5_dsp_lib) {
            LOGI("Preloaded liblhdcv5.so from: %s", dsp_paths[i]);
            break;
        }
    }
    if (!g_v5_dsp_lib) {
        LOGW("Warning: could not preload liblhdcv5.so: %s", dlerror());
    }

    // Load liblhdcv5BT_enc.so
    const char *enc_paths[] = {
        "/apex/com.android.btservices/lib64/liblhdcv5BT_enc.so",
        "/data/adb/modules/lhdc_codec_old/apex_lib64/liblhdcv5BT_enc.so",
        "/data/adb/modules/lhdc_codec_support/apex_lib64/liblhdcv5BT_enc.so",
        "liblhdcv5BT_enc.so",
        "/system/lib64/liblhdcv5BT_enc.so"
    };

    for (int i = 0; i < 5; i++) {
        g_v5_lib = dlopen(enc_paths[i], RTLD_NOW);
        if (g_v5_lib) {
            LOGI("Loaded LHDC V5 encoder library from: %s", enc_paths[i]);
            break;
        }
    }

    if (!g_v5_lib) {
        LOGE("Failed to open liblhdcv5BT_enc.so: %s", dlerror());
        return false;
    }

    fn_lhdcv5BT_get_handle = dlsym(g_v5_lib, "lhdcv5BT_get_handle");
    fn_lhdcv5BT_free_handle = dlsym(g_v5_lib, "lhdcv5BT_free_handle");
    fn_lhdcv5BT_init_encoder = dlsym(g_v5_lib, "lhdcv5BT_init_encoder");
    fn_lhdcv5BT_get_block_Size = dlsym(g_v5_lib, "lhdcv5BT_get_block_Size");
    fn_lhdcv5BT_get_bitrate = dlsym(g_v5_lib, "lhdcv5BT_get_bitrate");
    fn_lhdcv5BT_set_bitrate = dlsym(g_v5_lib, "lhdcv5BT_set_bitrate");
    fn_lhdcv5BT_set_max_bitrate = dlsym(g_v5_lib, "lhdcv5BT_set_max_bitrate");
    fn_lhdcv5BT_adjust_bitrate = dlsym(g_v5_lib, "lhdcv5BT_adjust_bitrate");
    fn_lhdcv5BT_set_ext_func_state = dlsym(g_v5_lib, "lhdcv5BT_set_ext_func_state");
    fn_lhdcv5BT_get_user_exApiver = dlsym(g_v5_lib, "lhdcv5BT_get_user_exApiver");
    fn_lhdcv5BT_get_user_exconfig = dlsym(g_v5_lib, "lhdcv5BT_get_user_exconfig");
    fn_lhdcv5BT_set_user_exconfig = dlsym(g_v5_lib, "lhdcv5BT_set_user_exconfig");
    fn_lhdcv5BT_set_user_exdata = dlsym(g_v5_lib, "lhdcv5BT_set_user_exdata");
    fn_lhdcv5BT_encode = dlsym(g_v5_lib, "lhdcv5BT_encode");

    if (!fn_lhdcv5BT_get_handle || !fn_lhdcv5BT_init_encoder || !fn_lhdcv5BT_encode) {
        LOGE("Failed to resolve one or more LHDC V5 symbols!");
        return false;
    }

    LOGI("All LHDC V5 symbols resolved successfully!");
    return true;
}

// Global settings
static uint32_t g_sample_rate = 48000;
static uint32_t g_bits = 24;
static uint32_t g_mtu = 660;
static uint32_t g_block_size = 240;
static uint32_t g_bytes_per_frame = 1440;
static uint32_t s_target_high_bitrate = 6; // Default 500 kbps (MID - 48k/24b batched 2 frames/pkt)
static uint32_t s_last_configured_target = 6;
static uint32_t s_current_bitrate_idx = 6;
static uint32_t s_clean_queue_count = 0;
static uint32_t s_congested_count = 0;
static uint32_t s_warmup_frames = 0;
static uint32_t s_poll_ticks = 0;

#define LHDC_LIVE_TMP  "/data/misc/bluetooth/.lhdc_live.tmp"
#define LHDC_LIVE_PATH "/data/misc/bluetooth/lhdc_live.json"

static uint32_t idx_to_kbps(uint32_t idx) {
    switch (idx) {
        case 8: return 1000;
        case 7: return 900;
        case 6: return 500;
        case 5: return 400;
        case 4: return 320;
        default: return 500;
    }
}

static bool read_abr_enabled(void) {
    char abr_prop[92] = {0};
    if (__system_property_get("persist.vendor.bluetooth.lhdc_abr", abr_prop) > 0 ||
        __system_property_get("vendor.bluetooth.lhdc.abr", abr_prop) > 0) {
        if (strcmp(abr_prop, "false") == 0 || strcmp(abr_prop, "0") == 0) {
            return false;
        }
    }
    return true;
}

static void publish_live_state(HANDLE_LHDCV5_BT handle, bool active, uint32_t queue_len, bool abr_enabled, bool force) {
    static bool     s_prev_active = false;
    static uint32_t s_prev_kbps = 0;
    static uint32_t s_prev_idx = 99;
    static uint32_t s_prev_target = 99;
    static uint32_t s_prev_mtu = 0;
    static bool     s_prev_abr = true;
    static time_t   s_prev_ts = 0;

    time_t now = time(NULL);
    uint32_t neg_kbps = idx_to_kbps(s_current_bitrate_idx);
    if (active && handle && fn_lhdcv5BT_get_bitrate) {
        uint32_t br = 0;
        if (fn_lhdcv5BT_get_bitrate(handle, &br) == 0 && br > 0) {
            neg_kbps = (br >= 10000) ? (br / 1000) : br;
        }
    } else if (!active) {
        neg_kbps = 0;
    }

    bool changed = force ||
                   (active != s_prev_active) ||
                   (neg_kbps != s_prev_kbps) ||
                   (s_current_bitrate_idx != s_prev_idx) ||
                   (s_target_high_bitrate != s_prev_target) ||
                   (g_mtu != s_prev_mtu) ||
                   (abr_enabled != s_prev_abr);

    if (!changed) {
        // Rate-limit heartbeat refreshes to <= 1 Hz so audio thread does near-zero I/O
        if ((now - s_prev_ts) < 1) return;
    }

    char buf[384];
    int n = snprintf(buf, sizeof(buf),
        "{\"active\":%s,\"codec\":\"LHDC V5\",\"negotiated_bitrate_kbps\":%u,\"target_bitrate_kbps\":%u,"
        "\"negotiated_mtu\":%u,\"sample_rate\":%u,\"bits_per_sample\":%u,\"bitrate_idx\":%u,\"target_idx\":%u,"
        "\"abr_enabled\":%s,\"abr_stepped_down\":%s,\"queue_len\":%u,\"updated_at\":%lld}\n",
        active ? "true" : "false",
        neg_kbps,
        idx_to_kbps(s_target_high_bitrate),
        g_mtu,
        g_sample_rate,
        g_bits,
        s_current_bitrate_idx,
        s_target_high_bitrate,
        abr_enabled ? "true" : "false",
        (active && s_current_bitrate_idx < s_target_high_bitrate) ? "true" : "false",
        queue_len,
        (long long)now);

    if (n <= 0 || n >= (int)sizeof(buf)) return;

    int fd = open(LHDC_LIVE_TMP, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd >= 0) {
        ssize_t w = write(fd, buf, (size_t)n);
        close(fd);
        if (w == n) {
            chmod(LHDC_LIVE_TMP, 0644);
            rename(LHDC_LIVE_TMP, LHDC_LIVE_PATH);
        }
    }

    s_prev_active = active;
    s_prev_kbps = neg_kbps;
    s_prev_idx = s_current_bitrate_idx;
    s_prev_target = s_target_high_bitrate;
    s_prev_mtu = g_mtu;
    s_prev_abr = abr_enabled;
    s_prev_ts = now;
}

static uint32_t get_congestion_threshold() {
    char prop[92] = {0};
    if (__system_property_get("persist.bluetooth.lhdc_max_queue", prop) > 0) {
        int val = atoi(prop);
        if (val >= 20 && val <= 100) return (uint32_t)val;
    }
    return 80; // 80 packets (gives 40-packet safety cushion before Fluoride 120 limit)
}

__attribute__((visibility("default")))
HANDLE_LHDC_BT lhdcBT_get_handle(uint32_t version) {
    LOGI("lhdcBT_get_handle: caller requested version=%u -> bridging to V5 (version=1)", version);
    if (!init_v5_lib()) return NULL;
    HANDLE_LHDCV5_BT handle = NULL;
    int32_t ret = fn_lhdcv5BT_get_handle(1, &handle);
    LOGI("lhdcBT_get_handle: fn_lhdcv5BT_get_handle returned %d, handle=%p", ret, handle);
    if (ret != 0 || !handle) {
        LOGE("lhdcBT_get_handle failed to allocate V5 handle!");
        return NULL;
    }
    return (HANDLE_LHDC_BT)handle;
}

__attribute__((visibility("default")))
int32_t lhdcBT_free_handle(HANDLE_LHDC_BT handle) {
    LOGI("lhdcBT_free_handle: handle=%p", handle);
    publish_live_state(NULL, false, 0, read_abr_enabled(), true);
    if (!handle || !init_v5_lib()) return 0;
    return fn_lhdcv5BT_free_handle((HANDLE_LHDCV5_BT)handle);
}

static uint32_t map_v3_to_v5_bitrate(int bitrate_inx) {
    (void)bitrate_inx;
    char prop[92] = {0};
    if (__system_property_get("persist.bluetooth.lhdc_bitrate", prop) > 0) {
        if (strcmp(prop, "1000") == 0) return 8;
        if (strcmp(prop, "900") == 0) return 7;
        if (strcmp(prop, "500") == 0) return 6;
    }
    return 6; // Default 500 kbps (MID - 2 frames/pkt)
}

__attribute__((visibility("default")))
int32_t lhdcBT_get_bitrate(HANDLE_LHDC_BT handle) {
    if (!handle || !init_v5_lib()) return (s_current_bitrate_idx == 6) ? 500 : 900;
    uint32_t br = 900000;
    if (fn_lhdcv5BT_get_bitrate) {
        fn_lhdcv5BT_get_bitrate((HANDLE_LHDCV5_BT)handle, &br);
    }
    return (int32_t)(br / 1000);
}

__attribute__((visibility("default")))
int32_t lhdcBT_set_bitrate(HANDLE_LHDC_BT handle, int bitrate_inx) {
    LOGI("lhdcBT_set_bitrate: caller requested index=%d", bitrate_inx);
    if (!handle || !init_v5_lib()) return -1;

    uint32_t v5_br = map_v3_to_v5_bitrate(bitrate_inx);
    s_last_configured_target = v5_br;
    s_target_high_bitrate = v5_br;
    s_current_bitrate_idx = v5_br;
    s_clean_queue_count = 0;
    s_congested_count = 0;
    s_warmup_frames = 0;

    if (fn_lhdcv5BT_set_max_bitrate) {
        fn_lhdcv5BT_set_max_bitrate((HANDLE_LHDCV5_BT)handle, v5_br);
    }
    int32_t ret = fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, v5_br);
    LOGI("lhdcBT_set_bitrate: set V5 target index %u -> ret=%d", v5_br, ret);
    publish_live_state((HANDLE_LHDCV5_BT)handle, true, 0, read_abr_enabled(), true);
    return ret;
}

__attribute__((visibility("default")))
int32_t lhdcBT_set_max_bitrate(HANDLE_LHDC_BT handle, uint32_t max_bitrate_inx) {
    LOGI("lhdcBT_set_max_bitrate: caller requested max=%u", max_bitrate_inx);
    if (!handle || !init_v5_lib()) return -1;

    uint32_t max_br = map_v3_to_v5_bitrate((int)max_bitrate_inx);
    s_last_configured_target = max_br;
    s_target_high_bitrate = max_br;
    s_current_bitrate_idx = max_br;
    s_clean_queue_count = 0;
    s_congested_count = 0;

    if (fn_lhdcv5BT_set_max_bitrate) {
        fn_lhdcv5BT_set_max_bitrate((HANDLE_LHDCV5_BT)handle, max_br);
    }
    int32_t ret = fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, max_br);
    publish_live_state((HANDLE_LHDCV5_BT)handle, true, 0, read_abr_enabled(), true);
    return ret;
}

static bool     s_abr_enabled = true;
static uint32_t s_last_queue_len = 0;

static bool sync_target_and_abr(HANDLE_LHDCV5_BT handle, uint32_t queue_len) {
    bool prev_abr = s_abr_enabled;
    s_abr_enabled = read_abr_enabled();
    uint32_t new_target = map_v3_to_v5_bitrate(0);

    if (new_target != s_last_configured_target ||
        (!s_abr_enabled && s_current_bitrate_idx != new_target)) {
        LOGI("sync_target_and_abr: target/abr update: target %u -> %u (cur=%u, abr=%d)",
             s_last_configured_target, new_target, s_current_bitrate_idx, s_abr_enabled ? 1 : 0);
        s_last_configured_target = new_target;
        s_target_high_bitrate = new_target;
        s_current_bitrate_idx = new_target;
        if (fn_lhdcv5BT_set_max_bitrate) {
            fn_lhdcv5BT_set_max_bitrate(handle, new_target);
        }
        if (fn_lhdcv5BT_set_bitrate) {
            fn_lhdcv5BT_set_bitrate(handle, new_target);
        }
        s_clean_queue_count = 0;
        s_congested_count = 0;
        publish_live_state(handle, true, queue_len, s_abr_enabled, true);
        return true;
    }

    if (s_abr_enabled != prev_abr) {
        LOGI("sync_target_and_abr: ABR toggled -> %s", s_abr_enabled ? "ENABLED" : "DISABLED");
        publish_live_state(handle, true, queue_len, s_abr_enabled, true);
    }
    return false;
}

__attribute__((visibility("default")))
int32_t lhdcBT_adjust_bitrate(HANDLE_LHDC_BT handle, uint32_t queueLen) {
    if (!handle || !init_v5_lib()) return -1;

    s_last_queue_len = queueLen;
    s_poll_ticks++;

    // Poll user target bitrate & ABR flag on first tick and every 20 ticks (~100ms)
    if (s_poll_ticks == 1 || (s_poll_ticks % 20) == 0) {
        if (sync_target_and_abr((HANDLE_LHDCV5_BT)handle, queueLen)) {
            return 0;
        }
    }

    // Skip ABR congestion downscaling during initial connection warmup (2000 frames ~ 10 sec)
    if (s_warmup_frames < 2000) {
        s_warmup_frames++;
        if ((s_poll_ticks % 200) == 0) {
            publish_live_state((HANDLE_LHDCV5_BT)handle, true, queueLen, s_abr_enabled, false);
        }
        return 0;
    }

    uint32_t threshold = get_congestion_threshold();
    bool state_changed = false;

    if (s_abr_enabled && queueLen > threshold) {
        s_congested_count++;
        // 5 consecutive congested frames to filter transient radio multiplexing spikes
        if (s_congested_count >= 5) {
            if (s_current_bitrate_idx > 6) {
                LOGW("lhdcBT_adjust_bitrate: queue congested (len=%u > %u) -> ABR stepping down index %u -> 6 (500k)",
                     queueLen, threshold, s_current_bitrate_idx);
                s_current_bitrate_idx = 6;
                if (fn_lhdcv5BT_set_bitrate) {
                    fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, 6);
                }
                state_changed = true;
            } else if (queueLen > 110 && s_current_bitrate_idx > 4) {
                LOGW("lhdcBT_adjust_bitrate: severe queue congestion (len=%u > 110) -> emergency downscale to index 4",
                     queueLen);
                s_current_bitrate_idx = 4;
                if (fn_lhdcv5BT_set_bitrate) {
                    fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, 4);
                }
                state_changed = true;
            }
            s_clean_queue_count = 0;
        }
    } else {
        s_congested_count = 0;
        if (queueLen <= 50) {
            s_clean_queue_count++;

            // ABR step-up recovery:
            // When link stays healthy for 300 frames (~1.5s), restore target bitrate
            if (s_abr_enabled && s_current_bitrate_idx < s_target_high_bitrate && s_clean_queue_count >= 300) {
                LOGI("lhdcBT_adjust_bitrate: queue clean for %u frames -> ABR restoring to target index %u",
                     s_clean_queue_count, s_target_high_bitrate);
                s_current_bitrate_idx = s_target_high_bitrate;
                if (fn_lhdcv5BT_set_bitrate) {
                    fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, s_target_high_bitrate);
                }
                s_clean_queue_count = 0;
                state_changed = true;
            }
        }
    }

    if (state_changed || (s_poll_ticks % 200) == 0) {
        publish_live_state((HANDLE_LHDCV5_BT)handle, true, queueLen, s_abr_enabled, state_changed);
    }
    return 0;
}

__attribute__((visibility("default")))
int32_t lhdcBT_init_encoder(HANDLE_LHDC_BT handle, uint32_t sample_rate, uint32_t bits_per_sample,
                            uint32_t bitrate_inx, uint32_t arg4, uint32_t arg5,
                            uint32_t arg6, uint32_t arg7) {
    uint32_t mtu = 665;
    uint32_t interval = 20;

    if (arg6 >= 300) {
        mtu = arg6;
        interval = arg7;
    } else if (arg4 >= 300) {
        mtu = arg4;
        interval = arg5;
    }

    LOGI("lhdcBT_init_encoder: sr=%u, bits=%u, br_inx=%u, mtu=%u, interval=%u", 
         sample_rate, bits_per_sample, bitrate_inx, mtu, interval);
    if (!handle || !init_v5_lib()) return -1;

    if (sample_rate != 44100 && sample_rate != 48000 && sample_rate != 96000) {
        LOGW("Non-standard sample_rate=%u, defaulting to 48000", sample_rate);
        sample_rate = 48000;
    }
    if (bits_per_sample != 16 && bits_per_sample != 24) {
        LOGW("Non-standard bits=%u, defaulting to 24", bits_per_sample);
        bits_per_sample = 24;
    }

    g_sample_rate = sample_rate;
    g_bits = bits_per_sample;

    uint32_t v5_br = map_v3_to_v5_bitrate((int)bitrate_inx);
    s_last_configured_target = v5_br;
    s_target_high_bitrate = v5_br;
    s_current_bitrate_idx = v5_br;
    s_clean_queue_count = 0;
    s_congested_count = 0;
    s_warmup_frames = 0;

    // MTU Clamping:
    // If target bitrate is 1000 kbps (v5_br == 8), 1 frame is ~628 bytes.
    // MTU must be at least 660 to fit 1 frame without overflow.
    // At MTU 660, 628 bytes is strictly 1 frame per packet (0 batching)!
    // If target bitrate is 900 kbps (564 bytes) or 500 kbps (314 bytes), MTU is clamped to 600
    // so both remain strictly single-frame unbatched (0 batching).
    char mtu_prop[92] = {0};
    if (__system_property_get("persist.bluetooth.lhdc_mtu", mtu_prop) > 0) {
        int custom_mtu = atoi(mtu_prop);
        if (custom_mtu >= 300 && custom_mtu <= 1000) {
            g_mtu = (uint32_t)custom_mtu;
        } else {
            g_mtu = 660;
        }
    } else {
        g_mtu = 660;
    }

    // Physical constraint safety guard:
    // At 1000 kbps (v5_br == 8), a single LHDC frame is exactly 626 bytes.
    // If MTU is configured < 660 (e.g. 600), the frame cannot fit in 1 packet and
    // lhdcv5BT_encode will fail with ret=-10 (written=0, dropping all audio silently).
    // Automatically clamp to 660 to ensure zero-loss unbatched delivery.
    if (v5_br == 8 && g_mtu < 660) {
        LOGW("Target is 1000 kbps (626B frame) but MTU=%u (< 660). Clamping MTU to 660 to prevent silent -10 drops!", g_mtu);
        g_mtu = 660;
    }

    uint32_t v5_interval = 20;
    if (interval == 10) v5_interval = 10;

    int32_t ret = fn_lhdcv5BT_init_encoder((HANDLE_LHDCV5_BT)handle, sample_rate, bits_per_sample, v5_br, g_mtu, v5_interval, 0);
    LOGI("lhdcv5BT_init_encoder returned %d (v5_br=%u, mtu=%u, interval=%u)", ret, v5_br, g_mtu, v5_interval);

    if (fn_lhdcv5BT_set_max_bitrate) {
        fn_lhdcv5BT_set_max_bitrate((HANDLE_LHDCV5_BT)handle, v5_br);
    }
    if (fn_lhdcv5BT_set_bitrate) {
        fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, v5_br);
    }

    uint32_t samples = 0;
    fn_lhdcv5BT_get_block_Size((HANDLE_LHDCV5_BT)handle, &samples);
    g_block_size = samples ? samples : (sample_rate >= 96000 ? 480 : 240);

    uint32_t bytes_per_sample = (bits_per_sample / 8) * 2;
    g_bytes_per_frame = g_block_size * bytes_per_sample;
    LOGI("init_encoder config: block_size=%u, bytes_per_frame=%u", g_block_size, g_bytes_per_frame);
    s_poll_ticks = 0;
    publish_live_state((HANDLE_LHDCV5_BT)handle, true, 0, read_abr_enabled(), true);

    return ret;
}

__attribute__((visibility("default")))
int lhdcBT_get_block_Size(HANDLE_LHDC_BT handle) {
    if (!handle || !init_v5_lib()) return (int)g_block_size;
    uint32_t samples = 0;
    fn_lhdcv5BT_get_block_Size((HANDLE_LHDCV5_BT)handle, &samples);
    if (samples) g_block_size = samples;
    return (int)g_block_size;
}

__attribute__((visibility("default")))
int32_t lhdcBT_set_ext_func_state(HANDLE_LHDC_BT handle, int field, bool enabled, void *priv, uint32_t len) {
    if (!handle || !init_v5_lib()) return -1;
    return fn_lhdcv5BT_set_ext_func_state((HANDLE_LHDCV5_BT)handle, field, enabled, priv, len);
}

__attribute__((visibility("default")))
int32_t lhdcBT_set_hasMinBitrateLimit(HANDLE_LHDC_BT handle, int value) {
    (void)handle;
    (void)value;
    return 0;
}

__attribute__((visibility("default")))
int32_t lhdcBT_get_user_exApiver(HANDLE_LHDC_BT handle, char *userConfig, int clen) {
    if (!handle || !init_v5_lib() || !fn_lhdcv5BT_get_user_exApiver) return -1;
    return fn_lhdcv5BT_get_user_exApiver((HANDLE_LHDCV5_BT)handle, userConfig, clen);
}

__attribute__((visibility("default")))
int32_t lhdcBT_get_user_exconfig(HANDLE_LHDC_BT handle, char *userConfig, int clen) {
    if (!handle || !init_v5_lib() || !fn_lhdcv5BT_get_user_exconfig) return -1;
    return fn_lhdcv5BT_get_user_exconfig((HANDLE_LHDCV5_BT)handle, userConfig, clen);
}

__attribute__((visibility("default")))
int32_t lhdcBT_set_user_exconfig(HANDLE_LHDC_BT handle, const char *userConfig, const int clen) {
    if (!handle || !init_v5_lib() || !fn_lhdcv5BT_set_user_exconfig) return -1;
    return fn_lhdcv5BT_set_user_exconfig((HANDLE_LHDCV5_BT)handle, userConfig, clen);
}

__attribute__((visibility("default")))
void lhdcBT_set_user_exdata(HANDLE_LHDC_BT handle, const char *userConfig, const int clen) {
    if (!handle || !init_v5_lib() || !fn_lhdcv5BT_set_user_exdata) return;
    fn_lhdcv5BT_set_user_exdata((HANDLE_LHDCV5_BT)handle, userConfig, clen);
}

int lhdcBT_encodeV3(HANDLE_LHDC_BT handle, void* p_pcm, unsigned char* out_put, uint32_t * written, uint32_t * out_frames);

__attribute__((visibility("default")))
int lhdcBT_encode(HANDLE_LHDC_BT handle, void* p_pcm, unsigned char* p_stream) {
    uint32_t written = 0, out_frames = 0;
    lhdcBT_encodeV3(handle, p_pcm, p_stream, &written, &out_frames);
    return (int)written;
}

__attribute__((visibility("default")))
int lhdcBT_encodeV3(HANDLE_LHDC_BT handle, void* p_pcm, unsigned char* out_put, uint32_t * written, uint32_t * out_frames) {
    if (!handle || !p_pcm || !out_put || !written || !out_frames) {
        LOGE("lhdcBT_encodeV3: invalid null param");
        return -1;
    }
    if (!init_v5_lib()) {
        *written = 0;
        *out_frames = 0;
        return 0;
    }

    static uint32_t s_encode_count = 0;
    s_encode_count++;
    if (s_encode_count == 1 || (s_encode_count % 20) == 0) {
        sync_target_and_abr((HANDLE_LHDCV5_BT)handle, s_last_queue_len);
    }
    publish_live_state((HANDLE_LHDCV5_BT)handle, true, s_last_queue_len, s_abr_enabled, false);

    uint32_t pcm_bytes = g_bytes_per_frame;
    uint32_t out_buf_size = 1024;

    int32_t ret = fn_lhdcv5BT_encode((HANDLE_LHDCV5_BT)handle, p_pcm, pcm_bytes, out_put, out_buf_size, written, out_frames);
    if (ret != 0) {
        LOGW("lhdcv5BT_encode ret=%d", ret);
        *written = 0;
        *out_frames = 0;
        return 0;
    }

    if (s_encode_count % 100 == 1) {
        LOGI("lhdcBT_encodeV3: frame #%u encoded, written=%u bytes, out_frames=%u (br_idx=%u)",
             s_encode_count, *written, *out_frames, s_current_bitrate_idx);
    }

    return 0;
}
