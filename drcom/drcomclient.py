#!/usr/bin/env python
# -*- coding: utf-8 -*-
##
## drcom-client PUM v1.0, Python User Mode
##
##         drcomclient.py
##
## Copyright (c) 2009, drcom-client Team
## Author:		Henry Huang <henry.s.huang@gmail.com>
##				Longshow <longshow@yeah.net>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public
## License as published by the Free Software Foundation; either
## version 2.1 of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
#
## You should have received a copy of the GNU General Public
## License along with this program; if not, write to the
## Free Software Foundation, Inc., 59 Temple Place - Suite 330,
## Boston, MA 02111-1307, USA.

## check OS/Python Version
import os, sys
py_version = sys.version_info[1]
kernel_version = os.uname()[2]

## import modules needed
try:
	import gtk, pygtk
except:
	print "Please install python-gtk2 first before running drcom-client."
	sys.exit(0)
pygtk.require('2.0')
try:
	import pynotify
except:
	print "Please install python-notify first before running drcom-client."
	sys.exit(0)
import time, atexit
import socket, fcntl, struct
if py_version == 6:
	import hashlib
else:
	import md5
import re, binascii
from operator import xor
import locale, gettext
import thread, Queue
try:
	import gnome.ui
except:
	pass

## global variables
conf_name = 'drcom.conf'
addr_name = 'server_ip'
conf_path = '/home/' + os.environ['USER'] + '/.drcom'
sound_path = '/usr/share/drcom/resource/drcom.wav'
icon_path = '/usr/share/drcom/resource/drcom.png'
license_path ='/usr/share/drcom/resource/COPYING'
lang_path = '/usr/share/drcom/resource/po/'
type_path = os.path.join(conf_path, 'drcom_type')
mod_path = '/lib/modules/'+kernel_version+'/extra/drcom.ko'
pid_file = 'drcom.pid'
dataQueue = Queue.Queue()
sys.path.append(conf_path)

## Debug Option -- False, True, Local
Debug = 'False'
if Debug == 'Local':
	IP_ADDR = '127.0.0.1'
	PORT = 8080
else:
	IP_ADDR = '202.1.1.1'
	PORT = 61440

## I18N
APP = "drcom"
local_path = os.path.realpath(os.path.dirname(lang_path))
langs = []
lc, encoding = locale.getdefaultlocale()
if (lc):
	langs = [lc]

language = os.environ.get('LANG', None)
if (language):
	langs += language.split(":")
result = gettext.bindtextdomain(APP, local_path)
gettext.textdomain(APP)
lang = gettext.translation(APP, local_path, languages=langs, fallback = True)
_ = lang.gettext

#class drcom_client():
class drcom_client:
	'''
		This is the main class for Graphical User Interface and Dr.COM Protocol Implementation 
	'''
	## -- build-in functions
	def hex_xor(self,xor_oper1,xor_oper2,oper_len):
		'''
			HEX-based XOR Calculation
		'''
		xor_result = ''
		for i in range(0,oper_len):
			temp = chr(xor(ord(xor_oper1[i]),ord(xor_oper2[i])))
			xor_result = xor_result + temp
		return xor_result

	def show_hex(self,hex_oper):
		'''
			Hexdecimal Expression
		'''
		for i in range(0,len(hex_oper)):
			print hex(ord(hex_oper[i])),
		print '\n'

	def show_dec(self,dec_oper):
		'''
			Hexdecimal -> Decimal 
		'''
		dec_result = ''
		for i in range(0,len(dec_oper)):
			dec_hex = hex(ord(dec_oper[i]))[2:]
			dec_result = dec_result + '0'*(2-len(dec_hex)) + dec_hex
		return str(int(dec_result,16))

	def md5_key(self,md5_content):
		'''
			MD5 Calculation
		'''
		if py_version == 6:
			md5_temp = hashlib.md5()
		else:
			md5_temp = md5.new()
		md5_temp.update(md5_content)
		return md5_temp.digest()

	def show_usage(self, time_usage, vol_usage, cash_usage):
		'''
			Adjust the expression of Usage
		'''
		self.info=_('Used ') + self.show_dec(time_usage) + _(' Min, ') +\
					self.show_dec(vol_usage) + _(' KB')	
		if cash_usage == '\xff\xff\xff\xff':
			return True

		self.info += '\n'
		if len(str(self.show_dec(cash_usage)))==4:
			self.info += _('Balance') + self.show_dec(cash_usage)[0:2] + '.' +\
						self.show_dec(cash_usage)[2:4] + _(' yuan.')
		if len(str(self.show_dec(cash_usage)))==3:
			self.info += _('Balance') + self.show_dec(cash_usage)[0:1] + '.' +\
						self.show_dec(cash_usage)[1:3] + _(' yuan.')
		if len(str(self.show_dec(cash_usage)))==2:
			self.info += _('Balance')+'0'+'.'+self.show_dec(cash_usage)[0:2] +\
						_(' yuan.')
		if len(str(self.show_dec(cash_usage)))==1:
			self.info += _('Balance')+'0'+'.'+'0'+self.show_dec(cash_usage)+\
						_(' yuan.')
	## --

