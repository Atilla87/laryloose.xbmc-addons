# -*- coding: utf-8 -*-

import re, cookielib, time, xbmcgui, xbmc, os, urllib2
from urllib2 import Request, URLError, urlopen as urlopen2
from urlparse import parse_qs
from urllib import quote, urlencode, unquote_plus, unquote
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException
from socket import gaierror, error
from t0mm0.common.net import Net
from jsunpacker import cJsUnpacker

COOKIEFILE = xbmc.translatePath( 'special://temp/dabdate_cookie.lwp' )

cj = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)
if os.path.isfile(COOKIEFILE):
    cj.load(COOKIEFILE)
    xbmc.log( "Cookie is loaded", xbmc.LOGINFO )
xbmc.log( "Cookie is set, " + COOKIEFILE, xbmc.LOGINFO )

hosterlist = [
	('youtube', '.*www\.youtube\.com'),
	('putlocker', '.*www\.putlocker\.com/(?:file|embed)/'),
	('sockshare', '.*www\.sockshare\.com/(?:file|embed)/'),
	('videoslasher', '.*www\.videoslasher\.com/embed/'),
	('faststream', '.*faststream\.in'),
	('flashx', '.*flashx\.tv'),
	('vk', '.*vk\.(me|com)/'),
	('streamcloud', '.*streamcloud\.eu'),
	('vidstream', '.*vidstream\.in'),
	('xvidstage', '.*xvidstage\.com'),
	('nowvideo', '.*nowvideo\.(?:eu|sx)'),
	('movshare', '.*movshare\.net'),
	('divxstage', '.*(?:embed\.divxstage\.eu|divxstage\.eu/video)'),
	('videoweed', '.*videoweed\.es'),
	('novamov', '.*novamov\.com'),
	('primeshare', '.*primeshare'),
	('videomega', '.*videomega\.tv'),
	('bitshare', '.*bitshare\.com'),
	('movreel', '.*movreel\.com'),
	('uploadc', '.*uploadc\.com'),
	('youwatch', '.*youwatch\.org'),
	('yandex', '.*yandex\.ru'),
	('K1no', '.*k1-city\.com'),
	('sharedsx', '.*shared\.sx'),
	('vivosx', '.*vivo\.sx'),
	('cloudyvideos', '.*cloudyvideos\.com'),
	('openload', '.*openload\.'),
	('vidx', '.*vidx\.to')]

