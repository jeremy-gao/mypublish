#!/usr/bin/env python
# -*- coding:utf-8 -*-
# 保留destdir输入是为了保证本地和线上路径不一致以及不同版本之间的对比.
# rsync -ac --list-only --delete --links --copy-links --exclude=".svn" --exclude=".log" /home/www /home/mnt
from bottle import view, run, static_file, route, request, default_app
from beaker.middleware import SessionMiddleware
from PublishModule import ExistCommand
import subprocess
import ConfigParser
import os


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
        # get ansi2html.sh parent path
        current_path = os.path.dirname(__file__)
        # get bash environment
        bash_shell = os.environ.get('SHELL')
        # get ansi2html.sh path
        gitdiffhtml = bash_shell + " " + current_path + '/ansi2html.sh'
        child1 = subprocess.Popen(cmdstr1, shell=True, stdout=subprocess.PIPE)
        child2 = subprocess.Popen(gitdiffhtml, shell=True, stdin=child1.stdout, stdout=subprocess.PIPE)
        returncode = child2.communicate()
    except Exception, e:
        returncode = e
    finally:
        return returncode


@route('/')
@view('index')
def index():
    host = ConfigParser.ConfigParser()
    host.read('./config.ini')
    hostlist = host.get('hosts', 'list')
    apppath = host.get('app', 'path')
    # -- get exclude_groups --
    exclude_groups = host.options('exclude_groups')
    hiddenp = ""
    for group in exclude_groups:
        hiddenp += '<p id="' + group + '" data="' + host.get('exclude_groups', group).replace(" ", "\n") + '"> </p>'
    # core_exclude = host.get('core', 'exclude')
    # customer_exclude = host.get('customer', 'exclude')
    # finance_exclude = host.get('finance', 'exclude')
    # merchant_exclude = host.get('merchant', 'exclude')
    # route_exclude = host.get('route', 'exclude')
    # slim_exclude = host.get('slim', 'exclude')
    appdict = {}
    appversionlist = []
    for appname in os.listdir(apppath):
        # print apppath + appname
        for appversion in os.listdir(apppath + appname):
            if len(appversion) > 0:
                appversionlist.append(appversion)
        # print appversionlist
        appdict[appname] = appversionlist
        appversionlist = []
    return dict(hostlist=hostlist, appdict=appdict, apppath=apppath, hiddenp=hiddenp)


session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 600,
    'session.data_dir': '/tmp/',
    'session.auto': True
}
# read config.ini
cf = ConfigParser.ConfigParser()
cf.read('./config.ini')


@route('/diff.html', method="POST")
@view('diff')
def difflist():
    exclude_list = cf.get('default', 'exclude').split(',')
    rsyncopts = cf.get('default', 'rsync_opts')
    user = cf.get('default', 'user')
    try_run = cf.get('default', 'try_run')
    exclude = ""
    for exlist in exclude_list:
        exclude += "--exclude=" + exlist + " "
    # get exclude file name from index forms
    excludefile = request.forms.get('excludefile').strip()
    if excludefile != "":
        for exfile in excludefile.strip().split('\r\n'):
            exclude += "--exclude=" + '"' + exfile + '"' + " "

    # get selected hostip
    hostip = request.forms.get('hostip')
    # global targetdir
    targetdir = request.forms.get('targetdir')
    # global destdir
    destdir = request.forms.get('destdir')
    # session
    sessiondir = request.environ.get('beaker.session')
    # add targetdir and destdir and exclude to session
    sessiondir['hostip'] = hostip
    sessiondir['targetdir'] = targetdir
    sessiondir['destdir'] = destdir
    sessiondir['exclude'] = exclude
    sessiondir.save()
    commandrsync = "rsync " + rsyncopts + " " + try_run + " " + exclude + targetdir + " " \
                   + user + "@" + hostip + ":" + destdir
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
    rsyncopts = cf.get('default', 'rsync_opts')
    user = cf.get('default', 'user')
    pushcontent = request.forms.get('pushfile').strip()
    listsyncfile = []
    if len(pushcontent) != 0:
        for pushlist in pushcontent.split('\r\n'):
            sessiondir = request.environ.get('beaker.session')
            # destdir = sessiondir.get('destdir')
            desthost = sessiondir.get('hostip')
            # ----get session exclude ----###
            exclude = sessiondir.get('exclude')
            # 循环执行
            commandrsync = "rsync " + "-v " + rsyncopts + " " + exclude + pushlist + " " \
                           + user + "@" + desthost + ":" + pushlist
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
        desthost = sessiondir.get('hostip')
        targetdir = sessiondir.get('targetdir')
        # ----get session exclude ----###
        exclude = sessiondir.get('exclude')
        commandrsync = "rsync " + "-v " + rsyncopts + " " + exclude + targetdir + " " \
                       + user + "@" + desthost + ":" + destdir
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
        desthost = sessiondir.get('hostip')
        filename = request.GET.get('filename')
        if os.path.isfile(filename):
            user = cf.get('default', 'user')
            fileExiststr = "ssh " + desthost + " -l " + user + " [ -f " + filename + " ]"
            returnstatus = subprocess.call(fileExiststr, shell=True)
            if returnstatus == 0:
                cmdstr1 = "ssh " + user + "@" + desthost + " cat " + filename
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


@route('/svnupdate.html&<dirpath:path>')
@view('svnupdate')
def svnupdate(dirpath):
    if os.path.isdir(dirpath):
        # sudo root nopasswd
        # sudo svn up /home/www/svn/core/v2.3.5/ --username xxx --password xxx
        existcmd = ExistCommand.ExistCommand('svn')
        if existcmd:
            # svn_url = cf.get('svn', 'svn_url')
            username = cf.get('svn', 'username')
            password = cf.get('svn', 'password')
            svnupcmd = "sudo svn up " + dirpath + " --username " + username + " --password " + password
            # print svnupcmd
            try:
                retuncode = execsubpro(svnupcmd)
            except Exception, e:
                return dict(retuncode=e)
            else:
                return dict(retuncode=retuncode)

        else:
            return dict(dirpath="别逗了!根本没有svn命令,请先安装subversion软件--.")
    else:
        return dict(dirpath="别逗了!目录不存在,你让我update什么--.")


myapp = SessionMiddleware(default_app(), session_opts)
run(app=myapp, host="0.0.0.0", port=8080, debug=True)
