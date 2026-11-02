#include "delta_ota.h"
#include "tinf.h"
#include <esp_heap_caps.h>
#include <mbedtls/sha256.h>

DeltaOTA deltaOTA;

static void* safe_alloc(size_t size) {
    void* ptr = heap_caps_malloc(size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    if (!ptr) {
        ptr = malloc(size);
    }
    return ptr;
}

static void safe_free(void* ptr) {
    if (ptr) {
        free(ptr);
    }
}

static int64_t cp_offtin(const uint8_t *buf) {
    int64_t y = buf[7] & 0x7F;
    for (int i = 6; i >= 0; i--) {
        y = y * 256 + buf[i];
    }
    if (buf[7] & 0x80) y = -y;
    return y;
}

DeltaOTA::DeltaOTA() : 
    _status(DeltaStatus::IDLE),
    _progress(0),
    _expectedSize(0),
    _receivedBytes(0),
    _patchBuffer(nullptr)
{
    memset(_lastError, 0, sizeof(_lastError));
}

DeltaOTA::~DeltaOTA() {
    reset();
}

void DeltaOTA::reset() {
    if (_patchBuffer) {
        safe_free(_patchBuffer);
        _patchBuffer = nullptr;
    }
    _status = DeltaStatus::IDLE;
    _progress = 0;
    _expectedSize = 0;
    _receivedBytes = 0;
    memset(_lastError, 0, sizeof(_lastError));
}

bool DeltaOTA::begin(uint32_t expectedPatchSize) {
    reset();
    
    if (expectedPatchSize < DELTA_HEADER_SIZE || expectedPatchSize > (1024 * 1024)) {
        snprintf(_lastError, sizeof(_lastError), "Invalid patch size: %u", expectedPatchSize);
        _status = DeltaStatus::ERROR_HEADER;
        return false;
    }

    _patchBuffer = (uint8_t*)safe_alloc(expectedPatchSize);
    if (!_patchBuffer) {
        snprintf(_lastError, sizeof(_lastError), "PSRAM alloc failed for %u bytes", expectedPatchSize);
        _status = DeltaStatus::ERROR_MEMORY;
        return false;
    }

    _expectedSize = expectedPatchSize;
    _receivedBytes = 0;
    _status = DeltaStatus::RECEIVING;
    _progress = 0;
    Serial.printf("[DELTA] OTA Initialized. Allocated %u bytes in PSRAM.\n", expectedPatchSize);
    return true;
}

bool DeltaOTA::writeChunk(uint32_t offset, const uint8_t* data, size_t len) {
    if (_status != DeltaStatus::RECEIVING || !_patchBuffer) {
        snprintf(_lastError, sizeof(_lastError), "Not in RECEIVING state");
        return false;
    }

    if (offset + len > _expectedSize) {
        snprintf(_lastError, sizeof(_lastError), "Chunk overflow: %u + %u > %u", offset, (uint32_t)len, _expectedSize);
        return false;
    }

    memcpy(_patchBuffer + offset, data, len);
    _receivedBytes = max(_receivedBytes, offset + (uint32_t)len);
    _progress = (uint8_t)((_receivedBytes * 100ULL) / _expectedSize);

    if (_receivedBytes >= _expectedSize) {
        _status = DeltaStatus::RECEIVED_ALL;
        Serial.printf("[DELTA] All %u bytes received successfully! Ready to apply.\n", _expectedSize);
    }

    return true;
}

bool DeltaOTA::applyPatch() {
    if (!_patchBuffer || _receivedBytes < DELTA_HEADER_SIZE) {
        snprintf(_lastError, sizeof(_lastError), "No patch data available");
        _status = DeltaStatus::ERROR_HEADER;
        return false;
    }

    // 1. Validate Header
    const AquaDeltaHeader* hdr = (const AquaDeltaHeader*)_patchBuffer;
    if (memcmp(hdr->magic, DELTA_OTA_MAGIC, 8) != 0 || hdr->version != 1) {
        snprintf(_lastError, sizeof(_lastError), "Invalid AquaDelta header magic/version");
        _status = DeltaStatus::ERROR_HEADER;
        return false;
    }

    Serial.printf("[DELTA] Valid Header: OldSize=%u, NewSize=%u, DiffComp=%u, DiffRaw=%u\n",
                  hdr->oldSize, hdr->newSize, hdr->diffCompLen, hdr->diffRawLen);

    // 2. Locate active partition
    const esp_partition_t* running = esp_ota_get_running_partition();
    if (!running) {
        snprintf(_lastError, sizeof(_lastError), "Cannot find running partition");
        _status = DeltaStatus::ERROR_FLASH;
        return false;
    }

    Serial.printf("[DELTA] Running partition: %s (addr: 0x%06X, size: 0x%06X)\n",
                  running->label, running->address, running->size);

    if (hdr->oldSize > running->size) {
        snprintf(_lastError, sizeof(_lastError), "Old size %u exceeds partition %u", hdr->oldSize, running->size);
        _status = DeltaStatus::ERROR_HEADER;
        return false;
    }

    // 3. Allocate PSRAM buffers
    _status = DeltaStatus::DECOMPRESSING;
    Serial.println("[DELTA] Allocating PSRAM buffers for decompression & reconstruction...");

    uint8_t* old_buf = (uint8_t*)safe_alloc(hdr->oldSize);
    uint8_t* ctrl_raw = (uint8_t*)safe_alloc(hdr->ctrlRawLen);
    uint8_t* diff_raw = (uint8_t*)safe_alloc(hdr->diffRawLen);
    uint8_t* extra_raw = (uint8_t*)safe_alloc(hdr->extraRawLen);
    uint8_t* reconstructed = (uint8_t*)safe_alloc(hdr->newSize);

    if (!old_buf || !ctrl_raw || !diff_raw || !extra_raw || !reconstructed) {
        safe_free(old_buf);
        safe_free(ctrl_raw);
        safe_free(diff_raw);
        safe_free(extra_raw);
        safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "Failed allocating PSRAM buffers");
        _status = DeltaStatus::ERROR_MEMORY;
        return false;
    }

    // 4. Read old firmware from flash
    esp_err_t err = esp_partition_read(running, 0, old_buf, hdr->oldSize);
    if (err != ESP_OK) {
        safe_free(old_buf);
        safe_free(ctrl_raw);
        safe_free(diff_raw);
        safe_free(extra_raw);
        safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "Failed reading running partition (err: %d)", err);
        _status = DeltaStatus::ERROR_FLASH;
        return false;
    }

    // 5. Decompress streams with tinf
    const uint8_t* stream_ptr = _patchBuffer + DELTA_HEADER_SIZE;
    
    unsigned int ctrl_out_len = hdr->ctrlRawLen;
    int t_res = tinf_zlib_uncompress(ctrl_raw, &ctrl_out_len, stream_ptr, hdr->ctrlCompLen);
    if (t_res != TINF_OK || ctrl_out_len != hdr->ctrlRawLen) {
        safe_free(old_buf); safe_free(ctrl_raw); safe_free(diff_raw); safe_free(extra_raw); safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "Ctrl decompress failed (tinf: %d)", t_res);
        _status = DeltaStatus::ERROR_DECOMPRESS;
        return false;
    }
    stream_ptr += hdr->ctrlCompLen;

    unsigned int diff_out_len = hdr->diffRawLen;
    t_res = tinf_zlib_uncompress(diff_raw, &diff_out_len, stream_ptr, hdr->diffCompLen);
    if (t_res != TINF_OK || diff_out_len != hdr->diffRawLen) {
        safe_free(old_buf); safe_free(ctrl_raw); safe_free(diff_raw); safe_free(extra_raw); safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "Diff decompress failed (tinf: %d)", t_res);
        _status = DeltaStatus::ERROR_DECOMPRESS;
        return false;
    }
    stream_ptr += hdr->diffCompLen;

    unsigned int extra_out_len = hdr->extraRawLen;
    t_res = tinf_zlib_uncompress(extra_raw, &extra_out_len, stream_ptr, hdr->extraCompLen);
    if (t_res != TINF_OK || extra_out_len != hdr->extraRawLen) {
        safe_free(old_buf); safe_free(ctrl_raw); safe_free(diff_raw); safe_free(extra_raw); safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "Extra decompress failed (tinf: %d)", t_res);
        _status = DeltaStatus::ERROR_DECOMPRESS;
        return false;
    }

    Serial.println("[DELTA] Streams decompressed successfully!");

    // 6. Execute binary differential reconstruction
    _status = DeltaStatus::RECONSTRUCTING;
    Serial.println("[DELTA] Reconstructing target binary bit-for-bit...");

    int64_t oldpos = 0;
    int64_t newpos = 0;
    uint32_t c_ptr = 0;
    uint32_t d_ptr = 0;
    uint32_t e_ptr = 0;

    while (newpos < (int64_t)hdr->newSize && c_ptr < hdr->ctrlRawLen) {
        int64_t c0 = cp_offtin(ctrl_raw + c_ptr);
        int64_t c1 = cp_offtin(ctrl_raw + c_ptr + 8);
        int64_t c2 = cp_offtin(ctrl_raw + c_ptr + 16);
        c_ptr += 24;

        for (int64_t i = 0; i < c0; i++) {
            if (oldpos + i >= 0 && oldpos + i < (int64_t)hdr->oldSize) {
                reconstructed[newpos + i] = (uint8_t)(old_buf[oldpos + i] + diff_raw[d_ptr + i]);
            } else {
                reconstructed[newpos + i] = diff_raw[d_ptr + i];
            }
        }
        newpos += c0;
        oldpos += c0;
        d_ptr += c0;

        if (c1 > 0) {
            memcpy(reconstructed + newpos, extra_raw + e_ptr, c1);
            newpos += c1;
            e_ptr += c1;
        }

        oldpos += c2;
    }

    // Free intermediate diff buffers
    safe_free(old_buf);
    safe_free(ctrl_raw);
    safe_free(diff_raw);
    safe_free(extra_raw);

    // 7. Cryptographic SHA-256 verification
    _status = DeltaStatus::VERIFYING;
    Serial.println("[DELTA] Verifying cryptographic SHA-256 integrity...");

    uint8_t calc_sha[32];
    mbedtls_sha256_context sha_ctx;
    mbedtls_sha256_init(&sha_ctx);
    mbedtls_sha256_starts(&sha_ctx, 0);
    mbedtls_sha256_update(&sha_ctx, reconstructed, hdr->newSize);
    mbedtls_sha256_finish(&sha_ctx, calc_sha);
    mbedtls_sha256_free(&sha_ctx);

    if (memcmp(calc_sha, hdr->targetSha256, 32) != 0) {
        safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "Target SHA-256 checksum MISMATCH!");
        _status = DeltaStatus::ERROR_CHECKSUM;
        Serial.println("[DELTA] CRITICAL ERROR: Target SHA-256 checksum MISMATCH!");
        return false;
    }

    Serial.println("[DELTA] [SUCCESS] Target SHA-256 bit-for-bit checksum verified!");

    // 8. Flash to next OTA update partition
    _status = DeltaStatus::FLASHING;
    const esp_partition_t* update_part = esp_ota_get_next_update_partition(NULL);
    if (!update_part) {
        safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "No available OTA update partition");
        _status = DeltaStatus::ERROR_FLASH;
        return false;
    }

    Serial.printf("[DELTA] Flashing reconstructed image to %s (addr: 0x%06X)...\n",
                  update_part->label, update_part->address);

    esp_ota_handle_t ota_handle;
    err = esp_ota_begin(update_part, hdr->newSize, &ota_handle);
    if (err != ESP_OK) {
        safe_free(reconstructed);
        snprintf(_lastError, sizeof(_lastError), "esp_ota_begin failed (%d)", err);
        _status = DeltaStatus::ERROR_FLASH;
        return false;
    }

    err = esp_ota_write(ota_handle, reconstructed, hdr->newSize);
    safe_free(reconstructed); // Free reconstructed image

    if (err != ESP_OK) {
        esp_ota_abort(ota_handle);
        snprintf(_lastError, sizeof(_lastError), "esp_ota_write failed (%d)", err);
        _status = DeltaStatus::ERROR_FLASH;
        return false;
    }

    err = esp_ota_end(ota_handle);
    if (err != ESP_OK) {
        snprintf(_lastError, sizeof(_lastError), "esp_ota_end failed (%d)", err);
        _status = DeltaStatus::ERROR_FLASH;
        return false;
    }

    err = esp_ota_set_boot_partition(update_part);
    if (err != ESP_OK) {
        snprintf(_lastError, sizeof(_lastError), "esp_ota_set_boot_partition failed (%d)", err);
        _status = DeltaStatus::ERROR_FLASH;
        return false;
    }

    _status = DeltaStatus::SUCCESS_REBOOTING;
    Serial.println("\n=======================================================");
    Serial.println("  AquaDelta OTA Flashed Successfully!");
    Serial.printf("  New boot partition: %s\n", update_part->label);
    Serial.println("  Rebooting into updated AquaFeeder Firmware in 2s...");
    Serial.println("=======================================================\n");

    delay(2000);
    esp_restart();
    return true;
}
