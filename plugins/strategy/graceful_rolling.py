# -*- coding: utf-8 -*-
# (c) 2026, The Kubespray Contributors
# GNU General Public License v3.0+
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Implements Issue #12929: graceful rolling upgrade strategy with a
# configurable sliding-window concurrency per play and per Ansible group.
from __future__ import annotations

DOCUMENTATION = """
name: graceful_rolling
short_description: Sliding-window rolling upgrade strategy
description:
  - Hosts advance through the play as fast as possible, like the free strategy.
  - The number of hosts that may run concurrently is capped by the play variable
    C(graceful_rolling_concurrency). When unset it defaults to the configured
    Ansible forks value, so the behaviour matches C(host_pinned).
  - As soon as one host finishes its last task it opens a slot for the next
    waiting host. There is no batch synchronisation point.
  - An optional C(graceful_rolling_per_group) play variable further constrains
    concurrency per Ansible group. Useful to keep the control-plane at one
    parallel host while allowing workers to run at a higher concurrency.
  - Solves the batch-synchronisation bottleneck of C(serial) and the
    PodDisruptionBudget deadlock that can occur during Kubernetes node upgrades.
  - This strategy is opt-in. The default kubespray upgrade strategy is
    C(linear). Enable with C(-e upgrade_strategy=graceful_rolling) or by
    setting C(upgrade_strategy: graceful_rolling) in your inventory.
  - See docs/operations/upgrade-strategies.md for a full comparison and
    docs/developers/graceful-rolling-strategy.md for the design notes.
notes:
  - Handler flushing is per-host, inherited from C(host_pinned). Node-local
    handlers such as I(restart kubelet) fire as soon as the respective node
    completes all its tasks.
  - C(max_fail_percentage) and C(any_errors_fatal) emit a warning when used
    with this strategy because tasks are executed independently on each host,
    matching the behaviour of the C(free) strategy.
  - C(run_once) tasks are passed through to Ansible's built-in iterator
    handling, identical to the C(free) strategy: the task runs once for the
    first applicable host; all other hosts skip it. No ordering guarantees
    relative to other hosts are provided.
  - The C(throttle:) task keyword is fully supported. It limits how many
    workers may execute the same task simultaneously, independently of the
    play-level C(graceful_rolling_concurrency) slot limit. For example,
    C(throttle: 3) on a heavy download task caps that task at three
    concurrent executions even when C(graceful_rolling_concurrency) is 20.
    The two constraints are applied independently; C(ALLOW_BASE_THROTTLING)
    is C(False) because the strategy handles throttle in its own run loop,
    not in C(StrategyBase._queue_task), to avoid double-counting.
options:
  graceful_rolling_concurrency:
    description:
      - Maximum number of hosts allowed to be running the play simultaneously.
      - Accepts a plain integer (e.g. C(5)) or a percentage string (e.g. C("20%")).
        Percentages are resolved against the total number of play hosts at
        strategy initialisation time, rounded to the nearest integer, and
        clamped to a minimum of 1.
      - Capped at the number of configured Ansible forks.
      - When absent, defaults to the configured Ansible forks value.
    type: raw
    vars:
      - name: graceful_rolling_concurrency
  graceful_rolling_per_group:
    description:
      - Mapping of Ansible group name to the maximum concurrent hosts within
        that group.
      - Hosts not matched by any listed key are only subject to the global
        C(graceful_rolling_concurrency) limit.
      - The special key C(default) sets a fallback limit for hosts that do not
        belong to any explicitly listed group.
    type: dict
    vars:
      - name: graceful_rolling_per_group
"""

import time

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.handler import Handler
from ansible.playbook.included_file import IncludedFile
from ansible.plugins.loader import action_loader
from ansible.plugins.strategy.free import StrategyModule as FreeStrategyModule
from ansible.plugins.strategy.host_pinned import StrategyModule as HostPinnedStrategyModule
from ansible.template import Templar as TemplateEngine
from ansible.utils.display import Display

display = Display()


