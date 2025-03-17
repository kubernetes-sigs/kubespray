#!/usr/bin/env python

import subprocess
import ruamel.yaml
import os

last_tag = (
    subprocess.Popen(
        ["git", "describe", "--tags", "--abbrev=0"], stdout=subprocess.PIPE
    )
    .communicate()[0]
    .rstrip()
    .decode("utf-8")
    .removeprefix("v")
    .split(".")
)
# Use CI provided base ref if available, else use HEAD to guess
git_branch = os.getenv(
    "GITHUB_BASE_REF",
    (
        subprocess.Popen(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stdout=subprocess.PIPE
        )
        .communicate()[0]
        .rstrip()
        .decode("utf-8")
    ),
)
if git_branch.startswith("release"):
    version_comp_index = 2
else:
    version_comp_index = 1

last_tag[version_comp_index] = str(int(last_tag[version_comp_index]) + 1)
new_tag = ".".join(last_tag)

yaml = ruamel.yaml.YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.explicit_start = True

with open(
    "galaxy.yml",
) as galaxy_yml:
    config = yaml.load(galaxy_yml)

config["version"] = new_tag

with open("galaxy.yml", "w") as galaxy_yml:
    yaml.dump(config, galaxy_yml)
