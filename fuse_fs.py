import os
import sys
import shutil
import subprocess
from fuse import FUSE, FuseOSError, Operations
import stat
import errno
class NetworkedFileSystem(Operations):
    def __init__(self, remote, base_remote_path, mountpoint):
        self.remote = remote
        self.base_remote_path = base_remote_path
        self.mountpoint = mountpoint
        self.local_cache = "/tmp/networkedfs_cache/"
        self.modified_fds = set()
        # Unmount the filesystem if it's already mounted
        if os.path.ismount(self.mountpoint):
            os.system(f'fusermount -uz {self.mountpoint}')

        # Clear and recreate mountpoint and cache directories
        self._clear_directory(self.mountpoint)
        self._clear_directory(self.local_cache)

    def _remote_to_local(self, path):
        return os.path.join(self.local_cache, os.path.basename(path))

    def _construct_remote_path(self, path):
        return f"{self.remote}:{self.base_remote_path.rstrip('/')}{path}"

    def _clear_directory(self, dir_path):
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.mkdir(dir_path)

    def getattr(self, path, fh=None):
        # Construct command to SSH and get the file stats
        command = (f'ssh {self.remote} "stat -c \'%f %s %X %Y %Z %u %g %h\' '
               f'{self.base_remote_path.rstrip("/")}{path}"')
        
        local_path = self._remote_to_local(path)
        if os.path.exists(local_path):
            st = os.lstat(local_path)
            return {
            'st_mode': st.st_mode,
            'st_size': st.st_size,
            'st_atime': st.st_atime,
            'st_mtime': st.st_mtime,
            'st_ctime': st.st_ctime,
            'st_uid': st.st_uid,
            'st_gid': st.st_gid,
            'st_nlink': st.st_nlink
            }

        print(f"{local_path} does not exist.. using remote")
        # Execute the command and get the output
        
        try:
            result = subprocess.check_output(command, shell=True).decode('utf-8').split()

            # Map the results to the relevant fields
            stat_data = {
                'st_mode': int(result[0], 16),  # Convert hex mode to int mode
                'st_size': int(result[1]),
                'st_atime': float(result[2]),
                'st_mtime': float(result[3]),
                'st_ctime': float(result[4]),
                'st_uid': int(result[5]),
                'st_gid': int(result[6]),
                'st_nlink': int(result[7]),
            }
        except:
            raise FuseOSError(errno.ENOENT)



        # Ensure the mode clearly identifies it as a file or directory
        if stat.S_ISREG(stat_data['st_mode']):
            stat_data['st_mode'] |= stat.S_IFREG
        elif stat.S_ISDIR(stat_data['st_mode']):
            stat_data['st_mode'] |= stat.S_IFDIR    


        return stat_data


    def readdir(self, path, fh):
        command = f"ssh {self.remote} 'ls {self.base_remote_path.rstrip('/')}{path}'"
        result = subprocess.check_output(command, shell=True).decode('utf-8').splitlines()
        # Always include '.' and '..' for directory listings
        return ['.', '..'] + result

    def open(self, path, flags):
        local_path = self._remote_to_local(path)
        if not os.path.exists(local_path):
            print(f"opening- {local_path} does not exist in cache, downloading")
            os.system(f'scp {self._construct_remote_path(path)} {local_path}')
        return os.open(local_path, flags)

    def read(self, path, size, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, size)

    def write(self, path, data, offset, fh):
        print(path)
        os.lseek(fh, offset, os.SEEK_SET)
        written = os.write(fh, data)
        self.modified_fds.add(fh)  # mark the file descriptor as modified
        return written

    def create(self, path, mode, fi=None):
        local_path = self._remote_to_local(path)
        fd = os.open(local_path, os.O_WRONLY | os.O_CREAT, mode)
        # Upload the empty file to the remote server
        os.system(f'scp {local_path} {self._construct_remote_path(path)}')
        return fd

    def release(self, path, fh):
        os.close(fh)
        if fh in self.modified_fds:
            os.system(f'scp {self._remote_to_local(path)} {self._construct_remote_path(path)}')
            self.modified_fds.remove(fh)  # remove the descriptor from the modified set
        # Delete the file from the cache
        return 0


    def chmod(self, path, mode):
        local_path = self._remote_to_local(path)
        os.chmod(local_path, mode)
        os.system(f'scp {local_path} {self._construct_remote_path(path)}')
        return 0


    def mkdir(self, path, mode):
        local_path = self._remote_to_local(path)
        os.mkdir(local_path, mode)
        return 0

    def unlink(self, path):
        local_path = self._remote_to_local(path)
        if os.path.exists(local_path):
            os.remove(local_path)
        
        # Remove the file on the remote server
        os.system(f'ssh {self.remote} "rm {self.base_remote_path.rstrip("/")}{path}"')
        return 0

    def rmdir(self, path):
        local_path = self._remote_to_local(path)
        if os.path.exists(local_path):
            os.rmdir(local_path)
        
        # Remove the directory on the remote server
        os.system(f'ssh {self.remote} "rmdir {self.base_remote_path.rstrip("/")}{path}"')
        return 0

def main(mountpoint, remote, base_remote_path):
    if not os.path.ismount(mountpoint):
        FUSE(NetworkedFileSystem(remote, base_remote_path, mountpoint), mountpoint, nothreads=True, foreground=True)
    else:
        print(f"{mountpoint} is already mounted. Please unmount first.")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f'usage: {sys.argv[0]} <mountpoint> <remote> <base_remote_path>')
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3])

