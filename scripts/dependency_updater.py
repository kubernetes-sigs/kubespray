import os
import re
import sys
import logging
import requests
import time
import json
import argparse
import hashlib
from ruamel.yaml import YAML
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor
from dependency_config import component_info, architectures, oses, path_download, path_checksum, path_main, path_readme, path_version_diff


yaml = YAML()
yaml.explicit_start = True
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=4, offset=2)


pwd = os.getcwd()
cache_dir = './cache'
cache_expiry_seconds = 86400
os.makedirs(cache_dir, exist_ok=True)


github_api_url = 'https://api.github.com/graphql'
gh_token = os.getenv('GH_TOKEN')
if not gh_token:
    logging.error('GH_TOKEN is not set. You can set it via "export GH_TOKEN=<your-token>". Exiting.')
    sys.exit(1)


def setup_logging(loglevel):
    log_format = '%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s'
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {loglevel}')
    logging.basicConfig(level=numeric_level, format=log_format)

def get_session_with_retries():
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=50,
        pool_maxsize=50,
        max_retries=Retry(total=3, backoff_factor=1)
    )

    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def load_from_cache(component):
    cache_file = os.path.join(cache_dir, f'{component}.json')
    if os.path.exists(cache_file):
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age < cache_expiry_seconds:
            logging.info(f'Using cached release info for {component}')
            with open(cache_file, 'r') as f:
                return json.load(f)
    return None

def save_to_cache(component, data):
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f'{component}.json')
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f'Cached release info for {component}')

def get_current_version(component, component_data):
    kube_major_version = component_data['kube_major_version']
    placeholder_version = [kube_major_version if item == 'kube_major_version' else item for item in component_data['placeholder_version']]
    if component.startswith('kube'):
        current_version = main_yaml_data
    else:    
        current_version = download_yaml_data
    for key in placeholder_version:
        current_version = current_version.get(key)
    return current_version

def get_release(component, component_data, session, number_of_releases=10):
    release = load_from_cache(component)
    if not release:    
        try:
            query = """
                query {
                    repository(owner: "%s", name: "%s") {
                        releases(first: %s, orderBy: {field: CREATED_AT, direction: DESC}) {
                            nodes {
                                tagName
                                url
                                description
                                publishedAt
                                isLatest
                            }
                        }
                    }
                }
            """ % (component_data['owner'], component_data['repo'], number_of_releases)

            headers = {
                'Authorization': f'Bearer {gh_token}',
                'Content-Type': 'application/json'
            }

            response = session.post(github_api_url, json={'query': query}, headers=headers)
            response.raise_for_status()

            data = response.json()
            logging.debug(f'Component {component} releases: {data}')
            # Look for the release marked as latest
            for release_node in data['data']['repository']['releases']['nodes']:
                if release_node['isLatest']:
                    release = release_node
                    save_to_cache(component, release)
                    return release

            logging.warning(f'No latest release found for {component}')
            return None
        except Exception as e:
            logging.error(f'Error fetching latest release for {component}: {e}')
            return None
    return release

def get_release_tag(component, component_data, session):
    tag = load_from_cache(component)
    if not tag:
        try:
            query = """
                query {
                repository(owner: "%s", name: "%s") {
                    refs(refPrefix: "refs/tags/", first: 1, orderBy: {field: TAG_COMMIT_DATE, direction: DESC}) {
                    edges {
                        node {
                        name
                        }
                    }
                    }
                }
                }
            """ % (component_data['owner'], component_data['repo'])

            headers = {
                'Authorization': f'Bearer {gh_token}',
                'Content-Type': 'application/json'
            }

            response = session.post(github_api_url, json={'query': query}, headers=headers)
            response.raise_for_status()

            data = response.json()
            logging.debug(f'Component {component} releases: {data}')
            tag = data['data']['repository']['refs']['edges'][0]['node']
            save_to_cache(component, tag)
            return tag
        except Exception as e:
            logging.error(f'Error fetching tags for {component}: {e}')
            return None
    return tag

