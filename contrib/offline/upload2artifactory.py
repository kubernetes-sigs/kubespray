#!/usr/bin/env python3
""" recursively upload each file to private repo in Artifactory """
""" Uses environment variables: USERNAME, TOKEN, and BASE_URL. """
import os
import subprocess


def upload_files(base_url, username, token):
    """recurse current dir and upload each file with curl"""
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, os.getcwd())
            destination_url = f"{base_url}/{relative_path}"

            # Construct and execute the curl command
            command = [
                "curl",
                "-u",
                f"{username}:{token}",
                "-T",
                file_path,
                destination_url,
            ]
            print(f"Uploading {file_path} to {destination_url}")
            try:
                result = subprocess.run(
                    command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                print(f"Success: {result.stdout.decode('utf-8')}")
            except subprocess.CalledProcessError as e:
                print(f"Error uploading {file_path}: {e.stderr.decode('utf-8')}")


if __name__ == "__main__":
    a_user = os.getenv("USERNAME")
    a_token = os.getenv("TOKEN")
    a_url = os.getenv("BASE_URL")
    if not a_user or not a_token or not a_url:
        print("Error: Environment variables USERNAME, TOKEN, and BASE_URL must be set.")
        exit()
    upload_files(a_url, a_user, a_token)
