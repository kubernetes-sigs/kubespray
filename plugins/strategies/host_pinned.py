from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: host_pinned
    short_description: Executes tasks on each host without waiting for other hosts, with limited concurrency
    description:
        - Strategy that behaves like the 'host_pinned' (or 'free') strategy but allows for a 'throttle' parameter to limit the number of active hosts.
        - This allows for a "rolling update" style of execution where a new host picks up work as soon as a slot is available, rather than waiting for a whole batch to finish (like 'linear' with 'serial').
        - If 'throttle' is not specified, it falls back to 'serial' (if a single integer) or 'forks'.
    version_added: "2.x"
    author: VannTen (@VannTen)
'''

import time

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.handler import Handler
from ansible.playbook.included_file import IncludedFile
from ansible.plugins.loader import action_loader
from ansible.plugins.strategy import StrategyBase
from ansible.template import Templar
from ansible.module_utils.common.text.converters import to_text
from ansible.utils.display import Display

display = Display()


class StrategyModule(StrategyBase):

    ALLOW_BASE_THROTTLING = False

    def __init__(self, tqm):
        super(StrategyModule, self).__init__(tqm)
        self._host_pinned = True
        self._rolling_play = True

    def run(self, iterator, play_context):
        # the last host to be given a task
        last_host = 0

        result = self._tqm.RUN_OK

        # Validation and Setup
        throttle = getattr(iterator._play, 'throttle', 0)

        # Proper throttle handling (None vs 0) and validation
        if throttle is None:
            throttle = 0
        try:
            throttle = int(throttle)
        except ValueError:
            raise AnsibleError("Invalid throttle value: %s" % throttle)

        # Serial fallback lookup: if throttle is not set (0), try usage of serial
        if throttle == 0:
            serial = getattr(iterator._play, 'serial', None)
            if serial and len(serial) == 1:
                try:
                    # Only support explicit integer count for fallback
                    throttle = int(serial[0])
                except (ValueError, TypeError):
                    pass

        # start with all workers being counted as being free
        workers_free = len(self._workers)
        if self._rolling_play and throttle > 0:
            workers_free = min(workers_free, throttle)

        self._set_hosts_cache(iterator._play)

        if iterator._play.max_fail_percentage is not None:
            display.warning("Using max_fail_percentage with the free strategy is not supported, as tasks are executed independently on each host")

        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            hosts_left = self.get_hosts_left(iterator)

            if len(hosts_left) == 0:
                self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                result = False
                break

            work_to_do = False        # assume we have no more work to do
            starting_host = last_host  # save current position so we know when we've looped back around and need to break

            # try and find an unblocked host with a task to run
            host_results = []
            while True:
                host = hosts_left[last_host]
                display.debug("next free host: %s" % host)
                host_name = host.get_name()

                # peek at the next task for the host, to see if there's
                # anything to do do for this host
                (state, task) = iterator.get_next_task_for_host(host, peek=True)
                display.debug("free host state: %s" % state, host=host_name)
                display.debug("free host task: %s" % task, host=host_name)

                # check if there is work to do, either there is a task or the host is still blocked which could
                # mean that it is processing an include task and after its result is processed there might be
                # more tasks to run
                if (task or self._blocked_hosts.get(host_name, False)) and not self._tqm._unreachable_hosts.get(host_name, False):
                    display.debug("this host has work to do", host=host_name)
                    # set the flag so the outer loop knows we've still found
                    # some work which needs to be done
                    work_to_do = True

                if not self._tqm._unreachable_hosts.get(host_name, False) and task:
                    # check to see if this host is blocked (still executing a previous task)
                    if not self._blocked_hosts.get(host_name, False):
                        display.debug("getting variables", host=host_name)
                        task_vars = self._variable_manager.get_vars(play=iterator._play, host=host, task=task,
                                                                    _hosts=self._hosts_cache,
                                                                    _hosts_all=self._hosts_cache_all)
                        self.add_tqm_variables(task_vars, play=iterator._play)
                        templar = Templar(loader=self._loader, variables=task_vars)
                        display.debug("done getting variables", host=host_name)

                        if not self._rolling_play:
                            try:
                                task_throttle = int(templar.template(task.throttle))
                            except Exception as e:
                                raise AnsibleError("Failed to convert the throttle value to an integer.", obj=task._ds, orig_exc=e)

                            if task_throttle > 0:
                                same_tasks = 0
                                for worker in self._workers:
                                    if worker and worker.is_alive() and worker._task._uuid == task._uuid:
                                        same_tasks += 1

                                display.debug("task: %s, same_tasks: %d" % (task.get_name(), same_tasks))
                                if same_tasks >= task_throttle:
                                    break

                        # advance the host, mark the host blocked, and queue it
                        self._blocked_hosts[host_name] = True
                        iterator.set_state_for_host(host.get_name(), state)

                        try:
                            action = action_loader.get(task.action, class_only=True, collection_list=task.collections)
                        except KeyError:
                            # we don't care here, because the action may simply not have a
                            # corresponding action plugin
                            action = None

                        try:
                            task.name = to_text(templar.template(task.name, fail_on_undefined=False), nonstring='empty')
                            display.debug("done templating", host=host_name)
                        except Exception:
                            # just ignore any errors during task name templating,
                            # we don't care if it just shows the raw name
                            display.debug("templating failed for some reason", host=host_name)

                        run_once = templar.template(task.run_once) or action and getattr(action, 'BYPASS_HOST_LOOP', False)
                        if run_once:
                            if action and getattr(action, 'BYPASS_HOST_LOOP', False):
                                raise AnsibleError("The '%s' module bypasses the host loop, which is currently not supported in the free strategy "
                                                   "and would instead execute for every host in the inventory list." % task.action, obj=task._ds)
                            else:
                                display.warning("Using run_once with the free strategy is not currently supported. This task will still be "
                                                "executed for every host in the inventory list.")

                        # check to see if this task should be skipped, due to it being a member of a
                        # role which has already run (and whether that role allows duplicate execution)
                        if not isinstance(task, Handler) and task._role:
                            role_obj = self._get_cached_role(task, iterator._play)
                            if role_obj.has_run(host) and role_obj._metadata.allow_duplicates is False:
                                display.debug("'%s' skipped because role has already run" % task, host=host_name)
                                del self._blocked_hosts[host_name]
                                continue

                        if task.action in C._ACTION_META:
                            self._execute_meta(task, play_context, iterator, target_host=host)
                            self._blocked_hosts[host_name] = False
                        else:
                            # handle step if needed, skip meta actions as they are used internally
                            if not self._step or self._take_step(task, host_name):
                                if task.any_errors_fatal:
                                    display.warning("Using any_errors_fatal with the free strategy is not supported, "
                                                    "as tasks are executed independently on each host")
                                if isinstance(task, Handler):
                                    self._tqm.send_callback('v2_playbook_on_handler_task_start', task)
                                else:
                                    self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
                                self._queue_task(host, task, task_vars, play_context)
                                # each task is counted as a worker being busy
                                workers_free -= 1
                                del task_vars
                    else:
                        display.debug("%s is blocked, skipping for now" % host_name)

                # all workers have tasks to do (and the current host isn't done with the play).
                # loop back to starting host and break out
                if self._host_pinned and workers_free == 0 and work_to_do:
                    last_host = starting_host
                    break

                # move on to the next host and make sure we
                # haven't gone past the end of our hosts list
                last_host += 1
                if last_host > len(hosts_left) - 1:
                    last_host = 0

                # if we've looped around back to the start, break out
                if last_host == starting_host:
                    break

            results = self._process_pending_results(iterator)
            host_results.extend(results)

            # each result is counted as a worker being free again
            workers_free += len(results)

            self.update_active_connections(results)

            included_files = IncludedFile.process_include_results(
                host_results,
                iterator=iterator,
                loader=self._loader,
                variable_manager=self._variable_manager
            )

            if len(included_files) > 0:
                all_blocks = dict((host, []) for host in hosts_left)
                failed_includes_hosts = set()
                for included_file in included_files:
                    display.debug("collecting new blocks for %s" % included_file)
                    is_handler = False
                    try:
                        if included_file._is_role:
                            new_ir = self._copy_included_file(included_file)

                            new_blocks, handler_blocks = new_ir.get_block_list(
                                play=iterator._play,
                                variable_manager=self._variable_manager,
                                loader=self._loader,
                            )
                        else:
                            is_handler = isinstance(included_file._task, Handler)
                            new_blocks = self._load_included_file(included_file, iterator=iterator, is_handler=is_handler)

                        # let PlayIterator know about any new handlers included via include_role or
                        # import_role within include_role/include_taks
                        iterator.handlers = [h for b in iterator._play.handlers for h in b.block]
                    except AnsibleParserError:
                        raise
                    except AnsibleError as e:
                        if included_file._is_role:
                            # include_role does not have on_include callback so display the error
                            display.error(to_text(e), wrap_text=False)
                        for r in included_file._results:
                            r._result['failed'] = True
                            failed_includes_hosts.add(r._host)
                        continue

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
                            final_block = new_block.filter_tagged_tasks(task_vars)
                        for host in hosts_left:
                            if host in included_file._hosts:
                                all_blocks[host].append(final_block)
                    display.debug("done collecting new blocks for %s" % included_file)

                for host in failed_includes_hosts:
                    self._tqm._failed_hosts[host.get_name()] = True
                    iterator.mark_host_failed(host)

                display.debug("adding all collected blocks from %d included file(s) to iterator" % len(included_files))
                for host in hosts_left:
                    iterator.add_tasks(host, all_blocks[host])
                display.debug("done adding collected blocks to iterator")

            # pause briefly so we don't spin lock
            time.sleep(C.DEFAULT_INTERNAL_POLL_INTERVAL)

        # collect all the final results
        results = self._wait_on_pending_results(iterator)

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered
        return super(StrategyModule, self).run(iterator, play_context, result)
