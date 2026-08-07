// ----------------------------------------------------------------------------
// The Dalaran C SDK for Dalaran.
// This file is part of the dalaran_c Rust crate.
// ----------------------------------------------------------------------------
//
// All Dalaran functions and types are thread-safe,
// which means you can share a `dl_recording_stream` across threads.
// ----------------------------------------------------------------------------

#ifndef DALARAN_H
#define DALARAN_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdint.h>
#include "arrow_c_data_interface.h"
#include "compiler_utils.h"
#include "sdk_info.h"

// ----------------------------------------------------------------------------
// Types:

/// A Utf8 string with a length in bytes.
typedef struct dl_string {
    /// Pointer to a UTF8 string.
    ///
    /// Does *not* need to be null-terminated.
    /// Dalaran is guaranteed to not read beyond utf8[length_in_bytes-1].
    const char* utf8;

    /// The length of the string in bytes (*excluding* null-terminator, if any).
    uint32_t length_in_bytes;
} dl_string;

/// A byte slice.
typedef struct dl_bytes {
    /// Pointer to the bytes.
    ///
    /// Dalaran is guaranteed to not read beyond bytes[length-1].
    const uint8_t* bytes;

    /// The length of the data in bytes.
    uint32_t length;
} dl_bytes;

#ifndef __cplusplus

#include <string.h> // For strlen

/// Create a `dl_string` from a null-terminated string.
///
/// Calling with NULL is safe.
dl_string dl_make_string(const char* utf8) {
    uint32_t length_in_bytes = 0;
    if (utf8 != NULL) {
        length_in_bytes = (uint32_t)strlen(utf8);
    }
    return (dl_string){.utf8 = utf8, .length_in_bytes = length_in_bytes};
}

#endif

/// Type of store log messages are sent to.
typedef uint32_t dl_store_kind;

enum {
    DL_STORE_KIND_RECORDING = 1,
    DL_STORE_KIND_BLUEPRINT = 2,
};

/// Special value for `dl_recording_stream` methods to indicate the most appropriate
/// globally available recording stream for recordings.
/// (i.e. thread-local first, then global scope)
#define DL_REC_STREAM_CURRENT_RECORDING 0xFFFFFFFF

/// Special value for `dl_recording_stream` methods to indicate the most appropriate
/// globally available recording stream for blueprints.
/// (i.e. thread-local first, then global scope)
#define DL_REC_STREAM_CURRENT_BLUEPRINT 0xFFFFFFFE

/// Handle to a component type that can be registered.
typedef uint32_t dl_component_type_handle;

/// Special value for `dl_component_type_handle` to indicate an invalid handle.
#define DL_COMPONENT_TYPE_HANDLE_INVALID 0xFFFFFFFF

/// A unique handle for a recording stream.
/// A recording stream handles everything related to logging data into Dalaran.
///
/// ## Multithreading and ordering
///
/// Internally, all operations are linearized into a pipeline:
/// - All operations sent by a given thread will take effect in the same exact order as that
///   thread originally sent them in, from its point of view.
/// - There isn't any well defined global order across multiple threads.
///
/// This means that e.g. flushing the pipeline (`dl_recording_stream_flush_blocking`) guarantees
/// that all previous data sent by the calling thread has been recorded; no more, no less.
/// (e.g. it does not mean that all file caches are flushed)
///
/// ## Shutdown
///
/// The recording stream can only be shutdown by dropping all instances of it, at which point
/// it will automatically take care of flushing any pending data that might remain in the
/// pipeline.
///
/// TODO(andreas): The only way of having two instances of a `RecordingStream` is currently to
/// set it as a the global.
typedef uint32_t dl_recording_stream;

