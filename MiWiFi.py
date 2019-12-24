#!/usr/bin/env python
# coding=utf-8
#-*- coding: utf-8 -*-

# 小米路由器远程管理 API

import random
import math
import time
import hashlib
import json
import re

import requests


def regex_find(pattern, text):
    '''
    return list
    '''
    match_return = re.compile(pattern, re.IGNORECASE).findall(text)
    return match_return


class MiWiFi(object):
    """
    docstring for MiWiFi
    """

    def __init__(self, host):
        super(MiWiFi, self).__init__()
        self.host = host
        self.deviceId = None
        self.type = '0'
        self.nonce = None
        self.password = None
        self.stok = None
        self.cookies = None

        # 小米路由器首页
        # self.URL_ROOT = "http://miwifi.com"
        self.URL_ROOT = "http://" + host
        # 小米路由器登录页面
        self.URL_LOGIN = "%s/cgi-bin/luci/api/xqsystem/login" % self.URL_ROOT
        # 小米路由器当前设备清单页面，登录后取得 stok 值才能完成拼接
        self.URL_ACTION = None
        self.URL_DeviceListDaemon = None

    def get_key_deviceId(self):
        self.URL_MAIN_PAGE = "%s/cgi-bin/luci/web" % self.URL_ROOT
        try:
            r = requests.get(self.URL_MAIN_PAGE, timeout=5)
            pattern = r'''(?<=key: ')(.*)(?=')'''
            key = regex_find(pattern, r.text)[0]
            pattern = r'''(?<=var deviceId = ')(.*)(?=')'''
            deviceId = regex_find(pattern, r.text)[0]
        except Exception as e:
            raise
        return key, deviceId

    def nonceCreat(self, miwifi_deviceId):
        """
        docstring for nonceCreat()
        模仿小米路由器的登录页面，计算 hash 所需的 nonce 值
        """
        self.deviceId = miwifi_deviceId
        miwifi_type = self.type
        miwifi_time = str(int(math.floor(time.time())))
        miwifi_random = str(int(math.floor(random.random() * 10000)))
        self.nonce = '_'.join(
            [miwifi_type, miwifi_deviceId, miwifi_time, miwifi_random])

        return self.nonce

    def oldPwd(self, password, key):
        """
        docstring for oldPwd()
        模仿小米路由器的登录页面，计算密码的 hash
        """
        token = password + key
        token_1 = hashlib.sha1(token.encode('utf-8')).hexdigest()
        token_2 = self.nonce + token_1
        self.password = hashlib.sha1(token_2.encode('utf-8')).hexdigest()
        return self.password

    def login(self, password):
        """
        docstring for login()
        登录小米路由器，并取得对应的 cookie 和用于拼接 URL 所需的 stok
        """
        key, deviceId = self.get_key_deviceId()
        nonce = self.nonceCreat(deviceId)
        password = self.oldPwd(password, key)
        payload = {'username': 'admin', 'logtype': '2',
                   'password': password, 'nonce': nonce}
        # print payload

        try:
            r = requests.post(self.URL_LOGIN, data=payload, timeout=5)
            # print r.text
            stok = json.loads(r.text).get('url').split('=')[1].split('/')[0]
        except Exception as e:
            raise

        r.cookies.create_cookie(name='__guid',value='86847064.4146078363660605400.{}.557'.format(time.time()*1000))
        self.stok = stok
        self.cookies = r.cookies
        print(r.cookies)
        self.URL_ACTION = "%s/cgi-bin/luci/;stok=%s/api" % (
            self.URL_ROOT, self.stok)
        self.URL_DeviceListDaemon = "%s/xqsystem/device_list" % self.URL_ACTION
        return stok, r.cookies

    def listDevice(self):
        """
        docstring for listDevice()
        列出小米路由器上当前的设备清单
        """
        if self.URL_DeviceListDaemon != None and self.cookies != None:
            try:
                r = requests.get(self.URL_DeviceListDaemon,
                                 cookies=self.cookies, timeout=5)
                # print json.dumps(json.loads(r.text), indent=4)
                return json.loads(r.text).get('list')
            except Exception as e:
                raise
                return None
        else:
            raise
            return None

    def runAction(self, action):
        """
        docstring for runAction()
        run a custom action like "pppoe_status", "pppoe_stop", "pppoe_start" ...
        """
        if self.URL_DeviceListDaemon != None and self.cookies != None:
            try:
                r = requests.get('%s/xqnetwork/%s' %
                                 (self.URL_ACTION, action), cookies=self.cookies, timeout=5)
                return json.loads(r.text)
            except Exception as e:
                raise
                return None
        else:
            raise
            return None


if __name__ == '__main__':
    miwifi = MiWiFi('192.168.31.1')
    # deviceId = ''
    password = '123456789'
    stok, cookies = miwifi.login(password)
    print(miwifi.listDevice())
