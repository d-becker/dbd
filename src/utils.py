from enum import Enum, auto, unique

import docker

def image_exists_locally(client: docker.DockerClient, image_name: str) -> bool:
    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        return False
    else:
        return True
    