/// Options to control the behavior of `spawn`.
///
/// Refer to the field-level documentation for more information about each individual options.
///
/// The defaults are ok for most use cases.
typedef struct dl_spawn_options {
    /// The port to listen on.
    ///
    /// Defaults to `9876` if set to `0`.
    uint16_t port;

    /// An upper limit on how much memory the Dalaran Viewer should use.
    /// When this limit is reached, Dalaran will drop the oldest data.
    /// Example: `16GB` or `50%` (of system total).
    ///
    /// Defaults to `75%` if null.
    dl_string memory_limit;

    /// An upper limit on how much memory the gRPC server running
    /// in the same process as the Dalaran Viewer should use.
    /// When this limit is reached, Dalaran will drop the oldest data.
    /// Example: `16GB` or `50%` (of system total).
    ///
    /// Defaults to `0B` if null.
    dl_string server_memory_limit;

    /// Hide the normal Dalaran welcome screen.
    bool hide_welcome_screen;

    /// Detach Dalaran Viewer process from the application process.
    bool detach_process;

    /// Specifies the name of the Dalaran executable.
    ///
    /// You can omit the `.exe` suffix on Windows.
    ///
    /// Defaults to `dalaran` if null.
    dl_string executable_name;

    /// Enforce a specific executable to use instead of searching through PATH
    /// for [`Self::executable_name`].
    ///
    /// Unspecified by default.
    dl_string executable_path;
} dl_spawn_options;

/// Recommended settings for the [`Importer`].
///
/// The importer is free to ignore some or all of these.
///
/// Refer to the field-level documentation for more information about each individual options.
//
// TODO(#3841): expose timepoint settings once we implement stateless APIs
typedef struct dl_importer_settings {
    /// The recommended `RecordingId` to log the data to.
    ///
    /// Unspecified by default.
    dl_string recording_id;

    /// What should the logged entity paths be prefixed with?
    ///
    /// Unspecified by default.
    dl_string entity_path_prefix;

    /// Should the logged data be static?
    ///
    /// Defaults to `false` if not set.
    bool static_;
} dl_importer_settings;

/* Deprecated since 0.32.0: use dl_importer_settings instead. */
typedef dl_importer_settings dl_data_loader_settings;

typedef struct dl_store_info {
    /// The user-chosen name of the application doing the logging.
    dl_string application_id;

    /// The user-chosen name of the recording being logged to.
    ///
    /// Defaults to a random ID if unspecified.
    dl_string recording_id;

    /// `DL_STORE_KIND_RECORDING` or `DL_STORE_KIND_BLUEPRINT`
    dl_store_kind store_kind;
} dl_store_info;

/// Definition of a component descriptor that can be registered.
typedef struct dl_component_descriptor {
    /// Optional name of the `Archetype` associated with this data.
    ///
    /// Null if the data wasn't logged through an archetype.
    ///
    /// Example: `dalaran.archetypes.Points3D`.
    dl_string archetype;

    /// Optional name of the field within `Archetype` associated with this data.
    ///
    /// Null if the data wasn't logged through an archetype.
    ///
    /// Example: `positions`.
    dl_string component;

    /// Semantic type associated with this data.
    ///
    /// This is fully implied by the `component`, but included for semantic convenience.
    ///
    /// Example: `dalaran.components.Position3D`.
    dl_string component_type;
} dl_component_descriptor;

/// Definition of a component type that can be registered.
typedef struct dl_component_type {
    /// The complete descriptor for this component.
    dl_component_descriptor descriptor;

    /// The arrow schema used for arrow arrays of instances of this component.
    struct ArrowSchema schema;
} dl_component_type;

/// Arrow-encoded data of a single batch components for a single entity.
typedef struct dl_component_batch {
    /// The component type to use for this batch.
    dl_component_type_handle component_type;

    /// A batch of instances of this component serialized into an arrow array.
    struct ArrowArray array;
} dl_component_batch;

/// Arrow-encoded log data for a single entity.
/// May contain many components.
typedef struct dl_data_row {
    /// Where to log to, e.g. `world/camera`.
    dl_string entity_path;

    /// Number of different component batches.
    uint32_t num_component_batches;

    /// One for each component.
    dl_component_batch* component_batches;
} dl_data_row;

/// Arrow-encoded data of a column of components.
///
/// This is essentially an array of `dl_component_batch` with all batches
/// continuously in a single array.
typedef struct dl_component_column {
    /// The component type used for the components inside the list array.
    ///
    /// This is *not* the type of the arrow list array itself, but of the underlying batch.
    dl_component_type_handle component_type;

    /// A ListArray with the datatype `List(component_type)`.
    struct ArrowArray array;
} dl_component_column;

