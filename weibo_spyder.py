# -*- coding: utf-8 -*-
import requests
from selenium import webdriver
import datetime
from datetime import timedelta
import urllib
import lxml
from lxml import html
etree = html.etree
import time
import random
import numpy
import pandas as pd

class Weibo_spyder():

    def __init__(self, keyword, begin_date, end_date , user_name , password, interval = 1, approve='全部' ):
        self.begin_date = datetime.datetime(int(begin_date.split('-')[0]),int(begin_date.split('-')[1]),int(begin_date.split('-')[2]))
        self.end_date = datetime.datetime(int(end_date.split('-')[0]),int(end_date.split('-')[1]),int(end_date.split('-')[2]))
        self.interval = interval
        self.url_time = self.set_time()
        self._keyword = keyword
        self.keyword = self.set_kw(keyword)
        self.approve = approve
        self.url = self.get_url()
        self.page_n = 1
        self.set_req(user_name,password)
        self.set_excel()

    def set_req(self, user_name ,password):
        wd = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe')
        wd.maximize_window()
        wd.get('http://www.weibo.com/login.php')
        wd.find_element_by_xpath('//*[@id="loginname"]').send_keys(user_name)
        wd.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').send_keys(password)
        wd.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()
        cookies = wd.get_cookies()
        self.req = requests.Session()
        for cookie in cookies:
            self.req.cookies.set(cookie['name'], cookie['value'])  # 转换cookies
        wd.quit()

    def set_excel(self):
        try:
            self.dfo = pd.read_excel('data/' + self._keyword + self.approve + '原创' + '.xls')
            self.dft = pd.read_excel('data/' + self._keyword + self.approve + '转发' + '.xls')
        except:
            self.dfo = pd.DataFrame(columns=['用户ID', '用户认证状态', '转发数', '用户主页', '发布日期','微博内容','原创类型'])
            self.dft = pd.DataFrame(columns=['用户ID', '用户认证状态', '转发数', '用户主页', '转发日期','微博内容','原微博用户id', '原微博认证状态', '原微博转发数量', '原微博用户主页', '原微博发布日期','转发微博内容','转发类型'])
            self.dfo.to_excel('data/' + self._keyword + self.approve + '原创' + '.xls')
            self.dft.to_excel('data/' + self._keyword + self.approve + '转发' + '.xls')

    def set_time(self):
        self.start_time =  self.begin_date
        self.end_time = self.begin_date + timedelta(days = self.interval - 1)
        return self.start_time.strftime("%Y-%m-%d") + ':' + self.end_time.strftime("%Y-%m-%d")

    def set_kw(self,kw):
        once = urllib.parse.urlencode({"kw": kw})[3:]
        return urllib.parse.urlencode({"kw": once})[3:]

    def get_url(self):
        if self.approve == '全部':
            return "http://s.weibo.com/weibo/" + self.keyword + "&typeall=1&suball=1&timescope=custom:" + self.url_time + "&page="
        elif self.approve == '认证':
            return "http://s.weibo.com/weibo/" + self.keyword + "&vip=1&suball=1&timescope=custom:" + self.url_time + "&page="
        elif self.approve == '媒体':
            return "http://s.weibo.com/weibo/"+ self.keyword +"&category=4&suball=1&timescope=custom:"+ self.url_time +"&page="

    def get_page(self,url,page_n):
        self.aaa = False
        self.hasMore = True
        try:
            data = self.req.get(url + str(page_n)).text
            print (url + str(page_n))
        except:
            self.aaa = False
            self.hasMore = False
            return 0
        lines = data.splitlines()
        for line in lines:
            if line.startswith('<script>STK && STK.pageletM && STK.pageletM.view({"pid":"pl_weibo_direct"'):
                self.aaa = True
                n = line.find('html":"')
                if n > 0:
                    j = line[n + 7: -12].encode("utf-8").decode('unicode_escape').replace("\\", "")
                    if (j.find('<div class="search_noresult">') > 0):
                        self.hasMore = False
                    else:
                        page = etree.HTML(j)
                        ps = page.xpath("//div[@class='WB_cardwrap S_bg2 clearfix']")
                        return ps
        if not self.hasMore:
            print (self.url_time + "完成")

    def get_data(self,p):
        self.TransPond = False
        name = str(p.xpath("descendant::a[@class='W_texta W_fb']/@nick-name")[0])
        content_node = p.xpath("descendant::p[@class='comment_txt']")[0]
        content = str(content_node.xpath('string(.)'))
        try:
            content_url = 'http://s.weibo.com/ajax/direct/morethan140?' + str(p.xpath("descendant::p[@class='comment_txt']")[0].xpath("descendant::a[@class='WB_text_opt']/@action-data")[0]) + '&checkcode=127459667&_t=0&__rnd' + str(int(time.time()))
            print(content_url)
            full_content = self.req.get(content_url).text
            n = full_content.find('html":"')
            j = full_content[n + 7: -3].encode("utf-8").decode('unicode_escape').replace("\\", "")
            content_node = etree.HTML(j)
            content = str(etree.HTML(j).xpath('string(.)'))
            time.sleep(random.randint(8, 12))
            if full_content == """":"100000","msg":"","data":""":
                print("checkcode errpr")
                self.aaa ==False
                break
        except:
            pass
        Types = self.getType(content_node)
        try:
            approve = str(p.xpath("descendant::div[@class='feed_content wbcon']/a/@alt")[0])
        except:
            approve = str('微博普通用户')
            pass
        user_page = str(p.xpath("descendant::a[@class='W_texta W_fb']/@href")[0])  # 用户主页
        try:
            tcount = str(p.xpath("descendant::a[@suda-data='key=tblog_search_weibo&value=weibo_ss_page_z']//text()")[1])
        except:
            tcount = ''
        # 抓取转发内容
        if len(p.xpath("descendant::a[@class='W_texta W_fb']/@nick-name")) == 2:
            self.TransPond = True
            t_name = str(p.xpath("descendant::a[@class='W_texta W_fb']/@nick-name")[1])
            t_content_node = p.xpath("descendant::p[@class='comment_txt']")[1]
            t_content = str(t_content_node.xpath('string(.)'))
            try:
                t_content_url = 'http://s.weibo.com/ajax/direct/morethan140?' + str(p.xpath("descendant::p[@class='comment_txt']")[1].xpath("descendant::a[@class='WB_text_opt']/@action-data")[-1]) + '&checkcode=127459667&_t=0&__rnd' + '&_t=0&__rnd' + str(int(time.time()))
                print(t_content_url)
                t_full_content = self.req.get(t_content_url).text
                n = t_full_content.find('html":"')
                j = t_full_content[n + 7: -3].encode("utf-8").decode('unicode_escape').replace("\\", "")
                t_content_node = etree.HTML(j)
                t_content = str(t_content_node.xpath('string(.)'))
                time.sleep(random.randint(8, 12))
				if t_content == """":"100000","msg":"","data":""":
					print("checkcode errpr")
					self.aaa ==False
					break
            except:
                pass
            t_Types = self.getType(t_content_node)
            try:
                t_approve = str(p.xpath("descendant::div[@node-type='feed_list_forwardContent']/a[2]/@alt")[0])
            except:
                t_approve = '微博普通用户'
                pass
            t_user_page = str(p.xpath("descendant::a[@class='W_texta W_fb']/@href")[1])
            date = self.Changedatetime(str(p.xpath("descendant::a[@node-type='feed_list_item_date']/@date")[1])[:-3])
            t_date = self.Changedatetime(str(p.xpath("descendant::a[@node-type='feed_list_item_date']/@date")[0])[:-3])
            t_tcount = str(p.xpath("descendant::a[@suda-data='key=tblog_search_weibo&value=weibo_zhuan_z']//text()")[1])
            t_Types = self.find_pic(p,t_Types)
            line = [name, approve, tcount, user_page, date, content, t_name, t_approve, t_tcount, t_user_page, t_date, t_content,t_Types]
            return line
        else:
            date = self.Changedatetime(str(p.xpath("descendant::a[@node-type='feed_list_item_date']/@date")[0])[:-3])
            Types = self.find_pic(p,Types)
            line = [name, approve, tcount, user_page, date, content ,Types]
            return line

    def getType(self,node):
        Type = ''
        if len(node.xpath("descendant::a[@class='video_link']")) != 0:
            Type = Type + '视频;'
        if len(node.xpath("descendant::em[@class='W_autocut W_linkb']")) != 0:
            if len(node.xpath("descendant::a[@class='W_btn_c6']")) != 0:
                Type = Type + '文章;'
            else:
                Type = Type + '链接;'
        return Type

    def find_pic(self,p,Types):
        if len(p.xpath("descendant::div[@class='media_box']/@node-type")) !=0 or len(p.xpath("descendant::ul[@class='WB_media_a WB_media_a_m1 clearfix']")) !=0:
            return Types +'图片;'
        else:
            if Types == '':
                return '纯文字'
            else:
                return Types

    def Changedatetime(self,timestamp):
        try:
            dt = datetime.datetime.fromtimestamp(float(timestamp))
            str1 = dt.strftime('%Y-%m-%d')
            return str1
        except:
            return ''

    def change_url(self):
        if self.hasMore:
            self.aaa = True
            self.page_n += 1
            return self.url_time ,self.aaa
        else:
            self.aaa = True
            self.page_n = 1
            self.start_time = self.start_time + timedelta(days=self.interval)
            self.end_time = self.end_time + timedelta(days=self.interval)
            if self.end_time > self.end_date :
                self.aaa = False
                self.end_time = self.end_date
                return self.start_time.strftime("%Y-%m-%d") + ':' + self.end_time.strftime("%Y-%m-%d"), self.aaa
            return self.start_time.strftime("%Y-%m-%d") + ':' + self.end_time.strftime("%Y-%m-%d") ,self.aaa

    def save_data(self,l):
        if len(l) == 7:
            self.dfo.loc[len(self.dfo)] = l
            self.dfo.to_excel('data/' + self._keyword + self.approve + '原创' + '.xls')
            print (l)
        else:
            self.dft.loc[len(self.dfo)] = l
            self.dft.to_excel('data/' + self._keyword + self.approve + '转发' + '.xls')
            print(l)

    def download(self):
        self.aaa = True
        print (self._keyword + ' ' + self.approve + ' ' + self.begin_date.strftime("%Y-%m-%d") + ':' + self.end_date.strftime("%Y-%m-%d"))
        while self.aaa == True:
            self.url = self.get_url()
            print (self.url_time + ' 第' + str(self.page_n) + '页')
            page = self.get_page(self.url,self.page_n)
            if self.hasMore:
                try:
                    for p in page:
                        l = self.get_data(p)
                        self.save_data(l)
                except TypeError:
                    continue
            self.url_time ,self.aaa = self.change_url()
            sleeptime = random.randint(30, 45)
            print ('sleep ' + str(sleeptime) + ' seconds...')
            time.sleep(sleeptime)
        print('Finish')

    def get_pp(self,user_page):
        user_page_ = 'https:' + user_page + ''
        data = self.req.get(user_page_).text
        lines = data.splitlines()
        for line in lines:
            if line.startswith("$CONFIG['onick']='"):
                name = line[18:-3]
            if line.startswith('<script>FM.view({"ns":"","domid":"Pl_Core_T8CustomTriColumn__3"'):
                break
        n = line.find('html":"')
        if n > 0:
            j = line[n + 7: -12].replace('\\', '')
            # soup = BeautifulSoup(j,'lxml')
            page = etree.HTML(j)
            ps = page.xpath("//td[@class='S_line1']")
            concern = str(ps[0].xpath("descendant::strong//text()"))[2:-2]
            fans = str(ps[1].xpath("descendant::strong//text()"))[2:-2]
            Weibo = str(ps[2].xpath("descendant::strong//text()"))[2:-2]
            print(name + ' 关注数：' + concern + ' 粉丝数：' + fans + ' 微博数' + Weibo)
            return name, concern, fans, Weibo
        else:
            print('Be Caught')

    def getUser(self):
        user_pages = self.dfo.用户主页.values.tolist()
        try:
            for i in self.dft.原微博用户主页.tolist():
                if type(i) == str:
                    user_pages.append(i)
            for i in self.dft.用户主页.tolist():
                if type(i) == str:
                    user_pages.append(i)
        except:
            pass
        user_pages = list(set(user_pages))
        dfu = pd.DataFrame(columns=['用户ID','用户主页','关注数','粉丝数','微博数'])
        l = 0

        dic = {}
        for i in user_pages:
            try:
                user_id, concern, fans, Weibo = self.get_pp(i)
            except:
                continue
            dfu.loc[l] = [user_id, i, concern, fans, Weibo]
            dic[user_id] = {}
            dic[user_id]['concern'] = concern
            dic[user_id]['fans'] = fans
            dic[user_id]['Weibo'] = Weibo
            dfu.to_excel('data/' + self._keyword + '用户信息.xls')
            sleeptime = random.randint(15, 25)
            print('sleep ' + str(sleeptime) + ' seconds...')
            time.sleep(sleeptime)
            l += 1

        self.dfo = self.dfo.fillna('')
        self.dft = self.dft.fillna('')
        self.fill_UserI(self.dfo,dic)
        self.fill_UserI(self.dft, dic)
        self.dfo.to_excel('data/' + self._keyword + self.approve + '原创' + '.xls')
        self.dft.to_excel('data/' + self._keyword + self.approve + '转发' + '.xls')
        print('Finish')

    def fill_UserI(self,df,dic):
        for i in range(len(df)):
            try:
                key = df.loc[i]['用户ID']
                df.loc[i, '关注数'] = dic[key]['concern']
                df.loc[i, '粉丝数'] = dic[key]['fans']
                df.loc[i, '微博数'] = dic[key]['Weibo']
                if len(df.loc[i]) == 9:
                    key = df.loc[i]['原微博用户id']
                    df.loc[i, '原微博用户关注数'] = dic[key]['concern']
                    df.loc[i, '原微博用户转发数'] = dic[key]['fans']
                    df.loc[i, '原微博用户微博数'] = dic[key]['Weibo']
            except:
                continue

if __name__ == '__main__':
    spyder = Weibo_spyder(keyword = '',begin_date = 'yyyy-mm-dd',end_date = 'yyyy-mm-dd' ,user_name = '微博登录名' ,password = '登录密码',interval = 1 ,approve='媒体' )  #认证状态为  '全部'  '认证'  '媒体'
    spyder.download()     #抓取搜索结果
    spyder.getUser()      #获取个人信息保存到excel并写入搜索结果
