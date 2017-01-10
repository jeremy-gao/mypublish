#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os


class ExistCommand:
    def __init__(self, command):
        self.command = command

    def existcomand(self):
        for cmdpath in os.environ.get('PATH').split(':'):
            if os.path.isdir(cmdpath) and self.command in os.listdir(cmdpath):
                return True
            else:
                continue
        return False


if __name__ == "__main__":
    isexistcommand = ExistCommand('bash')
    print isexistcommand.existcomand()
