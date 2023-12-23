# User-Level Networked Filesystem

This project implements a user-level filesystem using FUSE (Filesystem in Userspace) that allows users to interact with a remote filesystem via SCP and SSH. The system abstracts the complexities of remote file management, providing a seamless interface for performing local filesystem operations that are transparently redirected to a remote system.

## Overview

The User-Level Networked Filesystem integrates local and remote filesystems by utilizing SSH for command execution on the remote server and SCP for file transfer. This integration enables various filesystem operations such as file creation, reading, writing, and deletion to be executed on a remote server as if they were being performed locally.

## Installation

Before you begin, ensure you have Python installed on your system along with the `fusepy` library, which is a Python wrapper for FUSE. You will also need SSH and SCP set up on both the local and remote machines for remote communication.

To install `fusepy`, you can use pip:

```bash
pip install fusepy
```

## Usage

The main file of this project is `fuse_fs.py`, which can be executed with the following command structure:

```bash
./fuse_fs.py <mountpoint> <remote> <base_remote_path>
```

- `<mountpoint>`: The local directory where the remote filesystem will be mounted.
- `<remote>`: SSH host for the remote filesystem in the format `user@hostname`.
- `<base_remote_path>`: The root directory on the remote server which you want to access through FUSE.

Example:

```bash
./fuse_fs.py /users/localuser/fuse_mnt user@remotehost.com /users/remoteuser/
```

This command will mount the remote directory `/users/remoteuser/` from `remotehost.com` to your local directory `/users/localuser/fuse_mnt`.

## Features

- **Transparent File Operations**: Perform file operations like read, write, open, and delete as if they are on a local directory.
- **Caching**: Local caching of files for improved read and write performance.
- **SSH & SCP Integration**: Secure communication using SSH and SCP.
