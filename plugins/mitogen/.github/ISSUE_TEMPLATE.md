
Feel free to write an issue in your preferred format, however if in doubt, use
the following checklist as a guide for what to include.

* Have you tried the latest master version from Git?
* Mention your host and target OS and versions
* Mention your host and target Python versions
* If reporting a performance issue, mention the number of targets and a rough
  description of your workload (lots of copies, lots of tiny file edits, etc.)
* If reporting a crash or hang in Ansible, please rerun with -vvvv and include
  the last 200 lines of output, along with a full copy of any traceback or
  error text in the log. Beware "-vvvv" may include secret data! Edit as
  necessary before posting.
* If reporting any kind of problem with Ansible, please include the Ansible
  version along with output of "ansible-config dump --only-changed".