/// Describes whether an array is known to be sorted or not.
typedef uint32_t dl_sorting_status;

enum {
    /// It's not known whether the array is sorted or not.
    DL_SORTING_STATUS_UNKNOWN = 0,

    /// The array is known to be sorted.
    DL_SORTING_STATUS_SORTED = 1,

    /// The array is known to be unsorted.
    DL_SORTING_STATUS_UNSORTED = 2,
};

/// Describes the type of a timeline or time point.
typedef uint32_t dl_time_type;

enum {
    // 0 no longer in use

    /// Used e.g. for frames in a film.
    DL_TIME_TYPE_SEQUENCE = 1,

    /// Nanoseconds.
    DL_TIME_TYPE_DURATION = 2,

    /// Nanoseconds since Unix epoch (1970-01-01 00:00:00 UTC).
    DL_TIME_TYPE_TIMESTAMP = 3,
};

/// Definition of a timeline.
typedef struct dl_timeline {
    /// The name of the timeline.
    dl_string name;

    /// The type of the timeline.
    dl_time_type type;
} dl_timeline;

/// A column of timestamps for a given timeline.
typedef struct dl_time_column {
    /// The timeline this column belongs to.
    dl_timeline timeline;

    /// Time points as a primitive array of i64.
    struct ArrowArray array;

    /// The sorting order of the `times` array.
    dl_sorting_status sorting_status;
} dl_time_column;

/// Log sink which streams messages to an existing Dalaran gRPC server.
///
/// This is a gRPC client: it connects to a server but does not host one.
/// Use `dl_grpc_server_sink` to host a server that SDKs and Viewers can connect to.
///
/// The behavior of this sink is the same as the one set by `dl_recording_stream_connect_grpc`.
typedef struct dl_grpc_sink {
    /// A Dalaran gRPC URL.
    ///
    /// The scheme must be one of `dalaran://`, `dalaran+http://`, or `dalaran+https://`,
    /// and the pathname must be `/proxy`.
    ///
    /// The default is `dalaran+http://127.0.0.1:9876/proxy`.
    dl_string url;
} dl_grpc_sink;

/// Log sink which writes messages to a file.
typedef struct dl_file_sink {
    /// Path to the output file.
    dl_string path;
} dl_file_sink;

/// Log sink which hosts a Dalaran gRPC server.
///
/// This is a gRPC server: SDKs and Viewers connect to it.
/// Use `dl_grpc_sink` to connect as a client to an existing server.
/// Replacing the recording's sinks or freeing the recording shuts down the server.
typedef struct dl_grpc_server_sink {
    /// IP address on which to listen, such as `0.0.0.0` to listen on all interfaces.
    dl_string bind_ip;

    /// TCP port on which to listen.
    uint16_t port;

    /// Maximum amount of log data to retain for late-connecting clients, such as `1GiB`.
    ///
    /// Once this limit is reached, the earliest temporal data is dropped.
    /// Static data is never dropped.
    dl_string server_memory_limit;

    /// Whether each new client should receive the newest retained messages first.
    bool newest_first;

    /// Optional origin patterns allowed to make cross-origin requests to the server.
    ///
    /// The array and its strings only need to remain valid for the
    /// `dl_recording_stream_set_sinks` call.
    /// Set this to `NULL` when `num_cors_allow_origins` is zero.
    const dl_string* cors_allow_origins;

    /// Number of entries in `cors_allow_origins`.
    uint32_t num_cors_allow_origins;
} dl_grpc_server_sink;

enum {
    DL_LOG_SINK_KIND_GRPC = 0,
    DL_LOG_SINK_KIND_FILE = 1,
    DL_LOG_SINK_KIND_GRPC_SERVER = 2,
};

/// Used to tag the kind of `dl_log_sink`.
typedef uint8_t dl_log_sink_kind;

