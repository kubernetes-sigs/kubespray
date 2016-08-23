#!/bin/sh
set -e

# Text color variables
txtbld=$(tput bold)             # Bold
bldred=${txtbld}$(tput setaf 1) #  red
bldgre=${txtbld}$(tput setaf 2) #  green
bldylw=${txtbld}$(tput setaf 3) #  yellow
txtrst=$(tput sgr0)             # Reset
err=${bldred}ERROR${txtrst}
info=${bldgre}INFO${txtrst}
warn=${bldylw}WARNING${txtrst}

usage()
{
    cat << EOF
Generates a file which contains useful git informations

Usage : $(basename $0) [global|diff]
    ex :
      Generate git information
      $(basename $0) global
      Generate diff from latest tag
      $(basename $0) diff
EOF
}

if [ $# != 1 ]; then
    printf "\n$err : Needs 1 argument\n"
    usage
    exit 2
fi;

current_commit=$(git rev-parse HEAD)
latest_tag=$(git describe --abbrev=0 --tags)
latest_tag_commit=$(git show-ref -s ${latest_tag})
tags_list=$(git tag --points-at "${latest_tag}")

case ${1} in
    "global")
cat<<EOF
deployment date="$(date '+%d-%m-%Y %Hh%M')"
deployment_timestamp=$(date '+%s')
user="$USER"
current commit (HEAD)="${current_commit}"
current_commit_timestamp=$(git log -1 --pretty=format:%ct)
latest tag(s) (current branch)="${tags_list}"
latest tag commit="${latest_tag_commit}"
current branch="$(git rev-parse --abbrev-ref HEAD)"
branches list="$(git describe --contains --all HEAD)"
git root directory="$(git rev-parse --show-toplevel)"
EOF
        if ! git diff-index --quiet HEAD --; then
           printf "unstaged changes=\"/etc/.git-ansible.diff\""
        fi

        if [ "${current_commit}" = "${latest_tag_commit}" ]; then
            printf "\ncurrent_commit_tag=\"${latest_tag}\""
        else
           printf "\nlast tag was "$(git describe --tags | awk -F- '{print $2}')" commits ago =\""
           printf "$(git log --pretty=format:"    %h - %s" ${latest_tag}..HEAD)\""
        fi
        ;;

    "diff")
       git diff
       ;;
    *)
        usage
        printf "$err: Unknown argument ${1}"
		exit 1;
	    ;;
esac
