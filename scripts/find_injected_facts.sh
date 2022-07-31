# see https://github.com/kubernetes-sigs/kubespray/pull/8927
# run me from top dir like ./scripts/find_injected_facts.sh
git grep -h -E -o '([$_/]|filter(: "?|=)|ansible_facts.)?ansible_[a-z_*]*' | # find strings looking like injected facts (ansible_...), but also capture some prefixes if they exist
  grep -v filter | # ansible_ prefix can still be used in setup module's filter argument, remove these matches
  egrep -v '^[$_/]|ansible_facts' | # filter out different variations of ansible_something that are not injected facts
  sort -u |
  grep -vf <(cat scripts/not_facts | sed -e 's/^/^/' -e 's/$/$/') # filter out strings from "not_facts"; sed wraps them with ^...$ for more precise matching
