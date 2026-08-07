# Run-time memory tracking and profiling.

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.

[![Latest version](https://img.shields.io/crates/v/dl_memory.svg)](https://crates.io/crates/dl_memory)
[![Documentation](https://docs.rs/dl_memory/badge.svg)](https://docs.rs/dl_memory)
![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

This is a library for tracking memory use in a running application.
This is useful for tracking leaks, and for figuring out what is using up memory.

`dl_memory` includes an opt-in sampling profiler for allocation callstacks.
Each time memory is allocated there is a chance a callstack will be collected.
This information is tracked until deallocation.
You can thus get information about what callstacks lead to the most live allocations,
giving you a very useful memory profile of your running app, with minimal overhead.
