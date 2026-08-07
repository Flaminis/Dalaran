# Dalaran web viewer

Embed the Dalaran web viewer within your app.

<p align="center">
  <picture>
    <img src="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/full.png" alt="">
    <source media="(max-width: 480px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/480w.png">
    <source media="(max-width: 768px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/768w.png">
    <source media="(max-width: 1024px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/1024w.png">
    <source media="(max-width: 1200px)" srcset="https://static.rerun.io/opf_screenshot/bee51040cba93c0bae62ef6c57fa703704012a41/1200w.png">
  </picture>
</p>

This package is framework-agnostic. A React wrapper is available at <https://www.npmjs.com/package/@dalaran/web-viewer-react>.

## Install

```sh
npm i @dalaran/web-viewer
```

ℹ️ Note:
The package version is equal to the supported Dalaran SDK version, and [DLR files are only partially stable across different versions](https://dalaran.dev/blog/release-0.23).
This means that:
- `@dalaran/web-viewer@0.10.0` can only connect to a data source (`.dlr` file, gRPC connection, etc.) that originates from a Dalaran SDK with version `0.10.0`!
- For versions after `@dalaran/web-viewer@0.23.0`, the Viewer can load data from the previous _minor_ version of Dalaran, e.g. `0.24` can load `0.23` files.

## Usage

The entrypoint for this packages is the [`WebViewer`](https://ref.dalaran.dev/docs/js/0.35.0/web-viewer/classes/WebViewer.html) class.
The web viewer is an object which manages a canvas element:

```js
import { WebViewer } from "@dalaran/web-viewer";

const dlr = "…";
const parentElement = document.body;

const viewer = new WebViewer();
await viewer.start(dlr, parentElement, { width: "800px", height: "600px" });
// …
viewer.stop();
```

The `dlr` in the snippet above should be a URL pointing to either:
- A hosted `.dlr` file, such as <https://app.dalaran.dev/version/0.35.0/examples/dna.dlr>
- A gRPC connection to the SDK opened via the [`serve`](https://www.dalaran.dev/docs/reference/sdk/operating-modes#serve) API

If `dlr` is not set, the Viewer will display the same welcome screen as <https://app.dalaran.dev>.
This can be disabled by setting `hide_welcome_screen` to `true` in the options object of `viewer.start`.

⚠ It's important to set the viewer's width and height, as without it the viewer may not display correctly.
Setting the values to empty strings is valid, as long as you style the canvas through other means.

For a full example, see https://github.com/rerun-io/web-viewer-example.
You can open the example via CodeSandbox: https://codesandbox.io/s/github/rerun-io/web-viewer-example

ℹ️ Note:
This package only targets recent versions of browsers.
If your target browser does not support Wasm imports or top-level await, you may need to install additional plugins for your bundler.

For more information about using the package, visit:
- [Integration docs](https://dalaran.dev/docs/howto/integrations/embed-web#using-the-javascript-package).
- [Package docs](https://ref.dalaran.dev/docs/js/0.26.0/web-viewer/index.html).
