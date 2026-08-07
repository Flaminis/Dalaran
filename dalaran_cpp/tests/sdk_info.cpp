#include <dalaran.hpp>

static_assert(DALARAN_VERSION_GE(0, 18, 0), "Dalaran version was expected to be at least 0.18.0");
static_assert(
    DALARAN_VERSION_GE(
        DALARAN_SDK_HEADER_VERSION_MAJOR, DALARAN_SDK_HEADER_VERSION_MINOR,
        DALARAN_SDK_HEADER_VERSION_PATCH
    ),
    "Dalaran version is equal to this version."
);
static_assert(
    !DALARAN_VERSION_GE(
        DALARAN_SDK_HEADER_VERSION_MAJOR, DALARAN_SDK_HEADER_VERSION_MINOR,
        DALARAN_SDK_HEADER_VERSION_PATCH + 1
    ),
    "Dalaran version is not greater than this version."
);
static_assert(
    !DALARAN_VERSION_GE(
        DALARAN_SDK_HEADER_VERSION_MAJOR, DALARAN_SDK_HEADER_VERSION_MINOR + 1,
        DALARAN_SDK_HEADER_VERSION_PATCH
    ),
    "Dalaran version is not greater than this version."
);
static_assert(
    !DALARAN_VERSION_GE(
        DALARAN_SDK_HEADER_VERSION_MAJOR + 1, DALARAN_SDK_HEADER_VERSION_MINOR,
        DALARAN_SDK_HEADER_VERSION_PATCH
    ),
    "Dalaran version is not greater than this version."
);

#if DALARAN_VERSION_GE(0, 18, 0)
static_assert(true, "Dalaran can be used in a macro.");
#else
static_assert(false, "Dalaran can be used in a macro, but we shouldn't be able to get here.");
#endif
