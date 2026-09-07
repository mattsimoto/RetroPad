#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/hid/IOHIDKeys.h>
#include <IOKit/IOReturn.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAX_PLAYERS 4

typedef struct __IOHIDUserDevice *IOHIDUserDeviceRef;
typedef IOHIDUserDeviceRef (*IOHIDUserDeviceCreateFn)(CFAllocatorRef, CFDictionaryRef);
typedef IOReturn (*IOHIDUserDeviceHandleReportFn)(IOHIDUserDeviceRef, const uint8_t *, CFIndex);

static IOHIDUserDeviceCreateFn pIOHIDUserDeviceCreate = NULL;
static IOHIDUserDeviceHandleReportFn pIOHIDUserDeviceHandleReport = NULL;
static void *iokit_handle = NULL;
static IOHIDUserDeviceRef devices[MAX_PLAYERS] = {0};

static int load_hid_api(void) {
    if (pIOHIDUserDeviceCreate && pIOHIDUserDeviceHandleReport) return 1;
    iokit_handle = dlopen("/System/Library/Frameworks/IOKit.framework/IOKit", RTLD_LAZY | RTLD_LOCAL);
    if (!iokit_handle) {
        fprintf(stderr, "RetroPad: could not open IOKit: %s\n", dlerror());
        return 0;
    }
    pIOHIDUserDeviceCreate = (IOHIDUserDeviceCreateFn)dlsym(iokit_handle, "IOHIDUserDeviceCreate");
    pIOHIDUserDeviceHandleReport = (IOHIDUserDeviceHandleReportFn)dlsym(iokit_handle, "IOHIDUserDeviceHandleReport");
    if (!pIOHIDUserDeviceCreate || !pIOHIDUserDeviceHandleReport) {
        fprintf(stderr, "RetroPad: this macOS version does not expose the required IOHIDUserDevice runtime API.\n");
        return 0;
    }
    return 1;
}

static const uint8_t gamepad_descriptor[] = {
    0x05,0x01, 0x09,0x05, 0xA1,0x01,
      0x05,0x09, 0x19,0x01, 0x29,0x10, 0x15,0x00, 0x25,0x01,
      0x75,0x01, 0x95,0x10, 0x81,0x02,
      0x05,0x01, 0x09,0x39, 0x15,0x00, 0x25,0x07,
      0x35,0x00, 0x46,0x3B,0x01, 0x65,0x14,
      0x75,0x04, 0x95,0x01, 0x81,0x42,
      0x75,0x04, 0x95,0x01, 0x81,0x03,
      0x09,0x30, 0x09,0x31, 0x09,0x33, 0x09,0x34,
      0x15,0x81, 0x25,0x7F, 0x75,0x08, 0x95,0x04, 0x81,0x02,
    0xC0
};

static void set_num(CFMutableDictionaryRef d, CFStringRef key, int value) {
    CFNumberRef n = CFNumberCreate(kCFAllocatorDefault, kCFNumberIntType, &value);
    if (n) { CFDictionarySetValue(d, key, n); CFRelease(n); }
}

static IOHIDUserDeviceRef create_device(int player) {
    CFMutableDictionaryRef props = CFDictionaryCreateMutable(kCFAllocatorDefault, 0,
        &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks);
    if (!props) return NULL;

    CFDataRef desc = CFDataCreate(kCFAllocatorDefault, gamepad_descriptor, sizeof(gamepad_descriptor));
    CFStringRef product = CFStringCreateWithFormat(kCFAllocatorDefault, NULL, CFSTR("RetroPad P%d"), player);
    CFStringRef serial = CFStringCreateWithFormat(kCFAllocatorDefault, NULL, CFSTR("RETROPAD-P%d"), player);
    CFDictionarySetValue(props, CFSTR(kIOHIDReportDescriptorKey), desc);
    CFDictionarySetValue(props, CFSTR(kIOHIDManufacturerKey), CFSTR("RetroPad"));
    CFDictionarySetValue(props, CFSTR(kIOHIDProductKey), product);
    CFDictionarySetValue(props, CFSTR(kIOHIDSerialNumberKey), serial);
    CFDictionarySetValue(props, CFSTR(kIOHIDTransportKey), CFSTR("Virtual"));
    set_num(props, CFSTR(kIOHIDVendorIDKey), 0x1209);
    set_num(props, CFSTR(kIOHIDProductIDKey), 0x5240 + player);
    set_num(props, CFSTR(kIOHIDVersionNumberKey), 0x0300);
    set_num(props, CFSTR(kIOHIDPrimaryUsagePageKey), 0x01);
    set_num(props, CFSTR(kIOHIDPrimaryUsageKey), 0x05);

    if (!load_hid_api()) { CFRelease(desc); CFRelease(product); CFRelease(serial); CFRelease(props); return NULL; }
    IOHIDUserDeviceRef dev = pIOHIDUserDeviceCreate(kCFAllocatorDefault, props);
    CFRelease(desc); CFRelease(product); CFRelease(serial); CFRelease(props);
    return dev;
}

static int ensure_device(int player) {
    if (player < 1 || player > MAX_PLAYERS) return 0;
    int i = player - 1;
    if (!devices[i]) {
        devices[i] = create_device(player);
        if (!devices[i]) return 0;
        fprintf(stderr, "RetroPad P%d virtual HID created\n", player);
        fflush(stderr);
    }
    return 1;
}

static int hexval(char c) {
    if (c >= '0' && c <= '9') return c-'0';
    if (c >= 'a' && c <= 'f') return c-'a'+10;
    if (c >= 'A' && c <= 'F') return c-'A'+10;
    return -1;
}

int main(void) {
    char line[256];
    setvbuf(stdout, NULL, _IOLBF, 0);
    while (fgets(line, sizeof(line), stdin)) {
        int player = 0;
        char hex[128] = {0};
        if (sscanf(line, "CREATE %d", &player) == 1) {
            printf("%s %d\n", ensure_device(player) ? "READY" : "ERROR", player);
            continue;
        }
        if (sscanf(line, "REPORT %d %127s", &player, hex) == 2) {
            if (!ensure_device(player)) { printf("ERROR %d\n", player); continue; }
            size_t len = strlen(hex) / 2;
            if (len > 64) len = 64;
            uint8_t buf[64];
            int ok = 1;
            for (size_t i=0;i<len;i++) {
                int hi=hexval(hex[i*2]), lo=hexval(hex[i*2+1]);
                if (hi<0 || lo<0) { ok=0; break; }
                buf[i]=(uint8_t)((hi<<4)|lo);
            }
            if (!ok) { printf("ERROR %d\n", player); continue; }
            IOReturn r = pIOHIDUserDeviceHandleReport(devices[player-1], buf, (CFIndex)len);
            printf("%s %d\n", r==kIOReturnSuccess ? "OK" : "ERROR", player);
            continue;
        }
        if (!strncmp(line, "QUIT", 4)) break;
    }
    for (int i=0;i<MAX_PLAYERS;i++) if (devices[i]) CFRelease(devices[i]);
    if (iokit_handle) dlclose(iokit_handle);
    return 0;
}