/// A sink for log messages.
///
/// See specific log sink types for more information:
/// * `dl_grpc_sink`
/// * `dl_file_sink`
/// * `dl_grpc_server_sink`
typedef struct dl_log_sink {
    dl_log_sink_kind kind;

    union {
        dl_grpc_sink grpc;
        dl_file_sink file;
        dl_grpc_server_sink grpc_server;
    };
} dl_log_sink;

/// Error codes returned by the Dalaran C SDK as part of `dl_error`.
///
/// Category codes are used to group errors together, but are never returned directly.
typedef uint32_t dl_error_code;

// ⚠️ Remember to also update `enum CErrorCode` AND `enum class ErrorCode` !
enum {
    DL_ERROR_CODE_OK = 0,
    DL_ERROR_CODE_OUT_OF_MEMORY,
    DL_ERROR_CODE_NOT_IMPLEMENTED,
    DL_ERROR_CODE_SDK_VERSION_MISMATCH,

    // Invalid argument errors.
    _DL_ERROR_CODE_CATEGORY_ARGUMENT = 0x00000010,
    DL_ERROR_CODE_UNEXPECTED_NULL_ARGUMENT,
    DL_ERROR_CODE_INVALID_STRING_ARGUMENT,
    DL_ERROR_CODE_INVALID_ENUM_VALUE,
    DL_ERROR_CODE_INVALID_RECORDING_STREAM_HANDLE,
    DL_ERROR_CODE_INVALID_SOCKET_ADDRESS,
    DL_ERROR_CODE_INVALID_COMPONENT_TYPE_HANDLE,
    DL_ERROR_CODE_INVALID_TIME_ARGUMENT,
    DL_ERROR_CODE_INVALID_TENSOR_DIMENSION,
    DL_ERROR_CODE_INVALID_COMPONENT,
    DL_ERROR_CODE_INVALID_SERVER_URL = 0x00000001a,
    DL_ERROR_CODE_FILE_READ,
    DL_ERROR_CODE_INVALID_MEMORY_LIMIT,

    // Recording stream errors
    _DL_ERROR_CODE_CATEGORY_RECORDING_STREAM = 0x00000100,
    DL_ERROR_CODE_RECORDING_STREAM_RUNTIME_FAILURE,
    DL_ERROR_CODE_RECORDING_STREAM_CREATION_FAILURE,
    DL_ERROR_CODE_RECORDING_STREAM_SAVE_FAILURE,
    DL_ERROR_CODE_RECORDING_STREAM_STDOUT_FAILURE,
    DL_ERROR_CODE_RECORDING_STREAM_SPAWN_FAILURE,
    DL_ERROR_CODE_RECORDING_STREAM_CHUNK_VALIDATION_FAILURE,
    DL_ERROR_CODE_RECORDING_STREAM_SERVE_GRPC_FAILURE,
    DL_ERROR_CODE_RECORDING_STREAM_FLUSH_TIMEOUT,
    DL_ERROR_CODE_RECORDING_STREAM_FLUSH_FAILURE,

    // Arrow data processing errors.
    _DL_ERROR_CODE_CATEGORY_ARROW = 0x00001000,
    DL_ERROR_CODE_ARROW_FFI_SCHEMA_IMPORT_ERROR,
    DL_ERROR_CODE_ARROW_FFI_ARRAY_IMPORT_ERROR,

    // Utility errors.
    _DL_ERROR_CODE_CATEGORY_UTILITIES = 0x00010000,
    DL_ERROR_CODE_VIDEO_LOAD_ERROR,

    // Errors relating to file IO.
    _DL_ERROR_CODE_CATEGORY_FILE_IO = 0x00100000,
    DL_ERROR_CODE_FILE_OPEN_FAILURE,

    // Errors directly translated from arrow::StatusCode.
    _DL_ERROR_CODE_CATEGORY_ARROW_CPP_STATUS = 0x10000000,

    // Generic errors.
    DL_ERROR_CODE_UNKNOWN,
};

/// Error outcome object (success or error) that may be filled for fallible operations.
///
/// Passing this error struct is always optional, and you can pass `NULL` if you don't care about
/// the error in which case failure will be silent.
/// If no error occurs, the error struct will be left untouched.
typedef struct dl_error {
    /// Error code indicating the type of error.
    dl_error_code code;

    /// Human readable description of the error in null-terminated UTF8.
    //
    // NOTE: You must update `CError::MAX_MESSAGE_SIZE_BYTES` too if you modify this value.
    char description[2048];
} dl_error;

