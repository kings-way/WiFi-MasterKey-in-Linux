# -*- coding: utf-8 -*-
#!/usr/bin/env python
#author md5_salt
#this script may get password of the wifi nearby, run it directly, mac os only
#before run, make a soft link of airport
#sudo ln -s /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport /usr/sbin/airport

import md5
from Crypto.Cipher import AES
import requests
import random
import re
import commands

class wifi:
	aesKey = 'k%7Ve#8Ie!5Fb&8E'
	aesIV = 'y!0Oe#2Wj#6Pw!3V'
	aesMode = AES.MODE_CBC

	dhid = ''
	mac = ''
	ii = ''

	salt = ''#from server

	def __init__(self):
		self.RegisterNewDevice()

	def __sign(self, data, salt):
		request_str = ''
		for key in sorted(data):
			request_str += data[key]
		return md5.md5(request_str + salt).hexdigest().upper()

	def __decrypt(self, ciphertext):
		#[length][password][timestamp]
		decryptor = AES.new(self.aesKey, self.aesMode, IV=self.aesIV)
		return decryptor.decrypt(ciphertext.decode('hex')).strip()[3:-13]

	def RegisterNewDevice(self):
		salt = '1Hf%5Yh&7Og$1Wh!6Vr&7Rs!3Nj#1Aa$'
		data = {}
		data['appid'] = '0008'
		data['chanid'] = 'gw'
		data['ii'] = md5.md5(str(random.randint(1,10000))).hexdigest()
		data['imei'] = data['ii']
		data['lang'] = 'cn'
		data['mac'] = data['ii'][:12]#md5.md5(str(random.randint(1,10000))).hexdigest()[:12]
		data['manuf'] = 'Apple'
		data['method'] = 'getTouristSwitch'
		data['misc'] = 'Mac OS'
		data['model'] = '10.10.3'
		data['os'] = 'Mac OS'
		data['osver'] = '10.10.3'
		data['osvercd'] = '10.10.3'
		data['pid'] = 'initdev:commonswitch'
		data['scrl'] = '813'
		data['scrs'] = '1440'
		data['wkver'] = '324'
		data['st'] = 'm'
		data['v'] = '324'
		data['sign'] = self.__sign(data, salt)

		url = 'http://wifiapi02.51y5.net/wifiapi/fa.cmd'

		useragent = 'WiFiMasterKey/1.1.0 (Mac OS X Version 10.10.3 (Build 14D136))'
		headers = {'User-Agent': useragent}

		r = requests.post(url, data=data, headers=headers).json()

		if r['retCd'] == '0' and r['initdev']['retCd'] == '0':
			self.imei = data['imei']
			self.ii = data['ii']
			self.mac = data['mac']
			self.dhid = r['initdev']['dhid']
			self.salt = salt
			return True
		else:
			return False

	def query(self, ssid, bssid):
		data = {}
		data['appid'] = '0008'
		data['bssid'] = ','.join(bssid)
		data['chanid'] = 'gw'
		data['dhid'] = self.dhid
		data['ii'] = self.ii
		data['lang'] = 'cn'
		data['mac'] = self.mac
		data['method'] = 'getSecurityCheckSwitch'
		data['pid'] = 'qryapwithoutpwd:commonswitch'
		data['ssid'] = ','.join(ssid)
		data['st'] = 'm'
		data['uhid'] = 'a0000000000000000000000000000001'
		data['v'] = '324'
		data['sign'] = self.__sign(data, self.salt)

		url = 'http://wifiapi02.51y5.net/wifiapi/fa.cmd'

		useragent = 'WiFiMasterKey/1.1.0 (Mac OS X Version 10.10.3 (Build 14D136))'
		headers = {'User-Agent': useragent}

		r = requests.post(url, data=data, headers=headers).json()

		self.salt = r['retSn']

		if r['retCd'] == '-1111':
			print self.__request(ssid, bssid)#maybe some problem

		if r['retCd'] == '0':
			if r['qryapwithoutpwd']['retCd'] == '0':
				ret = '='*10 + '\n'
				for d in r['qryapwithoutpwd']['psws']:
					wifi = r['qryapwithoutpwd']['psws'][d]
					rsp = self.__request(wifi['ssid'], wifi['bssid'])
					if rsp['flag']:
						del rsp['flag']
						ret += '\n'.join([x + ' : ' + str(rsp[x]) for x in rsp])
						ret += '\n' + '='*10 + '\n'
				print ret
			else:
				print r['qryapwithoutpwd']['retMsg']
		else:
			print r['retMsg']


	def __request(self, ssid, bssid):
		data = {}
		data['appid'] = '0008'
		data['bssid'] = bssid
		data['chanid'] = 'gw'
		data['dhid'] = self.dhid
		data['ii'] = self.ii
		data['lang'] = 'cn'
		data['mac'] = self.mac
		data['method'] = 'getDeepSecChkSwitch'
		data['pid'] = 'qryapwd:commonswitch'
		data['ssid'] = ssid
		data['st'] = 'm'
		data['uhid'] = 'a0000000000000000000000000000001'
		data['v'] = '324'
		data['sign'] = self.__sign(data, self.salt)

		url = 'http://wifiapi02.51y5.net/wifiapi/fa.cmd'

		useragent = 'WiFiMasterKey/1.1.0 (Mac OS X Version 10.10.3 (Build 14D136))'
		headers = {'User-Agent': useragent}

		r = requests.post(url, data=data, headers=headers).json()

		self.salt = r['retSn']

		if r['retCd'] == '-1111':
			return self.request(ssid, bssid)#maybe some problem

		if r['retCd'] == '0':
			if r['qryapwd']['retCd'] == '0':
				ret = {}
				for d in r['qryapwd']['psws']:
					wifi = r['qryapwd']['psws'][d]
					ret['ssid'] = wifi['ssid']
					ret['bssid'] = wifi['bssid']
					if wifi['pwd']:
						ret['pwd'] = self.__decrypt(wifi['pwd'])
					if wifi['xUser']:
						ret['xUser'] = wifi['xUser']
						ret['xPwd'] = ['xPwd']
				ret['flag'] = True
				return ret
			else:
				return {'msg':r['qryapwd']['retMsg'], 'flag':False}
		else:
			return {'msg':r['retMsg'], 'flag':False}

	def request(self, ssid, bssid):
		wifi = self.__request(ssid, bssid)
		if wifi['flag']:
			del wifi['flag']
			ret = '='*10 + '\n'
			ret += '\n'.join([x + ' : ' + str(wifi[x]) for x in wifi])
			ret += '\n' + '='*10 + '\n'
			print ret
		else:
			print wifi['msg']
if __name__ == '__main__':
	pattern = r"\s*(.*)\s+(([0-9a-f]{2}:){5}[0-9a-f]{2})"
	status, output = commands.getstatusoutput('airport -s')
	ssid = []
	bssid = []
	for ss, bss, dummy in re.compile(pattern, re.M).findall(output):
		ssid.append(ss)
		bssid.append(bss)
	wifi().query(ssid, bssid)
