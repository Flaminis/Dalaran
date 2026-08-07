<!--[metadata]
title = "Multiprocess logging"
description = "Log to the same Dalaran viewer from multiple Python processes with `multiprocessing` and `@dl.shutdown_at_exit`."
thumbnail = "https://static.rerun.io/multiprocessing/959e2c675f52a7ca83e11e5170903e8f0f53f5ed/480w.png"
thumbnail_dimensions = [480, 480]
tags = ["API example"]
-->

Demonstrates how Dalaran can work with the Python `multiprocessing` library.

<picture>
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/multiprocessing/72bcb7550d84f8e5ed5a39221093239e655f06de/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/multiprocessing/72bcb7550d84f8e5ed5a39221093239e655f06de/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/multiprocessing/72bcb7550d84f8e5ed5a39221093239e655f06de/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/multiprocessing/72bcb7550d84f8e5ed5a39221093239e655f06de/1200w.png">
  <img src="https://static.rerun.io/multiprocessing/72bcb7550d84f8e5ed5a39221093239e655f06de/full.png" alt="">
</picture>

## Used Dalaran types
[`Boxes2D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes2d), [`TextLog`](https://www.dalaran.dev/docs/reference/types/archetypes/text_log)

## Logging and visualizing with Dalaran
This example demonstrates how to use the Dalaran SDK with `multiprocessing` to log data from multiple processes to the same Dalaran viewer.
It starts with the definition of the function for logging, the `task`, followed by typical usage of Python's `multiprocessing` library.

The function `task` is decorated with `@dl.shutdown_at_exit`. This decorator ensures that data is flushed when the task completes, even if the normal `atexit`-handlers are not called at the termination of a multiprocessing process.

```python
@dl.shutdown_at_exit
def task(child_index: int) -> None:
    dl.init("dalaran_example_multiprocessing")

    dl.connect_grpc()

    title = f"task_{child_index}"
    dl.log(
        "log",
        dl.TextLog(
            f"Logging from pid={os.getpid()}, thread={threading.get_ident()} using the Dalaran recording id {dl.get_recording_id()}"
        ),
    )
    if child_index == 0:
        dl.log(title, dl.Boxes2D(array=[5, 5, 80, 80], array_format=dl.Box2DFormat.XYWH, labels=title))
    else:
        dl.log(
            title,
            dl.Boxes2D(
                array=[10 + child_index * 10, 20 + child_index * 5, 30, 40],
                array_format=dl.Box2DFormat.XYWH,
                labels=title,
            ),
        )
```

The main function initializes Dalaran with a specific application ID and manages the multiprocessing processes for logging data to the Dalaran viewer.

> Caution: Ensure that the `recording id` specified in the main function matches the one used in the logging functions
 ```python
def main() -> None:
    # … existing code …

    dl.init("dalaran_example_multiprocessing")
    dl.spawn(connect=False)  # this is the Viewer that each child process will connect to

    task(0)

    for i in [1, 2, 3]:
        p = multiprocessing.Process(target=task, args=(i,))
        p.start()
        p.join()
 ```

## Run the code
To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:rerun-io/rerun.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/multiprocessing
```
To experiment with the provided example, simply execute the main Python script:
```bash
python -m multiprocessing # run the example
```
If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:
```bash
python -m multiprocessing --help
```