// ----------------------------------------------------------------------------
// Functions:

/// Returns a human-readable version string of the Dalaran C SDK.
///
/// This should match the string in `DALARAN_SDK_HEADER_VERSION`.
/// If not, the SDK's binary and the C header are out of sync.
extern const char* dl_version_string(void);

/// Converts a 32-bit `float` to the bits of an IEEE 754 16-bit half-precision float.
///
/// Rounds to nearest, ties to even. Values too large to represent become infinity,
/// and `NaN` stays `NaN`.
extern uint16_t dl_f16_from_f32(float value);

/// Spawns a new Dalaran Viewer process from an executable available in PATH, ready to
/// listen for incoming gRPC connections.
///
/// `spawn_opts` can be set to NULL to use the recommended defaults.
///
/// If a Dalaran Viewer is already listening on this gRPC port, this does nothing.
extern void dl_spawn(const dl_spawn_options* spawn_opts, dl_error* error);

/// Registers a new component type to be used in `dl_component_batch`.
///
/// A component with a given name can only be registered once.
/// Takes ownership of the passed arrow schema and will release it once it is no longer needed.
extern dl_component_type_handle dl_register_component_type(
    dl_component_type component_type, dl_error* error
);

/// Creates a new recording stream to log to.
///
/// You must call this at least once to enable logging.
///
/// Usually you only have one recording stream, so you can call
/// `dl_recording_stream_set_global` afterwards once to make it available globally via
/// `DL_REC_STREAM_CURRENT_RECORDING` and `DL_REC_STREAM_CURRENT_BLUEPRINT` respectively.
///
/// @return A handle to the recording stream, or null if an error occurred.
extern dl_recording_stream dl_recording_stream_new(
    const dl_store_info* store_info, bool default_enabled, dl_error* error
);

/// Free the given recording stream. The handle will be invalid after this.
///
/// Flushes the stream before freeing it, but does *not* block.
///
/// Does nothing for `DL_REC_STREAM_CURRENT_RECORDING` and `DL_REC_STREAM_CURRENT_BLUEPRINT`.
///
/// No-op for destroyed/non-existing streams.
extern void dl_recording_stream_free(dl_recording_stream stream);

/// Replaces the currently active recording of the specified type in the global scope with
/// the specified one.
extern void dl_recording_stream_set_global(dl_recording_stream stream, dl_store_kind store_kind);

/// Replaces the currently active recording of the specified type in the thread-local scope
/// with the specified one.
extern void dl_recording_stream_set_thread_local(
    dl_recording_stream stream, dl_store_kind store_kind
);

/// Check whether the recording stream is enabled.
extern bool dl_recording_stream_is_enabled(dl_recording_stream stream, dl_error* error);

/// Stream data to multiple different sinks.
///
/// Any previously active sinks will be dropped.
///
/// See `dl_log_sink` for more information about what each sink does.
extern void dl_recording_stream_set_sinks(
    dl_recording_stream stream, dl_log_sink* sinks, uint32_t num_sinks, dl_error* error
);

/// Connect to a remote Dalaran Viewer on the given URL.
///
/// Requires that you first start a Dalaran Viewer by typing 'dalaran' in a terminal.
///
/// url:
/// The scheme must be one of `dalaran://`, `dalaran+http://`, or `dalaran+https://`,
/// and the pathname must be `/proxy`.
///
/// The default is `dalaran+http://127.0.0.1:9876/proxy`.
///
/// This function returns immediately and will only raise an error for argument parsing errors,
/// not for connection errors as these happen asynchronously.
extern void dl_recording_stream_connect_grpc(
    dl_recording_stream stream, dl_string url, dl_error* error
);

