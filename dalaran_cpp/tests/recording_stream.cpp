#include <array>
#include <filesystem>
#include <optional>
#include <vector>

#include <arrow/array/array_base.h>
#include <arrow/buffer.h>
#include <catch2/catch_test_macros.hpp>
#include <catch2/generators/catch_generators.hpp>
#include <dalaran.hpp>

#include <dalaran/c/dalaran.h>

#include "error_check.hpp"

namespace fs = std::filesystem;

#define TEST_TAG "[recording_stream]"

struct BadComponent {};

// Not making this static makes lsan_suppressions.supp miss this.
// Output of use counter for this shared_ptr indicates that we're not leaking the shared ptr itself.
// If we do leak it, it's very unclear how that would be happening - somewhere in the FFI transition?
// But then why would it not show up for anything else? More likely a false positive.
static std::shared_ptr<arrow::Array> null_arrow_array() {
    return std::make_shared<arrow::NullArray>(1);
}

template <>
struct dalaran::Loggable<BadComponent> {
    static constexpr dalaran::ComponentDescriptor Descriptor = "bad!";
    static dalaran::Error error;

    static const std::shared_ptr<arrow::DataType>& arrow_datatype() {
        return dalaran::Loggable<dalaran::components::Position2D>::arrow_datatype();
    }

    static dalaran::Result<std::shared_ptr<arrow::Array>> to_arrow(const BadComponent*, size_t) {
        return error;
    }
};

dalaran::Error dalaran::Loggable<BadComponent>::error =
    dalaran::Error(dalaran::ErrorCode::Unknown, "BadComponent");

struct BadArchetype {
    size_t num_instances() const {
        return 1;
    }
};

namespace dalaran {
    template <>
    struct AsComponents<BadArchetype> {
        static dalaran::Result<Collection<dalaran::ComponentBatch>> as_batches(const BadArchetype&) {
            return Loggable<BadComponent>::error;
        }
    };
} // namespace dalaran

namespace dalaran {
    std::ostream& operator<<(std::ostream& os, StoreKind kind) {
        switch (kind) {
            case dalaran::StoreKind::Recording:
                os << "StoreKind::Recording";
                break;
            case dalaran::StoreKind::Blueprint:
                os << "StoreKind::Blueprint";
                break;
            default:
                FAIL("Unknown StoreKind");
                break;
        }
        return os;
    }
} // namespace dalaran

SCENARIO("RecordingStream can be created, destroyed and lists correct properties", TEST_TAG) {
    const auto kind = GENERATE(dalaran::StoreKind::Recording, dalaran::StoreKind::Blueprint);

    GIVEN("recording stream kind" << kind) {
        AND_GIVEN("a valid application id") {
            THEN("creating a new stream does not log an error") {
                dalaran::RecordingStream stream = check_logged_error([&] {
                    return dalaran::RecordingStream("dalaran_example_test", std::string_view(), kind);
                });

                AND_THEN("it does not crash on destruction") {}

                AND_THEN("it reports the correct kind") {
                    CHECK(stream.kind() == kind);
                }
            }
        }

        // We changed to taking std::string_view instead of const char* and constructing such from nullptr crashes
        // at least on some C++ implementations.
        // If we'd want to support this in earnest we'd have to create out own string_view type.
        //
        // AND_GIVEN("a nullptr for the application id") {
        //     THEN("creating a new stream logs a null argument error") {
        //         check_logged_error(
        //             [&] { dalaran::RecordingStream stream(nullptr, kind); },
        //             dalaran::ErrorCode::UnexpectedNullArgument
        //         );
        //     }
        // }
        AND_GIVEN("invalid utf8 character sequence for the application id") {
            THEN("creating a new stream logs an invalid string argument error") {
                check_logged_error(
                    [&] { dalaran::RecordingStream stream("\xc3\x28", std::string_view(), kind); },
                    dalaran::ErrorCode::InvalidStringArgument
                );
            }
        }
    }
}

