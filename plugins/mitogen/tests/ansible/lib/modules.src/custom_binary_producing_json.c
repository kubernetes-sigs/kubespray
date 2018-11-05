#include <stdio.h>


int main(void)
{
    fprintf(stderr, "binary_producing_json: oh noes\n");
    printf("{"
            "\"changed\": true, "
            "\"failed\": false, "
            "\"msg\": \"Hello, world.\""
            "}\n");
    return 0;
}
