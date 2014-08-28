import subprocess

class SubprocessFailedException(Exception):
    def __init__(self, reason, returncode):
        self.returncode = returncode
        super(SubprocessFailedException, self).__init__(reason)

def exec_cmd(arguments, environment={}, stdin=None, raiseonerr=True):
    p = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
    stdout, stderr = p.communicate(input=stdin)
    if raiseonerr and p.returncode != 0:
        raise SubprocessFailedException("Subprocess {} returned {}!".format(' '.join(arguments), p.returncode), p.returncode)

    return stdout, stderr, p.returncode
