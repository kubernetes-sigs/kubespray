#!/usr/bin/env python
import argparse
import openstack
import logging
import datetime
import time

log = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Cleanup OpenStack resources")

parser.add_argument(
    "--hours",
    type=int,
    default=4,
    help="Age (in hours) of VMs to cleanup (default: 4h)",
)
parser.add_argument("--dry-run", action="store_true", help="Do not delete anything")

args = parser.parse_args()

oldest_allowed = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
    hours=args.hours
)


def main():
    logging.basicConfig(level=logging.INFO)
    if args.dry_run:
        log.info("Running in dry-run mode")

    conn = openstack.connect()

    log.info("Deleting servers...")
    map_if_old(conn.compute.delete_server, conn.compute.servers())

    log.info("Deleting ports...")
    try:
        map_if_old(conn.network.delete_port, conn.network.ports())
    except openstack.exceptions.ConflictException as ex:
        # Need to find subnet-id which should be removed from a router
        for sn in conn.network.subnets():
            try:
                fn_if_old(conn.network.delete_subnet, sn)
            except openstack.exceptions.ConflictException:
                for r in conn.network.routers():
                    log.info("Deleting subnet %s from router %s", sn, r)
                    try:
                        conn.network.remove_interface_from_router(r, subnet_id=sn.id)
                    except Exception as ex:
                        log.error("Failed to delete subnet from router", exc_info=True)

        for ip in conn.network.ips():
            fn_if_old(conn.network.delete_ip, ip)

        # After removing unnecessary subnet from router, retry to delete ports
        map_if_old(conn.network.delete_port, conn.network.ports())

    log.info("Deleting security groups...")
    try:
        map_if_old(conn.network.delete_security_group, conn.network.security_groups())
    except openstack.exceptions.ConflictException as ex:
        # Need to delete port when security groups is in used
        map_if_old(conn.network.delete_port, conn.network.ports())
        map_if_old(conn.network.delete_security_group, conn.network.security_groups())

    log.info("Deleting Subnets...")
    map_if_old(conn.network.delete_subnet, conn.network.subnets())

    log.info("Deleting networks...")
    for n in conn.network.networks():
        if not n.is_router_external:
            fn_if_old(conn.network.delete_network, n)

    log.info("Deleting keypairs...")
    map_if_old(
        conn.compute.delete_keypair,
        (conn.compute.get_keypair(x.name) for x in conn.compute.keypairs()),
        # LIST API for keypairs does not give us a created_at (WTF)
    )


# runs the given fn to all elements of the that are older than allowed
def map_if_old(fn, items):
    for item in items:
        fn_if_old(fn, item)


# run the given fn function only if the passed item is older than allowed
def fn_if_old(fn, item):
    created_at = datetime.datetime.fromisoformat(item.created_at)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=datetime.timezone.utc)
        # Handle TZ unaware object by assuming UTC
        # Can't compare to oldest_allowed otherwise
    if item.name == "default":  # skip default security group
        return
    if created_at < oldest_allowed:
        log.info("Will delete %s %s)", item.name, item.id)
        if not args.dry_run:
            fn(item)


if __name__ == "__main__":
    # execute only if run as a script
    main()
