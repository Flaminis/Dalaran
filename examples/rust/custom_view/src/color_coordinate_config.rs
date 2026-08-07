//! Custom blueprint configuration for the color coordinates view.
//!
//! Built-in views get this from `.fbs` + codegen. This example does it manually:
//! define a component, make it [`dalaran::Loggable`], group it in an [`dalaran::Archetype`], provide
//! reflection, and register an editor UI.

use dalaran::external::egui;
use dalaran::external::dl_sdk_types::reflection::{
    ArchetypeFieldFlags, ArchetypeFieldReflection, ArchetypeReflection,
};
use dalaran::external::dl_sdk_types::{ArchetypeName, ComponentDescriptor};
use dalaran::external::dl_viewer_context::MaybeMutRef;

/// Blueprint properties for the color coordinates view.
pub struct ColorCoordinatesConfiguration;

impl ColorCoordinatesConfiguration {
    pub fn descriptor_mode() -> ComponentDescriptor {
        ComponentDescriptor {
            archetype: Some(<Self as dalaran::Archetype>::name()),
            component: "ColorCoordinates:mode".into(),
            component_type: Some(<ColorCoordinatesMode as dalaran::Component>::name()),
        }
    }

    /// Minimal reflection metadata for the `mode` field.
    pub fn field_mode() -> ArchetypeFieldReflection {
        ArchetypeFieldReflection {
            name: "mode",
            display_name: "Coordinates mode",
            component_type: <ColorCoordinatesMode as dalaran::Component>::name(),
            docstring_md: "The color channels to use as 2D coordinates.",
            flags: ArchetypeFieldFlags::UI_EDITABLE,
        }
    }

    /// Reflection metadata for the custom archetype.
    ///
    /// Register once with [`dalaran::external::dl_viewer::App::add_archetype_reflection`] to enable
    /// `dl_view::view_property_ui::<ColorCoordinatesConfiguration>`.
    pub fn reflection() -> ArchetypeReflection {
        ArchetypeReflection {
            display_name: <Self as dalaran::Archetype>::display_name(),
            deprecation_summary: None,
            view_types: &[],
            scope: Some("blueprint"),
            fields: vec![Self::field_mode()],
        }
    }
}

impl dalaran::Archetype for ColorCoordinatesConfiguration {
    fn name() -> ArchetypeName {
        "dalaran.blueprint.archetypes.ColorCoordinates".into()
    }

    fn display_name() -> &'static str {
        "Coordinates mode"
    }

    fn required_components() -> std::borrow::Cow<'static, [ComponentDescriptor]> {
        std::borrow::Cow::Borrowed(&[])
    }

    fn optional_components() -> std::borrow::Cow<'static, [ComponentDescriptor]> {
        std::borrow::Cow::Owned(vec![Self::descriptor_mode()])
    }
}

impl dalaran::external::dl_sdk_types::ArchetypeReflectionMarker for ColorCoordinatesConfiguration {}

/// The different modes for displaying color coordinates in the custom view.
///
/// This blueprint component is manually encoded as a `UInt32` below.
#[derive(Default, Debug, PartialEq, Eq, Clone, Copy, dalaran::SizeBytes)]
pub enum ColorCoordinatesMode {
    #[default]
    Hs,
    Hv,
    Rg,
}

impl ColorCoordinatesMode {
    pub const ALL: [ColorCoordinatesMode; 3] = [
        ColorCoordinatesMode::Hs,
        ColorCoordinatesMode::Hv,
        ColorCoordinatesMode::Rg,
    ];

    fn as_u32(self) -> u32 {
        match self {
            Self::Hs => 0,
            Self::Hv => 1,
            Self::Rg => 2,
        }
    }

    fn from_u32(value: u32) -> dalaran::DeserializationResult<Self> {
        match value {
            0 => Ok(Self::Hs),
            1 => Ok(Self::Hv),
            2 => Ok(Self::Rg),
            _ => Err(dalaran::DeserializationError::ValidationError(format!(
                "invalid color coordinates mode: {value}"
            ))),
        }
    }
}

impl dalaran::Loggable for ColorCoordinatesMode {
    // Components are stored as Arrow arrays; encode the enum as stable `UInt32` values.
    fn arrow_datatype() -> dalaran::external::arrow::datatypes::DataType {
        <dalaran::datatypes::UInt32 as dalaran::Loggable>::arrow_datatype()
    }

    fn to_arrow_opt<'a>(
        data: impl IntoIterator<Item = Option<impl Into<std::borrow::Cow<'a, Self>>>>,
    ) -> dalaran::SerializationResult<dalaran::external::arrow::array::ArrayRef>
    where
        Self: 'a,
    {
        <dalaran::datatypes::UInt32 as dalaran::Loggable>::to_arrow_opt(
            data.into_iter()
                .map(|mode| mode.map(|mode| dalaran::datatypes::UInt32(mode.into().as_u32()))),
        )
    }

    fn from_arrow_opt(
        data: &dyn dalaran::external::arrow::array::Array,
    ) -> dalaran::DeserializationResult<Vec<Option<Self>>> {
        <dalaran::datatypes::UInt32 as dalaran::Loggable>::from_arrow_opt(data)?
            .into_iter()
            .map(|mode| mode.map(|mode| Self::from_u32(mode.0)).transpose())
            .collect()
    }
}

impl dalaran::Component for ColorCoordinatesMode {
    // Pick a stable fully-qualified component type name.
    fn name() -> dalaran::ComponentType {
        "dalaran.blueprint.components.ColorCoordinatesMode".into()
    }
}

impl std::fmt::Display for ColorCoordinatesMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ColorCoordinatesMode::Hs => "Hue/Saturation".fmt(f),
            ColorCoordinatesMode::Hv => "Hue/Value".fmt(f),
            ColorCoordinatesMode::Rg => "Red/Green".fmt(f),
        }
    }
}

/// Single-line editor for `ColorCoordinatesMode`.
///
/// The registry writes back the value when the returned response is marked as changed.
pub fn edit_view_color_coordinates_mode(
    ui: &mut egui::Ui,
    value: &mut MaybeMutRef<'_, ColorCoordinatesMode>,
) -> egui::Response {
    if let Some(value) = value.as_mut() {
        let previous_value = *value;
        let mut response = egui::ComboBox::from_id_salt("color_coordinates_mode")
            .selected_text(value.to_string())
            .show_ui(ui, |ui| {
                for mode in ColorCoordinatesMode::ALL {
                    ui.selectable_value(value, mode, mode.to_string());
                }
            })
            .response;

        if *value != previous_value {
            response.mark_changed();
        }

        response
    } else {
        ui.label(value.to_string())
    }
}
