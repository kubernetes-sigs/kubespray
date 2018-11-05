"""
mitop.py is a version of the UNIX top command that knows how to display process
lists from multiple machines in a single listing.

This is a basic, initial version showing overall program layout. A future
version will extend it to:

    * Only notify the master of changed processes, rather than all processes.
    * Runtime-reconfigurable filters and aggregations handled on the remote
      machines rather than forcing a bottleneck in the master.

"""

import curses
import subprocess
import sys
import time

import mitogen.core
import mitogen.master
import mitogen.select
import mitogen.utils


class Host(object):
    """
    A target host from the perspective of the master process.
    """
    #: String hostname.
    name = None

    #: mitogen.parent.Context used to call functions on the host.
    context = None

    #: mitogen.core.Receiver the target delivers state updates to.
    recv = None

    def __init__(self):
        #: Mapping of pid -> Process() for each process described
        #: in the host's previous status update.
        self.procs = {}


class Process(object):
    """
    A single process running on a target host.
    """
    host = None
    user = None
    pid = None
    ppid = None
    pgid = None
    command = None
    rss = None
    pcpu = None
    rss = None


def child_main(sender, delay):
    """
    Executed on the main thread of the Python interpreter running on each
    target machine, Context.call() from the master. It simply sends the output
    of the UNIX 'ps' command at regular intervals toward a Receiver on master.
    
    :param mitogen.core.Sender sender:
        The Sender to use for delivering our result. This could target
        anywhere, but the sender supplied by the master simply causes results
        to be delivered to the master's associated per-host Receiver.
    """
    args = ['ps', '-axwwo', 'user,pid,ppid,pgid,%cpu,rss,command']
    while True:
        sender.send(subprocess.check_output(args).decode())
        time.sleep(delay)


def parse_output(host, s):
    prev_pids = set(host.procs)

    for line in s.splitlines()[1:]:
        bits = line.split(None, 6)
        pid = int(bits[1])
        new = pid not in prev_pids
        prev_pids.discard(pid)

        try:
            proc = host.procs[pid]
        except KeyError:
            host.procs[pid] = proc = Process()
            proc.hostname = host.name

        proc.new = new
        proc.user = bits[0]
        proc.pid = pid
        proc.ppid = int(bits[2])
        proc.pgid = int(bits[3])
        proc.pcpu = float(bits[4])
        proc.rss = int(bits[5]) / 1024
        proc.command = bits[6]

    # These PIDs had no update, so probably they are dead now.
    for pid in prev_pids:
        del host.procs[pid]


class Painter(object):
    """
    This is ncurses (screen drawing) magic, you can ignore it. :)
    """
    def __init__(self, hosts):
        self.stdscr = curses.initscr()
        curses.start_color()
        self.height, self.width = self.stdscr.getmaxyx()
        curses.cbreak()
        curses.noecho()
        self.stdscr.keypad(1)
        self.hosts = hosts
        self.format = (
            '%(hostname)10.10s '
            '%(pid)7.7s '
            '%(ppid)7.7s '
            '%(pcpu)6.6s '
            '%(rss)5.5s '
            '%(command)20s'
        )

    def close(self):
        curses.endwin()

    def paint(self):
        self.stdscr.erase()
        self.stdscr.addstr(0, 0, time.ctime())

        all_procs = []
        for host in self.hosts:
            all_procs.extend(host.procs.values())

        all_procs.sort(key=(lambda proc: -proc.pcpu))

        self.stdscr.addstr(1, 0, self.format % {
            'hostname': 'HOST',
            'pid': 'PID',
            'ppid': 'PPID',
            'pcpu': '%CPU',
            'rss': 'RSS',
            'command': 'COMMAND',
        })
        for i, proc in enumerate(all_procs):
            if (i+3) >= self.height:
                break
            if proc.new:
                self.stdscr.attron(curses.A_BOLD)
            else:
                self.stdscr.attroff(curses.A_BOLD)
            self.stdscr.addstr(2+i, 0, self.format % dict(
                vars(proc),
                command=proc.command[:self.width-36]
            ))

        self.stdscr.refresh()


def master_main(painter, router, select, delay):
    """
    Loop until CTRL+C is pressed, waiting for the next result delivered by the
    Select. Use parse_output() to turn that result ('ps' command output) into
    rich data, and finally repaint the screen if the repaint delay has passed.
    """
    next_paint = 0
    while True:
        msg = select.get()
        parse_output(msg.receiver.host, msg.unpickle())
        if next_paint < time.time():
            next_paint = time.time() + delay
            painter.paint()


@mitogen.main()
def main(router):
    """
    Main program entry point. @mitogen.main() is just a helper to handle
    reliable setup/destruction of Broker, Router and the logging package.
    """
    argv = sys.argv[1:]
    if not len(argv):
        print('mitop: Need a list of SSH hosts to connect to.')
        sys.exit(1)

    delay = 2.0
    select = mitogen.select.Select(oneshot=False)
    hosts = []

    # For each hostname on the command line, create a Host instance, a Mitogen
    # connection, a Receiver to accept messages from the host, and finally
    # start child_main() on the host to pump messages into the receiver.
    for hostname in argv:
        print('Starting on', hostname)
        host = Host()
        host.name = hostname

        if host.name == 'localhost':
            host.context = router.local()
        else:
            host.context = router.ssh(hostname=host.name)

        # A receiver wires up a handle (via Router.add_handler()) to an
        # internal thread-safe queue object, which can be drained through calls
        # to recv.get().
        host.recv = mitogen.core.Receiver(router)
        host.recv.host = host

        # But we don't want to receive data from just one receiver, we want to
        # receive data from many. In this case we can use a Select(). It knows
        # how to efficiently sleep while waiting for the first message sent to
        # many receivers.
        select.add(host.recv)

        # The inverse of a Receiver is a Sender. Unlike receivers, senders are
        # serializable, so we can call the .to_sender() helper method to create
        # one equivalent to our host's receiver, and pass it directly to the
        # host as a function parameter.
        sender = host.recv.to_sender()

        # Finally invoke the function in the remote target. Since child_main()
        # is an infinite loop, using .call() would block the parent, since
        # child_main() never returns. Instead use .call_async(), which returns
        # another Receiver. We also want to wait for results from it --
        # although child_main() never returns, if it crashes the exception will
        # be delivered instead.
        call_recv = host.context.call_async(child_main, sender, delay)
        call_recv.host = host

        # Adding call_recv to the select will cause mitogen.core.CallError to
        # be thrown by .get() if startup of any context fails, causing halt of
        # master_main(), and the exception to be printed.
        select.add(call_recv)
        hosts.append(host)

    # Painter just wraps up all the prehistory ncurses code and keeps it out of
    # master_main().
    painter = Painter(hosts)
    try:
        try:
            master_main(painter, router, select, delay)
        except KeyboardInterrupt:
            # Shut down gracefully when the user presses CTRL+C.
            pass
    finally:
        painter.close()
