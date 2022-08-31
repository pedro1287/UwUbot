from cProfile import run
import pstats
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import tlmedia
import S5Crypto
import asyncio
import aiohttp
import moodlews
import moodle_client
from moodle_client import MoodleClient2
from yarl import URL
import re
from draft_to_calendar import send_calendar

def sign_url(token: str, url: URL):
    query: dict = dict(url.query)
    query["token"] = token
    path = "webservice" + url.path
    return url.with_path(path).with_query(query)

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'📤Uploading...⏳')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        host = user_info['moodle_host']
        if host != 'https://eva.uo.edu.cu/':
            proxy = ProxyCloud.parse(user_info['proxy'])
            if cloudtype == 'moodle':
                client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
                loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    tokenize = False
                    if user_info['tokenize']!=0:
                       tokenize = True
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                          elif user_info['uploadtype'] == 'draft':
                                fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          elif user_info['uploadtype'] == 'perfil':
                                fileid,resp = client.upload_file_perfil(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          elif user_info['uploadtype'] == 'blog':
                                fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          elif user_info['uploadtype'] == 'calendar':
                                fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                                draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return draftlist
            else:
                if host != 'https://mrrr/' or 'https://rrr/':
                    bot.editMessageText(message,'Retrying♻️...')
                    host = user_info['moodle_host']
                    user = user_info['moodle_user']
                    passw = user_info['moodle_password']
                    repoid = user_info['moodle_repo_id']
                    token = moodlews.get_webservice_token(host,user,passw,proxy=proxy)
                    print('ya tomo aki')
                    for f in files:
                        data = asyncio.run(moodlews.webservice_upload_file(host,token,file,progressfunc=uploadFile,proxy=proxy,args=(bot,message,filename,thread)))
                        print(data)
                        while not moodlews.store_exist(file):pass
                        data = moodlews.get_store(file)
                        if data[0]:
                            urls = moodlews.make_draft_urls(data[0])
                            draftlist.append({'file':file,'url':urls[0]})
                            return draftlist
                    else:
                        err = data[1]
                        bot.editMessageText(message,'❗Error.',err)
                else:
                    print('no chilvio el otro v:')
                    cli = MoodleClient2(host,user,passw,repoid,proxy)
                    for file in files:
                        data = asyncio.run(cli.LoginUpload(file, uploadFile, (bot, message, filename, thread)))
                        while cli.status is None: pass
                        data = cli.get_store(file)
                        if data:
                            if 'error' in data:
                                err = data['error']
                                bot.editMessageText(message,'❗Error.',err)
                            else:
                                draftlist.append({'file': file, 'url': data['url']})
                                return draftlist
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'🚀Uploading please wait.')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
    except Exception as ex:
        bot.editMessageText(message,f'❗Error {str(ex)}.')


def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'📄Creating TXT...⏳')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype'] == 'calendar' or getUser['uploadtype'] == 'perfil':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
        try:

            import urllib

            user_info = jdb.get_user(update.message.sender.username)
            cloudtype = user_info['cloudtype']
            proxy = ProxyCloud.parse(user_info['proxy'])
            if cloudtype == 'moodle':
                client = MoodleClient(user_info['moodle_user'],
                                    user_info['moodle_password'],
                                    user_info['moodle_host'],
                                    user_info['moodle_repo_id'],
                                    proxy=proxy)
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            if getUser['uploadtype'] == 'calendario':
                nuevo = []
                #if len(files)>0:
                    #for f in files:
                        #url = urllib.parse.unquote(f['directurl'],encoding='utf-8', errors='replace')
                        #nuevo.append(str(url))
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    nuevo.append(f['directurl']+separator)
                    fi += 1
                urls = asyncio.run(send_calendar(host,user,passw,nuevo))
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    client.logout()
                nuevito = []
                for url in urls:
                    url_signed = (str(sign_url(modif, URL(url))))
                    nuevito.append(url_signed)
                loco = '\n'.join(map(str, nuevito))
                fname = str(txtname)
                with open(fname, "w") as f:
                    f.write(str(loco))
                #fname = str(randint(100000000, 9999999999)) + ".txt"
                bot.sendMessage(message.chat.id,'✔Calendar direct Links!')
                bot.sendFile(update.message.chat.id,fname)
            else:
                return
        except:
            bot.sendMessage(message.chat.id,'❗Could not move to calendar.')
    else:
        bot.editMessageText(message,'❗Cloud error, crash.')