SCENARIO("RecordingStream can be set as global and thread local", TEST_TAG) {
    for (auto kind : std::array{dalaran::StoreKind::Recording, dalaran::StoreKind::Blueprint}) {
        GIVEN("a store kind" << kind) {
            WHEN("querying the current one") {
                auto& stream = dalaran::RecordingStream::current(kind);

                THEN("it reports the correct kind") {
                    CHECK(stream.kind() == kind);
                }

                THEN("it is not enabled") {
                    CHECK(!stream.is_enabled());
                }
            }

            WHEN("creating a new stream") {
                dalaran::RecordingStream stream("test", std::string_view(), kind);

                THEN("it can be set as global") {
                    stream.set_global();
                }
                THEN("it can be set as thread local") {
                    stream.set_thread_local();
                }

                // TODO(andreas): There's no way of telling right now if the set stream is
                // functional.
            }
        }
    }
}

SCENARIO("RecordingStream can be used for logging archetypes and components", TEST_TAG) {
    for (auto kind : std::array{dalaran::StoreKind::Recording, dalaran::StoreKind::Blueprint}) {
        GIVEN("a store kind" << kind) {
            WHEN("creating a new stream") {
                dalaran::RecordingStream stream("test", std::string_view(), kind);

                GIVEN("component batches") {
                    auto batch0 = dalaran::ComponentBatch::from_loggable<dalaran::Position2D>(
                                      {{1.0, 2.0}, {4.0, 5.0}},
                                      dalaran::Points2D::Descriptor_positions
                    )
                                      .value_or_throw();
                    auto batch1 = dalaran::ComponentBatch::from_loggable<dalaran::Color>(
                                      {dalaran::Color(0xFF0000FF)},
                                      dalaran::Points2D::Descriptor_colors
                    )
                                      .value_or_throw();
                    THEN("single component batch can be logged") {
                        stream.log("log_archetype-splat", batch0);
                        stream.log_static("log_archetype-splat", batch0);
                    }
                    THEN("component batches can be listed out") {
                        stream.log("log_archetype-splat", batch0, batch1);
                        stream.log_static("log_archetype-splat", batch0, batch1);
                    }
                    THEN("a collection of component batches can be logged") {
                        dalaran::Collection<dalaran::ComponentBatch> batches = {batch0, batch1};
                        stream.log("log_archetype-splat", batches);
                        stream.log_static("log_archetype-splat", batches);
                    }
                }
                GIVEN("component batches wrapped in `dalaran::Result`") {
                    auto batch0 = dalaran::ComponentBatch::from_loggable<dalaran::Position2D>(
                        {{1.0, 2.0}, {4.0, 5.0}},
                        dalaran::Points2D::Descriptor_positions
                    );
                    auto batch1 = dalaran::ComponentBatch::from_loggable<dalaran::Color>(
                        {dalaran::Color(0xFF0000FF)},
                        dalaran::Points2D::Descriptor_colors
                    );
                    THEN("single component batch can be logged") {
                        stream.log("log_archetype-splat", batch0);
                        stream.log_static("log_archetype-splat", batch0);
                    }
                    THEN("component batches can be listed out") {
                        stream.log("log_archetype-splat", batch0, batch1);
                        stream.log_static("log_archetype-splat", batch0, batch1);
                    }
                    THEN("collection of component batch results can be logged") {
                        dalaran::Collection<dalaran::Result<dalaran::ComponentBatch>> batches = {
                            batch0,
                            batch1,
                        };
                        stream.log("log_archetype-splat", batches);
                        stream.log_static("log_archetype-splat", batches);
                    }
                }

                THEN("an archetype can be logged") {
                    stream.log(
                        "log_archetype-splat",
                        dalaran::Points2D({dalaran::Vec2D{1.0, 2.0}, dalaran::Vec2D{4.0, 5.0}})
                            .with_colors(dalaran::Color(0xFF0000FF))
                    );
                    stream.log_static(
                        "log_archetype-splat",
                        dalaran::Points2D({dalaran::Vec2D{1.0, 2.0}, dalaran::Vec2D{4.0, 5.0}})
                            .with_colors(dalaran::Color(0xFF0000FF))
                    );
                }
                THEN("several archetypes can be logged") {
                    stream.log(
                        "log_archetype-splat",
                        dalaran::Points2D({dalaran::Vec2D{1.0, 2.0}, dalaran::Vec2D{4.0, 5.0}})
                            .with_colors(dalaran::Color(0xFF0000FF)),
                        dalaran::Points2D({dalaran::Vec2D{1.0, 2.0}, dalaran::Vec2D{4.0, 5.0}})
                            .with_colors(dalaran::Color(0xFF0000FF))
                    );
                    stream.log_static(
                        "log_archetype-splat",
                        dalaran::Points2D({dalaran::Vec2D{1.0, 2.0}, dalaran::Vec2D{4.0, 5.0}})
                            .with_colors(dalaran::Color(0xFF0000FF)),
                        dalaran::Points2D({dalaran::Vec2D{1.0, 2.0}, dalaran::Vec2D{4.0, 5.0}})
                            .with_colors(dalaran::Color(0xFF0000FF))
                    );
                }

                // TODO(andreas): There's no way of telling right now if the set stream is
                // functional and where those messages went.
            }
        }
    }
}

