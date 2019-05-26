#!/bin/bash
# A naive premoderation script to allow Gitlab CI pipeline on a specific PRs' comment
# Exits with 0, if the pipeline is good to go
# Exits with 1, if the user is not allowed to start pipeline
# Exits with 2, if script is unable to get issue id from CI_BUILD_REF_NAME variable
# Exits with 3, if missing the magic comment in the pipeline to start the pipeline

CURL_ARGS="-fs --retry 4 --retry-delay 5"
MAGIC="${MAGIC:-ci check this}"

# Get PR number from CI_BUILD_REF_NAME
issue=$(echo ${CI_BUILD_REF_NAME} | perl -ne '/^pr-(\d+)-\S+$/ && print $1')

if [ "$issue" = "" ]; then
  echo "Unable to get issue id from: $CI_BUILD_REF_NAME"
  exit 2
fi

echo "Checking for '$MAGIC' comment in PR $issue"

# Get the user name from the PR comments with the wanted magic incantation casted
user=$(curl ${CURL_ARGS} "https://api.github.com/repos/kubernetes-sigs/kubespray/issues/${issue}/comments" \
  | jq -M "map(select(.body | contains (\"$MAGIC\"))) | .[0] .user.login" | tr -d '"')

# Check for the required user group membership to allow (exit 0) or decline (exit >0) the pipeline
if [ "$user" = "" ] || [ "$user" = "null" ]; then
  echo "Missing '$MAGIC' comment from one of the OWNERS"
  exit 3
else
  echo "Found comment from user: $user"
fi

curl ${CURL_ARGS} "https://api.github.com/orgs/kubernetes-sigs/members/${user}"

if [ $? -ne 0 ]; then
  echo "User does not have permissions to start CI run"
  exit 1
else
  echo "$user has allowed CI to start"
fi

exit 0
