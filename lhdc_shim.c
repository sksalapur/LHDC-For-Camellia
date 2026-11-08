#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <dlfcn.h>
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
static uint32_t g_sample_rate = 96000;
static uint32_t g_bits = 24;
static uint32_t g_mtu = 600;
static uint32_t g_block_size = 480;
static uint32_t g_bytes_per_frame = 2880;
static uint32_t s_target_high_bitrate = 7; // Default 900 kbps (HIGH)
static uint32_t s_current_bitrate_idx = 7;
static uint32_t s_clean_queue_count = 0;

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
    if (!handle || !init_v5_lib()) return 0;
    return fn_lhdcv5BT_free_handle((HANDLE_LHDCV5_BT)handle);
}

#include <sys/system_properties.h>

static uint32_t map_v3_to_v5_bitrate(int bitrate_inx) {
    char prop[92] = {0};
    if (__system_property_get("persist.bluetooth.lhdc_bitrate", prop) > 0) {
        if (strcmp(prop, "1000") == 0) return 8;
        if (strcmp(prop, "900") == 0) return 7;
        if (strcmp(prop, "500") == 0) return 6;
    }
    if (bitrate_inx == 1 || bitrate_inx == 5 || bitrate_inx == 6) return 6;
    return 7; // Default 900 kbps
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
    s_target_high_bitrate = v5_br;
    s_current_bitrate_idx = v5_br;
    s_clean_queue_count = 0;

    if (fn_lhdcv5BT_set_max_bitrate) {
        fn_lhdcv5BT_set_max_bitrate((HANDLE_LHDCV5_BT)handle, v5_br);
    }
    int32_t ret = fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, v5_br);
    LOGI("lhdcBT_set_bitrate: set V5 target index %u -> ret=%d", v5_br, ret);
    return ret;
}

__attribute__((visibility("default")))
int32_t lhdcBT_set_max_bitrate(HANDLE_LHDC_BT handle, uint32_t max_bitrate_inx) {
    LOGI("lhdcBT_set_max_bitrate: caller requested max=%u", max_bitrate_inx);
    if (!handle || !init_v5_lib()) return -1;

    uint32_t max_br = map_v3_to_v5_bitrate((int)max_bitrate_inx);
    s_target_high_bitrate = max_br;
    s_current_bitrate_idx = max_br;
    s_clean_queue_count = 0;

    if (fn_lhdcv5BT_set_max_bitrate) {
        fn_lhdcv5BT_set_max_bitrate((HANDLE_LHDCV5_BT)handle, max_br);
    }
    return fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, max_br);
}

__attribute__((visibility("default")))
int32_t lhdcBT_adjust_bitrate(HANDLE_LHDC_BT handle, uint32_t queueLen) {
    if (!handle || !init_v5_lib()) return -1;

    // Dynamic queue congestion relief:
    // If Fluoride queue reaches > 3 (e.g. during AVRCP volume event or RF retransmission),
    // immediately downscale to 500 kbps (index 6, 314 bytes/frame) to drain the queue in <20ms
    // and permanently prevent the 28-packet overflow limit from dropping packets.
    if (queueLen > 3) {
        if (s_current_bitrate_idx != 6) {
            LOGW("lhdcBT_adjust_bitrate: queue congested (len=%u) -> downscaling to 500 kbps", queueLen);
            s_current_bitrate_idx = 6;
            if (fn_lhdcv5BT_set_bitrate) {
                fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, 6);
            }
        }
        s_clean_queue_count = 0;
    } else if (queueLen == 0) {
        s_clean_queue_count++;
        // When queue has stayed completely clear for 100 consecutive frames (~2 seconds),
        // restore target high bitrate if allowed by system property.
        if (s_clean_queue_count >= 100 && s_current_bitrate_idx != s_target_high_bitrate) {
            uint32_t allowed_target = map_v3_to_v5_bitrate(0);
            if (allowed_target == 6) {
                s_target_high_bitrate = 6;
                s_current_bitrate_idx = 6;
                return 0;
            }
            LOGI("lhdcBT_adjust_bitrate: queue cleared -> recovering to %u kbps", (s_target_high_bitrate == 7) ? 900 : 1000);
            s_current_bitrate_idx = s_target_high_bitrate;
            if (fn_lhdcv5BT_set_bitrate) {
                fn_lhdcv5BT_set_bitrate((HANDLE_LHDCV5_BT)handle, s_target_high_bitrate);
            }
            s_clean_queue_count = 0;
        }
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
        LOGW("Non-standard sample_rate=%u, defaulting to 96000", sample_rate);
        sample_rate = 96000;
    }
    if (bits_per_sample != 16 && bits_per_sample != 24) {
        LOGW("Non-standard bits=%u, defaulting to 24", bits_per_sample);
        bits_per_sample = 24;
    }

    g_sample_rate = sample_rate;
    g_bits = bits_per_sample;
    // Critical: Clamp encoder MTU to 600 bytes.
    // At 600 bytes MTU:
    // - 900 kbps produces 564 bytes/frame. 2 * 564 = 1128 > 600 -> exactly 1 frame per packet (0 batching).
    // - 500 kbps produces 314 bytes/frame. 2 * 314 = 628 > 600 -> exactly 1 frame per packet (0 batching).
    // Neither rate batches subframes into packets! 100% of calls produce written > 0 (1 frame).
    // This permanently prevents receiver buffer starvation and eliminates diaphragm plastic movement noise.
    g_mtu = 600;

    uint32_t v5_br = map_v3_to_v5_bitrate((int)bitrate_inx);
    s_target_high_bitrate = v5_br;
    s_current_bitrate_idx = v5_br;
    s_clean_queue_count = 0;

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

    uint32_t pcm_bytes = g_bytes_per_frame;
    uint32_t out_buf_size = 1024;

    int32_t ret = fn_lhdcv5BT_encode((HANDLE_LHDCV5_BT)handle, p_pcm, pcm_bytes, out_put, out_buf_size, written, out_frames);
    if (ret != 0) {
        LOGW("lhdcv5BT_encode ret=%d", ret);
        *written = 0;
        *out_frames = 0;
        return 0;
    }

    static uint32_t s_encode_count = 0;
    s_encode_count++;
    if (s_encode_count % 100 == 1) {
        LOGI("lhdcBT_encodeV3: frame #%u encoded, written=%u bytes, out_frames=%u (br_idx=%u)",
             s_encode_count, *written, *out_frames, s_current_bitrate_idx);
    }

    return 0;
}
