"""DNA-abacus example, connecting to a separately-running viewer over gRPC."""

import dalaran as dl

dl.init("dalaran_example_dna_abacus")
dl.connect_grpc()  # connect to the viewer running at the default URL

# … log data as in the spawn-based example …
