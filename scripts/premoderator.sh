#!/bin/bash
# A naive premoderation script to allow Gitlab CI pipeline on a specific PRs' comment
# Exits with 0, if the pipeline is good to go
# Exits with 1, if the user is not allowed to start pipeline
# Exits with 2, if script is unable to get issue id from CI_COMMIT_REF_NAME variable
# Exits with 3, if missing the magic comment in the pipeline to start the pipeline

CURL_ARGS="-fs --retry 4 --retry-delay 5"
MAGIC="${MAGIC:-ci check this}"
exit_code=0

# Get PR number from CI_COMMIT_REF_NAME
issue=$(echo ${CI_COMMIT_REF_NAME} | perl -ne '/^pr-(\d+)-\S+$/ && print $1')

if [ "$issue" = "" ]; then
  echo "Unable to get issue id from: $CI_COMMIT_REF_NAME"
  exit 2
fi

echo "Fetching labels from PR $issue"
labels=$(curl ${CURL_ARGS} "https://api.github.com/repos/kubernetes-sigs/kubespray/issues/${issue}?access_token=${GITHUB_TOKEN}" | jq '{labels: .labels}' | jq '.labels[].name' | jq -s '')
labels_to_patch=$(echo -n $labels | jq '. + ["needs-ci-auth"]' | tr -d "\n")

echo "Checking for '$MAGIC' comment in PR $issue"

# Get the user name from the PR comments with the wanted magic incantation casted
user=$(curl ${CURL_ARGS} "https://api.github.com/repos/kubernetes-sigs/kubespray/issues/${issue}/comments" | jq -M "map(select(.body | contains (\"$MAGIC\"))) | .[0] .user.login" | tr -d '"')

# Check for the required user group membership to allow (exit 0) or decline (exit >0) the pipeline
if [ "$user" = "" ] || [ "$user" = "null" ]; then
  echo "Missing '$MAGIC' comment from one of the OWNERS"
  exit_code=3
else
  echo "Found comment from user: $user"

  curl ${CURL_ARGS} "https://api.github.com/orgs/kubernetes-sigs/members/${user}"

  if [ $? -ne 0 ]; then
    echo "User does not have permissions to start CI run"
    exit_code=1
  else
    labels_to_patch=$(echo -n $labels | jq '. - ["needs-ci-auth"]' | tr -d "\n")
    exit_code=0
    echo "$user has allowed CI to start"
  fi
fi

# Patch labels on PR
curl ${CURL_ARGS} --request PATCH "https://api.github.com/repos/kubernetes-sigs/kubespray/issues/${issue}?access_token=${GITHUB_TOKEN}" -H "Content-Type: application/json" -d "{\"labels\": ${labels_to_patch}}"

exit $exit_code
