# Rust quick start

## Installing Dalaran

To use the Dalaran SDK in your project, you need the [`dalaran` crate](https://crates.io/crates/dalaran) which you can add with `cargo add dalaran`.

Let's try it out in a brand-new Rust project:

```sh
cargo init cube && cd cube && cargo add dalaran --features native_viewer
```

Note that the Dalaran SDK requires a working installation of Rust 1.95+.

## Logging your own data

Add the following code to your `main.rs` file:

```rust
${EXAMPLE_CODE_RUST_CONNECT}
```

You can now run your application:

```shell
cargo run
```

Once everything finishes compiling, you will see the points in this viewer:

![Demo recording](https://static.rerun.io/intro_rust_result/cc780eb9bf014d8b1a68fac174b654931f92e14f/768w.png)

${HOW_DOES_IT_WORK}
