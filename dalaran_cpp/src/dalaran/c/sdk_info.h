/// Returns the version of the Dalaran C SDK.
///
/// This should match the string returned by `dl_version_string` (C) or `dalaran::version_string` (C++).
/// If not, the SDK's binary and the C header are out of sync.
#define DALARAN_SDK_HEADER_VERSION "0.1.0"

/// Major version of the Dalaran C SDK.
#define DALARAN_SDK_HEADER_VERSION_MAJOR 0

/// Minor version of the Dalaran C SDK.
#define DALARAN_SDK_HEADER_VERSION_MINOR 1

/// Patch version of the Dalaran C SDK.
#define DALARAN_SDK_HEADER_VERSION_PATCH 0

/// Is the Dalaran library version greater or equal to this?
///
/// Example usage:
/// ```
/// #if DALARAN_VERSION_GE(0, 18, 0)
///    // Use features from Dalaran 0.18
/// #endif
/// ```
#define DALARAN_VERSION_GE(major, minor, patch)                                                      \
    ((major) == DALARAN_SDK_HEADER_VERSION_MAJOR                                                     \
         ? ((minor) == DALARAN_SDK_HEADER_VERSION_MINOR ? (patch) <= DALARAN_SDK_HEADER_VERSION_PATCH  \
                                                      : (minor) <= DALARAN_SDK_HEADER_VERSION_MINOR) \
         : (major) <= DALARAN_SDK_HEADER_VERSION_MAJOR)
