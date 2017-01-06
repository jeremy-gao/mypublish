#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bottle import view, run, static_file, route, request, default_app
import subprocess, ConfigParser, os
from beaker.middleware import SessionMiddleware


# rsync -ac --list-only --delete --links --copy-links --exclude=".svn" --exclude=".log" /home/www /home/mnt

@route('/assets/js/skin/default/<filepath:path>')
def static_filepath(filepath):
    return static_file(filepath, root="./assets/js/skin/default/")


@route('/assets/<filepath:path>')
def static_filepath(filepath):
    return static_file(filepath, root="./assets/")


def execsubpro(cmdstr):
    try:
        returncode = subprocess.check_output(cmdstr, shell=True)
    except Exception, e:
        returncode = e
    finally:
        return returncode


def execsubproPopen(cmdstr1):
    filecontent = execsubpro(cmdstr1)
    filepath = '/tmp/remotefile.php'
    try:
        with open(filepath, 'w') as f:
            f.write(filecontent)
            f.flush()
    except Exception, e:
        filepath = e
        return filepath
    else:
        return filepath


def ColordiffsubproPopen(cmdstr1):
    try:
        child1 = subprocess.Popen(cmdstr1, shell=True, stdout=subprocess.PIPE)
        child2 = subprocess.Popen('bash ./ansi2html.sh', shell=True, stdin=child1.stdout, stdout=subprocess.PIPE)
        returncode = child2.communicate()
    except Exception, e:
        returncode = e
    finally:
        return returncode


@route('/')
@view('index')
def index():
    pass


# targetdir = ""
# destdir = ""
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 600,
    'session.data_dir': '/tmp/',
    'session.auto': True
}


@route('/diff.html', method="POST")
@view('diff')
def difflist():
    cf = ConfigParser.ConfigParser()
    cf.read('./config.ini')
    exclude_list = cf.get('default', 'exclude').split(',')
    rsyncopts = cf.get('default', 'rsync_opts')
    user = cf.get('default', 'user')
    try_run = cf.get('default', 'try_run')
    exclude = ""
    for exlist in exclude_list:
        exclude += "--exclude=" + exlist + " "
    # get exclude file name
    excludefile = request.forms.get('excludefile').strip()
    if excludefile != "":
        for exfile in excludefile.strip().split('\r\n'):
            exclude += "--exclude=" + '"' + exfile + '"' + " "
    # global targetdir
    targetdir = request.forms.get('targetdir')
    # global destdir
    destdir = request.forms.get('destdir')
    # session
    sessiondir = request.environ.get('beaker.session')
    # add targetdir and destdir and exclude to session
    sessiondir['targetdir'] = targetdir
    sessiondir['destdir'] = destdir
    sessiondir['exclude'] = exclude
    sessiondir.save()
    commandrsync = "rsync " + rsyncopts + " " + try_run + " " + exclude + targetdir + " " + user + "@" + destdir
    try:
        syncdirname = os.path.dirname(targetdir)
        difffile = execsubpro(commandrsync).split('\n')
    except Exception, e:
        return dict(difffile=e, syncdirname="checksum failed........")
    else:
        return dict(difffile=difffile, syncdirname=syncdirname)


@route('/push.html', method="POST")
@view('push')
def pushfile():
    cf = ConfigParser.ConfigParser()
    cf.read('./config.ini')
    # exclude_list = cf.get('default', 'exclude').split(',')
    rsyncopts = cf.get('default', 'rsync_opts')
    user = cf.get('default', 'user')
    # exclude = ""
    # for exlist in exclude_list:
    #     exclude += "--exclude=" + exlist + " "
    pushcontent = request.forms.get('pushfile').strip()
    ##get exclude file name
    # excludefile = request.forms.get('excludefile').strip()
    # if excludefile != "":
    #     for exfile in excludefile.strip().split('\r\n'):
    #         exclude += "--exclude=" + '"' + exfile + '"' + " "
    listsyncfile = []
    if len(pushcontent) != 0:
        for pushlist in pushcontent.split('\r\n'):
            sessiondir = request.environ.get('beaker.session')
            destdir = sessiondir.get('destdir')
            targethost = destdir.split(":")[0]
            # ----get session exclude ----###
            exclude = sessiondir.get('exclude')
            # 循环执行
            commandrsync = "rsync " + "-v " + rsyncopts + " " + exclude + pushlist + " " + user + "@" + targethost + ":" + pushlist
            try:
                syncfile = execsubpro(commandrsync).split('\n')
            except Exception, e:
                return dict(sucess="同步失败，请联系管理员!!!", e=e)
            else:
                listsyncfile.append(syncfile)
        returnsucess = "Hi,恭喜你,发步成功了!"
        return dict(listsyncfile=listsyncfile, returnsucess=returnsucess)
    else:
        sessiondir = request.environ.get('beaker.session')
        destdir = sessiondir.get('destdir')
        targethost = destdir.split(":")[0]
        targetdir = sessiondir.get('targetdir')
        # ----get session exclude ----###
        exclude = sessiondir.get('exclude')
        commandrsync = "rsync " + "-v " + rsyncopts + " " + exclude + targetdir + " " + user + "@" + targethost + ":" + targetdir
        try:
            syncfile = execsubpro(commandrsync).split('\n')
        except Exception, e:
            return dict(sucess="同步失败，请联系管理员!!!", e=e)
        else:
            listsyncfile.append(syncfile)
        returnsucess = "Hi,恭喜你,发步成功了!"
        return dict(listsyncfile=listsyncfile, returnsucess=returnsucess)


@route('/compare.html')
@view('compare')
def comparefile():
    if request.GET.get('filename'):
        sessiondir = request.environ.get('beaker.session')
        destdir = sessiondir.get('destdir')
        targethost = destdir.split(":")[0]
        filename = request.GET.get('filename')
        if os.path.isfile(filename):
            cf = ConfigParser.ConfigParser()
            cf.read('./config.ini')
            user = cf.get('default', 'user')
            fileExiststr = "ssh " + targethost + " -l " + user + " [ -f " + filename + " ]"
            returnstatus = subprocess.call(fileExiststr, shell=True)
            if returnstatus == 0:
                cmdstr1 = "ssh " + user + "@" + targethost + " cat " + filename
                remotefile = execsubproPopen(cmdstr1)
                if os.path.isfile(remotefile):
                    diffcmdstr = "git diff --color " + remotefile + " " + filename
                    returndiff = ColordiffsubproPopen(diffcmdstr)
                    return dict(returndiff=returndiff[0])
                else:
                    return dict(returndiff="出错了骚年,没有远程文件或者远程文件下载失败！请联系管理员检查....")
            else:
                return dict(returndiff="骚年,线上服务器没有此文件！请先同步此文件到线上服务器或者联系管理员检查....")
        else:
            return dict(returndiff="骚年,暂不支持对比目录或者其他非普通文件!!!!")
    else:
        returndiff = "骚年,没有获取到要对比的文件，或者对比文件无效!!!!"
        return dict(returndiff=returndiff)


myapp = SessionMiddleware(default_app(), session_opts)
run(app=myapp, host="0.0.0.0", port=8080, debug=True)
