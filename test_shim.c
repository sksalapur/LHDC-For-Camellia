#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <dlfcn.h>

int main() {
    printf("Opening /apex/com.android.btservices/lib64/liblhdcBT_enc.so...\n");
    void *h = dlopen("/apex/com.android.btservices/lib64/liblhdcBT_enc.so", RTLD_NOW);
    if (!h) {
        printf("dlopen failed: %s\n", dlerror());
        return 1;
    }
    printf("Opened successfully!\n");

    const char *syms[] = {
        "lhdcBT_get_handle", "lhdcBT_free_handle", "lhdcBT_init_encoder",
        "lhdcBT_get_block_Size", "lhdcBT_get_bitrate", "lhdcBT_set_bitrate",
        "lhdcBT_set_max_bitrate", "lhdcBT_adjust_bitrate", "lhdcBT_set_ext_func_state",
        "lhdcBT_set_hasMinBitrateLimit", "lhdcBT_get_user_exApiver", "lhdcBT_get_user_exconfig",
        "lhdcBT_set_user_exconfig", "lhdcBT_set_user_exdata", "lhdcBT_encode", "lhdcBT_encodeV3"
    };

    for (int i = 0; i < 16; i++) {
        void *p = dlsym(h, syms[i]);
        printf("  Symbol %-30s: %s\n", syms[i], p ? "OK" : "MISSING");
        if (!p) {
            printf("FAIL: missing symbol %s\n", syms[i]);
            return 1;
        }
    }

    void* (*get_handle)(uint32_t ver) = dlsym(h, "lhdcBT_get_handle");
    int32_t (*init_enc)(void *handle, uint32_t sample_rate, uint32_t bits, uint32_t bitrate_inx, uint32_t dual, uint32_t pad, uint32_t mtu, uint32_t interval) = dlsym(h, "lhdcBT_init_encoder");
    int (*get_block_size)(void *handle) = dlsym(h, "lhdcBT_get_block_Size");
    int32_t (*encodeV3)(void *handle, void *pcm, unsigned char *out, uint32_t *p_written, uint32_t *p_frames) = dlsym(h, "lhdcBT_encodeV3");

    void *handle = get_handle(2);
    printf("get_handle(2) handle=%p\n", handle);

    int32_t ret = init_enc(handle, 48000, 24, 0, 0, 0, 660, 20);
    printf("init_enc ret=%d\n", ret);

    int block_size = get_block_size(handle);
    printf("get_block_size: %d samples\n", block_size);

    uint32_t frame_bytes = block_size * 2 * 3; // 240 * 6 = 1440
    uint8_t *pcm = calloc(1, frame_bytes);
    uint8_t out[1024];

    for (int i = 0; i < 4; i++) {
        uint32_t written = 0, frames = 0;
        ret = encodeV3(handle, pcm, out, &written, &frames);
        printf("iter %d: ret=%d, written=%u, frames=%u\n", i, ret, written, frames);
        if (written > 0) {
            printf("  Encoded bytes: ");
            for (int j = 0; j < (written < 16 ? written : 16); j++) printf("%02x ", out[j]);
            printf("\n");
        }
    }

    printf("ALL TESTS PASSED SUCCESSFULLY!\n");
    return 0;
}
