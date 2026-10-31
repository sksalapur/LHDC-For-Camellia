#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <dlfcn.h>

int main() {
    void *h = dlopen("/system/lib64/liblhdcv5BT_enc.so", RTLD_NOW);
    if (!h) { printf("dlopen failed: %s\n", dlerror()); return 1; }
    int32_t (*get_handle)(uint32_t ver, void **handle) = dlsym(h, "lhdcv5BT_get_handle");
    int32_t (*init_enc)(void *handle, uint32_t sample_rate, uint32_t bits, uint32_t bitrate_inx, uint32_t mtu, uint32_t interval, uint32_t lossless) = dlsym(h, "lhdcv5BT_init_encoder");
    int32_t (*get_block_size)(void *handle, uint32_t *samples) = dlsym(h, "lhdcv5BT_get_block_Size");
    int32_t (*encode)(void *handle, void *pcm, uint32_t pcm_bytes, uint8_t *out, uint32_t out_bytes, uint32_t *p_out_bytes, uint32_t *p_out_frames) = dlsym(h, "lhdcv5BT_encode");

    void *handle = NULL;
    get_handle(1, &handle);
    uint32_t samples = 0;

    printf("=== Interval 10ms, 1440 bytes ===\n");
    init_enc(handle, 48000, 24, 9, 660, 10, 0);
    get_block_size(handle, &samples);
    printf("block_size=%u\n", samples);
    uint8_t pcm1[1440] = {0};
    uint8_t out[1024];
    for (int i = 0; i < 6; i++) {
        uint32_t written = 0, out_frames = 0;
        int r = encode(handle, pcm1, 1440, out, sizeof(out), &written, &out_frames);
        printf("Iter %d: ret=%d, written=%u, out_frames=%u\n", i, r, written, out_frames);
    }

    printf("=== Interval 5ms, 1440 bytes ===\n");
    init_enc(handle, 48000, 24, 9, 660, 5, 0);
    for (int i = 0; i < 4; i++) {
        uint32_t written = 0, out_frames = 0;
        int r = encode(handle, pcm1, 1440, out, sizeof(out), &written, &out_frames);
        printf("Iter %d: ret=%d, written=%u, out_frames=%u\n", i, r, written, out_frames);
    }

    printf("=== Interval 20ms, 1440 bytes ===\n");
    init_enc(handle, 48000, 24, 9, 660, 20, 0);
    for (int i = 0; i < 8; i++) {
        uint32_t written = 0, out_frames = 0;
        int r = encode(handle, pcm1, 1440, out, sizeof(out), &written, &out_frames);
        printf("Iter %d: ret=%d, written=%u, out_frames=%u\n", i, r, written, out_frames);
    }
    return 0;
}