class StrategyModule(HostPinnedStrategyModule):
    """Sliding-window rolling upgrade strategy for kubespray.

    Class hierarchy
    ---------------
    Inherits from ``HostPinnedStrategyModule``, which itself inherits from
    ``FreeStrategyModule``.  ``HostPinnedStrategyModule`` does **not** define
    its own ``run()``; it only sets ``_host_pinned = True`` in ``__init__``.
    Therefore:

    * The ``_host_pinned`` flag is inherited from ``HostPinnedStrategyModule``
      and causes the inner dispatch loop to break when ``workers_free == 0``
      (correct slot-limiting semantics).
    * Our ``run()`` is a fork of ``FreeStrategyModule.run()`` — that is the
      actual base implementation in the MRO.  The drift-detection script
      tracks ``free.StrategyModule.run()`` for exactly this reason.

    We add a configurable sliding-window concurrency cap on top: as soon as
    one host finishes the play it immediately frees a slot for the next
    waiting host.

    MRO: StrategyModule → HostPinnedStrategyModule → FreeStrategyModule → StrategyBase
    """

    # Throttling is handled manually in run(); disable base-class throttle
    ALLOW_BASE_THROTTLING = False

    # Key used in active_per_group for hosts not matched by any explicit group.
    _DEFAULT_BUCKET = "__default__"

    def __init__(self, tqm):
        super().__init__(tqm)
        # _host_pinned = True is already set by HostPinnedStrategyModule.__init__.

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_concurrency_value(raw, total_hosts, max_workers):
        """Parse a raw concurrency value: plain int or percentage string.

        Args:
            raw: int or string, optionally ending with ``'%'``.
            total_hosts: total number of hosts in the play; used as the
                denominator when *raw* is a percentage.
            max_workers: upper bound (the configured Ansible forks count).

        Returns:
            int in the range ``[1, max_workers]``.
        """
        if isinstance(raw, str) and raw.strip().endswith("%"):
            pct = float(raw.strip()[:-1]) / 100.0
            result = max(1, int(round(pct * total_hosts)))
        else:
            result = int(raw)
        return min(result, max_workers)

    def _read_concurrency_config(self, iterator, first_host, total_hosts):
        """Return (global_concurrency, per_group_limits) from play vars.

        Reads ``graceful_rolling_concurrency`` and
        ``graceful_rolling_per_group`` from the play's variable scope,
        templates any Jinja2 expressions, and enforces the upper bound of
        the configured fork count.

        Args:
            iterator: the play iterator (used to resolve play variables).
            first_host: any live host (required by ``get_vars``).
            total_hosts: total host count of the play; used as the
                denominator when ``graceful_rolling_concurrency`` is a
                percentage string such as ``"20%"``.
        """
        play_vars = self._variable_manager.get_vars(
            play=iterator._play, host=first_host
        )
        templar = TemplateEngine(loader=self._loader, variables=play_vars)  # Templar in 2.18

        raw_concurrency = play_vars.get(
            "graceful_rolling_concurrency", len(self._workers)
        )
        concurrency = self._parse_concurrency_value(
            templar.template(raw_concurrency),
            total_hosts,
            len(self._workers),
        )

        per_group_limits = {}
        raw_per_group = play_vars.get("graceful_rolling_per_group", {})
        if raw_per_group:
            resolved = templar.template(raw_per_group)
            per_group_limits = {
                k: self._parse_concurrency_value(v, total_hosts, len(self._workers))
                for k, v in resolved.items()
            }

        display.vv(
            "graceful_rolling: concurrency=%d per_group_limits=%s"
            % (concurrency, per_group_limits)
        )
        return concurrency, per_group_limits

    # ------------------------------------------------------------------
    # Per-group concurrency helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _host_group_names(host):
        """Return the set of Ansible group names for *host* (excluding 'all')."""
        return {g.name for g in host.get_groups() if g.name != "all"}

    @staticmethod
    def _explicit_groups(per_group_limits):
        """Return the set of explicitly named groups from *per_group_limits*.

        Strips the special ``'default'`` key so callers can iterate only
        over real group names.
        """
        return set(per_group_limits) - {"default"}

    def _can_start_host(self, host, active_per_group, per_group_limits):
        """Return True if starting *host* would not violate any group limit.

        Checks every per-group limit whose group contains *host*.  The
        special key ``'default'`` applies to hosts that are not a member of
        any other explicitly listed group.

        Args:
            host: Ansible Host object about to receive its first task.
            active_per_group: current active-host counts, keyed by group
                name (``'__default__'`` for the catch-all bucket).
            per_group_limits: mapping of group name → limit from play vars.
        """
        if not per_group_limits:
            return True

        group_names = self._host_group_names(host)
        explicit_groups = self._explicit_groups(per_group_limits)

        # Check every explicit group this host belongs to.
        for gname in explicit_groups:
            if gname in group_names:
                if active_per_group.get(gname, 0) >= per_group_limits[gname]:
                    display.vvv(
                        "graceful_rolling: host '%s' deferred — "
                        "group '%s' at limit %d"
                        % (host.get_name(), gname, per_group_limits[gname])
                    )
                    return False

        # Apply the 'default' catch-all only if this host is not in any
        # explicitly-listed group.
        if "default" in per_group_limits and not (group_names & explicit_groups):
            default_limit = per_group_limits["default"]
            if active_per_group.get(self._DEFAULT_BUCKET, 0) >= default_limit:
                display.vvv(
                    "graceful_rolling: host '%s' deferred — "
                    "default limit %d"
                    % (host.get_name(), default_limit)
                )
                return False

        return True

    def _register_host_start(self, host, started, active_per_group, per_group_limits):
        """Record that *host* has been given its first task.

        Increments the relevant per-group active counters.
        """
        host_name = host.get_name()
        if host_name in started:
            return
        started.add(host_name)
        if not per_group_limits:
            return

        group_names = self._host_group_names(host)
        explicit_groups = self._explicit_groups(per_group_limits)

        for gname in explicit_groups:
            if gname in group_names:
                active_per_group[gname] = active_per_group.get(gname, 0) + 1

        if "default" in per_group_limits and not (group_names & explicit_groups):
            active_per_group[self._DEFAULT_BUCKET] = (
                active_per_group.get(self._DEFAULT_BUCKET, 0) + 1
            )

    def _register_host_finish(
        self, host_name, host_map, finished, started, active_per_group, per_group_limits
    ):
        """Record that *host_name* has finished all its tasks.

        Decrements the relevant per-group active counters, which may allow a
        previously deferred host to start.
        """
        if host_name in finished or host_name not in started:
            return
        finished.add(host_name)
        display.vv("graceful_rolling: host '%s' finished the play" % host_name)

        if not per_group_limits or host_name not in host_map:
            return

        host = host_map[host_name]
        group_names = self._host_group_names(host)
        explicit_groups = self._explicit_groups(per_group_limits)

        for gname in explicit_groups:
            if gname in group_names:
                active_per_group[gname] = max(
                    0, active_per_group.get(gname, 0) - 1
                )

        if "default" in per_group_limits and not (group_names & explicit_groups):
            active_per_group[self._DEFAULT_BUCKET] = max(
                0, active_per_group.get(self._DEFAULT_BUCKET, 0) - 1
            )

    # ------------------------------------------------------------------
    # Main execution loop
    # ------------------------------------------------------------------

    def run(self, iterator, play_context):
        """Execute the graceful_rolling strategy.

        This is a near-verbatim copy of ``free.StrategyModule.run()`` with
        five targeted modifications (marked with ``# GR:`` comments).
        ansible-core provides no override points inside the free strategy
        loop, so the copy is structurally unavoidable.  A drift-detection
        script (``tests/scripts/check_free_strategy_drift.py``) tracks the
        upstream sha256 of ``free.StrategyModule.run()`` and must be re-run
        (with ``--update``) after every ansible-core version bump, to verify
        that no upstream change requires a corresponding update here.

        1. ``workers_free`` is initialised from ``graceful_rolling_concurrency``
           instead of ``len(self._workers)``.
        2. Configuration is read once from play vars after the first
           ``hosts_left`` is available.
        3. Finished hosts are detected by comparing successive ``hosts_left``
           sets; their per-group counters are decremented on finish.
        4. New hosts (not yet started) are vetoed by ``_can_start_host()``
           when a per-group limit would be exceeded.
        5. ``_register_host_start()`` is called when the first task is queued
           for a host.

        At the end, ``StrategyBase.run()`` is called directly (bypassing
        ``FreeStrategyModule.run()``) to perform clean-up without re-running
        the free strategy execution loop.
        """
        last_host = 0
        result = self._tqm.RUN_OK

        self._set_hosts_cache(iterator._play)

        if iterator._play.max_fail_percentage is not None:
            display.warning(
                "Using max_fail_percentage with the graceful_rolling strategy "
                "is not supported, as tasks are executed independently on each host"
            )

        # GR: Per-group concurrency state ----------------------------------
        started_hosts: set[str] = set()
        finished_hosts: set[str] = set()
        active_per_group: dict[str, int] = {}
        host_map: dict[str, object] = {}  # hostname → Host object
        previous_host_set: set[str] = set()

        # GR: Configuration (populated lazily on first non-empty hosts_left)
        _config_read = False
        concurrency = len(self._workers)  # overwritten after first read
        per_group_limits: dict[str, int] = {}
        # GR: Initialise workers_free with our own concurrency limit instead
        #     of the total worker-pool size.  Overwritten after config read.
        workers_free = len(self._workers)
        # ------------------------------------------------------------------

        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            hosts_left = self.get_hosts_left(iterator)

            # GR: Read concurrency configuration once we have live hosts.
            if not _config_read and hosts_left:
                concurrency, per_group_limits = self._read_concurrency_config(
                    iterator, hosts_left[0], len(hosts_left)
                )
                workers_free = concurrency
                _config_read = True
                for h in hosts_left:
                    host_map[h.get_name()] = h

            # GR: Detect hosts that finished since the last outer iteration.
            current_host_set = {h.get_name() for h in hosts_left}
            for hn in previous_host_set - current_host_set:
                self._register_host_finish(
                    hn, host_map, finished_hosts, started_hosts,
                    active_per_group, per_group_limits,
                )
            previous_host_set = current_host_set
            # ------------------------------------------------------------------

            if len(hosts_left) == 0:
                self._tqm.send_callback("v2_playbook_on_no_hosts_remaining")
                result = False
                break

            work_to_do = False
            starting_host = last_host

            host_results = []
            meta_task_dummy_results_count = 0
            _dispatched = False  # GR: tracks whether any task was queued this iteration

            while True:
                host = hosts_left[last_host]
                display.debug("next free host: %s" % host)
                host_name = host.get_name()

                (state, task) = iterator.get_next_task_for_host(host, peek=True)
                display.debug("free host state: %s" % state, host=host_name)
                display.debug("free host task: %s" % task, host=host_name)

                # GR: Detect play completion per-host in the inner loop.
                # get_hosts_left() only removes unreachable hosts, so the
                # outer-loop set-difference never fires for successful
                # completions.  When task is None and no result is pending
                # the host has finished all its tasks — decrement per-group
                # counters immediately so deferred hosts can proceed.
                if (
                    task is None
                    and not self._blocked_hosts.get(host_name, False)
                    and not self._tqm._unreachable_hosts.get(host_name, False)
                ):
                    self._register_host_finish(
                        host_name, host_map, finished_hosts, started_hosts,
                        active_per_group, per_group_limits,
                    )

                if (
                    task or self._blocked_hosts.get(host_name, False)
                ) and not self._tqm._unreachable_hosts.get(host_name, False):
                    display.debug("this host has work to do", host=host_name)
                    work_to_do = True

                if (
                    not self._tqm._unreachable_hosts.get(host_name, False)
                    and task
                ):
                    if not self._blocked_hosts.get(host_name, False):

                        # GR: Veto new hosts that would exceed a group limit.
                        if host_name not in started_hosts:
                            if not self._can_start_host(
                                host, active_per_group, per_group_limits
                            ):
                                # Skip and try the next host in the list.
                                last_host += 1
                                if last_host > len(hosts_left) - 1:
                                    last_host = 0
                                if last_host == starting_host:
                                    break
                                continue
                        # --------------------------------------------------

                        display.debug("getting variables", host=host_name)
                        task_vars = self._variable_manager.get_vars(
                            play=iterator._play,
                            host=host,
                            task=task,
                            _hosts=self._hosts_cache,
                            _hosts_all=self._hosts_cache_all,
                        )
                        self.add_tqm_variables(task_vars, play=iterator._play)
                        templar = TemplateEngine(
                            loader=self._loader, variables=task_vars  # Templar in 2.18
                        )
                        display.debug("done getting variables", host=host_name)

                        try:
                            throttle = int(templar.template(task.throttle))
                        except Exception as ex:
                            raise AnsibleError(
                                "Failed to convert the throttle value to an integer.",
                                obj=task.throttle,
                            ) from ex

                        if throttle > 0:
                            same_tasks = 0
                            for worker in self._workers:
                                if (
                                    worker
                                    and worker.is_alive()
                                    and worker._task._uuid == task._uuid
                                ):
                                    same_tasks += 1
                            display.debug(
                                "task: %s, same_tasks: %d"
                                % (task.get_name(), same_tasks)
                            )
                            if same_tasks >= throttle:
                                break

                        self._blocked_hosts[host_name] = True
                        iterator.set_state_for_host(host.name, state)
                        if isinstance(task, Handler):
                            task.remove_host(host)

                        try:
                            action = action_loader.get(
                                task.action,
                                class_only=True,
                                collection_list=task.collections,
                            )
                        except KeyError:
                            action = None

                        # GR: Check if this task belongs to a role that has
                        # already run on this host and does not allow duplicate
                        # execution.  Skip the task and clear the blocked state
                        # so the host is not permanently stuck. (Mirrors the
                        # same check in ansible.plugins.strategy.free.)
                        if not isinstance(task, Handler) and task._role:
                            role_obj = self._get_cached_role(task, iterator._play)
                            if (
                                role_obj.has_run(host)
                                and task._role._metadata.allow_duplicates is False
                            ):
                                display.debug(
                                    "'%s' skipped because role has already run"
                                    % task,
                                    host=host_name,
                                )
                                del self._blocked_hosts[host_name]
                                continue

                        # task.post_validate_attribute("name") is ansible-core 2.19+;
                        # in 2.18 task.name is templated by the callback layer itself.

                        # run_once tasks are handled naturally by Ansible's
                        # task iterator: the iterator runs the task for the
                        # first applicable host and marks it as complete so
                        # all other hosts skip it.  No special handling needed.

                        if task.action in C._ACTION_META:
                            meta_task_dummy_results_count += 1
                            workers_free -= 1
                            _dispatched = True
                            self._execute_meta(
                                task, play_context, iterator, target_host=host
                            )
                            self._blocked_hosts[host_name] = False
                        else:
                            if not self._step or self._take_step(task, host_name):
                                if task.any_errors_fatal:
                                    display.warning(
                                        "Using any_errors_fatal with the "
                                        "graceful_rolling strategy is not "
                                        "supported, as tasks are executed "
                                        "independently on each host"
                                    )
                                if isinstance(task, Handler):
                                    self._tqm.send_callback(
                                        "v2_playbook_on_handler_task_start", task
                                    )
                                else:
                                    self._tqm.send_callback(
                                        "v2_playbook_on_task_start",
                                        task,
                                        is_conditional=False,
                                    )
                                self._queue_task(
                                    host, task, task_vars, play_context
                                )
                                _dispatched = True
                                # GR: Record that this host has started.
                                self._register_host_start(
                                    host, started_hosts,
                                    active_per_group, per_group_limits,
                                )
                                workers_free -= 1
                                del task_vars
                    else:
                        display.debug(
                            "%s is blocked, skipping for now" % host_name
                        )

                # host_pinned: stop when all concurrency slots are taken.
                if self._host_pinned and workers_free == 0 and work_to_do:
                    last_host = starting_host
                    break

                last_host += 1
                if last_host > len(hosts_left) - 1:
                    last_host = 0

                if last_host == starting_host:
                    break

            # GR: Detect dead worker processes early so we raise an error
            # instead of spinning in a busy-wait loop forever.
            if self._tqm.has_dead_workers():
                raise AnsibleError(
                    "graceful_rolling: a worker process died unexpectedly. "
                    "Check the logs for details."
                )

            results = self._process_pending_results(iterator)
            host_results.extend(results)

            workers_free += len(results) + meta_task_dummy_results_count

            self.update_active_connections(results)

            included_files = IncludedFile.process_include_results(
                host_results,
                iterator=iterator,
                loader=self._loader,
                variable_manager=self._variable_manager,
            )

            if len(included_files) > 0:
                all_blocks = {host: [] for host in hosts_left}
                failed_includes_hosts = set()

                for included_file in included_files:
                    display.debug(
                        "collecting new blocks for %s" % included_file
                    )
                    is_handler = False
                    try:
                        if included_file._is_role:
                            new_ir = self._copy_included_file(included_file)
                            new_blocks, _handler_blocks = new_ir.get_block_list(
                                play=iterator._play,
                                variable_manager=self._variable_manager,
                                loader=self._loader,
                            )
                        else:
                            is_handler = isinstance(
                                included_file._task, Handler
                            )
                            new_blocks = self._load_included_file(
                                included_file,
                                iterator=iterator,
                                is_handler=is_handler,
                                handle_stats_and_callbacks=False,
                            )

                        iterator.handlers = [
                            h
                            for b in iterator._play.handlers
                            for h in b.block
                        ]
                    except AnsibleParserError:
                        raise
                    except AnsibleError as ex:
                        display.error(ex)
                        for r in included_file._results:
                            r._return_data["failed"] = True
                            r._return_data["reason"] = str(ex)
                            self._tqm._stats.increment(
                                "failures", r.host.name
                            )
                            self._tqm.send_callback(
                                "v2_runner_on_failed", r
                            )
                            failed_includes_hosts.add(r.host)
                        continue
                    else:
                        for host in included_file._hosts:
                            self._tqm._stats.increment("ok", host.name)
                        self._tqm.send_callback(
                            "v2_playbook_on_include", included_file
                        )

                    for new_block in new_blocks:
                        if is_handler:
                            for task in new_block.block:
                                task.notified_hosts = included_file._hosts[:]
                            final_block = new_block
                        else:
                            task_vars = self._variable_manager.get_vars(
                                play=iterator._play,
                                task=new_block.get_first_parent_include(),
                                _hosts=self._hosts_cache,
                                _hosts_all=self._hosts_cache_all,
                            )
                            final_block = new_block.filter_tagged_tasks(
                                task_vars
                            )
                        for host in hosts_left:
                            if host in included_file._hosts:
                                all_blocks[host].append(final_block)
                    display.debug(
                        "done collecting new blocks for %s" % included_file
                    )

                for host in failed_includes_hosts:
                    self._tqm._failed_hosts[host.name] = True
                    iterator.mark_host_failed(host)

                display.debug(
                    "adding blocks from %d included file(s) to iterator"
                    % len(included_files)
                )
                for host in hosts_left:
                    iterator.add_tasks(host, all_blocks[host])
                display.debug("done adding collected blocks to iterator")

            # GR: When nothing was dispatched but work remains (all waiting
            # hosts are blocked by a per-group limit) back off longer to avoid
            # busy-spinning while in-flight results arrive.
            if _dispatched or not work_to_do:
                time.sleep(C.DEFAULT_INTERNAL_POLL_INTERVAL)
            else:
                time.sleep(C.DEFAULT_INTERNAL_POLL_INTERVAL * 10)

        # Collect any remaining in-flight results.
        self._wait_on_pending_results(iterator)

        # Delegate to StrategyBase.run() for clean-up (advance all hosts to
        # COMPLETE state, compute final return code).  We deliberately skip
        # FreeStrategyModule.run() to avoid re-executing the free loop.
        return super(FreeStrategyModule, self).run(iterator, play_context, result)
