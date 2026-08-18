---
status: disfavored
---

# glibc/pymalloc fragmentation inflates RSS beyond live objects

Fragmentation can hold RSS high after frees and would explain "RSS never
drops", but not growth proportional to cumulative traffic, and not
Private_Dirty tracking RssAnon exactly at half a GiB. At most a
second-order contributor on top of the store retention. Becomes
interesting only if `view.clear` empties the store yet RSS stays pinned
*and* subsequent growth resumes at the old rate.
