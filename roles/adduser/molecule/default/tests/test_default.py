import os
from pathlib import Path

import testinfra.utils.ansible_runner
import yaml
from ansible.cli.playbook import PlaybookCLI
from ansible.playbook import Playbook

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ["MOLECULE_INVENTORY_FILE"]
).get_hosts("all")


def read_playbook(playbook):
    cli_args = [os.path.realpath(playbook), testinfra_hosts]
    cli = PlaybookCLI(cli_args)
    cli.parse()
    loader, inventory, variable_manager = cli._play_prereqs()

    pb = Playbook.load(cli.args[0], variable_manager, loader)

    for play in pb.get_plays():
        yield variable_manager.get_vars(play)


def get_playbook():
    playbooks_path = Path(__file__).parent.parent
    with open(os.path.join(playbooks_path, "molecule.yml"), "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        if "playbooks" in data["provisioner"].keys():
            if "converge" in data["provisioner"]["playbooks"].keys():
                return data["provisioner"]["playbooks"]["converge"]
        else:
            return os.path.join(playbooks_path, "converge.yml")


def test_user(host):
    for vars in read_playbook(get_playbook()):
        assert host.user(vars["user"]["name"]).exists
        if "group" in vars["user"].keys():
            assert host.group(vars["user"]["group"]).exists
        else:
            assert host.group(vars["user"]["name"]).exists