##--------------------------------
## Dr.COM Protocol Implementation
##--------------------------------

	def init_conf(self):
		'''
			Initialize all parameters used in Class drcom-client()
		'''
		## Exception Info
		self.exception_id = {
			'00':_("Unknown errors"),
			'01':_("No active network card"),
			'02':_("Can not get your ip address"),
			'03':_("Can not get your MAC address"),
			'04':_("Can not get your DNS address"),
			'05':_("Fail to bind your port"),
			'06':_("Can not get your server ip address"),
			'07':_("Can not set up a socket"),
			'10':_("You have already LOGIN"),
			'11':_("You should LOGIN first"),
			'20':_("Connection lost when login[request]"),
			'21':_("Connection lost when login[response]"),
			'22':_("Connection lost when keep_alive[request]"),
			'23':_("Connection lost when keep_alive[response]"),
			'24':_("Connection lost when logout[request]"),
			'25':_("Connection lost when logout[response]"),
			'26':_("Connection lost when changing password[request]"),
			'27':_("Connection lost when changing password[response]"),
			'30':_("Incorrect account name or password"),
			'31':_("Login successful!"),
			'32':_("Logout successful!"),
			'33':_("No money left in your account!"),
			'34':_("Account is working now!"),
			'35':_("Logout failed!"),
			'40':_("Password validation not the same"),
			'41':_("New password successfully"),
			'42':_("Incorrect old password"),
			'43':_("Please logout first"),
			'50':_("Fail to start No.38 timer"),
			'51':_("Fail to stop No.38 timer"),
			'52':_("Fail to start No.40 timer"),
			'53':_("Fail to stop No.40 timer"),
			'54':_("Fail to start auth module,\nRUN \'sudo modprobe drcom\'"),
			'55':_("Fail to stop auth module"),
			## FIXME: kdrcom is not a good name:(
			'56':_("Cannot find drcom module,\nRUN \'sudo drcom start\'"),
			'60':_("Unknown type of keep_alive packet"),
			'61':_("Update your client"),
		}

		## basic network parameters
		self.BUFFER = 1024
		self.server_brand = 'Drco'
		self.ifname = self.get_ifname()
		self.md5_tail = '\x14\x00\x07\x0b'
		self.host_ip = self.get_ip_addr()
		self.host_ip_dec = socket.inet_ntoa(self.host_ip)
		self.mac_addr = self.get_mac_addr()

		## Packet ID
		self.host_packet_id = {
			'_login_request_'   :'\x01\x10',
			'_login_auth_'      :'\x03\x01',
			'_logout_request_'  :'\x01\x0e',
			'_logout_auth_'     :'\x06\x01',
			'_passwd_request_'  :'\x01\x0d',
			'_new_passwd_'      :'\x09\x01',
			'_alive_40_client_' :'\x07',
			'_alive_38_client_' :'\xff',
			'_alive_4_client_'  :'\xfe',
			}
		self.server_packet_id = {
			'\x02\x10'    :'_login_response_',
			'\x02\x0e'    :'_logout_response_',
			'\x02\x0d'    :'_passwd_response_',
			'\x04\x00'    :'_success_',
			'\x05\x00'    :'_failure_',
			'\x07'        :'_alive_40_server_',
			'\x07\x01\x10':'_alive_38_server_',
			'\x4d\x26'    :'_alive_4_server_',
			'\x4d\x38'    :'_Serv_Info_',
			'\x4d\x3a'    :'_Notice_',
			}

		## parameters used in keep_alive
		self.alive_account0 = 0x1a
		self.alive_account1 = 0x2e
		self.server_ack_40 = '\x12\x56\xd3\x03'

		## local address array
		self.local_addr = []
		self.local_mask = []

		self.timer_38 = 200
		self.timer_40 = 160
		self.module_auth = 'non-AUTH'

	def kernel_module_check(self):
		'''
			Check whether the kernel module drcom.ko exists
		'''
		flag = os.path.exists(type_path)
		if flag == True:
			fd = file(type_path, 'r')
			drcom_type = fd.read()
			fd.close()
			if drcom_type == 'AUTH':			
				flag = os.path.exists(mod_path)
				if flag == True:
					return True
				else:
					err_num = '56' 
					self.exception(err_num)
					self.quit_common()
			else:
				## fake True!
				return True
		else:
			flag = os.path.exists(mod_path)
			if flag == True:
				return True
			else:
				err_num = '56'
				self.exception(err_num)
				self.quit_common()

	def get_ifname(self):
		'''
			Get the active Network Interface Name 
		'''
		## List all network interfaces
		ifname_space = os.popen("/sbin/ifconfig -s| awk '{print $1}'").read()
		ifname_start = ifname_space.find('\n')
		ifname_name = []
		while(ifname_start != -1):
			ifname_end = ifname_space.find('\n',ifname_start+1)
			if ifname_end == -1:
				break
			ifname = ifname_space[ifname_start+1:ifname_end]
			ifname_name.append(ifname)
			ifname_start = ifname_end

		## Choose one active network interface automatically
		ifname_status = os.popen("/sbin/ifconfig | awk '{print $1,$3}'").read()
		for i in range(0,len(ifname_name)-1):
## FIXME: will it ommit the last ifname?
#		for i in range(0, len(ifname_name)):
			ifname_start = ifname_status.find(ifname_name[i])
			ifname_end = ifname_status.find(ifname_name[i+1])
