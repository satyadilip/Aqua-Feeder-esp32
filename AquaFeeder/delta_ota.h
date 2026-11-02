#pragma once

#include <Arduino.h>
#include <esp_ota_ops.h>
#include <esp_partition.h>

#define DELTA_OTA_MAGIC "AQUADELT"
#define DELTA_HEADER_SIZE 80

struct AquaDeltaHeader {
    char magic[8];           // "AQUADELT"
    uint16_t version;        // Format version (1)
    uint16_t flags;          // Flags (0)
    uint32_t oldSize;        // Source firmware size (bytes)
    uint32_t newSize;        // Target firmware size (bytes)
    uint32_t ctrlCompLen;    // Compressed ctrl stream length
    uint32_t ctrlRawLen;     // Decompressed ctrl stream length
    uint32_t diffCompLen;    // Compressed diff stream length
    uint32_t diffRawLen;     // Decompressed diff stream length
    uint32_t extraCompLen;   // Compressed extra stream length
    uint32_t extraRawLen;    // Decompressed extra stream length
    uint32_t targetCrc32;    // Target CRC32
    uint8_t targetSha256[32];// Target SHA-256 hash
} __attribute__((packed));

enum class DeltaStatus {
    IDLE,
    RECEIVING,
    RECEIVED_ALL,
    DECOMPRESSING,
    RECONSTRUCTING,
    VERIFYING,
    FLASHING,
    SUCCESS_REBOOTING,
    ERROR_HEADER,
    ERROR_MEMORY,
    ERROR_DECOMPRESS,
    ERROR_CHECKSUM,
    ERROR_FLASH
};

class DeltaOTA {
public:
    DeltaOTA();
    ~DeltaOTA();

    bool begin(uint32_t expectedPatchSize);
    bool writeChunk(uint32_t offset, const uint8_t* data, size_t len);
    bool applyPatch();
    
    DeltaStatus getStatus() const { return _status; }
    uint8_t getProgress() const { return _progress; }
    uint32_t getReceivedBytes() const { return _receivedBytes; }
    uint32_t getExpectedSize() const { return _expectedSize; }
    const char* getLastError() const { return _lastError; }
    
    void reset();

private:
    DeltaStatus _status;
    uint8_t _progress;
    char _lastError[64];
    uint32_t _expectedSize;
    uint32_t _receivedBytes;
    uint8_t* _patchBuffer;
};

extern DeltaOTA deltaOTA;
