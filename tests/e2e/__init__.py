"""P4.9 black-box E2E test package.

These tests exercise the public ``sim-retire`` CLI exclusively as an external
subprocess.  They never import framework internals (engine, research, cli
builders, policies, executors, repositories).  See ``cli_harness.py``.
"""