#			if i == len(ifname_name)-1:
#				ifname_end = len(ifname_status)
#			else:
#				ifname_end = ifname_status.find(ifname_name[i+1])
			ifname_region = ifname_status[ifname_start:ifname_end]
			ifname_index = ifname_region.find('RUNNING')
			if ifname_index != -1 and 'lo' not in ifname_name[i]:
				return ifname_name[i]

		err_num = '01'
		self.exception(err_num)
		self.quit_common()

	def get_ip_addr(self):
		'''
			Get host IP address
		'''
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			ip_addr = fcntl.ioctl(s.fileno(),0x8915,\
					struct.pack('256s', self.ifname[:15]))[20:24]
		except:
			err_num = '02'
			self.exception(err_num)
			self.quit_common()

		return ip_addr


	def get_mac_addr(self):
		'''
			Get host MAC address
		'''
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			mac_addr = fcntl.ioctl(s.fileno(), 0x8927,\
					struct.pack('256s', self.ifname[:15]))[18:24]
		except:
			err_num = '03'
			self.exception(err_num)
			self.quit_common()
		
		return mac_addr

	def get_dns_addr(self):
		'''
			Get host DNS address
		'''
		try :
			fp = open('/etc/resolv.conf','r')
			content = fp.read()
			fp.close()
			dns = re.findall(r'^nameserver (.*)',content,re.M)

			if len(dns)>1:
				dnsp,dnss = dns[:2]
				dnsp,dnss = socket.inet_aton(dnsp),socket.inet_aton(dnss)
			else:
				## Only one DNS here
				dnsp = socket.inet_aton(dns[0])
				dnss = '\x00\x00\x00\x00'
		except:
			err_num = '04'
			self.exception(err_num)
			self.quit_common()

		return dnsp,dnss

	def read_conf(self):
		'''
			Fetch the password from ~/.drcom/drcom.conf or create a Blank file.
		'''
		## check whether DIRECTORY "~/.drcom/" exist
		## Or create a new one
		pathname = conf_path
		if os.path.exists(pathname) == False:
			os.mkdir(pathname)
		
		## Read server_ip.conf, and acquire server_ip
		file_path = os.path.join(pathname,addr_name)
		list_dir = os.listdir(pathname)
		if addr_name in list_dir:
			f = file(file_path,'r')
			self.server_ip = f.read()
			f.close()
			## No Server IP in server_ip.conf
			if len(self.server_ip) == 0:
				self.server_ip = IP_ADDR
			self.server_port = PORT
		else:
			self.server_ip = IP_ADDR
			self.server_port = PORT

		file_path = os.path.join(pathname,conf_name)
		if conf_name in list_dir:
			f = file(file_path,'r')
			account_pass = f.read()		
			f.close()
			account_end = account_pass.find(',')
			if account_end == -1:
				self.passwd_flag = False		
				self.account = ''
				self.password = ''
				return False
			self.account = account_pass[:account_end]
			
			## prevent the input of RETURN character.
			if account_pass[len(account_pass)-1] == '\x0a':
				password = account_pass[account_end+1:len(account_pass)-1]
				## FIXME: it is better to encrypt the password while storing in the "drcom.conf"
				self.password = password
			else:
				password = account_pass[account_end+1:len(account_pass)]
				self.password = password

			## Debug Option
			if Debug != 'False':
				print 'Your password:'
				self.show_hex(self.password)
				print 'Your Server IP:'
				self.show_hex(self.server_ip)
			
			self.passwd_flag = True
			return True

		self.passwd_flag = False		
		self.account = ''
		self.password = ''
		return False		

	def listen(self):
		'''
			Listen the instructions from GUI, Server acknowledgement and Timer Response.
		'''
		## FIXME: cost much resource for Off-line State
		while self.run_listen:
			## FIXME: Without sleep, CPU Usage would be ~= 40%
			time.sleep(0.1)
			try:
				data = dataQueue.get(block=False)
			except Queue.Empty:
				pass
			else:
				## Debug Option
				if Debug !=  'False':
					print data

				## GUI COMMAND				
				if data == '_quit_':
					## Turn off all threads while Quit
					self.run_listen = 0
					self.run_serv_ack = 0
					self.run_38_timer = 0
					self.run_40_timer = 0

				elif data == '_login_':
					self.login_request()
				elif data == '_logout_':
					self.logout_request()
				elif data == '_passwd_':
					self.passwd_request()

				## Server ACK
				elif data == '_serv_ack_':
					## FIXME: why put serv_ack packet in the Queue
					try:
						recv_data = dataQueue.get(block=False)
					except:
						pass
					else:
						self.packet_process(recv_data)

				## Timer Response
				## FIXME: if _timer_XX is behind _serv_ack_[logout] in dataQueue
				elif self.status == 'ON':
					if data == '_timer_38_':
						self.alive_38_request()
					elif data == '_timer_40_':
						self.alive_40_request()
				else:
					pass

	def serv_ack(self):
		'''
			Listen the packets from Server Acknowledgement by UDP
		'''
		## FIXME: cost much resource for Off-line State
		while self.run_serv_ack:
			## FIXME: Without sleep, CPU Usage would be ~= 40%
			time.sleep(0.1)
			try:
				recv_data, recv_addr = self.drcom_sock.recvfrom(self.BUFFER)
			except:
				pass
			else:
				## FIXME: aweful way for "recv_addr" to be removed
				self.serv_addr = recv_addr
				self.recv_addr = recv_addr
				self.server_ip = self.serv_addr[0]
				dataQueue.put('_serv_ack_')
				dataQueue.put(recv_data)

	def set_38_timer(self):
		'''
			Timer for alive_38_request
		'''
		while self.run_38_timer:
			## FIXME: aweful way to setup a Timer
			try:
				self.i += 1
			except:
				self.i = 0
			time.sleep(0.1)
			if self.i/self.timer_38*self.timer_38 == self.i:
				dataQueue.put('_timer_38_')

	def set_40_timer(self):
		'''
			Timer for alive_40_request
		'''

		while self.run_40_timer:
			## FIXME: aweful way to setup a Timer
			try:
				self.j += 1
			except:
				self.j = 0
			time.sleep(0.1)
			if self.j/self.timer_40*self.timer_40 == self.j:
				dataQueue.put('_timer_40_')

	def packet_process(self, recv_data):
		'''
			Do the appropriate job according to the Packet ID
		'''
		## Debug Option
		if Debug != 'False':
			self.show_hex(recv_data)

		## FIXME:!!No server_packet_id named '\x4d\x26\x6b' will occur errors!
		## FIXME: Linear judgement for server_packet_id
		if self.status == 'PW':
			if recv_data[0:2] in self.server_packet_id:
				if self.server_packet_id[recv_data[0:2]] == '_success_':
					self.passwd_success(recv_data)
				elif self.server_packet_id[recv_data[0:2]] == '_failure_':
					self.passwd_failure(recv_data)

		elif self.status == 'OFF':
			## FIXME:!!No server_packet_id named '\x4d\x26\x6b' will occur errors!!
			if recv_data [0:2] in self.server_packet_id:
				if self.server_packet_id[recv_data[0:2]] == '_login_response_':
					self.login_auth(recv_data)
				elif self.server_packet_id[recv_data[0:2]] == '_passwd_response_':
					self.passwd_auth(recv_data)
				elif self.server_packet_id[recv_data[0:2]] == '_success_':
					self.login_success(recv_data)
				elif self.server_packet_id[recv_data[0:2]] == '_failure_':
					self.login_failure(recv_data)

		elif self.status == 'ON':
			## FIXME:!!No server_packet_id named '\x4d\x26\x6b' will occur errors!!
			if recv_data[0:3] in self.server_packet_id:
				if self.server_packet_id[recv_data[0:3]] == '_alive_38_server_':
					## FIXME: Only need to check alive_version once
					self.alive_version_check(recv_data)
			elif recv_data [0:2] in self.server_packet_id:
				if self.server_packet_id[recv_data[0:2]] == '_alive_4_server_'\
					and len(recv_data) == 4:
					self.alive_4_reply(recv_data)
				elif self.server_packet_id[recv_data[0:2]] == '_logout_response_':
					self.logout_auth(recv_data)
				elif self.server_packet_id[recv_data[0:2]] == '_success_':
					self.logout_success(recv_data)
				elif self.server_packet_id[recv_data[0:2]] == '_failure_':
					self.logout_failure(recv_data)
			elif recv_data [0:1] in self.server_packet_id:
				if self.server_packet_id[recv_data[0:1]] == '_alive_40_server_'\
					and len(recv_data) == 40:
					self.alive_40_reply(recv_data)
#				elif self.server_packet_id[recv_data[0:2]] == '_Server_Info':
#					pass
#				elif self.server_packet_id[recv_data[0:2]] == '_Notice_':
#					pass

	def login_request(self):
		'''
			Login Request
		'''
		try:
			if self.status == 'ON':
				err_num = '10'
				self.exception(err_num)
				return False
		except:
			## not login yet
			self.status= 'OFF'

		## FIXME: not smart to do these every login request
		self.init_conf()
		self.server_ip_save()
		self.password_save()
		self.kernel_module_check()

		## socket initialization
		self.drcom_sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.drcom_sock.setblocking(0)

		## Debug Option
		if Debug != 'Local':

			try:
				## bind host_ip:port
				self.drcom_sock.bind((self.host_ip_dec,self.server_port))
	
			except:
				err_num = '05'
				self.exception(err_num)
				## FIXME: it must be successful in closing socket.
				self.drcom_sock.close()
				return False
		
		proc_name='_login_request_'
		send_data=self.host_packet_id[proc_name]+'\x51\x02\x03'+'\x00'*15

		try:
			self.drcom_sock.sendto(send_data,(self.server_ip,self.server_port))
		except:
			err_num = '20'
			self.exception(err_num)
			## FIXME: it must be successful in closing socket.
			self.drcom_sock.close()
			return False

	def login_auth(self,recv_data):
		'''
			Login Authentication
		'''
		proc_name='_login_auth_'

		## the first MD5 calculation
		self.service_identifier=recv_data[4:8]
		length=len(self.account)+20
		data_head=self.host_packet_id[proc_name]+'\x00'+ chr(length)
		md5_content=self.host_packet_id[proc_name]+\
			self.service_identifier+self.password
		self.login_a_md5=self.md5_key(md5_content)

		## MAC Address XOR calculation
		usr_name_zero='\x00'*(36-len(self.account))+'\x09\x01'
		mac_length=len(self.mac_addr)
		mac_xor=self.hex_xor(self.mac_addr,self.login_a_md5,mac_length)

		## the second MD5 calculation
		md5_content='\x01'+self.password+self.service_identifier+'\x00'*4
		login_b_md5=self.md5_key(md5_content)
		nic_ip_zero='\x00'*12
		num_nic=1

		## the third MD5 calculation
		data_front=data_head+self.login_a_md5+self.account+usr_name_zero+\
			mac_xor+login_b_md5+chr (num_nic)+\
			self.host_ip+nic_ip_zero
		md5_content=data_front+self.md5_tail
		login_c_md5=self.md5_key(md5_content)[0:8]

		## Add host DNS address
		host_name='\x00'*32
		host_dnsp=self.get_dns_addr()[0]
		host_dnss=self.get_dns_addr()[1]

		## FIXME: not valid for "drcom v3.72 u31 2227 build"
