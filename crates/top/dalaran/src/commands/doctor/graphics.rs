//! The graphics check: can wgpu find an adapter the Viewer can actually draw on?
//!
//! This is the single most common cause of "the Viewer shows a black screen" or "the Viewer
//! refuses to start", and it is the one thing a user cannot find out on their own: `glxinfo` and
//! friends answer a different question than the one wgpu asks.
//!
//! The whole module is gated on the `native_viewer` feature, because that is what pulls in
//! `dl_renderer` (and thus wgpu). A build without a Viewer has no graphics to diagnose.

use super::report::{Check, Status};

/// Enumerates wgpu adapters and reports what the Viewer would end up drawing with.
#[cfg(feature = "native_viewer")]
pub fn check_graphics(tokio_runtime: &tokio::runtime::Handle) -> Check {
    use dl_renderer::external::wgpu;

    let enabled_backends = backend_names(wgpu::Instance::enabled_backend_features());

    // The exact same descriptor the Viewer uses, environment overrides (`WGPU_BACKEND`,
    // `WGPU_POWER_PREF`, ...) included, so that what we report is what the Viewer will get.
    let descriptor = dl_renderer::device_caps::instance_descriptor(None);
    let requested_backends = backend_names(descriptor.backends);
    let enabled_for_instance = descriptor.backends;
    let instance = wgpu::Instance::new(descriptor);

    let adapters = tokio_runtime.block_on(instance.enumerate_adapters(wgpu::Backends::all()));

    let described = adapters
        .iter()
        .map(|adapter| describe_adapter(&adapter.get_info()))
        .collect::<Vec<_>>();

    let check = Check::new("graphics", Status::Ok, String::new())
        .with_detail("enabled_backends", serde_json::json!(enabled_backends))
        .with_detail("requested_backends", serde_json::json!(requested_backends))
        .with_detail("adapters", serde_json::json!(described))
        .with_detail("num_adapters", adapters.len());

    let Some(best) =
        dl_renderer::device_caps::select_adapter(&adapters, enabled_for_instance, None)
            .ok()
            .map(|adapter| adapter.get_info())
    else {
        return check
            .with_status(
                Status::Fail,
                format!(
                    "no usable graphics adapter for the enabled backend(s): {}",
                    requested_backends.join(", ")
                ),
            )
            .with_hint(
                "The Viewer cannot open a window without one. On a headless or containerized \
                 machine, install a software rasterizer (Mesa's `lavapipe`), or use \
                 `dalaran --serve-web` and view in a browser instead.",
            );
    };

    let check = check
        .with_detail("selected_adapter", describe_adapter(&best))
        .with_detail("selected_backend", best.backend.to_string());

    // A CPU adapter works, but at a few frames per second on any real recording. Users who end up
    // there by accident always think the Viewer is broken rather than slow.
    if best.device_type == wgpu::DeviceType::Cpu {
        return check
            .with_status(
                Status::Warn,
                format!("only software rendering is available ({})", best.name),
            )
            .with_hint(
                "Expect single-digit frame rates. Install a GPU driver wgpu can use, or set \
                 WGPU_BACKEND=gl to try the OpenGL fallback.",
            );
    }

    // Apple's Metal driver reports no version at all, so only mention the driver when there is
    // one; `Apple M4 Pro via metal ()` helps nobody.
    let driver = format!("{} {}", best.driver, best.driver_info);
    let driver = driver.trim();
    let summary = if driver.is_empty() {
        format!("{} via {}", best.name, best.backend)
    } else {
        format!("{} via {} ({driver})", best.name, best.backend)
    };

    check.with_status(Status::Ok, summary)
}

/// Without a Viewer there is no renderer to ask, so there is nothing to diagnose either.
#[cfg(not(feature = "native_viewer"))]
pub fn check_graphics(_tokio_runtime: &tokio::runtime::Handle) -> Check {
    Check::new(
        "graphics",
        Status::Skip,
        "this build has no native viewer, so it never touches the GPU",
    )
    .with_detail("native_viewer", false)
}

/// A JSON object describing one adapter, in the terms a driver bug report needs.
#[cfg(feature = "native_viewer")]
fn describe_adapter(info: &dl_renderer::external::wgpu::AdapterInfo) -> serde_json::Value {
    serde_json::json!({
        "name": info.name,
        "backend": info.backend.to_string(),
        "device_type": format!("{:?}", info.device_type),
        "driver": info.driver,
        "driver_info": info.driver_info,
        "vendor": format!("0x{:04x}", info.vendor),
        "device": format!("0x{:04x}", info.device),
    })
}

/// The lowercase names of the backends in `backends`, e.g. `["metal", "vulkan"]`.
#[cfg(feature = "native_viewer")]
fn backend_names(backends: dl_renderer::external::wgpu::Backends) -> Vec<String> {
    use dl_renderer::external::wgpu::Backends;

    [
        (Backends::VULKAN, "vulkan"),
        (Backends::METAL, "metal"),
        (Backends::DX12, "dx12"),
        (Backends::GL, "gl"),
        (Backends::BROWSER_WEBGPU, "webgpu"),
    ]
    .into_iter()
    .filter(|(backend, _)| backends.contains(*backend))
    .map(|(_, name)| name.to_owned())
    .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Whatever machine this runs on, the check must produce a well-formed result and must not
    /// panic - including on CI, where there may be no GPU at all.
    #[test]
    fn test_graphics_check_is_well_formed_everywhere() {
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .unwrap();

        let check = check_graphics(runtime.handle());
        assert_eq!(check.name, "graphics");
        assert!(!check.summary.is_empty());

        // A failure must always come with something the user can act on.
        if check.status == Status::Fail {
            assert!(check.hint.is_some());
        }
    }

    #[cfg(feature = "native_viewer")]
    #[test]
    fn test_backend_names_are_stable() {
        use dl_renderer::external::wgpu::Backends;

        assert_eq!(backend_names(Backends::empty()), Vec::<String>::new());
        assert_eq!(backend_names(Backends::METAL), ["metal"]);
        assert_eq!(
            backend_names(Backends::VULKAN | Backends::GL),
            ["vulkan", "gl"]
        );
    }
}