SCENARIO("RecordingStream can log to file", TEST_TAG) {
    const char* test_path = "build/test_output";
    fs::create_directories(test_path);

    std::string test_rrd0 = std::string(test_path) + "test-file-0.rrd";
    std::string test_rrd1 = std::string(test_path) + "test-file-1.rrd";

    fs::remove(test_rrd0);
    fs::remove(test_rrd1);

    GIVEN("a new RecordingStream") {
        auto stream0 = std::make_unique<dalaran::RecordingStream>("test");

        // We changed to taking std::string_view instead of const char* and constructing such from nullptr crashes
        // at least on some C++ implementations.
        // If we'd want to support this in earnest we'd have to create out own string_view type.
        //
        // AND_GIVEN("a nullptr for the save path") {
        //     THEN("then the save call returns a null argument error") {
        //         CHECK(stream0->save(nullptr).code == dalaran::ErrorCode::UnexpectedNullArgument);
        //     }
        // }
        AND_GIVEN("valid save path " << test_rrd0) {
            AND_GIVEN("a directory already existing at this path") {
                fs::create_directory(test_rrd0);
                THEN("then the save call fails") {
                    CHECK(
                        stream0->save(test_rrd0).code ==
                        dalaran::ErrorCode::RecordingStreamSaveFailure
                    );
                }
            }
            THEN("save call returns no error") {
                REQUIRE(stream0->save(test_rrd0).is_ok());

                THEN("a new file got immediately created") {
                    CHECK(fs::exists(test_rrd0));
                }

                WHEN("creating a second stream") {
                    auto stream1 = std::make_unique<dalaran::RecordingStream>("test2");

                    WHEN("saving that one to a different file " << test_rrd1) {
                        REQUIRE(stream1->save(test_rrd1).is_ok());

                        WHEN("logging an archetype to the second stream") {
                            check_logged_error([&] {
                                stream1->log(
                                    "archetype",
                                    dalaran::Points2D({
                                        dalaran::Vec2D{1.0, 2.0},
                                        dalaran::Vec2D{4.0, 5.0},
                                    })
                                );
                            });

                            THEN("after destruction, the second stream produced a bigger file") {
                                stream0.reset();
                                stream1.reset();
                                CHECK(fs::file_size(test_rrd0) < fs::file_size(test_rrd1));
                            }
                        }
                    }
                }
            }
        }
    }
}

void test_logging_to_grpc_connection(const char* url, const dalaran::RecordingStream& stream) {
    AND_GIVEN("an invalid url") {
        THEN("connect call fails") {
            CHECK(
                stream.connect_grpc("definitely not valid!").code ==
                dalaran::ErrorCode::InvalidServerUrl
            );
        }
    }
    AND_GIVEN("a valid socket url  " << url) {
        THEN("connect call returns no error") {
            CHECK(stream.connect_grpc(url).code == dalaran::ErrorCode::Ok);

            WHEN("logging an archetype and then flushing") {
                check_logged_error([&] {
                    stream.log(
                        "archetype",
                        dalaran::Points2D({dalaran::Vec2D{1.0, 2.0}, dalaran::Vec2D{4.0, 5.0}})
                    );
                });

                // The flush should fail, because there is no server on the other side:
                CHECK(
                    stream.flush_blocking().code == dalaran::ErrorCode::RecordingStreamFlushFailure
                );

                THEN("does not crash") {
                    // No easy way to see if it got sent.
                }

                THEN("the stream is still valid and we can log more things") {
                    // Regression test for https://github.com/rerun-io/rerun/issues/10884
                    check_logged_error([&] {
                        stream.log("archetype", dalaran::Points2D(dalaran::Vec2D{1.0, 2.0}));
                    });
                }
            }
        }
    }
}

