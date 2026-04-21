#!/usr/bin/python
# -*- coding: utf-8 -*-
'DDoS Compatibility Module (Build Your Own Botnet Simulation)'

# standard library
import os
import shlex
import socket
import subprocess

# utilities
import util

# globals
command = True
packages = ['util']
platforms = ['win32', 'linux', 'linux2', 'darwin']
usage = 'ddos [target_ip] [type=syn/icmp] [port]'
description = """
Compatibility wrapper for the legacy ddos command.
Instead of generating flood traffic, this module performs a limited firewall
probe using either a TCP connect check ("syn") or a single ICMP echo ("icmp").
"""


def _parse_action(action):
    """
    Parse a legacy ddos command string into a safe probe request.

    Supported examples:
      "192.168.1.10"
      "192.168.1.10 syn"
      "192.168.1.10 syn 443"
      "example.com icmp"
    """
    parts = shlex.split(action) if isinstance(action, str) and action.strip() else []

    target = parts[0] if len(parts) >= 1 else '127.0.0.1'
    probe_type = parts[1].lower() if len(parts) >= 2 else 'syn'
    port = parts[2] if len(parts) >= 3 else '80'

    if probe_type == 'tcp':
        probe_type = 'syn'

    if probe_type not in ('syn', 'icmp'):
        raise ValueError("invalid probe type '{}'; use 'syn' or 'icmp'".format(probe_type))

    if probe_type == 'syn':
        if not str(port).isdigit():
            raise ValueError("invalid TCP port '{}'".format(port))
        port = int(port)
        if port < 1 or port > 65535:
            raise ValueError("TCP port must be between 1 and 65535")
    else:
        port = None

    return target, probe_type, port


def _resolve_target(target):
    """
    Resolve a target hostname/IP and return the first usable address.
    """
    try:
        info = socket.getaddrinfo(target, None, 0, socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("unable to resolve target '{}': {}".format(target, exc))

    if not info:
        raise ValueError("unable to resolve target '{}'".format(target))

    family, _, _, _, sockaddr = info[0]
    address = sockaddr[0]
    return family, address


def _tcp_probe(target, port, timeout=3):
    """
    Perform a bounded TCP connect probe and classify the result.
    """
    family, address = _resolve_target(target)
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        result = sock.connect_ex((address, port))
        if result == 0:
            state = 'open'
            details = 'TCP connect succeeded'
        elif result in (111, 61, 10061):
            state = 'closed'
            details = 'connection refused'
        else:
            state = 'filtered_or_unreachable'
            details = 'connect_ex returned {}'.format(result)
    except socket.timeout:
        state = 'filtered_or_timed_out'
        details = 'connection attempt timed out'
    except Exception as exc:
        state = 'error'
        details = str(exc)
    finally:
        sock.close()

    return address, state, details


def _ping_command(address):
    """
    Build a single-echo ping command for the current platform.
    """
    if os.name == 'nt':
        return ['ping', '-n', '1', '-w', '2000', address]
    return ['ping', '-c', '1', '-W', '2', address]


def _icmp_probe(target):
    """
    Perform a single ICMP echo request using the system ping command.
    """
    _, address = _resolve_target(target)
    cmd = _ping_command(address)

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
    except OSError as exc:
        return address, 'error', "ping command unavailable: {}".format(exc)

    output = (process.stdout or process.stderr or '').strip().splitlines()
    details = output[-1] if output else 'no diagnostic output'

    if process.returncode == 0:
        state = 'reachable'
    else:
        state = 'blocked_or_unreachable'

    return address, state, details


def run(action=""):
    """
    Run a safe network probe while preserving the legacy ddos entrypoint.

    Args:
        action: Command string in the form "<target> <syn|icmp> [port]".

    Returns:
        str: Probe result summary.
    """
    try:
        target, probe_type, port = _parse_action(action)

        if probe_type == 'syn':
            address, state, details = _tcp_probe(target, port)
            return (
                "TCP probe complete: target={} resolved={} port={} state={} details={}"
                .format(target, address, port, state, details)
            )

        address, state, details = _icmp_probe(target)
        return (
            "ICMP probe complete: target={} resolved={} state={} details={}"
            .format(target, address, state, details)
        )
    except ValueError as exc:
        return "Error: {}. Usage: {}".format(exc, usage)
    except Exception as exc:
        return "{} error: {}".format(run.__name__, str(exc))
