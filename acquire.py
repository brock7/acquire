# -*- encoding=utf-8 -*-

import urllib2
import time
# from websocket import create_connection 
import websocket
import cookielib
import json
import ssl
import pdb
import sys

configs = open('config.txt').readlines()
if len(configs) < 2:
	print u'无效的配置'
	sys.exit(-1)
	
userId = configs[0].strip()
passwd = configs[1].strip()

user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0'
context = ssl._create_unverified_context()
site_cookie = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(site_cookie), 
	# urllib2.ProxyHandler({'https' : 'http://127.0.0.1:8080', 'http' : 'http://127.0.0.1:8080'}), 
	urllib2.HTTPSHandler(context=context))

def login():
	try:
		req = urllib2.Request('https://key.gf.com.cn/ws/pub/token/access_token/ownpwd?client_id=inspect&login_type=oa&password=%s&redirect_uri=%%2Fws%%2Fauth%%2Fuser%%2Flogin&response_type=token&user_id=%s' % (passwd, userId))
		req.add_header('User-agent', user_agent)
		response = opener.open(req, '')
		# print response.read()
		return response.getcode() == 200
	except urllib2.HTTPError, e:
		print e.code
		print e.reason
		print e.geturl()
		print e.read()
		return False	

def getSid():
	
	try:
		req = urllib2.Request("http://clickeggs.hippo.gf.com.cn/socket.io/?EIO=3&transport=polling&t=%d-0" % (time.time() * 1000))
		req.add_header('User-agent', user_agent)
		req.add_header('Referer', 'http://key.gf.com.cn/')
		req.add_header('Origin', 'http://key.gf.com.cn/')
		req.add_header('Connection', 'keep-alive')
		response = opener.open(req)
		html = response.read()
		html = html[5:]
		print html.decode('utf-8')
		jpkt = json.loads(html)
		# for k, v in jpkt.items():
		#	print k, v
	
		cookies = ''
		for item in site_cookie:
			cookies += '{0}={1}; '.format(item.name, item.value)
	
		sid = jpkt['sid']
		req = urllib2.Request("http://clickeggs.hippo.gf.com.cn/socket.io/?EIO=3&transport=polling&t=%d-2&sid=%s" % (time.time() * 1000, sid))
		req.add_header('User-agent', user_agent)
		req.add_header('Referer', 'http://key.gf.com.cn/')
		req.add_header('Origin', 'http://key.gf.com.cn/')
		req.add_header('Connection', 'keep-alive')
		response = opener.open(req)
		html = response.read()
		print html
		return sid, cookies
		
	except urllib2.HTTPError, e:
		print e.code
    	print e.reason
    	print e.geturl()
    	print e.read()
    	return '', ''

def acquire(sid, cookies):
	ws = websocket.WebSocket()

	#ws.connect("ws://clickeggs.hippo.gf.com.cn/socket.io/?EIO=3&transport=websocket&sid=%s" % (time.time() * 1000, jpkt['sid']), Cookie = cookies)
	ws.connect("ws://clickeggs.hippo.gf.com.cn/socket.io/?EIO=3&transport=websocket&sid=%s" % (sid), cookie = cookies, 
		header = ["User-Agent: " + user_agent, 'Pragma: no-cache'], origin = 'http://key.gf.com.com'
		#, http_proxy_host="127.0.0.1", http_proxy_port=8080
		)
	
	ws.send('2probe')
	print ws.recv()

	ws.send('5')
	# print ws.recv()

	ws.send('42["message",{"topic":"gmsv2.service.getuser","data":{"data":{"uid":"%s","version":"2.0"},"msgid":1}}]' % (userId))
	ws.send('42["message",{"topic":"gmsv2.service.getuser","data":{"data":{"uid":"%s","version":"2.0"},"msgid":2}}]' % (userId))
	# print ws.recv()

	ws.send('42["message",{"topic":"pns","data":{"data":{"event":"addRegId","regIds":["8d9e0f92393acb0a43e7f206ceeeec3220a2f145","5977"],"uuid":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0","seq":3}}}]')
	ws.send('42["message",{"topic":"pns","data":{"data":{"event":"addRegId","regIds":["8d9e0f92393acb0a43e7f206ceeeec3220a2f145","5977"],"uuid":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0","seq":4}}}]')
	while True:
		msg = ws.recv()
		if len(msg) == 0:
			break
			
		msg2 = msg[2:]
		try:
			jpkt = json.loads(msg2)
		except:
			print msg
			ws.send('2')
			print ws.recv()
			continue
		# print jpkt
		if jpkt[1]['topic'] == 'gmsv2.order.new':			
			data = jpkt[1]['data']['data']
			jpkt = json.loads(data)
			orderId = jpkt['data']['message'][0]['order_id']
			clientName = jpkt['data']['message'][0]['client_name']
			
			print orderId, clientName #, len(jpkt['data']['message'])
		
			if clientName == u'蚂蚁金服用户':
				print u'忽略蚂蚁金服用户'
				ws.send('2')
				print ws.recv()
				continue
		
			req = urllib2.Request("http://key.gf.com.cn/v2/order/%s/snatchrequest" % (orderId))
			req.add_header('User-agent', user_agent)
			response = opener.open(req, '')
			html = response.read()
			# jpkt = json.loads(html)
			print html.decode('utf-8')
			jpkt = json.loads(html)
			if jpkt['status'] == '200':
				break;
		ws.send('2')
		print ws.recv()

login()

while True:
	(sid, cookies) = getSid()
	if len(sid) == 0:
		continue
	acquire(sid, cookies)
	time.sleep(120)
	
