//! The `#[dalaran_type]` attribute proc-macro used by Dalaran's IDL definitions.
//!
//! Dalaran's type definitions are a subset of Rust that is parsed by `dl_types_builder` and
//! *also* compiled by rustc, purely so that we get name resolution, typo-checking,
//! rust-analyzer and `cargo fmt` for free. The definitions crate is never linked into anything.
//!
//! To make that work the definitions have to carry annotations that mean nothing to rustc:
//!
//! ```ignore
//! #[dalaran_type]
//! #[dalaran(state = "stable")]
//! #[rust(derive(Default, Copy, bytemuck::Pod))]
//! #[arrow(transparent)]
//! pub struct Position3D {
//!     /// The position.
//!     #[dalaran(required)]
//!     pub xyz: dalaran::datatypes::Vec3D,
//! }
//! ```
//!
//! `#[dalaran_type]` makes those compile. An attribute macro *consumes and replaces* the item it is
//! applied to, so it can simply delete the annotations before rustc ever tries to resolve them.
//! Note that this is not the same thing as helper-attribute registration: `attributes(…)` is a
//! `#[proc_macro_derive]` parameter and has no equivalent for attribute macros — it is also not
//! needed, precisely because a derive macro leaves the item in place while an attribute macro
//! does not.
//!
//! Attributes we do *not* recognize are left alone, on purpose. `#[repr(u8)]` in particular stays,
//! so rustc keeps validating it for us.

use proc_macro::TokenStream;
use quote::quote;

/// The annotations `#[dalaran_type]` strips.
///
/// Anything not in this list is passed through to rustc untouched — see the module docs.
const DALARAN_ATTRIBUTES: &[&str] = &[
    "arrow", "cpp", "default", "docs", "python", "dalaran", "rust",
];

/// Strips Dalaran's IDL annotations off a type definition so that rustc will accept it.
///
/// See the [crate docs](crate) for what this is for and why it is an attribute macro.
#[proc_macro_attribute]
pub fn dalaran_type(args: TokenStream, input: TokenStream) -> TokenStream {
    if !args.is_empty() {
        let args = proc_macro2::TokenStream::from(args);
        return syn::Error::new_spanned(
            args,
            "`#[dalaran_type]` takes no arguments; put them in `#[dalaran(…)]` instead",
        )
        .to_compile_error()
        .into();
    }

    let mut item = syn::parse_macro_input!(input as syn::Item);

    match &mut item {
        syn::Item::Struct(item) => {
            strip(&mut item.attrs);
            strip_fields(&mut item.fields);
        }

        syn::Item::Enum(item) => {
            strip(&mut item.attrs);
            for variant in &mut item.variants {
                strip(&mut variant.attrs);
                strip_fields(&mut variant.fields);
            }
        }

        other => {
            return syn::Error::new_spanned(
                other,
                "`#[dalaran_type]` can only be applied to a `struct` or an `enum`",
            )
            .to_compile_error()
            .into();
        }
    }

    quote!(#item).into()
}

fn strip_fields(fields: &mut syn::Fields) {
    for field in fields {
        strip(&mut field.attrs);
    }
}

fn strip(attrs: &mut Vec<syn::Attribute>) {
    attrs.retain(|attr| {
        attr.path()
            .get_ident()
            .is_none_or(|ident| !DALARAN_ATTRIBUTES.contains(&ident.to_string().as_str()))
    });
}