def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('tl_admin_user')

        #set in debug
        tl_admin_user = 'David_7amayo'

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or user_info:  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            mensaje = "🚫No tiene acceso.\n🧑‍💻Contacta a: @username\n"
            intento_msg = "❗El usuario @"+username+ " está solicitando permiso para usar el bot."
            bot.sendMessage(update.message.chat.id,mensaje)
            bot.sendMessage(1234567890,intento_msg)
            return

        msgText = ''
        try: msgText = update.message.text
        except:pass

        # comandos de admin
        if '/add' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '✔ @'+user+' has being added to the bot!'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'❗Command error /add username.')
            else:
                bot.sendMessage(update.message.chat.id,'❗You do not have administrator permissions.')
            return
        if '/admin' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_admin(user)
                    jdb.save()
                    msg = '✔Now @'+user+' is a bot administrator too!'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'❗Command error /admin username.')
            else:
                bot.sendMessage(update.message.chat.id,'❗You do not have administrator permissions.')
            return

        if '/preview' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user_evea_preview(user)
                    jdb.save()
                    msg = '✔The user @'+user+' now is in test mode.'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'❗Command error /preview username.')
            else:
                bot.sendMessage(update.message.chat.id,'❗You do not have administrator permissions.')
            return 
        if '/ban' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'❗You can not ban yourself.')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '𝚃𝚑𝚎 𝚞𝚜𝚎𝚛 @'+user+' 𝚑𝚊𝚜 𝚋𝚎𝚒𝚗𝚐 𝚋𝚊𝚗𝚗𝚎𝚍 𝚏𝚛𝚘𝚖 𝚝𝚑𝚎 𝚋𝚘𝚝!'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❗Command error /ban username.')
            else:
                bot.sendMessage(update.message.chat.id,'❗You do not have administrator permissions.')
            return
        if '/db' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                database = open('database.jdb','r')
                bot.sendMessage(update.message.chat.id,database.read())
                database.close()
            else:
                bot.sendMessage(update.message.chat.id,'❗You do not have administrator permissions.')
            return
        if '/useradm' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                message = bot.sendMessage(update.message.chat.id,'✅')
                message = bot.sendMessage(update.message.chat.id,'✔You are bot administrator, so you have total control over itself.')
            else:
                message = bot.sendMessage(update.message.chat.id,'❌')
                message = bot.sendMessage(update.message.chat.id,'❗You are just an user, for now you have limitated control.')
            return
        # end

        # comandos de usuario
        if '/help' in msgText:
            message = bot.sendMessage(update.message.chat.id,'𝚄𝚜𝚎𝚛 𝚐𝚞𝚒𝚍𝚎:')
            help = open('help.txt','r')
            bot.sendMessage(update.message.chat.id,help.read())
            help.close()
            return
        if '/moodles' in msgText:
            message = bot.sendMessage(update.message.chat.id,'𝙿𝚛𝚎𝚌𝚘𝚗𝚏𝚒𝚐𝚞𝚛𝚎𝚍 𝙼𝚘𝚘𝚍𝚕𝚎𝚜:')
            moodles = open('moodles.txt','r')
            bot.sendMessage(update.message.chat.id,moodles.read())
            moodles.close()
            return
        if '/xdlink' in msgText:

            try: 
                urls = str(msgText).split(' ')[1]
                channelid = getUser['channelid']
                xdlinkdd = xdlink.parse(urls, username)
                msg = f'**Aquí está su link encriptado en xdlink:** `{xdlinkdd}`'
                msgP = f'**Aquí está su link encriptado en xdlink protegido:** `{xdlinkdd}`'
                if channelid == 0:
                    bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msg)
                else: 
                    bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msgP)
            except:
                msg = f'》*El comando debe ir acompañado de un link moodle*'
                bot.sendMessage(chat_id = chatid, parse_mode = 'Markdown', text = msg)
            return

        if '/xdon' in msgText:
            getUser = user_info
            if getUser:
                getreturnUser['xdlink'] = 1
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
            return
            
        if '/xdoff' in msgText:
            getUser = user_info
            if getUser:
                getUser['xdlink'] = 0
                jdb.save_data_user(username,getUser)
                jdb.save()
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
            return


        if '/version' in msgText:
            message = bot.sendMessage(update.message.chat.id,'📦 Versión 9.7.5F Release (2022/30/08)')
            version = open('version.txt','r')
            bot.sendMessage(update.message.chat.id,información.read())
            información.close()
            return
        if '/cmds' in msgText:
            message = bot.sendMessage(update.message.chat.id,'🙂𝙵𝚘𝚛 𝚊𝚍𝚍 𝚝𝚑𝚒𝚜 𝚌𝚘𝚖𝚖𝚊𝚗𝚍𝚜 𝚝𝚘 𝚝𝚑𝚎 𝚚𝚞𝚒𝚌𝚔 𝚊𝚌𝚌𝚎𝚜𝚜 𝚖𝚎𝚗𝚞 𝚢𝚘𝚞 𝚖𝚞𝚜𝚝 𝚜𝚎𝚗𝚍 𝚝𝚑𝚎 𝚌𝚘𝚖𝚖𝚊𝚗𝚍 /setcommands 𝚝𝚘 @BotFather 𝚊𝚗𝚍 𝚝𝚑𝚎𝚗 𝚜𝚎𝚕𝚎𝚌𝚝 𝚢𝚘𝚞𝚛 𝚋𝚘𝚝, 𝚊𝚏𝚝𝚎𝚛 𝚘𝚗𝚕𝚢 𝚛𝚎𝚖𝚊𝚒𝚗𝚐𝚜 𝚛𝚎𝚜𝚎𝚗𝚍 𝚝𝚑𝚎 𝚖𝚎𝚜𝚜𝚊𝚐𝚎 𝚠𝚒𝚝𝚑 𝚝𝚑𝚎 𝚗𝚎𝚡𝚝 𝚌𝚘𝚖𝚖𝚊𝚗𝚍𝚜 𝚊𝚗𝚍... 𝚍𝚘𝚗𝚎😁.')
            commands = open('commands.txt','r')
            bot.sendMessage(update.message.chat.id,commands.read())
            commands.close()
            return
        if '/myuser' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '📚Perfect now the zips will be of '+ sizeof_fmt(size*1024*1024)+' the parts.'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'❗Command error /zips zips_size.')    
                return
        if '/gen' in msgText:
            pass444
        if '/acc' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❗Command error /acc user,password.')
            return

        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❗Command error /host cloud_url.')
            return
        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❗Command error /repo moodle_repo_id.')
            return
        if '/uptype' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❗Command error /uptype (evidence, draft, perfil, blog, calendar).')
            return


        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    msg = '✔Perfect, proxy equipped successfuly.'
                    bot.sendMessage(update.message.chat.id,msg)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'❗Error equipping proxy.')
            return
        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'🔒Proxy encrypted:\n{proxy}')
            return
        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'🔓Proxy decrypted:\n{proxy_de}')
            return
        if '/off_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['proxy'] = ''
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    msg = '✔Alrigth, proxy unequipped successfuly.\n'
                    bot.sendMessage(update.message.chat.id,msg)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'❗Error encrypting proxy.')
            return
                    
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'✔Task cancelled.')
            except Exception as ex:
                print(str(ex))
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'Analizyng⏳...')

        thread.store('msg',message)

        if '/start' in msgText:
            start_msg = '╭───⎔Hello! ' + str(username)+'\n│\n'
            start_msg+= '├Con este bot podrás descargar archivos gratis por datos móviles.\n│\n'
            start_msg+= '├Usa /version para conocer la versión actual del bot.\n'
            start_msg+= '╰─ⓘ UwU XD 〄\n'
            bot.editMessageText(message,start_msg)
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:

                List = client.getEvidences()
                List1=List[:45]
                total=len(List)
                List2=List[46:]
                info1 = f'<b>Archivos: {str(total)}</b>\n\n'
                info = f'<b>Archivos: {str(total)}</b>\n\n'
                
                i = 0
                for item in List1:
                    info += '<b>/del_'+str(i)+'</b>   /txt_'+str(i)+'\n'
                    #info += '<b>'+item['name']+':</b>\n'
                    for file in item['files']:                  
                        info += '<a href="'+file['directurl']+'">\t'+file['name']+'</a>\n'
                    info+='\n'
                    i+=1
                    bot.editMessageText(message, f'{info}',parse_mode="html")
                
                if len(List2)>0:
                    bot.sendMessage(update.message.chat.id,'⏳Conecting with the list number 2...')
                    for item in List2:
                        
                        info1 += '<b>/del_'+str(i)+'</b>   /txt_'+str(i)+'\n'
                        #info1 += '<b>'+item['name']+':</b>\n'
                        for file in item['files']:                  
                            info1 += '<a href="'+file['url']+'">\t'+file['name']+'</a>\n'
                        info1+='\n'
                        i+=1
                        bot.editMessageText(message, f'{info1}',parse_mode="html")
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'TXT here📃')
             else:
                bot.editMessageText(message,'❌')
                message = bot.sendMessage(update.message.chat.id,'❗Error and possible causes:\n1-Check your account.\n2-Server disabled: '+client.path)
             pass
        elif '/token' in msgText:
            message2 = bot.editMessageText(message,'🤖Getting token, please wait...')

            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                      user_info['moodle_password'],
                                      user_info['moodle_host'],
                                      user_info['moodle_repo_id'],proxy=proxy)
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    bot.editMessageText(message2,'🤖Your token is: '+modif)
                    client.logout()
                else:
                    bot.editMessageText(message2,'❗The moodle '+client.path+' does not have token.')
            except Exception as ex:
                bot.editMessageText(message2,'❗The moodle '+client.path+' does not have token or check out your account.')       
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'🗑️File deleted.')
            else:
                bot.editMessageText(message,'❌')
                message = bot.sendMessage(update.message.chat.id,'❗Error and possible causes:\n1-Check your account.\n2-Server disabled: '+client.path)
        elif '/delall' in msgText and user_info['cloudtype']=='moodle':
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfiles = client.getEvidences()
                for item in evfiles:
                    client.deleteEvidence(item)
                client.logout()
                bot.editMessageText(message,'🗑️Files deleted.')
            else:
                bot.editMessageText(message,'❌')
                message = bot.sendMessage(update.message.chat.id,'❗Error and possible causes:\n1-Check your account.\n2-Server disabled: '+client.path)
        elif '/delete' in msgText:
            enlace = msgText.split('/delete')[-1]
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged= client.login()
            if loged:
                #update.message.chat.id
                deleted = client.delete(enlace)

                bot.sendMessage(update.message.chat.id, "🗑File deleted successfully")


        elif '/uclv' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://moodle.uclv.edu.cu/"
            getUser['uploadtype'] =  "calendar"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 380
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Uclv configuration loaded!")
        elif '/evea' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://evea.uh.cu/"
            getUser['uploadtype'] =  "calendar"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 238
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Evea configuration loaded.")
        elif '/ucf' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://cursos.ucf.edu.cu/"
            getUser['uploadtype'] =  "draft"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 20
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Ucf configuration loaded.")
        elif '/eva' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://eva.uo.edu.cu/"
            getUser['uploadtype'] =  "draft"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 95
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Eva configuration loaded.")
        elif '/cursos' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://cursos.uo.edu.cu/"
            getUser['uploadtype'] =  "calendar"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 95
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Cursos configuration loaded.")
        elif '/eduvirtual' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://eduvirtual.uho.edu.cu/"
            getUser['uploadtype'] =  "blog"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 3
            getUser['zips'] = 8
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Eduvirtual configuration loaded.")
        elif '/gtmsld' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://aulauvs.gtm.sld.cu/"
            getUser['uploadtype'] =  "calendar"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 7
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Gtm sld configuration loaded.")
        elif '/hlgsld' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://aulavirtual.hlg.sld.cu/"
            getUser['uploadtype'] =  "calendar"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 5
            getUser['zips'] = 10
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Hlg sld configuration loaded.")
        elif '/cmwsld' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://uvs.ucm.cmw.sld.cu/"
            getUser['uploadtype'] =  "calendar"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 5
            getUser['zips'] = 200
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Cmw sld configuration loaded.")
        elif '/prisld' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://avucm.pri.sld.cu/"
            getUser['uploadtype'] =  "draft"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 5
            getUser['zips'] = 20
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"☑Pri sld configuration loaded.")
        elif 'http' in msgText:
            url = msgText
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            #if update:
            #    api_id = os.environ.get('api_id')
            #    api_hash = os.environ.get('api_hash')
            #    bot_token = os.environ.get('bot_token')
            #    
                # set in debug
            #    api_id = 7386053
            #    api_hash = '78d1c032f3aa546ff5176d9ff0e7f341'
            #    bot_token = '5124841893:AAH30p6ljtIzi2oPlaZwBmCfWQ1KelC6KUg'

            #    chat_id = int(update.message.chat.id)
            #    message_id = int(update.message.message_id)
            #    import asyncio
            #    asyncio.run(tlmedia.download_media(api_id,api_hash,bot_token,chat_id,message_id))
            #    return
            bot.editMessageText(message,'❗Error analizyng.')
    except Exception as ex:
           print(str(ex))
  

def main():
    #bot_token = ''
    

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()
    asyncio.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
