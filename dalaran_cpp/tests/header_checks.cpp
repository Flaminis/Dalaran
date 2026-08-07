#include <dalaran.hpp>

// ARROW_EXPORT is included by <arrow/util/visibility.h>
// ARROW_EXPAND is included by <arrow/util/macros.h>
// Both are included by almost all arrow headers.
#if defined(ARROW_EXPORT) || defined(ARROW_EXPAND)
static_assert(
    false,
    "ARROW_EXPORT or ARROW_EXPAND should not be defined. This indicates that we're leaking arrow "
    "headers through "
    "dalaran.hpp!"
);
#endif

#if defined(DALARAN_H)
static_assert(
    false,
    "DALARAN_H should not be defined. This indicates that we're leaking the c/dalaran.h "
    "through "
    "dalaran.hpp!"
);
#endif
