---
title: Embed Dalaran in Web pages
order: 100
---

Integrating the Dalaran Viewer into your web application can be accomplished either by [utilizing an iframe](#embedding-appdalaranio-using-an-iframe) or by using our [JavaScript package](#using-the-javascript-package).

## Embedding `app.dalaran.dev` using an `<iframe>`

This approach is straightforward and requires minimal setup. However, the drawback is that it lacks programmable control over the web viewer.

```html
<iframe src="https://app.dalaran.dev/version/{DALARAN_VERSION}/index.html?url={DLR_URL}"></iframe>
```

To implement this, fill in the placeholders:
- `DLR_URL` - The URL of the recording to display in the viewer.
- `DALARAN_VERSION` - The version of the Dalaran SDK used to generate the recording.

The `DLR_URL` can be a file served over `http` (e.g. `https://app.dalaran.dev/version/0.20.3/examples/arkit_scenes.dlr`), or a connection to an SDK using our [serve](https://www.dalaran.dev/docs/reference/sdk/operating-modes#serve) API (e.g. `dalaran+http://localhost:4321/proxy`).

For instance:

```html
<iframe src="https://app.dalaran.dev/version/0.20.3/?url=https://app.dalaran.dev/version/0.20.3/examples/arkit_scenes.dlr"></iframe>
```

### Matching the host page's theme

By default, the embedded viewer follows the user's OS theme (`prefers-color-scheme`). If your host page has its own theme toggle, you can pin the viewer to match by passing `theme=dark`, `theme=light`, or `theme=system`:

```html
<iframe src="https://app.dalaran.dev/version/{DALARAN_VERSION}/?url={DLR_URL}&theme=dark"></iframe>
```

This is useful for sites whose theme can differ from the OS preference — without it, a user on a light-mode OS visiting your dark-mode page would see a bright viewer panel against a dark background.

## Using the JavaScript package

We offer JavaScript bindings to the Dalaran Viewer via NPM. This method provides control over the Viewer but requires a JavaScript web application setup with a bundler.

Various packages are available:
- [@dalaran/web-viewer](https://www.npmjs.com/package/@dalaran/web-viewer): Suitable for JS apps without a framework or frameworks without dedicated packages.
- [@dalaran/web-viewer-react](https://www.npmjs.com/package/@dalaran/web-viewer-react): Designed specifically for React apps.

> [!NOTE]
> The stability of the `dlr` format is still evolving, so the package version corresponds to the supported Dalaran SDK version. Therefore, `@dalaran/web-viewer@0.10.0` can only connect to a data source (`.dlr` file, gRPC connection, etc.) originating from a Dalaran SDK with version `0.10.0`!

### Basic example

To begin, install the package ([@dalaran/web-viewer](https://www.npmjs.com/package/@dalaran/web-viewer)) from NPM:

```
npm i @dalaran/web-viewer
```

> [!NOTE]
> This package is compatible only with recent browser versions. If your target browser lacks support for Wasm imports or top-level await, additional plugins may be required for your bundler setup. For instance, if you're using [Vite](https://vitejs.dev/), you'll need to install [vite-plugin-wasm](https://www.npmjs.com/package/vite-plugin-wasm) and [vite-plugin-top-level-await](https://www.npmjs.com/package/vite-plugin-top-level-await) and integrate them into your `vite.config.js`.

Once installed and configured, import and use it within your application:

```js
import { WebViewer } from "@dalaran/web-viewer";

const rrdUrl = null;
const parentElement = document.body;

const viewer = new WebViewer();
await viewer.start(rrdUrl, parentElement);
```

The Viewer creates a `<canvas>` on the provided `parentElement` and executes within it.

The first argument for `start` determines the recordings to open in the viewer. It can be:
- `null` for an initially empty viewer
- a URL string to open a single recording
- an array of strings to open multiple recordings

Each URL can be either a file served over `http` or a connection to an SDK using our [serve](https://www.dalaran.dev/docs/reference/sdk/operating-modes#serve) API. See [web-viewer-serve-example](https://github.com/rerun-io/web-viewer-serve-example) for a full example of how to log data from our Python SDK to an embedded Dalaran Viewer.

### Controlling the canvas

By default, the web viewer attempts to expand the canvas to occupy all available space. You can customize its dimensions by placing it within a container:

```html,id=embed-web-viewer-canvas-control-html
<body>
  <div id="viewer-container"></div>
</body>
```

```css,id=embed-web-viewer-canvas-control-css
#viewer-container {
  position: relative;
  height: 640px;
  width: 100%;
}
```

```js,id=embed-web-viewer-canvas-control-js
const parentElement = document.getElementById("viewer-container");

const viewer = new WebViewer();
await viewer.start(null, parentElement);
```

### Viewer API

The Viewer API supports adding and removing recordings:

```js,id=embed-web-viewer-api-js-open-close
const rrdUrl = "https://app.dalaran.dev/version/0.20.3/examples/arkit_scenes.dlr";

// Open a recording:
viewer.open(rrdUrl);

// Later on…
viewer.close(rrdUrl);
```

Once finished with the Viewer, you can stop it and release all associated resources:

```js,id=embed-web-viewer-api-js-stop
viewer.stop();
```

This action also removes the canvas from the page.

You can `start` and `stop` the same `WebViewer` instance multiple times.

### Callbacks

The Viewer API also allows registering callbacks for certain events.

For example, here is how you would react to entities being selected in the Viewer:
```js
viewer.on("selection_change", (event) => {
  for (const item of event.items) {
    if (item.type === "entity") {
      console.log(item.entity_path);
    }
  }
});
```

