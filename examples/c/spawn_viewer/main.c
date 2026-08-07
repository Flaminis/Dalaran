#include <rerun.h>
#include <stdio.h>

int main(void) {
    dl_error error = {};
    dl_spawn(NULL, &error);

    if (error.code != 0) {
        printf("Error occurred: %s\n", error.description);
        return 1;
    }
}
