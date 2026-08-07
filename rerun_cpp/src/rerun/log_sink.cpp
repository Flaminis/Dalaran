#include "log_sink.hpp"
#include "c/rerun.h"
#include "string_utils.hpp"

#include <cassert>

namespace rerun {
    namespace detail {
        dl_log_sink to_dl_log_sink(LogSink sink) {
            switch (sink.kind) {
                case LogSink::Kind::Grpc: {
                    dl_log_sink out;
                    out.kind = DL_LOG_SINK_KIND_GRPC;
                    out.grpc.url = detail::to_dl_string(sink.grpc.url);
                    return out;
                }
                case LogSink::Kind::File: {
                    dl_log_sink out;
                    out.kind = DL_LOG_SINK_KIND_FILE;
                    out.file.path = detail::to_dl_string(sink.file.path);
                    return out;
                }
                case LogSink::Kind::GrpcServer: {
                    dl_log_sink out;
                    out.kind = DL_LOG_SINK_KIND_GRPC_SERVER;
                    const auto& server = *sink.grpc_server;
                    out.grpc_server.bind_ip = detail::to_dl_string(server.bind_ip);
                    out.grpc_server.port = server.port;
                    out.grpc_server.server_memory_limit =
                        detail::to_dl_string(server.server_memory_limit);
                    out.grpc_server.newest_first =
                        server.playback_behavior == PlaybackBehavior::NewestFirst;
                    out.grpc_server.cors_allow_origins = nullptr;
                    out.grpc_server.num_cors_allow_origins = 0;
                    return out;
                }
                default:
                    assert(false && "unreachable");
            }
            return {};
        }
    } // namespace detail
} // namespace rerun
