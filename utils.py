import subprocess

def run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs):
    return subprocess.run(cmd, check=check, stdout=stdout, stderr=stderr, **kwargs)

def check_output(cmd, **kwargs):
    return subprocess.check_output(cmd, **kwargs)

def update():
    cmds = ("git fetch",
            "git merge")
    for cmd in cmds:
        run(cmd)
    exit(0)
