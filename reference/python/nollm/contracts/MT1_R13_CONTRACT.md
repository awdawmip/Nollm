# MT1-R13: SafeRoot V3 Capability Storage and Archive Transaction Closure

## Contract

### SafeRoot V3: descriptor/handle-anchored storage

SafeRoot V3 replaces the path-based V2. The root descriptor (fd on POSIX, HANDLE on Windows) is the sole authority for child operations.

**Invariants:**
1. Root symlink/reparse rejected before resolution
2. All child directory traversal uses dir_fd-relative opens with O_NOFOLLOW/no-reparse
3. Final file opens use O_NOFOLLOW/no-reparse
4. Read loops until EOF (no silent short read)
5. Write loops until all bytes written (no silent short write)
6. replace=False is atomic no-clobber (link-based exclusive publish)
7. All authoritative artifacts require private inode (nlink==1)
8. Identity verified before and after read
9. fsync file and parent dir after writes

**Windows approach:**
- Use CreateFileW with FILE_FLAG_OPEN_REPARSE_POINT on every component
- Use GetFileInformationByHandle for identity and nlink
- Use WriteFile in a loop for write-all
- Use ReadFile in a loop for read-all
- Use MoveFileExW with MOVEFILE_WRITE_THROUGH for durable replace
- For no-clobber: create temp with CREATE_NEW, then link to target; if link fails, target exists

### Archive v5 transaction

Archive snapshot creation is transactional:
1. Validate workspace/policy before any memory-root write
2. Open single SafeRoot V3
3. Read sources through safe source-root (reject symlink/reparse)
4. Build manifest/object plan in memory
5. Stage under root-contained transaction dir
6. Validate staged artifacts (hash, inode, schema, closure)
7. Atomically publish manifest last
8. fsync all files and directories
9. On failure: clean staging or quarantine

### Cross-process coordinator

Replace threading.RLock with file-based coordinator:
- Lock dir under memory root with owner.json (fencing token, PID, timestamp)
- Stale reclaim only after identity/fencing check
- Serializes planner, commit, reconcile, recovery, ledger mutation
