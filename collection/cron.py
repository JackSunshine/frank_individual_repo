import subprocess
import time
import commands


def check_if_agent_running(agent):
    errcode, output = commands.getstatusoutput("ps -aux | grep -e %s | grep -v grep | awk '{print $2}'" % (agent))
    if output:
        return True
    return False


if __name__ == '__main__':
    while True:
        number = commands.getstatusoutput("wc -l db.log")
        if not check_if_agent_running('test.py'):
            if number is not 3377:
                subprocess.call('python test.py', shell=True)
                time.sleep(120)
            else:
                break
