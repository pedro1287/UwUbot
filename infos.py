from pyobigram.utils import sizeof_fmt,nice_time
import datetime
import time
import os

def text_progres(index,max):
	try:
		if max<1:
			max += 1
		porcent = index / max
		porcent *= 100
		porcent = round(porcent)
		make_text = ''
		index_make = 1
		make_text += '├'
		while(index_make<20):
			if porcent >= index_make * 5: make_text+= '▣'
			else: make_text+= '▢'
			index_make+=1
		make_text += ''
		return make_text
	except Exception as ex:
			return ''

def porcent(index,max):
    porcent = index / max
    porcent *= 100
    porcent = round(porcent)
    return porcent

def createDownloading(filename,totalBits,currentBits,speed,time,tid=''):
    msg = '╭───⎔Downloading: '+str(porcent(currentBits,totalBits))+'%\n'
    msg += '├File name: '+filename+'\n'
    msg += text_progres(currentBits,totalBits)+'\n'
    msg += '├Done: '+sizeof_fmt(currentBits)+' of '+sizeof_fmt(totalBits)+'\n'
    msg += '├Speed: '+sizeof_fmt(speed)+'/s\n'
    msg += '├ETA: '+str(datetime.timedelta(seconds=int(time)))+'s\n'
    msg += '╰─ⓘ UwU XD 〄\n'

    if tid!='':
        msg+= '/cancel_' + tid
    return msg
def createUploading(filename,totalBits,currentBits,speed,time,originalname=''):
    msg = '╭───⎔Uploading: '+str(porcent(currentBits,totalBits))+'%\n'
    msg += '├File name: '+filename+'\n'
    msg += text_progres(currentBits,totalBits)+'\n'
    msg += '├Done: '+sizeof_fmt(currentBits)+' of '+sizeof_fmt(totalBits)+'\n'
    msg += '├Speed: '+sizeof_fmt(speed)+'/s\n'
    msg += '├ETA: '+str(datetime.timedelta(seconds=int(time)))+'s\n'
    msg += '╰─ⓘ UwU XD 〄\n'

    return msg
def createCompresing(filename,filesize,splitsize):
    msg = '╭───⎔Compressing...\n'+'│'+'\n'
    msg+= '├File name: ' + str(filename)+'\n'
    msg+= '├Total size: ' + str(sizeof_fmt(filesize))+'\n'
    msg+= '├Parts size: ' + str(sizeof_fmt(splitsize))+'\n'+'│'+'\n'
    msg+= '╰─⎔Amount of parts: ' + str(round(int(filesize/splitsize)+1,1))+'\n\n'

    return msg
def createFinishUploading(filename,filesize,split_size,current,count,findex):
    msg = '<b>╭───⎔Completed!</b>\n'+'<b>│</b>'+'\n'
    msg+= '<b>├File name:</b> ' + str(filename)+'\n'
    msg+= '<b>├Total size:</b> ' + str(sizeof_fmt(filesize))+'\n'
    msg+= '<b>├Parts size:</b> ' + str(sizeof_fmt(split_size))+'\n'
    msg+= '<b>├Uploaded parts:</b> ' + str(current) + '/' + str(count) +'\n'+'<b>│</b>'+'\n'
    msg+= '<b>╰─⎔Delete file:</b> ' + '/delete'
    return msg

def createFileMsg(filename,files):
    import urllib
    if len(files)>0:
        msg= '<b>Links</b>\n'
        for f in files:
            url = urllib.parse.unquote(f['directurl'],encoding='utf-8', errors='replace')
            #msg+= '<a href="'+f['url']+'">' + f['name'] + '</a>'
            msg+= "<a href='"+url+"'>"+f['name']+'</a>\n'
        return msg
    return ''

def createFilesMsg(evfiles):
    msg = 'Files ('+str(len(evfiles))+')\n\n'
    i = 0
    for f in evfiles:
            try:
                fextarray = str(f['files'][0]['name']).split('.')
                fext = ''
                if len(fextarray)>=3:
                    fext = '.'+fextarray[-2]
                else:
                    fext = '.'+fextarray[-1]
                fname = f['name'] + fext
                msg+= '/txt_'+ str(i) + ' /del_'+ str(i) + '\n' + fname +'\n\n'
                i+=1
            except:pass
    return msg
def createStat(username,userdata,isadmin):
    from pyobigram.utils import sizeof_fmt
    msg = '╭───⎔User Settings!\n'+'│'+'\n'
    msg+= '├User: ' + str(userdata['moodle_user'])+'\n'
    msg+= '├Password: ' + '********\n'
    msg+= '├Cloud URL: '+ str(userdata['moodle_host'])+'\n'
    if userdata['cloudtype'] == 'moodle':
        msg+= '├Cloud ID: ' + str(userdata['moodle_repo_id'])+'\n'
    msg+= '├Upload type: ' + str(userdata['uploadtype'])+'\n'
    if userdata['cloudtype'] == 'cloud':
        msg+= '├Directory: /' + str(userdata['dir'])+'\n'
    msg+= '├Zips size: ' + sizeof_fmt(userdata['zips']*1024*1024) + '\n│\n'
    proxy = 'X'
    if userdata['proxy'] !='':
       proxy = '✓'
    msg+= '├Proxy setted: ' + proxy + '\n'
    msg+= '├Calendar links: ' + 'X\n'
    msg+= '╰─ⓘ UwU XD 〄'
    return msg
    
