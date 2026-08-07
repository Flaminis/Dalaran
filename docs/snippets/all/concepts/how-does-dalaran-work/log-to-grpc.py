import dalaran as dl

dl.init("dalaran_example_log_to_grpc")

# Connect to the Dalaran gRPC server using the default address and url: dalaran+http://localhost:9876/proxy
dl.connect_grpc()

# Log data as usual, thereby pushing it into the gRPC connection.
while True:
    dl.log("/", dl.TextLog("Logging things…"))
