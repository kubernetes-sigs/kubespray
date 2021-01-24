# Container image collecting script for offline deployment

This script has two features:
(1) Get container images from an environment which is deployed online.
(2) Deploy local container registry and register the container images to the registry.

Step(1) should be done online site as a preparation, then we bring the gotten images
to the target offline environment.
Then we will run step(2) for registering the images to local registry.

Step(1) can be operated with:

```shell
manage-offline-container-images.sh   create
```

Step(2) can be operated with:

```shell
manage-offline-container-images.sh   register
```
