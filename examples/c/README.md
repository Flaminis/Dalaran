# Dalaran C API

The Dalaran C library provides a minimalistic C interface that encapsulates the shared building blocks of all Dalaran SDKs.
It's a key dependency of the Dalaran C++ SDK, serving as the primary language interface into the Rust codebase.

⚠️ It currently serves *exclusively* this language binding purpose.
It is not a full SDK yet as there's no utilities for serializing data for logging any of the built-in types.
As of now it can only log raw Arrow IPC messages.