SCENARIO("RecordingStream can construct LogSinks", TEST_TAG) {
    const char* url = "dalaran+http://127.0.0.1:9876/proxy";
    const char* invalid_url = "definitely not valid!";
    const char* test_path = "build/test_output";
    fs::create_directories(test_path);

    std::string test_rrd0 = std::string(test_path) + "test-file-log-sink-0.rrd";

    fs::remove_all(test_rrd0);

    GIVEN("a new RecordingStream") {
        dalaran::RecordingStream stream("test-local");

        AND_GIVEN("valid save path " << test_rrd0) {
            AND_GIVEN("a directory already existing at this path") {
                fs::create_directory(test_rrd0);
                THEN("set_sinks(FileSink) call fails") {
                    CHECK(
                        stream.set_sinks(dalaran::FileSink{test_rrd0}).code ==
                        dalaran::ErrorCode::RecordingStreamSaveFailure
                    );
                }
                fs::remove_all(test_rrd0);
            }
            THEN("set_sinks(FileSink) call returns no error") {
                CHECK(stream.set_sinks(dalaran::FileSink{test_rrd0}).code == dalaran::ErrorCode::Ok);
            }
        }

        AND_GIVEN("an invalid url " << invalid_url) {
            THEN("set_sinks(GrpcSink) call fails") {
                CHECK(
                    stream.set_sinks(dalaran::GrpcSink{invalid_url}).code ==
                    dalaran::ErrorCode::InvalidServerUrl
                );
            }
        }
        AND_GIVEN("a valid url " << url) {
            THEN("set_sinks(GrpcSink) call returns no error") {
                CHECK(stream.set_sinks(dalaran::GrpcSink{url}).code == dalaran::ErrorCode::Ok);
            }
        }

        AND_GIVEN("both a url " << url << " and a save path " << test_rrd0) {
            auto error = stream.set_sinks(dalaran::GrpcSink{url}, dalaran::FileSink{test_rrd0});
            AND_GIVEN("Error: " << error.description) {
                THEN("set_sinks(GrpcSink, FileSink) call returns no error") {
                    CHECK(error.code == dalaran::ErrorCode::Ok);
                }
            }
        }
    }
}

SCENARIO("RecordingStream can connect over grpc", TEST_TAG) {
    const char* url = "dalaran+http://127.0.0.1:9876/proxy";
    GIVEN("a new RecordingStream") {
        dalaran::RecordingStream stream("test-local");
        test_logging_to_grpc_connection(url, stream);
    }
    WHEN("setting a global RecordingStream and then discarding it") {
        {
            dalaran::RecordingStream stream("test-global");
            stream.set_global();
        }
        GIVEN("the current recording stream") {
            test_logging_to_grpc_connection(url, dalaran::RecordingStream::current());
        }
    }
}

SCENARIO("RecordingStream can set a grpc server sink", TEST_TAG) {
    dalaran::RecordingStream stream("test-local");
    dalaran::GrpcServerSink sink{
        "0.0.0.0",
        21522,
        "64MiB",
        dalaran::PlaybackBehavior::NewestFirst,
        {"https://*.example.com"}
    };
    CHECK(
        stream.set_sinks(sink, dalaran::FileSink{"build/test_output/server-sink.rrd"}).code ==
        dalaran::ErrorCode::Ok
    );
}

SCENARIO("RecordingStream can serve grpc", TEST_TAG) {
    GIVEN("a new serving RecordingStream") {
        dalaran::RecordingStream stream("test-local");
        THEN("serve_grpc call succeeds") {
            CHECK(
                stream.serve_grpc("0.0.0.0", 21521).value_or_throw() ==
                "dalaran+http://0.0.0.0:21521/proxy"
            );
        }
    }
}

SCENARIO("Recording stream handles invalid logging gracefully", TEST_TAG) {
    GIVEN("a new RecordingStream") {
        dalaran::RecordingStream stream("test");

        AND_GIVEN("a valid path") {
            const char* path = "valid";

            AND_GIVEN("a cell with a null buffer") {
                dalaran::ComponentBatch cell = {};
                cell.component_type = 0;

                THEN("try_log_data_row fails with UnexpectedNullArgument") {
                    CHECK(
                        stream.try_log_data_row(path, 1, &cell, true).code ==
                        dalaran::ErrorCode::UnexpectedNullArgument
                    );
                }
            }
            AND_GIVEN("a cell with an invalid component type") {
                dalaran::ComponentBatch cell = {};
                cell.component_type = DL_COMPONENT_TYPE_HANDLE_INVALID;
                cell.array = null_arrow_array();

                THEN("try_log_data_row fails with InvalidComponentTypeHandle") {
                    CHECK(
                        stream.try_log_data_row(path, 1, &cell, true).code ==
                        dalaran::ErrorCode::InvalidComponentTypeHandle
                    );
                }
            }
        }
    }
}

