#ifndef DL_DEPRECATED
// Mark as deprecated in C
#if defined(__GNUC__) || defined(__clang__)
#define DL_DEPRECATED(msg) __attribute__((deprecated))
#elif defined(_MSC_VER)
#define DL_DEPRECATED(msg) __declspec(deprecated(msg))
#else
#define DL_DEPRECATED(msg)
#endif // define checks
#endif // DL_DEPRECATED