/// Swaps the underlying sink for a gRPC server sink pre-configured to listen on `dalaran+http://{bind_ip}:{port}/proxy`.
///
/// The gRPC server will buffer all log data in memory so that late connecting viewers will get all the data.
/// You can control the amount of data buffered by the gRPC server with the `server_memory_limit` argument.
/// Once reached, the earliest logged data will be dropped. Static data is never dropped.
///
/// `newest_first` controls whether or not to play back the newest data first to clients.
///
/// `cors_allow_origins` is an optional array of origin patterns allowed to make cross-origin requests
/// to the gRPC server. By default only localhost and dalaran.dev are allowed.
/// Patterns are matched against the full Origin header (e.g. "https://example.com:8080"),
/// using glob-style matching where `*` matches any sequence of characters.
/// Examples: "https://*.example.com", "https://example.com:8080", "https://example.com:*".
extern void dl_recording_stream_serve_grpc(
    dl_recording_stream stream, dl_string bind_ip, uint16_t port, dl_string server_memory_limit,
    bool newest_first, const dl_string* cors_allow_origins, uint32_t num_cors_allow_origins,
    dl_error* error
);

/// Spawns a new Dalaran Viewer process from an executable available in PATH, then connects to it
/// over gRPC.
///
/// This function returns immediately and will only raise an error for argument parsing errors,
/// not for connection errors as these happen asynchronously.
///
/// ## Parameters
///
/// spawn_opts:
/// Configuration of the spawned process.
/// Refer to `dl_spawn_options` documentation for details.
/// Passing null is valid and will result in the recommended defaults.
extern void dl_recording_stream_spawn(
    dl_recording_stream stream, const dl_spawn_options* spawn_opts, dl_error* error
);

/// Stream all log-data to a given `.dlr` file.
///
/// This function returns immediately.
extern void dl_recording_stream_save(dl_recording_stream stream, dl_string path, dl_error* error);

/// Stream all log-data to stdout.
///
/// Pipe the result into the Dalaran Viewer to visualize it.
///
/// If there isn't any listener at the other end of the pipe, the `RecordingStream` will
/// default back to `buffered` mode, in order not to break the user's terminal.
///
/// This function returns immediately.
extern void dl_recording_stream_stdout(dl_recording_stream stream, dl_error* error);

/// Initiates a flush the batching pipeline and waits for it to propagate.
///
/// See `dl_recording_stream` docs for ordering semantics and multithreading guarantees.
/// No-op for destroyed/non-existing streams.
extern void dl_recording_stream_flush_blocking(
    dl_recording_stream stream, float timeout_sec, dl_error* error
);

/// Set the current index value of the recording, for a specific timeline, for the current calling thread.
///
/// Used for all subsequent logging performed from this same thread, until the next call
/// to one of the time setting methods.
///
/// For example:
/// `dl_recording_stream_set_time_sequence(stream, "frame_nr", DL_TIME_TYPE_SEQUENCE, frame_nr, &err)`.
extern void dl_recording_stream_set_time(
    dl_recording_stream stream, dl_string timeline_name, dl_time_type time_type, int64_t value,
    dl_error* error
);

/// Stops logging to the specified timeline for subsequent log calls.
///
/// The timeline is still there, but will not be updated with any new data.
///
/// No-op if the timeline doesn't exist.
void dl_recording_stream_disable_timeline(
    dl_recording_stream stream, dl_string timeline_name, dl_error* error
);

/// Clears out the current time of the recording, for the current calling thread.
///
/// Used for all subsequent logging performed from this same thread, until the next call
/// to one of the time setting methods.
///
/// No-op for destroyed/non-existing streams.
extern void dl_recording_stream_reset_time(dl_recording_stream stream);

/// Enable or disable automatic injection of the `log_tick` timeline into logged data.
///
/// `log_tick` is a per-recording counter that increments on every logging call.
/// It is disabled by default (it can also be controlled via the `DALARAN_LOG_TICK` environment variable).
///
/// No-op for destroyed/non-existing streams.
extern void dl_recording_stream_set_log_tick_enabled(dl_recording_stream stream, bool enabled);

/// Enable or disable automatic injection of the `log_time` timeline into logged data.
///
/// `log_time` is the wall-clock time at which data was logged.
/// It is enabled by default (it can also be controlled via the `DALARAN_LOG_TIME` environment variable).
///
/// No-op for destroyed/non-existing streams.
extern void dl_recording_stream_set_log_time_enabled(dl_recording_stream stream, bool enabled);

