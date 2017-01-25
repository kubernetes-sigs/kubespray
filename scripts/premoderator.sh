#!/bin/sh -eux -o pipefail
# A naive premoderation script to allow Gitlab CI pipeline on a specific PRs' comment
# Exits with 0, if the pipeline is good to go

CURL_ARGS="-fs --connect-timeout 5 --max-time 5 --retry-max-time 20 --retry 4 --retry-delay 5"
MAGIC="${MAGIC:-ci check this}"

# Get PR number from CI_BUILD_REF_NAME
issue=$(echo ${CI_BUILD_REF_NAME} | perl -ne '/^pr-(\d+)-\S+$/ && print $1')
# Get the user name from the PR comments with the wanted magic incantation casted
user=$(curl ${CURL_ARGS} "https://api.github.com/repos/kubernetes-incubator/kargo/issues/${issue}/comments" \
  | jq -M "map(select(.body | contains (\"$MAGIC\"))) | .[0] .user.login" | tr -d '"')
# Check for the required user group membership to allow (exit 0) or decline (exit >0) the pipeline
if [ "$user" = "null" ]; then
	echo "User does not have permissions to start CI run"
	exit 1
fi
curl ${CURL_ARGS} "https://api.github.com/orgs/kubernetes-incubator/members/${user}"