#		dhcp='\x00'*4
		dhcp='\xff\xff\xff\xff'
		
		## Add host system info
		host_unknown0='\x94'+'\x00'*3
		os_major='\x05'+'\x00'*3
		os_minor='\x01'+'\x00'*3
		os_build='\x28\x0A'+'\x00'*2
		host_unknown1='\x02'+'\x00'*3
		kernel_version='\x00'*32
		host_info=host_name+host_dnsp+dhcp+host_dnss+'\x00'*8+host_unknown0+\
			os_major+os_minor+os_build+host_unknown1+kernel_version
		zero3='\x00'*96

		## FIXME: not valid for "drcom v3.72 u31 2227 build"
#		unknown='\x03\x00\x02\x0C'+'\x20\x02\x60\x1a\x00\x00'
		unknown='\x03\x00\x02\x0C'+'\x00\xF3\x31\x9F\x01\x00'
		auto_logout=0
		multicast_mode=0

		## AUTH bit
		self.ip_dog = 1

		## FIXME: not valid for "drcom v3.72 u31 2227 build"
#		send_data=data_front+login_c_md5+chr(self.ip_dog)+'\x00'*4+host_info+zero3+\
#			unknown+'\x00'*6+chr(auto_logout)+chr(multicast_mode)+'\xf9\xf7'
		send_data=data_front+login_c_md5+chr(self.ip_dog)+'\x00'*4+host_info+zero3+\
			unknown+self.mac_addr+chr(auto_logout)+chr(multicast_mode)

		try:
			self.drcom_sock.sendto(send_data,(self.recv_addr))
		except:
			err_num = '21'
			self.exception(err_num)
			return False

	def login_failure(self, recv_data):
		'''
			Login Failed
		'''
		if (recv_data[4]=='\x03'):
			err_num = '30'
			self.exception(err_num)
		elif (recv_data[4]=='\x05'):
			err_num = '33'
			self.exception(err_num)
		elif (recv_data[4]=='\x15'):
			err_num = '61'
			self.exception(err_num)
		## FIXME: Condition of 'Error 34' not match in some Dr.COM networks
		elif len(recv_data)==15:
			err_num = '34'
			self.exception(err_num)
		elif len(recv_data)==22:
			err_num = '61'
			self.exception(err_num)

		self.status = 'OFF'

	def login_success(self, recv_data):
		'''
			Login Successfully
		'''	
		self.status = 'ON'

		## Turn ON NO.38 Timer
		self.run_38_timer = 1
		try:
			thread.start_new_thread(self.set_38_timer,())
		except:
			err_num = '50'
			self.exception(err_num)

		## Show Usage of the account
		time_usage = recv_data[8]+recv_data[7]+recv_data[6]+recv_data[5]
		vol_usage = recv_data[12]+recv_data[11]+recv_data[10]+recv_data[9]
		cash_usage = recv_data[16]+recv_data[15]+recv_data[14]+recv_data[13]
		self.show_usage(time_usage,vol_usage,cash_usage)

		## local address configuration and start auth module
		self.auth_info=recv_data[23:39]
		if self.ip_dog == 1:
			if recv_data[16+16+11] == '\x01':
				## No need to start auth module
				self.module_auth = 'non-AUTH'
					
			elif recv_data[16+16+11] == '\x00':
				## automatical configuration and start auth module
				self.module_auth = 'AUTH'
				self.auto_config(recv_data[16+16+11:])
				self.auth_module_start()

			else:
				err_num = '00'
				self.exception(err_num)
		
		## record the type of drcom network
		fd = file(type_path,'w')
		fd.write(self.module_auth)
		fd.close()

		## display the successful info
		err_num = '31'
		self.exception(err_num)

		## Warning:
		## threads_enter/leave() must adds here while X.org upgrades to 7.5.0
		## Otherwise, the whole Window will be frozen.
		gtk.gdk.threads_enter()
		self.tray.set_tooltip(_("Current State: Online"))
		gtk.gdk.threads_leave()

	def auto_config(self,recv_data):
		'''
			automatical configuration for except address
		'''
		## clean local_addr array
		self.local_addr = []

		## load local address
		lenth = len(recv_data)/12 * 12
		for i in range(0,lenth,12):
			if recv_data[i] == '\x00':
				addr = recv_data[i+4:i+8]
				mask = recv_data[i+8:i+12]
				self.local_addr.append(addr)
				self.local_addr.append(mask)
			elif recv_data[i] == '\x01':
				break

		## Note:
		## serv_ip -- binary, while server_ip -- decimal
		self.serv_ip = socket.inet_aton(self.serv_addr[0])
		self.local_addr.append(self.serv_ip[0]+'\x00'*3)
		self.local_addr.append('\xff'+'\x00'*3)

	def handy_config(self):
		'''
			Manual Configuration for except address
		'''
		## clean local_addr array
		self.local_addr = []

		## load host IP address
		host_ip = self.host_ip[0] + '\x00'*3 
		mask = '\xff' + '\x00'*3
		self.local_addr.append(host_ip)
		self.local_addr.append(mask)

		## load host DNS address
		dns1_ip=self.get_dns_addr()[0][0]+'\x00'*3
		dns2_ip=self.get_dns_addr()[1][0]+'\x00'*3
		if dns2_ip == '\x00'*4:
			self.local_addr.append(dns1_ip)
			self.local_addr.append(mask)
		else:
			self.local_addr.append(dns1_ip)
			self.local_addr.append(mask)
			self.local_addr.append(dns2_ip)
			self.local_addr.append(mask)

		## Note:
		## serv_ip -- binary, while server_ip -- decimal
		self.serv_ip = socket.inet_aton(self.serv_addr[0])
		self.local_addr.append(self.serv_ip[0]+'\x00'*3)
		self.local_addr.append('\xff'+'\x00'*3)

	def auth_module_start(self):
		'''
			Start auth module -- drcom.ko
		'''
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		## pass parameters first
		num = len(self.local_addr) / 2
		data = self.local_addr
		fmt = '16s'+'i'+'4s'* num*2
		param = struct.pack(fmt, self.ifname[:15], num, *data)

		try:
			s.setsockopt(socket.IPPROTO_IP, 64+2048+64+1, param)
		except:
			err_num = '54'
			self.exception(err_num)
			self.quit_common()

		## pass auth info then
		pid = os.getpid()
		auto_logout = 0
		auth_cmd = struct.pack('iii16s', 1, pid, auto_logout, self.auth_info)

		try:
			s.setsockopt(socket.IPPROTO_IP, 64+2048+64, auth_cmd)
		except:
			err_num = '54'
			self.exception(err_num)
			self.quit_common()

	def auth_module_stop(self):
		'''
			Stop auth module -- drcom.ko
		'''
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		auth_cmd = struct.pack('iii16s', 0, 0, 0, self.auth_info)
		try:
			s.setsockopt(socket.IPPROTO_IP, 64+2048+64, auth_cmd)
		except:
			err_num = '55'
			self.exception(err_num)

	def logout_request(self):
		'''
			Logout Request
		'''
		try:
			if self.status == 'OFF':
				err_num = '11'
				self.exception(err_num)
				return False
		except:
			## listen thread could not run normally if no init_conf()
			self.init_conf()
			err_num = '11'
			self.exception(err_num)
			return False

		proc_name='_logout_request_'
		send_data=self.host_packet_id[proc_name]+'\x80\x02\x03'+'\x00'*15
		try:
			self.drcom_sock.sendto(send_data,(self.serv_addr))
		except:
			err_num = '24'
			self.exception(err_num)

	def logout_auth(self, recv_data):
		'''
			Logout Authentification
		'''
		proc_name='_logout_auth_'
		self.service_identifier=recv_data[4:8]

		## MD5 calculation
		md5_content=self.host_packet_id[proc_name]+self.service_identifier+self.password
		logout_md5=self.md5_key(md5_content)

		## MAC address XOR calculation
		mac_xor=self.hex_xor(self.mac_addr,logout_md5,len(self.mac_addr))

		usr_name_zero='\x00'*(36-len(self.account))+'\x09\x01'
		length=len(self.account)+20
		send_data=self.host_packet_id[proc_name]+'\x00'+chr(length)+logout_md5+self.account+\
			usr_name_zero+mac_xor+self.auth_info

		try:
			self.drcom_sock.sendto(send_data,(self.serv_addr))
		except:
			err_num = '25'
			self.exception(err_num)
			return False

	def logout_failure(self, recv_data):
		'''
			Logout Failed
		'''
		err_num = '35'
		self.exception(err_num)
		self.status = 'ON'

	def logout_success(self, recv_data):
		'''
			Logout Successfully
		'''
		self.status = 'OFF'

		## Turn Off No.38 and No.40 Timers
		self.run_38_timer = 0
		self.run_40_timer = 0

		if self.ip_dog == 1:
			if self.module_auth == 'AUTH':
					self.auth_module_stop()

		## Warning: 
		## threads_enter/leave() must adds here while X.org upgrades to 7.5.0
		## Otherwise, the whole Window will be frozen.
		gtk.gdk.threads_enter()
		self.tray.set_tooltip(_("Current State: Offline"))
		gtk.gdk.threads_leave()

		## Show Usage of the account
		time_usage=recv_data[8]+recv_data[7]+recv_data[6]+recv_data[5]
		vol_usage=recv_data[12]+recv_data[11]+recv_data[10]+recv_data[9]
		cash_usage = recv_data[16]+recv_data[15]+recv_data[14]+recv_data[13]
		self.show_usage(time_usage,vol_usage,cash_usage)

		## display the successful info
		err_num = '32'
		self.exception(err_num)

		try:
			self.drcom_sock.close()
		except:
			err_num = '07'
			self.exception(err_num)
			self.quit_common()
			return False

	def passwd_request(self):
		'''
			Change Password Request
		'''
		self.get_newpasswd_account()
		try:
			if self.status == 'ON':
				err_num = '43'
				self.exception(err_num)
				return False
		except:
			self.status = 'OFF'

		## Password confirmation not match
		if self.new_password!=self.new_password_a:
			err_num = '40'
			self.exception(err_num)
			return False

		## socket initialization
		self.drcom_sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.drcom_sock.setblocking(0)

		## Debug Option
		if Debug != 'Local':
			try:	
				self.drcom_sock.bind((self.host_ip_dec,self.server_port))
			except:
				err_num = '05'
				self.exception(err_num)
				## FIXME: it must be successful in closing socket.
				self.drcom_sock.close()
				return False

		proc_name='_passwd_request_'
		send_data=self.host_packet_id[proc_name]+'\x51\x02\x03'+'\x00'*15

		try:
			self.drcom_sock.sendto(send_data,(self.server_ip,self.server_port))
		except:
			err_num = '26'
			self.exception(err_num)
			## FIXME: it must be successful in closing socket.
			self.drcom_sock.close()

	def passwd_auth(self, recv_data):
		'''
			Change Password Authentication
		'''
		proc_name='_new_passwd_'
		self.service_identifier=recv_data[4:8]
		length=len(self.old_account)+20
		passwd_data_head=self.host_packet_id[proc_name]+'\x00'+chr(length)

		## MD5 Calculation
		md5_content=self.host_packet_id[proc_name]+\
			self.service_identifier+self.old_password
		passwd_a_md5=self.md5_key(md5_content)
		passwd_usr_name_zero='\x00'*(16-len(self.old_account))
		passwd_data_front=passwd_data_head+passwd_a_md5+\
			self.old_account+passwd_usr_name_zero
		md5_content=passwd_a_md5+self.old_password
		passwd_b_md5=self.md5_key(md5_content)
		
		new_passwd=self.new_password+'\x00'*(16-len(self.new_password))
		new_passwd_xor=self.hex_xor(passwd_b_md5, new_passwd, 16)

		passwd_unknown='\x12'+'\x00'*3+'\x16'+'\x00'*3+'\x04'+'\x00'*7
		send_data=passwd_data_front+new_passwd_xor+passwd_unknown
		
		try:
			self.drcom_sock.sendto(send_data,(self.recv_addr))
		except:
			err_num = '27'
			self.exception(err_num)
			return False
		else:
			self.status = 'PW'

	def passwd_failure(self, recv_data):
		'''
			Change Password Failed
		'''
		if (recv_data[4]=='\x03'):
			err_num = '42'
			self.exception(err_num)
		elif (recv_data[4]=='\x15'):
			err_num = '61'
			self.exception(err_num)
		else:
			err_num = '00'
			self.exception(err_num)

		self.status = 'OFF'

	def passwd_success(self, recv_data):
		'''
			Change Password Successfully
		'''
		self.status = 'OFF'
		self.password=self.new_password
		self.passwordbox.set_text(self.password)
		self.password_save()

		err_num = '41'
		self.exception(err_num)
		
	def alive_version_check(self, recv_data):
		'''
			Check the version of keep_alive protocol
		'''
		if len(recv_data) == 16:
			self.version = 3.4
		else:
			self.version = 3.7

		## Debug Option
		if Debug != 'False':
			print 'keep_alive version =', self.version

		## start _timer_40_
		## FIXME: it may cause restart No.40 Timer accidentally
		try:
			self.run_40_timer
		except:
			self.run_40_timer = 1
			thread.start_new_thread(self.set_40_timer, ())

		else:
			if self.run_40_timer == 0:
				self.run_40_timer = 1
				thread.start_new_thread(self.set_40_timer,())

	def alive_38_request(self):
		'''
			No.38 keep_alive packet request
		'''
		proc_name='_alive_38_client_'
		unknown0 = '\x00\x00'
		send_data=self.host_packet_id[proc_name]+self.login_a_md5+'\x00'*3+self.auth_info+unknown0
		try:
			self.drcom_sock.sendto(send_data,(self.serv_addr))
		except:
			err_num = '22'
			self.exception(err_num)
			self.quit_common()

	def alive_40_request(self):
		'''
			No.40 keep_alive packet request
		'''
		if self.version == 3.4:
			self.alive_40_request_old()
		elif self.version == 3.7:
			self.alive_40_request_new()

	def alive_40_request_old(self):
		'''
			No.40 keep_alive packet request for version 3.4
		'''
		proc_name='_alive_40_client_'
		unknown0='\x3e\x00'
		self.alive_account0 += 0x01
		if self.alive_account0 >= 0xff:
			self.alive_account0 -= 0xff
		self.alive_account1 += 0x05
		if self.alive_account1 >= 0xff:
			self.alive_account1 -= 0xff

		account= 1
		send_data=self.host_packet_id[proc_name]+chr(self.alive_account0) +\
			'\x28\x00\x0b' + chr(account) +'\x1c\x00' +unknown0\
			+chr(self.alive_account1) + '\x00'*29
	
		try:
			self.drcom_sock.sendto(send_data,(self.serv_addr))
		except:
			err_num = '22'
			self.exception(err_num)
			self.quit_common()

	def alive_40_request_new(self):
		'''
			No.40 keep_alive packet request for version 3.7
		'''
		proc_name='_alive_40_client_'
		server_ack=self.server_ack_40
		unknown0='\x7a\x03'
		account = 1
		self.alive_account1 += 0x10
		if self.alive_account1 >= 0x3c:
			self.alive_account1 -= 0x3c

		send_data = self.host_packet_id[proc_name]+chr(self.alive_account0) +\
			'\x28\x00\x0b' + chr(account) +'\x1e\x00' +unknown0\
			+chr(self.alive_account1) + '\x00'*5 + server_ack +'\x00'*20
	
		try:
			self.drcom_sock.sendto(send_data,(self.serv_addr))
		except:
			err_num = '22'
			self.exception(err_num)
			self.quit_common()

	def alive_40_reply(self, recv_data):
		'''
			Reply to the No.40 packet received from server
		'''
		pkt_no=recv_data[5:6]
		if pkt_no=='\x02':
			self.server_ack_40=recv_data[16:20]
		elif pkt_no=='\x04':
			return True

		proc_name='_alive_40_client_'
		server_ack=self.server_ack_40
		self.alive_account0 += 1
		if self.alive_account0 >= 0xff:
			self.alive_account0 -= 0xff
		self.alive_account1 += 1
		if self.alive_account1 >= 0x3c:
			self.alive_account1 -= 0x3c

		unknown0='\x7a\x03'
		account= 3
		send_data=self.host_packet_id[proc_name]+chr(self.alive_account0) +\
			'\x28\x00\x0b' + chr(account) +'\x1e\x00' +unknown0\
			+ chr(self.alive_account1) + '\x00'*5 + server_ack +'\x03'+'\x00'*20

		try:
			self.drcom_sock.sendto(send_data,(self.serv_addr))
		except:
			err_num = '22'
			self.exception(err_num)
			self.quit_common()

	def alive_4_reply(self, recv_data):
		'''
			Reply to the No.4 packet received from server
		'''
		self.server_ack_4=recv_data[2:4]
		server_ack=self.server_ack_4
		proc_name='_alive_4_client_'
		msg_md5_content=self.login_a_md5+self.password
		a=self.md5_key(msg_md5_content)
		msg_ad=0
 		for i in range(0,16,2):
			msg_ad+=struct.unpack('H',a[i:i+2])[0]
		msg_add=str(msg_ad)
		msg_ad_=chr(int(msg_add[0:1]))+chr(int(msg_add[1:2]))
		xor=self.hex_xor(msg_ad_,server_ack,2)
		msg_=xor[0:1]
		msg__=xor[1:2]
		msg=msg_+msg__

		msg_content='\x01'+ (msg) +self.md5_tail+server_ack
		keep_alive_md5=self.md5_key(msg_content)
		send_data=self.host_packet_id[proc_name]+(msg)+'\x01'+keep_alive_md5+'\x00'+self.auth_info
		try:
			self.drcom_sock.sendto(send_data,self.serv_addr)
		except:
			err_num = '23'
			self.exception(err_num)
			self.quit_common()

