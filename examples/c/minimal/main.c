#include <rerun.h>
#include <stdio.h>

int main(void) {
    printf("Rerun C SDK Version: %s\n", dl_version_string());

    dl_error error = {0};
    const dl_store_info store_info = {
        .application_id = dl_make_string("c-example-app"),
        .recording_id = dl_make_string(NULL),
        .store_kind = DL_STORE_KIND_RECORDING,
    };
    dl_recording_stream rec = dl_recording_stream_new(&store_info, true, &error);

    // Connect to running viewer:
    //dl_recording_stream_connect_grpc(rec, dl_make_string("rerun+http://127.0.0.1:9876"), &error);

    // Spawn and connect:
    dl_recording_stream_spawn(rec, NULL, &error);

    if (error.code != 0) {
        printf("Error occurred: %s\n", error.description);
        return 1;
    }

    printf("rec: %d\n", rec);

    dl_recording_stream_free(rec);
}
