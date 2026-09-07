# incident.uncaught

An addon hook, or an offline tool that files its own failures, raised; the
traceback is the body under `log/patch-failures/_uncaught-<module>/`. Read
it when the count grows or the same record comes back after expiring. One
record is usually a request the upstream API shaped oddly, and gc expires it
unread after the retention window (`gc_patch_failures.py`); a recurring one
is a bug in the module the rule names, and the traceback says where.