## --------------------------
##  Graphical User Interface
## --------------------------

	def __init__(self):
		'''
			Main Window of Graphical User Interface
		'''
		gtk.gdk.threads_init()
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_size_request(300, 150)
		self.window.set_title(_("Drcom-Client"))
		self.window.connect("key_release_event",self.on_window_key_release_event)
		self.window.connect("delete_event", self.on_delete_event)
		self.tray = gtk.status_icon_new_from_file(icon_path)
		self.tray.set_tooltip(_('Current State: Offline'))
		self.tray.connect("activate",self.on_tray_button_press_event)
		self.tray.set_visible(True)
		
		self.read_conf()
		self.run_listen = 1
		thread.start_new_thread(self.listen,())
		self.run_serv_ack = 1
		thread.start_new_thread(self.serv_ack,())

		atexit.register(unlink)
		f = open(os.path.join(conf_path,pid_file), "w")
		f.write("%d" % os.getpid())
		f.close()

		## width of LABEL and ENTRY in this window
		LENGTH_LABEL_1 = 5
		LENGTH_ENTRY_1 = 20

		vbox = gtk.VBox(False, 0)
		self.window.add(vbox)
		vbox.show()

   		hbox = gtk.HBox(False,0)
		vbox.add(hbox)
		hbox.show()
     
		hbox0 = gtk.HBox(False,0)
		vbox.add(hbox0)
		hbox0.show()
	
		hbox1 = gtk.HBox(False,0)
		vbox.add(hbox1)
		hbox1.show()

		label = gtk.Label(_("Server IP"))
		label.set_width_chars(LENGTH_LABEL_1)
		hbox.pack_start(label, True, True, 0)
		label.show()

		self.serveripbox = gtk.Entry()
		self.serveripbox.set_max_length(50)
		self.serveripbox.set_visibility(True)
		self.serveripbox.set_width_chars(LENGTH_ENTRY_1)
		self.serveripbox.set_text(self.server_ip)

		hbox.pack_start(self.serveripbox, True, True, 0)
		self.serveripbox.show()

		label = gtk.Label(_("Account "))
		label.set_width_chars(LENGTH_LABEL_1)
		hbox0.pack_start(label, True, True, 0)
		label.show()
	
		self.accountbox = gtk.Entry()
		self.accountbox.set_max_length(50)
		self.accountbox.set_visibility(True)
		self.accountbox.set_width_chars(LENGTH_ENTRY_1)
		if self.passwd_flag==True:
			self.accountbox.set_text(self.account)
		hbox0.pack_start(self.accountbox, True, True, 0)
		self.accountbox.show()
	
		label = gtk.Label(_("Password"))
		label.set_width_chars(LENGTH_LABEL_1)
		hbox1.pack_start(label, True, True, 0)
		label.show()
	
		self.passwordbox = gtk.Entry()
		self.passwordbox.set_max_length(50)
		if self.passwd_flag==True:
			self.passwordbox.set_text(self.password)
		self.passwordbox.set_visibility(False)
		self.passwordbox.set_width_chars(LENGTH_ENTRY_1)
		hbox1.pack_start(self.passwordbox, True, True, 0)
		self.passwordbox.show()
	
		self.checkbutton = gtk.CheckButton(_("Save your Password"))
		if self.passwd_flag==True:
			self.checkbutton.set_active(True)
		else:
			self.checkbutton.set_active(False)
		vbox.pack_start(self.checkbutton, True, True, 0)
		self.checkbutton.show()
	
		hbox2 = gtk.HBox(False,0)
		vbox.add(hbox2)
		hbox2.show()

		button = gtk.Button(_('Login'))
		button.connect("clicked", self.on_tray_button_press_event)
		button.connect("clicked", self.gui_login)
		hbox2.pack_start(button, True, True, 0)
		button.show()
	
		button = gtk.Button(_('Logout'))
		button.connect("clicked", self.on_tray_button_press_event)
		button.connect("clicked", self.gui_logout)
		hbox2.pack_start(button, True, True, 0)
		button.show()

		button = gtk.Button(_('Quit'))
		button.connect("clicked", self.quit)
		hbox2.pack_start(button, True, True, 0)
		button.show()
		
		item_login = gtk.ImageMenuItem(_('Connect'))
		item_logout = gtk.ImageMenuItem(_('Disconnect'))
		item_passwd = gtk.ImageMenuItem(_('_Pass_Word'))
		item_about = gtk.ImageMenuItem(_('About'))
		item_quit = gtk.ImageMenuItem(_('Quit'))

		item_login.connect('activate', self.gui_login)
		item_logout.connect('activate', self.gui_logout)
		item_passwd.connect('activate', self.passwd)
		item_about.connect('activate', self.show_about)
		item_quit.connect('activate', self.quit)

		img = gtk.Image()
		img.set_from_stock(gtk.STOCK_CONNECT, 1)
		item_login.set_image(img)

		img = gtk.Image()
		img.set_from_stock(gtk.STOCK_DISCONNECT, 1)
		item_logout.set_image(img)
		
		img = gtk.Image()
		img.set_from_stock(gtk.STOCK_EDIT, 1)
		item_passwd.set_image(img)

		img = gtk.Image()
		img.set_from_stock(gtk.STOCK_ABOUT, 1)
		item_about.set_image(img)

		img = gtk.Image()
		img.set_from_stock(gtk.STOCK_QUIT, 1)
		item_quit.set_image(img)
		
		menu = gtk.Menu()
		menu.append(item_login)
		menu.append(item_logout)
		menu.append(gtk.SeparatorMenuItem())
		menu.append(item_passwd)
		menu.append(item_about)
		menu.append(gtk.SeparatorMenuItem())
		menu.append(item_quit)
		self.tray.connect('popup-menu', self.pop_menu, menu)
		icon = gtk.gdk.pixbuf_new_from_file(icon_path)
		self.window.set_icon(icon)
		self.window.show()
		gtk.main()

	## -- pass GUI instructions to listen thread
	def gui_login(self, widget):
		dataQueue.put('_login_')
	def gui_logout(self, widget):
		dataQueue.put('_logout_')
	def gui_passwd(self, widget):
		dataQueue.put('_passwd_')
	## --

	def passwd(self, widget):
		'''
			Window for Changing Passwords
		'''
		self.window1 = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window1.set_size_request(300, 150)
		self.window1.set_title(_("New Password"))
		self.window1.connect("key_release_event",self.on_window_key_release_event)
		self.window1.connect("delete_event", self.on_delete_event)
		self.tray.set_visible(True)

		## width of LABEL and ENTRY in this window
		LENGTH_LABEL_2 = 5
		LENGTH_ENTRY_2 = 15

		vbox = gtk.VBox(False, 0)
		self.window1.add(vbox)
		vbox.show()

		hbox = gtk.HBox(False,0)
		vbox.add(hbox)
		hbox.show()

		hbox1 = gtk.HBox(False,0)
		vbox.add(hbox1)
		hbox1.show()

		hbox4 = gtk.HBox(False,0)
		vbox.add(hbox4)
		hbox4.show()

		hbox3 = gtk.HBox(False,0)
		vbox.add(hbox3)
		hbox3.show()

		label = gtk.Label(_("Account"))
		label.set_width_chars(LENGTH_LABEL_2)
		hbox.pack_start(label, True, True, 0)
		label.show()

		self.accountboxa = gtk.Entry()
		self.accountboxa.set_max_length(50)
		self.accountboxa.set_visibility(True)
		self.accountboxa.set_width_chars(LENGTH_ENTRY_2)
		if self.passwd_flag==True:
			self.accountboxa.set_text(self.account)
		hbox.pack_start(self.accountboxa, True, True, 0)
		self.accountboxa.show()

		label = gtk.Label(_("Old Password"))
		label.set_width_chars(LENGTH_LABEL_2)
		hbox1.pack_start(label, True, True, 0)
		label.show()
			
		self.passwordboxa = gtk.Entry()
		self.passwordboxa.set_max_length(50)
		self.passwordboxa.set_visibility(False)
		self.passwordboxa.set_width_chars(LENGTH_ENTRY_2)
		hbox1.pack_start(self.passwordboxa, True, True, 0)
		self.passwordboxa.show()
			
		label = gtk.Label(_("Confirm"))
		label.set_width_chars(LENGTH_LABEL_2)
		hbox3.pack_start(label, True, True, 0)
		label.show()
			
		self.new_password_a_box = gtk.Entry()
		self.new_password_a_box.set_max_length(50)
		self.new_password_a_box.set_visibility(False)
		self.new_password_a_box.set_width_chars(LENGTH_ENTRY_2)
		hbox3.pack_start(self.new_password_a_box, True, True, 0)
		self.new_password_a_box.show()
	
		label = gtk.Label(_("New Password"))
		label.set_width_chars(LENGTH_LABEL_2)
		hbox4.pack_start(label, True, True, 0)
		label.show()
	
		self.new_passwordbox = gtk.Entry()
		self.new_passwordbox.set_max_length(50)
		self.new_passwordbox.set_visibility(False)
		self.new_passwordbox.set_width_chars(LENGTH_ENTRY_2)
		hbox4.pack_start(self.new_passwordbox, True, True, 0)
		self.new_passwordbox.show()

		hbox5 = gtk.HBox(False,0)
		vbox.add(hbox5)
		hbox5.show()
				
		button = gtk.Button(_('OK'))
		button.connect("clicked", self.on_tray_button1_press_event)
		button.connect("clicked", self.gui_passwd)
		self.window.hide()
		hbox5.pack_start(button, True, True, 0)
		button.show()
		
		button = gtk.Button(_('Cancel'))
		button.connect("clicked", self.on_tray_button1_press_event)
		hbox5.pack_start(button, True, True, 0)
		button.show()
		              
		icon = gtk.gdk.pixbuf_new_from_file(icon_path)
		self.window1.set_icon(icon)
		
		self.window1.show()
		gtk.main()

	def on_delete_event(self, widget, event=None, user_data=None):
		widget.hide()
		return True

	def on_window_key_release_event(self, widget, event):
		if event.keyval == gtk.keysyms.Escape:
			widget.hide()
	
	def on_tray_button_press_event(self, *args):
		if self.window.get_property('visible'):
			self.window.hide()
		else:
			self.window.present()

	def on_tray_button1_press_event(self, *args):
		if self.window1.get_property('visible'):
			self.window1.hide()
		else:
			self.window1.present()

	def server_ip_save(self):
		'''
			Save Server IP address
		'''
		server_ip = self.serveripbox.get_text()

		if len(server_ip) == 0:
			pass
		## prevent the input of RETURN character
		elif server_ip[len(server_ip)-1] == '\x0a':
			server_ip = server_ip[:len(server_ip)-1]

		f=file(os.path.join(conf_path,addr_name),'w')
		f.write(server_ip)
		f.close()

	def password_save(self):
		'''
			Save the Password
		'''
		self.get_account()
		if self.checkbutton.get_active()==True:
			if len(self.account)==0 and len(self.password)==0:
				f=file(os.path.join(conf_path,conf_name),'w')
				f.write('')
				f.close()
			else:
				f=file(os.path.join(conf_path,conf_name),'w')
				
				## FIXME: it is better to encrypt the password while storing in the "drcom.conf"
				password = self.password

				## prevent the input of RETURN character
				if password[len(password)-1] == '\x0a':
					password == password[:len(password)-1]

				f.write(self.account+','+password)
				f.close()
		else:
			f=file(os.path.join(conf_path,conf_name),'w')
			f.write('')
			f.close()
	
	def get_account(self):
		'''
			Read account and password from Edit-BOX in Main Window
		'''
		self.account=self.accountbox.get_text()
		self.password=self.passwordbox.get_text()

	def get_newpasswd_account(self):
		'''
			Read passwords from Edit-BOX in Password Window
		'''
		self.old_account=self.accountboxa.get_text()
		self.old_password=self.passwordboxa.get_text()
		self.new_password=self.new_passwordbox.get_text()
		self.new_password_a=self.new_password_a_box.get_text()

 	def balloons(self, tag, info):
		'''
			Display error information in a balloon box
		'''
		_notifyRealm = tag
		_Urgencies = {
       			'low': pynotify.URGENCY_LOW,
       			'critical': pynotify.URGENCY_CRITICAL,
       			'normal': pynotify.URGENCY_NORMAL
				}
		icon=None
		x = self.get_x()
		y = self.get_y()
		body=info
		urgency="low"
		summary=_notifyRealm
		pynotify.init(_notifyRealm)
		notifyInitialized = True
		toast = pynotify.Notification(summary, body)
		timeout = 5000
		toast.set_timeout(timeout)
		toast.set_urgency(_Urgencies[urgency])
		toast.set_hint("x", x)
		toast.set_hint("y", y)

		try:
			gnome.sound_init('localhost')
			gnome.sound_play(os.path.join(sound_path))
		except:
			pass

		toast.show()
		return False

	def get_x(self):
		x = self.tray.get_geometry()[1][0]
		if self.tray.get_visible()==True:
			x += int(self.tray.get_size()/2) 
		else:
			x -= int(self.tray.get_size()/2)
		return x

	def get_y(self):	
		y = self.tray.get_geometry()[1][1]
		if self.tray.get_visible()==True:
			y += int(self.tray.get_size()/2) 
		else:
			y -= int(self.tray.get_size()/2) 
		return y

	def pop_dialog(self, title, data):
		'''
			Pop out a dialog window
		'''
		dialog = gtk.Dialog(title, None, 0, (gtk.STOCK_OK, gtk.RESPONSE_OK))
		dialog.set_border_width(25)
		dialog.set_position(gtk.WIN_POS_CENTER_ALWAYS)
		label = gtk.Label(data)
		dialog.vbox.pack_start(label, True, True, 0)
		label.show()
		if dialog.run() == gtk.RESPONSE_OK:
			dialog.destroy()
		return True

	def show_about(self, widget):
		'''
			Display "About" window
		'''
		version = 'v1.0'
		license_file = open(license_path, "r")
		license = license_file.read()
		license_file.close()
		license = str(license)
		authors = ["Wheelz <kernel.zeng@gmail.com>",\
				"Henry Huang <henry.s.huang@gmail.com>",\
				"longshow <longshow@yeah.net>",]

		logo = gtk.gdk.pixbuf_new_from_file(icon_path)
		comments=_("drcom-client")
		translator_credits = "translator-credits"

		about=gtk.AboutDialog()
		try:
			gtk.about_dialog_set_email_hook(self.__url_hook, "mailto:")
			gtk.about_dialog_set_url_hook(self.__url_hook, "")
		except:
			pass

		about.set_name(_("drcom-client"))
		about.set_version(version)
		about.set_copyright(_("Copyright © 2009 drcom-client team"))
		about.set_license(license)
		about.set_website("http://www.drcom-client.org/")
		about.set_authors(authors)
		about.set_translator_credits(translator_credits)
		about.set_logo(logo)
        
		icon = gtk.gdk.pixbuf_new_from_file(icon_path)
		about.set_icon(icon)
               
		about.connect("response", lambda d, r: about.destroy())
        
		about.show_all()
		return True

	def __url_hook(self, widget, url, scheme):
		gnome.ui.url_show_on_screen(scheme + url, widget.get_screen())	
  	
	def pop_menu(self, widget, button, time, data=None):
		'''
			pop out a menu list
		'''
		if data:
			data.show_all()
      		data.popup(None, None, None, 3, time)
		return True

	def exception(self,err_num):
		'''
			Exception Processing
		'''
		## Warning:
		## threads_enter/leave() must adds here while X.org upgrades to 7.5.0
		## Otherwise, the whole Window will be frozen.
		gtk.gdk.threads_enter()
		if err_num == '31' or err_num == '32':
			self.balloons(self.exception_id[err_num], self.info)
		elif err_num == '41':
			self.balloons(_('Success'), self.exception_id[err_num])
		else:
			self.balloons(_('Error ')+err_num, self.exception_id[err_num])
		gtk.gdk.threads_leave()

	def quit_common(self):
		self.status = 'OFF'
		## Warning: 
		## threads_enter/leave() must adds here while X.org upgrades to 7.5.0
		## Otherwise, the whole Window will be frozen.
		gtk.gdk.threads_enter()
		self.tray.set_tooltip(_('Current State: Offline'))
		gtk.gdk.threads_leave()

		## FIXME: when serious errors happen,
		## Here comes a bug-- if you Quit, it will cause thread-errors.
		gtk.main()
		
	def quit(self,widget):
		'''
			Quit from Graphical User Interface
		'''
		## FIXME: program exits while threads not stop yet
		dataQueue.put('_quit_')
		time.sleep(0.1)
		gtk.main_quit()
		sys.exit(0)


def findpid():
	'''
		find the pid of this program
	'''
	f = open(os.path.join(conf_path,pid_file))
	p = f.read()
	f.close()
	return int(p)

def unlink():
	'''
		when Quit, unlink the pid file
	'''
	os.unlink(os.path.join(conf_path,pid_file))

def main():
	f = open("/tmp/drcom-log", "w")
	while 1:
		f.write('%s\n' % time.ctime(time.time()))
		f.flush()
		time.sleep(10)

##----------------------------
##       Main Entrance
##----------------------------
if __name__ == "__main__":

	## create a daemon process
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
		sys.exit(1)

	os.chdir("/")
	os.setsid()
	os.umask(0)

	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
		sys.exit(1)

	## one program is running...
	if os.path.exists(os.path.join(conf_path,pid_file)):
		p = findpid()
		print "drcom-client has already started."
		sys.exit(1)

	drcom_client()
	main()