/// Log the given data to the given stream.
///
/// If `inject_time` is set to `true`, the row's timestamp data will be
/// overridden using the recording streams internal clock.
///
/// Takes ownership of the passed data component batches and will release underlying
/// arrow data once it is no longer needed.
/// Any pointers passed via `dl_string` can be safely freed after this call.
extern void dl_recording_stream_log(
    dl_recording_stream stream, dl_data_row data_row, bool inject_time, dl_error* error
);

/// Logs the file at the given `path` using all `Importer`s available.
///
/// A single `path` might be handled by more than one importer.
///
/// This method blocks until either at least one `Importer` starts streaming data in
/// or all of them fail.
///
/// See <https://www.dalaran.dev/docs/concepts/logging-and-ingestion/importers/overview> for more information.
extern void dl_recording_stream_log_file_from_path(
    dl_recording_stream stream, dl_string path, dl_string entity_path_prefix, bool static_,
    dl_error* error
);

/// Logs the given `contents` using all `Importer`s available.
///
/// A single `path` might be handled by more than one importer.
///
/// This method blocks until either at least one `Importer` starts streaming data in
/// or all of them fail.
///
/// See <https://www.dalaran.dev/docs/concepts/logging-and-ingestion/importers/overview> for more information.
extern void dl_recording_stream_log_file_from_contents(
    dl_recording_stream stream, dl_string path, dl_bytes contents, dl_string entity_path_prefix,
    bool static_, dl_error* error
);

/// Sends the columns of components to the stream.
///
/// Unlike the regular `log` API, which is row-oriented, this API lets you submit the data
/// in a columnar form. The lengths of all `time_columns` and `component_columns`
/// must match. All data that occurs at the same index across the different time and components
/// arrays will act as a single logical row.
///
/// Note that this API ignores any stateful time set on the log stream via the
/// `dl_recording_stream_set_time_sequence`/`dl_recording_stream_set_time_nanos`/etc. APIs.
/// Furthermore, this will _not_ inject the default timelines `log_tick` and `log_time` timeline columns.
///
/// The contents of `time_columns` and `component_columns` AFTER this call is undefined.
extern void dl_recording_stream_send_columns(
    dl_recording_stream stream, dl_string entity_path,                      //
    dl_time_column* time_columns, uint32_t num_time_columns,                //
    dl_component_column* component_columns, uint32_t num_component_columns, //
    dl_error* error
);

// ----------------------------------------------------------------------------
// Other utilities

/// Allocation method for `dl_video_asset_read_frame_timestamps_nanos`.
typedef int64_t* (*dl_alloc_timestamps)(void* alloc_context, uint32_t num_timestamps);

/// Determines the presentation timestamps of all frames inside the video.
///
/// Returned timestamps are in nanoseconds since start and are guaranteed to be monotonically increasing.
///
/// \param media_type
/// If not specified (null or empty string), the media type will be guessed from the data.
/// \param alloc_func
/// Function used to allocate memory for the returned timestamps.
/// Guaranteed to be called exactly once with the `alloc_context` pointer as argument.
extern int64_t* dl_video_asset_read_frame_timestamps_nanos(
    const uint8_t* video_bytes, uint64_t video_bytes_len, dl_string media_type, void* alloc_context,
    dl_alloc_timestamps alloc_timestamps, dl_error* error
);

// ----------------------------------------------------------------------------
// Private functions

/// PRIVATE FUNCTION: do not use.
///
/// Escape a single part of an entity path, returning an new null-terminated string.
///
/// The returned string must be freed with `_dl_free_string`.
///
/// Returns `nullptr` on failure (e.g. invalid UTF8, ore null bytes in the string).
extern char* _dl_escape_entity_path_part(dl_string part);

/// PRIVATE FUNCTION: do not use.
///
/// Must only be called with the results from `_dl_escape_entity_path_part`.
extern void _dl_free_string(char* string);

// ----------------------------------------------------------------------------

#ifdef __cplusplus
}
#endif

#endif // DALARAN_H
