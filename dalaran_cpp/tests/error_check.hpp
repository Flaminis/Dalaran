#pragma once

#include <catch2/catch_test_macros.hpp>

#include <dalaran/error.hpp>

/// Checks if the given operation logs the expected status code.
template <typename Op>
auto check_logged_error(
    Op operation, dalaran::ErrorCode expected_status_code = dalaran::ErrorCode::Ok
) {
    static dalaran::Error last_logged_status;

    // Set to Ok since nothing logged indicates success for most methods.
    last_logged_status.code = dalaran::ErrorCode::Ok;

    dalaran::Error::set_log_handler(
        [](const dalaran::Error& status, void* userdata) {
            *static_cast<dalaran::Error*>(userdata) = status;
        },
        &last_logged_status
    );

    struct CheckOnDestruct {
        dalaran::ErrorCode expected_status_code;

        ~CheckOnDestruct() {
            CHECK(last_logged_status.code == expected_status_code);
            if (expected_status_code != dalaran::ErrorCode::Ok) {
                CHECK(last_logged_status.description.length() > 0);
            } else {
                CHECK(last_logged_status.description == "");
            }
            dalaran::Error::set_log_handler(nullptr);
        }
    } check = {expected_status_code};

    // `auto result = operation();` won't compile for void
    // but `return operation();` is just fine.
    return operation();
}