def calculate_checksum(cachefile, arch, url_download):
    if url_download.endswith('.sha256sum'):
        with open(f'cache/{cachefile}', 'r') as f:
            checksum_line = f.readline().strip()
            return checksum_line.split()[0]
    elif url_download.endswith('SHA256SUMS'):
        with open(f'cache/{cachefile}', 'r') as f:
            for line in f:
                if 'linux' in line and arch in line:
                    return line.split()[0]
    elif url_download.endswith('bsd'):
        with open(f'cache/{cachefile}', 'r') as f:
            for line in f:
                if 'SHA256' in line and 'linux' in line and arch in line:
                    return line.split()[0]
    sha256_hash = hashlib.sha256()
    with open(f'cache/{cachefile}', 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file_and_get_checksum(component, arch, url_download, session):
    cache_file = f'{component}-{arch}'
    if os.path.exists(f'cache/{cache_file}'):
        logging.info(f'Using cached file for {url_download}')
        return calculate_checksum(cache_file, arch, url_download)
    try:
        response = session.get(url_download, timeout=10)
        response.raise_for_status()
        with open(f'cache/{cache_file}', 'wb') as f:
            f.write(response.content)
        logging.info(f'Downloaded and cached file for {url_download}')
        return calculate_checksum(cache_file, arch, url_download)
    except Exception as e:
        logging.error(e)
        return None

def get_checksums(component, component_data, version, session):
    checksums = {}
    url_download_template = component_data['url_download'].replace('VERSION', version)
    if component_data['checksum_structure'] == 'os_arch':
        # OS -> Arch -> Checksum
        for os_name in oses:
            checksums[os_name] = {}
            for arch in architectures:
                url_download = url_download_template.replace('OS', os_name).replace('ARCH', arch)
                checksum = download_file_and_get_checksum(component, arch, url_download, session)
                if not checksum:
                    checksum = 0
                checksums[os_name][arch] = checksum
    elif component_data['checksum_structure'] == 'arch':
        # Arch -> Checksum
        for arch in architectures:
            url_download = url_download_template.replace('ARCH', arch)
            checksum = download_file_and_get_checksum(component, arch, url_download, session)
            if not checksum:
                checksum = 0
            checksums[arch] = checksum
    elif component_data['checksum_structure'] == 'simple':
        # Checksum
        checksum = download_file_and_get_checksum(component, '', url_download_template, session)
        if not checksum:
            checksum = 0
        checksums[version] = checksum
    return checksums

def update_yaml_checksum(component_data, checksums, version):
    placeholder_checksum = component_data['placeholder_checksum']
    checksum_structure = component_data['checksum_structure']
    current = checksum_yaml_data[placeholder_checksum]
    if checksum_structure == 'simple': 
        # Simple structure (placeholder_checksum -> version -> checksum)
        current[(version)] = checksums[version]
    elif checksum_structure == 'os_arch':  
        # OS structure (placeholder_checksum -> os -> arch -> version -> checksum)
        for os_name, arch_dict in checksums.items():
            os_current = current.setdefault(os_name, {})
            for arch, checksum in arch_dict.items():
                os_current[arch] = {(version): checksum, **os_current.get(arch, {})}
    elif checksum_structure == 'arch':
        # Arch structure (placeholder_checksum -> arch -> version -> checksum)
        for arch, checksum in checksums.items():
            current[arch] = {(version): checksum, **current.get(arch, {})}
    logging.info(f'Updated {placeholder_checksum} with {checksums}')

def resolve_kube_dependent_component_version(component, component_data, version):
    kube_major_version = component_data['kube_major_version']
    if component in ['crictl', 'crio']:
        try:
            component_major_minor_version = get_major_minor_version(version)
            if component_major_minor_version == kube_major_version:
                resolved_version = kube_major_version
            else:
                resolved_version = component_major_minor_version
        except (IndexError, AttributeError):
            logging.error(f'Error parsing version for {component}: {version}')
            return
    else:
        resolved_version = kube_major_version
    return resolved_version

def update_yaml_version(component, component_data, version):
    placeholder_version = component_data['placeholder_version']
    resolved_version = resolve_kube_dependent_component_version(component, component_data, version)
    updated_placeholder = [
        resolved_version if item == 'kube_major_version' else item 
        for item in placeholder_version
    ]
    current = download_yaml_data
    if len(updated_placeholder) == 1:
        current[updated_placeholder[0]] = version
    else:
        for key in updated_placeholder[:-1]:
            current = current.setdefault(key, {})
        final_key = updated_placeholder[-1]
        if final_key in current:
            current[final_key] = version
        else:
            new_entry = {final_key: version, **current}
            current.clear()
            current.update(new_entry)
    logging.info(f'Updated {updated_placeholder} to {version}')

def update_readme(component, version):
    for i, line in enumerate(readme_data):
        if component in line and re.search(r'v\d+\.\d+\.\d+', line):
            readme_data[i] = re.sub(r'v\d+\.\d+\.\d+', version, line)
            logging.info(f"Updated {component} to {version} in README")
            break
    return readme_data

def create_json_file(file_path):
    new_data = {}
    try:
        with open(file_path, 'w') as f:
            json.dump(new_data, f, indent=2)
        return new_data
    except Exception as e:
        logging.error(f'Failed to create {file_path}: {e}')
        return None

def save_json_file(file_path, data):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f'Failed to save {file_path}: {e}')
        return False

def load_yaml_file(yaml_file):
    try:
        with open(yaml_file, 'r') as f:
            return yaml.load(f)
    except Exception as e:
        logging.error(f'Failed to load {yaml_file}: {e}')
        return {}

def save_yaml_file(yaml_file, data):
    try:
        with open(yaml_file, 'w') as f:
            yaml.dump(data, f)
    except Exception as e:
        logging.error(f'Failed to save {yaml_file}: {e}')
        return False
    
def open_readme(path_readme):
    try:
        with open(path_readme, 'r') as f:
            return f.readlines()
    except Exception as e:
        logging.error(f'Failed to load {path_readme}: {e}')
        return False

