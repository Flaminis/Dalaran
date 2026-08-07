# dl_viewer_mcp

Part of the [`dalaran`](https://github.com/Flaminis/Dalaran) family of crates.

![MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Apache](https://img.shields.io/badge/license-Apache-blue.svg)

MCP server for the Dalaran Viewer. See the [docs](https://dalaran.dev/docs/reference/viewer/mcp) for more info.

## Development

There is a `.mcp.json` that Claude should pick up in the Dalaran repository root.

Use `cargo build -p dl_viewer_mcp` to build the updated mcp server, and then within claude use `/mcp` and select `dalaran` and
then reconnect, and it'll use the updated mcp (or reboot the cli).
