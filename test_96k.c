#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <dlfcn.h>

int main() {
    void *h = dlopen("/system/lib64/liblhdcv5BT_enc.so", RTLD_NOW);
    if (!h) {
        printf("dlopen failed: %s\n", dlerror());
        return 1;
    }

    int32_t (*get_handle)(uint32_t ver, void **handle) = dlsym(h, "lhdcv5BT_get_handle");
    int32_t (*init_enc)(void *handle, uint32_t sample_rate, uint32_t bits, uint32_t bitrate_inx, uint32_t mtu, uint32_t interval, uint32_t lossless) = dlsym(h, "lhdcv5BT_init_encoder");
    int32_t (*get_block_size)(void *handle, uint32_t *samples) = dlsym(h, "lhdcv5BT_get_block_Size");
    int32_t (*encode)(void *handle, void *pcm, uint32_t pcm_bytes, uint8_t *out, uint32_t out_bytes, uint32_t *p_out_bytes, uint32_t *p_out_frames) = dlsym(h, "lhdcv5BT_encode");

    void *handle = NULL;
    get_handle(1, &handle);
    int r = init_enc(handle, 96000, 24, 9, 660, 10, 0);
    printf("init_enc 96000 returned %d\n", r);

    uint32_t block_size = 0;
    get_block_size(handle, &block_size);
    printf("block_size = %u samples\n", block_size);

    uint32_t pcm_len = 2 * block_size * 2 * 3;
    uint8_t *pcm = calloc(1, pcm_len);

    uint8_t out[1024];
    for (int iter = 0; iter < 5; iter++) {
        uint32_t written = 0, out_frames = 0;
        int ret = encode(handle, pcm, pcm_len, out, sizeof(out), &written, &out_frames);
        printf("Call %d (in %u bytes PCM): ret=%d, written=%u bytes, out_frames=%u\n", iter, pcm_len, ret, written, out_frames);
    }

    return 0;
}