class get_stream_link:

	def __init__(self):
		self.net = Net()
	
	def get_stream(self, link):
		hoster = self.get_hostername(link)
		if   hoster == 'putlocker': return self.streamPutlockerSockshare(link, 'putlocker')
		elif hoster == 'sockshare': return self.streamPutlockerSockshare(link, 'sockshare')
		elif hoster == 'youtube': return self.youtube(link)
		elif hoster == 'videoslasher': return self.videoslaher(link)
		elif hoster == 'faststream': return self.generic1(link, 'Faststream', 10, 0)
		elif hoster == 'flashx': return self.flashx(link)
		elif hoster == 'vk': return self.vk(link)
		elif hoster == 'streamcloud': return self.streamcloud(link)
		elif hoster == 'vidstream': return self.vidstream(link)
		elif hoster == 'xvidstage': return self.xvidstage(link)
		elif hoster == 'videoweed': return self.videoweed(link)
		elif hoster == 'nowvideo': return self.generic2(link)
		elif hoster == 'movshare': return self.generic2(link)
		elif hoster == 'divxstage': return self.generic2(link)
		elif hoster == 'novamov': return self.generic2(link)
		elif hoster == 'primeshare': return self.primeshare(link)
		elif hoster == 'videomega': return self.videomega(link)
		elif hoster == 'bitshare': return self.bitshare(link)
		elif hoster == 'movreel': return self.movreel(link)
		elif hoster == 'uploadc': return self.uploadc(link)
		elif hoster == 'youwatch': return self.youwatch(link)
		elif hoster == 'yandex': return self.generic1(link, 'Yandex', 0, 0)
		elif hoster == 'vidx': return self.generic1(link, 'ViDX', 10, 0)
		elif hoster == 'K1no': return link
		elif hoster == 'sharedsx': return self.generic1(link, 'Shared.sx', 0, 1)
		elif hoster == 'vivosx': return self.generic1(link, 'Vivo.sx', 0, 1)
		elif hoster == 'cloudyvideos': return self.generic1(link, 'CloudyVideos', 2, 2)
		elif hoster == 'openload': return self.openload(link)
		return 'Not Supported'

	def getUrl(self, url):
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0')
		req.add_header('Referer', url)
		response = urllib2.urlopen(req)
		data = response.read()
		response.close()
		return data
		
	def get_adfly_link(self, adflink):
		print 'resolving adfly url: \'%s\' using http://dead.comuv.com/bypasser/process.php' % (adflink)
		data = self.net.http_POST('http://dead.comuv.com/bypasser/process.php', {'url':adflink}, {'Referer':'http://dead.comuv.com/', 'X-Requested-With':'XMLHttpRequest'}).content
		link = re.findall('<a[^>]*href="([^"]*)"', data, re.S|re.I|re.DOTALL)
		if link: return link[0]
		else: return 'empty'

	def get_adfly_link_2(self, adflink):
		print 'resolving adfly url: \'%s\' using http://cyberflux.info/shortlink.php' % (adflink)
		data = self.net.http_POST('http://cyberflux.info/shortlink.php', {'urllist':adflink}, {'Referer':'http://cyberflux.info/shortlink.php'}).content
		link = re.findall(adflink + '[ ]*=[ ]*<a[^>]*href=([^>]*)>', data, re.S|re.I|re.DOTALL)
		if link: return link[0]
		else: return 'empty'

	def waitmsg(self, sec, msg):
		isec = int(sec)
		if isec > 0:
			dialog = xbmcgui.DialogProgress()
			dialog.create('Resolving', '%s Link.. Wait %s sec.' % (msg, sec))
			dialog.update(0)
			c = 100 / isec
			i = 1
			p = 0
			while i < isec+1:
				p += int(c)
				time.sleep(1)
				dialog.update(int(p))
				i += 1
			dialog.close()
	
	def get_hostername(self, link):
		if link:
			for (hoster, urlrex) in hosterlist:
				if re.match(urlrex, link, re.S|re.I): return hoster
		return 'Not Supported'

	def get_stream_url(self, sUnpacked):
		if not sUnpacked: return
		stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked, re.S|re.I|re.DOTALL)
		if not stream_url: stream_url = re.findall("file','(.*?)'", sUnpacked, re.S|re.I|re.DOTALL)
		if not stream_url: stream_url = re.findall('file:"(.*?)"', sUnpacked, re.S|re.I|re.DOTALL)
		if stream_url: return stream_url[0]
		
	def openload(self, url):
		print url
		html = self.getUrl(url)
		encarray = re.findall('(ﾟωﾟﾉ=.*?\(\'_\'\));', html, re.DOTALL|re.S|re.I)
		if not encarray: return 'Error: Openload encarray not found'
		for t in encarray: print self.decodeOpenLoad(t)
		for i in xrange(0, len(encarray)):
			idx = re.compile(r"welikekodi_ya_rly = Math.round([^;]+);", re.DOTALL | re.IGNORECASE).findall(self.decodeOpenLoad(encarray[i]))
			if idx:
				idx = eval("int" + idx[0])
				if len(encarray) <= idx+i: return 'Error: idx out or range'
				vid = self.decodeOpenLoad(encarray[idx+i])
				req = urllib2.Request(vid, None, {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'})
				res = urllib2.urlopen(req)
				return res.geturl()
		return 'Error: Openload Protection'

	def decodeOpenLoad(self, aastring):
		# decodeOpenLoad made by mortael, please leave this line for proper credit :)
		aastring = aastring.replace("(ﾟДﾟ)[ﾟεﾟ]+(oﾟｰﾟo)+ ((c^_^o)-(c^_^o))+ (-~0)+ (ﾟДﾟ) ['c']+ (-~-~1)+","")
		aastring = aastring.replace("((ﾟｰﾟ) + (ﾟｰﾟ) + (ﾟΘﾟ))", "9")
		aastring = aastring.replace("((ﾟｰﾟ) + (ﾟｰﾟ))","8")
		aastring = aastring.replace("((ﾟｰﾟ) + (o^_^o))","7")
		aastring = aastring.replace("((o^_^o) +(o^_^o))","6")
		aastring = aastring.replace("((ﾟｰﾟ) + (ﾟΘﾟ))","5")
		aastring = aastring.replace("(ﾟｰﾟ)","4")
		aastring = aastring.replace("((o^_^o) - (ﾟΘﾟ))","2")
		aastring = aastring.replace("(o^_^o)","3")
		aastring = aastring.replace("(ﾟΘﾟ)","1")
		aastring = aastring.replace("(+!+[])","1")
		aastring = aastring.replace("(c^_^o)","0")
		aastring = aastring.replace("(0+0)","0")
		aastring = aastring.replace("(ﾟДﾟ)[ﾟεﾟ]","\\")
		aastring = aastring.replace("(3 +3 +0)","6")
		aastring = aastring.replace("(3 - 1 +0)","2")
		aastring = aastring.replace("(!+[]+!+[])","2")
		aastring = aastring.replace("(-~-~2)","4")
		aastring = aastring.replace("(-~-~1)","3")
		aastring = aastring.replace("(-~0)","1")
		aastring = aastring.replace("(-~1)","2")
		aastring = aastring.replace("(-~3)","4")
		aastring = aastring.replace("(0-0)","0")

		decodestring = re.search(r"\\\+([^(]+)", aastring, re.DOTALL | re.IGNORECASE).group(1)
		decodestring = "\\+"+ decodestring
		decodestring = decodestring.replace("+","")
		decodestring = decodestring.replace(" ","")
		decodestring = self.decode_ol(decodestring)
		decodestring = decodestring.replace("\\/","/")

		if 'toString' in decodestring:
			base = re.compile(r"toString\(a\+(\d+)", re.DOTALL | re.IGNORECASE).findall(decodestring)[0]
			base = int(base)
			match = re.compile(r"(\(\d[^)]+\))", re.DOTALL | re.IGNORECASE).findall(decodestring)
			for repl in match:
				match1 = re.compile(r"(\d+),(\d+)", re.DOTALL | re.IGNORECASE).findall(repl)
				base2 = base + int(match1[0][0])
				repl2 = self.base10toN(int(match1[0][1]),base2)
				decodestring = decodestring.replace(repl,repl2)
			decodestring = decodestring.replace("+","")
			decodestring = decodestring.replace("\"","")
			videourl = re.search(r"(http[^\}]+)", decodestring, re.DOTALL | re.IGNORECASE).group(1)
			videourl = videourl.replace("https", "http")
			return videourl
		else:
			return decodestring
	
	def decode_ol(self, encoded):
		for octc in (c for c in re.findall(r'\\(\d{2,3})', encoded)):
			encoded = encoded.replace(r'\%s' % octc, chr(int(octc, 8)))
		return encoded.decode('utf8')

	def base10toN(self, num, n):
		num_rep = {
			10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f', 16: 'g', 17: 'h', 18: 'i',
			19: 'j', 20: 'k', 21: 'l', 22: 'm', 23: 'n', 24: 'o', 25: 'p', 26: 'q', 27: 'r',
			28: 's', 29: 't', 30: 'u', 31: 'v', 32: 'w', 33: 'x', 34: 'y', 35: 'z'
			}

		new_num_string = ''
		current = num
		while current != 0:
			remainder = current % n
			if 36 > remainder > 9:
				remainder_string = num_rep[remainder]
			elif remainder >= 36:
				remainder_string = '(' + str(remainder) + ')'
			else:
				remainder_string = str(remainder)
			new_num_string = remainder_string + new_num_string
			current = current / n
		return new_num_string
		
	def youtube(self, url):
		print url
		match = re.compile('youtube.com/embed/([^\?]+)', re.DOTALL).findall(url)
		if match:
			youtubeID = match[0]
			if xbmc.getCondVisibility("System.Platform.xbox") == True:
				video_url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
			else:
				video_url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
			return video_url

	def uploadc(self, url):
		data = self.net.http_GET(url).content
		ipcount_val = re.findall('<input type="hidden" name="ipcount_val".*?value="(.*?)">', data)
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		fname = re.findall('<input type="hidden" name="fname".*?alue="(.*?)">', data)	
		if id and fname and ipcount_val:
			info = {'ipcount_val' : ipcount_val[0], 'op' : 'download2', 'usr_login' : '', 'id' : id[0], 'fname' : fname[0], 'method_free' : 'Slow access'}
			data2 = self.net.http_POST(url, info).content
			stream_url = self.get_stream_url(data2)
			if not stream_url:
				get_packedjava = re.findall("(\(p,a,c,k,e,d.*?)</script>", data2, re.S|re.DOTALL)
				if get_packedjava:
					sUnpacked = cJsUnpacker().unpackByString(get_packedjava[0])
					stream_url = self.get_stream_url(sUnpacked)
			if stream_url: return stream_url
			else: return 'Error: Konnte Datei nicht extrahieren'

	def youwatch(self, url):
		i = 0
		while not url == '' and i <= 3:
			i = i + 1
			print url
			data = self.net.http_GET(url).content
			print data
			stream_url = re.findall('file:"([^"]*(?:mkv|mp4|avi|mov|flv|mpg|mpeg))"', data)
			if stream_url: return stream_url[0]
			match = re.search('<iframe[^>]*src="([^"]*)"', data, re.S|re.I|re.DOTALL)
			if match: 
				url = re.sub('^//', 'http://', match.group(1))

	def movreel(self, url):
		data = self.net.http_GET(url).content
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		fname = re.findall('<input type="hidden" name="fname".*?value="(.*?)">', data)
		if id and fname:
			info = {'op': 'download1', 'usr_login': '', 'id': id[0], 'fname': fname[0], 'referer': '', 'method_free': ' Kostenloser Download'}
			data2 = self.net.http_POST(url, info).content
			id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data2)
			rand = re.findall('<input type="hidden" name="rand".*?value="(.*?)">', data2)
			if id and rand:
				info2 = {'op': 'download2', 'usr_login': '', 'id': id[0], 'rand': rand[0], 'referer': '', 'method_free': ' Kostenloser Download'}
				data = self.net.http_POST(url, info2).content
				stream_url = re.findall("var file_link = '(.*?)'", data, re.S)
				if stream_url: return stream_url[0]
				else: return 'Error: Konnte Datei nicht extrahieren'

	def bitshare(self, url):
		data = self.net.http_GET(url).content
		if re.match('.*?(Ihr Traffic.*?Heute ist verbraucht|Your Traffic is used up for today)', data, re.S|re.I): return 'Error: Ihr heutiger Traffic ist aufgebraucht'
		elif re.match(".*?The file owner decided to limit file.*?access", data, re.S|re.I): return 'Error: Nutzer hat Dateizugriff limitiert'
		elif re.match(".*?Sorry aber sie.*?nicht mehr als 1 Dateien gleichzeitig herunterladen", data, re.S|re.I): return 'Error: Mehr als 1 Datei gleichzeitig ist nicht erlaubt'
		else:
			stream_url = re.findall("url: '(http://.*?.bitshare.com/stream/.*?.avi)'", data)
			if stream_url: return stream_url[0]
			else: return 'Error: Konnte Datei nicht extrahieren'

	def videomega(self, url):
		if not re.match('.*?iframe.php', url):
			id = url.split('ref=')
			if id: url = "http://videomega.tv/iframe.php?ref=%s" % id[1]
		data = self.net.http_GET(url).content
		unescape = re.findall('unescape."(.*?)"', data, re.S)
		if unescape:
			javadata = urllib2.unquote(unescape[0])
			if javadata:
				stream_url = re.findall('file: "(.*?)"', javadata, re.S)
				if stream_url: return stream_url[0]
				else: return 'Error: Konnte Datei nicht extrahieren'

	def primeshare(self, url):
		data = self.getUrl(url)
		hash = re.findall('<input type="hidden".*?name="hash".*?value="(.*?)"', data)
		if hash:
			info = {'hash': hash[0]}
			self.waitmsg(16, "Primeshare")
			data = self.net.http_POST(url, info).content
			stream_url = re.findall('url: \'(.*?)\'', data, re.S)
			if stream_url: return stream_url[2]
			else: return 'Error: Konnte Datei nicht extrahieren'

	def videoweed(self, url):
		data = self.net.http_GET(url).content
		r = re.search('flashvars.domain="(.+?)".*flashvars.file="(.+?)".*' + 'flashvars.filekey="(.+?)"', data, re.DOTALL)
		if r:
			domain, fileid, filekey = r.groups()
			api_call = ('%s/api/player.api.php?user=undefined&codes=1&file=%s' + '&pass=undefined&key=%s') % (domain, fileid, filekey)
			if api_call:
				data = self.net.http_GET(api_call).content
				rapi = re.search('url=(.+?)&title=', data)
				if rapi:
					stream_url = rapi.group(1)
					if stream_url: return stream_url
					else: return 'Error: Konnte Datei nicht extrahieren'

	def vk(self, url):
		data = self.net.http_GET(url).content
		vars = re.findall('<param[^>]*name="flashvars"[^>]*value="([^"]*)"', data, re.I|re.S|re.DOTALL)
		if vars:
			urls = re.findall('url([0-9]+)=([^&]*)&', vars[0], re.I|re.S|re.DOTALL)
			if urls:
				maxres = 0
				maxurl = ''
				for (res, url) in urls:
					if (int(res) > maxres):
						maxres = int(res)
						maxurl = url
				return maxurl

	def xvidstage(self, url):
		data = self.net.http_GET(url).content
		info = {}
		for i in re.finditer('<input.*?name="(.*?)".*?value="(.*?)">', data):
			info[i.group(1)] = i.group(2)
		data = self.net.http_POST(url, info).content
		get_packedjava = re.findall("(\(p,a,c,k,e,d.*?)</script>", data, re.S|re.DOTALL)
		if get_packedjava:
			sJavascript = get_packedjava[1]
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				if re.match('.*?type="video/divx', sUnpacked):
					stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
					if stream_url: return stream_url[0]
				elif re.match(".*?file", sUnpacked):
					stream_url = re.findall("file','(.*?)'", sUnpacked)
					if stream_url: return stream_url[0]
					else: return 'Error: Konnte Datei nicht extrahieren'

	def vidstream(self, url):
		data = self.net.http_GET(url).content
		if re.match('.*?maintenance mode', data, re.S): return 'Error: Server wegen Wartungsarbeiten ausser Betrieb'
		info = {}
		for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)">', data):
			info[i.group(1)] = i.group(2)
		if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
		print 'URL: '+ url, info
		data = self.net.http_POST(url, info).content
		if re.match('.*?not found', data, re.S|re.I): return 'Error: Datei nicht gefunden'
		stream_url = re.findall('file: "([^"]*)"', data)
		if stream_url: return stream_url[0]
		else: return 'Error: Konnte Datei nicht extrahieren'

	def streamcloud(self, url):
		data = self.net.http_GET(url).content
		info = {}
		print url
		if re.match('.*?No such file with this filename', data, re.S|re.I): return 'Error: Dateiname nicht bekannt'
		for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)">', data):
			info[i.group(1)] = i.group(2).replace('download1', 'download2')
		if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
		data = self.net.http_POST(url, info).content
		if re.match('.*?This video is encoding now', data, re.S): return 'Error: Das Video wird aktuell konvertiert'
		if re.match('.*?The file you were looking for could not be found', data, re.S): return 'Error: Die Datei existiert nicht'
		stream_url = re.findall('file: "(.*?)"', data)
		if stream_url: return stream_url[0]
		else: return 'Error: Konnte Datei nicht extrahieren'

	def videoslaher(self, url):
		url = url.replace('file','embed')
		info = {'foo': "vs", 'confirm': "Close Ad and Watch as Free User"}
		data = self.net.http_POST(url, info).content
		code = re.findall("code: '(.*?)'", data, re.S)
		hash = re.findall("hash: '(.*?)'", data, re.S)
		xml_link = re.findall("playlist: '(/playlist/.*?)'", data, re.S)
		if code and hash and xml_link:
			data = self.net.http_GET("http://www.videoslasher.com"+xml_link[0]).content
			stream_url = re.findall('<media:content url="(.*?)"', data)
			if stream_url:
				info = {'user': "0", 'hash': hash[0], 'code': code[0]}
				data = self.net.http_POST("http://www.videoslasher.com/service/player/on-start", info).content
				if 'ok' in data: return stream_url[1]
				else: return 'Error: konnte stream nicht bestaetigen'
			else: return 'Error: Stream-URL nicht gefunden'
		else: return 'Error: konnte Logindaten nicht extrahieren'

	def streamPutlockerSockshare(self, url, provider):
		data = self.getUrl(url.replace('/file/','/embed/'))
		if re.match('.*?File Does not Exist', data, re.S): return 'Error: Die Datei existiert nicht'
		elif re.match('.*?Encoding to enable streaming is in progresss', data, re.S): return "Error: Die Datei wird aktuell konvertiert"
		else:
			enter = re.findall('<input type="hidden" value="(.*?)" name="fuck_you">', data)
			values = {'fuck_you': enter[0], 'confirm': 'Close+Ad+and+Watch+as+Free+User'}
			user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
			headers = { 'User-Agent' : user_agent}
			cookiejar = cookielib.LWPCookieJar()
			cookiejar = urllib2.HTTPCookieProcessor(cookiejar)
			opener = urllib2.build_opener(cookiejar)
			urllib2.install_opener(opener)
			data = urlencode(values)
			req = urllib2.Request(url, data, headers)
			try: response = urllib2.urlopen(req)
			except: return 'Error: Error @ urllib2.Request()'
			else:
				link = response.read()
				if link:
					embed = re.findall("get_file.php.stream=(.*?)'\,", link, re.S)
					if embed:
						req = urllib2.Request('http://www.%s.com/get_file.php?stream=%s' %(provider, embed[0]))
						req.add_header('User-Agent', user_agent)
						try: response = urllib2.urlopen(req)
						except: return 'Error: Error @ urllib2.Request()'
						else:
							link = response.read()
							if link:
								stream_url = re.findall('<media:content url="(.*?)"', link, re.S)
								filename = stream_url[1].replace('&amp;','&')
								if filename: return filename
								else: return 'Error: Konnte Datei nicht extrahieren'

	def flashx(self, url):
		print 'flashx: ' + url
		resp = self.net.http_GET(url)
		data = resp.content								
		for frm in re.findall('<form[^>]*method="POST"[^>]*>(.*?)</form>', data, re.S|re.I):
			info = {}
			for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', frm): info[i.group(1)] = i.group(2)
			if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
			info['referer'] = ""
			self.waitmsg(int(5), "flashx")
			data = self.net.http_POST(resp.get_url(), info).content
			get_packedjava = re.findall("(\(p,a,c,k,e,d.*?)</script>", data, re.S|re.DOTALL)
			if get_packedjava:
				sJavascript = get_packedjava[0]
				sUnpacked = cJsUnpacker().unpackByString(sJavascript)
				if sUnpacked:
					stream_url = re.findall('file:"([^"]*(?:mkv|mp4|avi|mov|flv|mpg|mpeg))"', sUnpacked)
					if stream_url: return stream_url[0]
					else: return 'Error: Konnte Datei nicht extrahieren'
	
	def generic1(self, url, hostername, waitseconds, filerexid):
		print hostername + ': ' + url
		filerex = [ 'file:[ ]*[\'\"]([^\'\"]+(?:mkv|mp4|avi|mov|flv|mpg|mpeg))[\"\']', 
					'data-url=[\'\"]([^\'\"]+)[\"\']',
					'<a[^>]*href="([^"]*)">[^<]*<input[^>]*value="Download"[^>]*>' ]
		resp = self.net.http_GET(url)
		data = resp.content
		for frm in re.findall('<form[^>]*method="POST"[^>]*>(.*?)</form>', data, re.S|re.I):
			info = {}
			for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', frm): info[i.group(1)] = i.group(2)
			if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
			info['referer'] = resp.get_url()
			self.waitmsg(int(waitseconds), hostername)
			data = self.net.http_POST(resp.get_url(), info).content
			if re.match('.*Video is processing now', data, re.S|re.I): return "Error: Die Datei wird aktuell konvertiert" 
			print "search for: " + filerex[filerexid]
			stream_url = re.findall(filerex[filerexid], data, re.S|re.I)
			if stream_url: return stream_url[0]
			else: return 'Error: Konnte Datei nicht extrahieren'

	def generic2(self, url):
		url = re.sub('[ ]+', '', url)
		data = self.net.http_GET(url).content
		if re.match('.*?The file is being converted', data, re.S|re.I): return "Error: Das Video wird aktuell konvertiert"
		dom = re.findall('flashvars.domain="(.*?)"', data)
		file = re.findall('flashvars.file="(.*?)"', data)
		key = re.findall('flashvars.filekey="(.*?)"', data)
		if file and not key:
			varname = re.findall('flashvars.filekey=(.*?);', data)
			if varname: key = re.findall('var[ ]+%s="(.*?)"'%(varname[0]), data)
		if dom and file and key:
			url = "%s/api/player.api.php?file=%s&key=%s"%(dom[0], file[0], key[0])
			if re.match('.*?The video has failed to convert', data, re.S|re.I): return "Error: Das Video wurde nicht fehlerfrei konvertiert"
			data = self.net.http_GET(url).content
			rapi = re.search('url=([^&]+)&title=', data)
			if rapi:
				stream_url = rapi.group(1)
				if stream_url: return stream_url
				else: return 'Error: Konnte Datei nicht extrahieren'
		else: return "Error: Video wurde nicht gefunden"