SCENARIO("Recording stream handles serialization failure during logging gracefully", TEST_TAG) {
    GIVEN("a new RecordingStream and a valid entity path") {
        dalaran::RecordingStream stream("test");
        const char* path = "valid";
        auto& expected_error = dalaran::Loggable<BadComponent>::error;

        AND_GIVEN("an component batch result that failed serialization") {
            const auto component = BadComponent();

            expected_error.code =
                GENERATE(dalaran::ErrorCode::Unknown, dalaran::ErrorCode::ArrowStatusCode_TypeError);

            auto batch_result = dalaran::ComponentBatch::from_loggable(
                component,
                dalaran::Loggable<BadComponent>::Descriptor
            );

            THEN("calling log with that batch logs the serialization error") {
                check_logged_error([&] { stream.log(path, batch_result); }, expected_error.code);
            }
            THEN("calling log with a collection wrapping that batch logs the serialization error") {
                check_logged_error(
                    [&] { stream.log(path, dalaran::Collection{batch_result}); },
                    expected_error.code
                );
            }
        }
        AND_GIVEN("an archetype that fails serialization") {
            auto archetype = BadArchetype();
            expected_error.code =
                GENERATE(dalaran::ErrorCode::Unknown, dalaran::ErrorCode::ArrowStatusCode_TypeError);

            THEN("calling log_archetype logs the serialization error") {
                check_logged_error([&] { stream.log(path, archetype); }, expected_error.code);
            }
            THEN("calling log_archetype forwards the serialization error") {
                CHECK(stream.try_log(path, archetype) == expected_error);
            }
        }
    }
}

SCENARIO("RecordingStream can set time without errors", TEST_TAG) {
    dalaran::RecordingStream stream("test");

    SECTION("set_time_sequence does not log errors") {
        check_logged_error([&] { stream.set_time_sequence("sequence", 1); });
    }

    SECTION("set_time_duration does not log errors") {
        using namespace std::chrono_literals;
        check_logged_error([&] { stream.set_time_duration("duration", 1.0s); });
        check_logged_error([&] { stream.set_time_duration("duration", 1000ms); });
    }
    SECTION("set_time_duration_secs does not log errors") {
        check_logged_error([&] { stream.set_time_duration_secs("duration", 1.0); });
    }
    SECTION("set_time_duration_nanos does not log errors") {
        check_logged_error([&] { stream.set_time_duration_nanos("duration", 1); });
    }
    SECTION("set_time_timestamp_secs_since_epoch does not log errors") {
        check_logged_error([&] { stream.set_time_timestamp_secs_since_epoch("capture_time", 1.0); }
        );
    }

    SECTION("set_time_timestamp_nanos_since_epoch does not log errors") {
        check_logged_error([&] { stream.set_time_timestamp_nanos_since_epoch("capture_time", 1); });
    }
    SECTION("set_time_timestamp does not log errors") {
        check_logged_error([&] {
            stream.set_time_timestamp("timepoint", std::chrono::system_clock::now());
        });
    }

    SECTION("Resetting time does not log errors") {
        check_logged_error([&] { stream.reset_time(); });
    }
    SECTION("Can set time again after resetting the time") {
        check_logged_error([&] { stream.reset_time(); });
        check_logged_error([&] { stream.set_time_duration_secs("duration", 1.0f); });
    }

    SECTION("Disabling timeline does not log errors") {
        check_logged_error([&] { stream.disable_timeline("doesn't exist"); });
        check_logged_error([&] { stream.set_time_sequence("exists!", 123); });
        check_logged_error([&] { stream.disable_timeline("exists"); });
    }
}

SCENARIO("Global RecordingStream doesn't cause crashes", TEST_TAG) {
    // This caused a crash on Mac & Linux due to issues with cleanup order of global variables
    // in Rust vs C++.
    // See:
    // * https://github.com/rerun-io/rerun/issues/5697
    // * https://github.com/rerun-io/rerun/issues/5260
    static dalaran::RecordingStream global_stream("global");
}