def save_readme(path_readme):
    try:
        with open(path_readme, 'w') as f:
            f.writelines(readme_data)
    except Exception as e:
        logging.error(f'Failed to save {path_readme}: {e}')
        return False
    
def process_version_string(component, version):
    if component in ['youki', 'nerdctl', 'cri_dockerd', 'containerd']:
        if version.startswith('v'):
            version = version[1:]
            return version
    match = re.search(r'release-(\d{8})', version) # gvisor
    if match:
        version = match.group(1)
    return version

def get_major_minor_version(version):
    match = re.match(r'^(v\d+)\.(\d+)', version)
    if match:
        return f"{match.group(1)}.{match.group(2)}"
    return version

def process_component(component, component_data, session):
    logging.info(f'Processing component: {component}')

    kube_version = main_yaml_data.get('kube_version')
    kube_major_version = get_major_minor_version(kube_version)
    component_data['kube_version'] = kube_version  # needed for nested components
    component_data['kube_major_version'] = kube_major_version  # needed for nested components

    # Get current version
    current_version = get_current_version(component, component_data)
    if not current_version:
        logging.info(f'Stop processing component {component}, current version unknown')
        return

    # Get latest version
    if component_data['release_type'] == 'tag':
        release = get_release_tag(component, component_data, session)
        if release:
            latest_version = release.get('name')
    else:
        release = get_release(component, component_data, session)
        latest_version = release.get('tagName')    

    if not latest_version:
        logging.info(f'Stop processing component {component}, latest version unknown.')
        return
    
    
    latest_version = process_version_string(component, latest_version)

    if current_version == latest_version:
        logging.info(f'Component {component}, version {current_version} is up to date')
        if args.skip_checksum and (current_version == latest_version):
            logging.info(f'Stop processing component {component} due to flag.')
            return
    else:
        logging.info(f'Component {component} version discrepancy, current={current_version}, latest={latest_version}')
    
    if args.ci_check:
        release['component'] = component
        release['owner'] = component_data['owner']
        release['repo'] = component_data['repo']
        release['release_type'] = component_data['release_type']
        if (current_version != latest_version):
            version_diff[component] = {
                'current_version' : current_version, # needed for dependecy-check
                'latest_version' : latest_version, # needed for dependecy-check
                'release' : release # needed for generate_pr_body
            }
        return
    
    checksums = get_checksums(component, component_data, latest_version, session)
    update_yaml_checksum(component_data, checksums, latest_version)
    if component not in ['kubeadm', 'kubectl', 'kubelet']: # kubernetes dependent components
        update_yaml_version(component, component_data, latest_version)
    if component in ['etcd', 'containerd', 'crio', 'calicoctl', 'krew', 'helm']: # in README
        if component in ['crio', 'crictl']:
            component_major_minor_version = get_major_minor_version(latest_version)
            if component_major_minor_version != kube_major_version: # do not update README
                return
            component = component.replace('crio', 'cri-o')
        elif component == 'containerd':
            latest_version = f'v{latest_version}'
        elif component == 'calicoctl':
            component = component.replace('calicoctl', 'calico')
        update_readme(component, latest_version)


def main(loglevel, component, max_workers):
    setup_logging(loglevel)
    session = get_session_with_retries()

    global main_yaml_data, checksum_yaml_data, download_yaml_data, readme_data, version_diff
    main_yaml_data = load_yaml_file(path_main)
    checksum_yaml_data = load_yaml_file(path_checksum)
    download_yaml_data = load_yaml_file(path_download)
    readme_data = open_readme(path_readme)

    if not (main_yaml_data and checksum_yaml_data and download_yaml_data and readme_data):
        logging.error(f'Failed to open required yaml file, current working directory is {pwd}. Exiting...')
        sys.exit(1)

    if args.ci_check:
        version_diff = create_json_file(path_version_diff)
        if version_diff is None:
            logging.error(f'Failed to create version_diff.json file')
            sys.exit(1)
    else:
        version_diff = {}

    if component != 'all':
        if component in component_info:
            process_component(component, component_info[component], session)
        else:
            logging.error(f'Component {component} not found in config.')
            sys.exit(1)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            logging.info(f'Running with {executor._max_workers} executors')
            for component, component_data in component_info.items():
                futures.append(executor.submit(process_component, component, component_data, session))
            for future in futures:
                future.result()

    if args.ci_check:
        save_json_file(path_version_diff, version_diff)
    

    save_yaml_file(path_checksum, checksum_yaml_data)
    save_yaml_file(path_download, download_yaml_data)
    save_readme(path_readme)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kubespray version and checksum updater for dependencies')
    parser.add_argument('--loglevel', default='INFO', help='Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    parser.add_argument('--component', default='all', help='Specify a component to process, default is all components')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum number of concurrent workers, use with caution(sometimes less is more)')
    parser.add_argument('--skip-checksum', action='store_true', help='Skip checksum if the current version is up to date')
    parser.add_argument('--ci-check', action='store_true', help='Check versions, store discrepancies in version_diff.json')
    

    args = parser.parse_args()

    main(args.loglevel, args.component, args.max_workers)