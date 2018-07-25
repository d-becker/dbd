import io, shutil
from pathlib import Path

from component_builder import Configuration, DistType

def generate_output(configuration: Configuration, output_location: Path) -> None:
    if not output_location.is_dir():
        raise ValueError("The provided output location is not a directory.")

    out = output_location / "{}_{}".format(configuration.name, configuration.timestamp)
    out.mkdir()

    with (out / "output_configuration.yaml").open("w") as file:
        config_report = generate_config_report(configuration)
        file.write(config_report)

    with (out / ".env").open("w") as file:
        env_file_text = generate_env_file_text(configuration)
        file.write(env_file_text)

    docker_dependency_dir = configuration.resource_path / "docker"
    docker_dependency_files = docker_dependency_dir.glob("*")
    for dependency_file in docker_dependency_files:
        shutil.copy(str(dependency_file), str(out))

def generate_config_report(configuration: Configuration) -> str:
    text = io.StringIO()

    text.write("name: {}\n".format(configuration.name))
    text.write("timestamp: {}\n".format(configuration.timestamp))
    text.write("components:\n")

    indentation = "  "
    for component, config in configuration.components.items():
        text.write(indentation + component + ":\n")

        text.write(indentation * 2 + "dist_type: "
                   + ("release" if config.dist_type == DistType.RELEASE else "snapshot")
                   + "\n")
        text.write(indentation * 2 + "version: " + config.version + "\n")
        text.write(indentation * 2 + "image_name: " + config.image_name + "\n")
    
    return text.getvalue()

def generate_env_file_text(configuration: Configuration) -> str:
    text = io.StringIO()

    for component, config in configuration.components.items():
        variable_name = "{}_IMAGE".format(component.upper())
        variable_value = config.image_name

        text.write("{}={}\n".format(variable_name, variable_value))

    return text.getvalue()
