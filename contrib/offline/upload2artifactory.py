#!/usr/bin/env python3
"""This is a helper script to manage-offline-files.sh.

After running manage-offline-files.sh, you can run upload2artifactory.py
to recursively upload each file to a generic repository in Artifactory.

This script recurses the $BASE_DIR directory and is intended to
be started from '$HOME/.ansible/collections/ansible_collections/kubernetes_sigs/kubespray/contrib/offline/offline-files'

Environment Variables:
    USERNAME -- At least permissions'Deploy/Cache' and 'Delete/Overwrite'.
    TOKEN -- Generate this with 'Set Me Up' in your user.
    BASE_URL -- The URL including the repository name.

"""
import os
import urllib.request
import base64
import re


def clean_version_numbers(path, depth=0):
    """Remove 'v' prefix from version numbers in the path using recursion"""
    if depth > 10:
        return path

    version_pattern = r'([/-])v(\d+(?:\.\d+)*(?:\.\d+)*)'
    cleaned_path = re.sub(version_pattern, r'\1\2', path)

    if re.search(r'[/-]v\d', cleaned_path):
        return clean_version_numbers(cleaned_path, depth + 1)
    else:
        return cleaned_path


def upload_file(file_path, destination_url, username, token):
    """Helper function to upload a single file"""
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()

        request = urllib.request.Request(destination_url, data=file_data, method='PUT') # NOQA
        auth_header = base64.b64encode(f"{username}:{token}".encode()).decode()
        request.add_header("Authorization", f"Basic {auth_header}")

        with urllib.request.urlopen(request) as response:
            if response.status in [200, 201]:
                print(f"Success: Uploaded {file_path}")
            else:
                print(f"Failed: {response.status} {response.read().decode('utf-8')}") # NOQA
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code} {e.reason} for {file_path}")
    except urllib.error.URLError as e:
        print(f"URLError: {e.reason} for {file_path}")
    except OSError as e:
        print(f"OSError: {e.strerror} for {file_path}")


def upload_files(base_dir, base_url, username, token):
    """ Recurse current dir and upload each file using urllib.request """
    base_dir = os.path.abspath(base_dir)
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, base_dir).lstrip(os.sep)
            # Clean version numbers from the path
            cleaned_relative_path = clean_version_numbers(relative_path)
            destination_url = f"{base_url}/{cleaned_relative_path}"
            print(f"Uploading {file_path} to {destination_url}")
            upload_file(file_path, destination_url, username, token)


if __name__ == "__main__":
    a_user = os.getenv("USERNAME")
    a_token = os.getenv("TOKEN")
    a_url = os.getenv("BASE_URL")
    a_dir = os.getenv("BASE_DIR")
    if not a_dir or not a_user or not a_token or not a_url:
        print(
            "Error: Environment variables BASE_DIR, USERNAME, TOKEN, and BASE_URL must be set." # NOQA
        )
        exit(22)
    upload_files(a_dir, a_url, a_user, a_token)
