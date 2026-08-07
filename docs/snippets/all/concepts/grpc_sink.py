"""Create and set a GRPC sink."""

import dalaran as dl

dl.init("dalaran_example_grpc_sink")

# The default URL is `dalaran+http://127.0.0.1:9876/proxy`
# This can be used to connect to a viewer on a different machine
dl.set_sinks(dl.GrpcSink("dalaran+http://127.0.0.1:9876/proxy"))
