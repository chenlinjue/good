# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 16:10:36 2020

@author: cheb
"""

import re
import requests
from threading import *
from bs4 import BeautifulSoup
from lxml import etree
from contextlib import closing
from multiprocessing import Pool
import time
from mylog import MyLog as mylog
from save2mysql import SavemovieData
from save1mysql import Savemovieadd
from func_timeout import func_set_timeout,FunctionTimedOut
import os,gc
#线程数 
nMaxThread = 5 
connectlock = BoundedSemaphore(nMaxThread)
gHeads = {"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
#自定义的路径
urla="https://www.dililitv.com/film"

class moviedataitem(object):
    Name = None
    Poster = None
    Director = None
    Screenwriter = None
    Tostar = None
    Type = None
    Country = None
    Time = None
    Filmlength = None
    Score = None
    Synopsis = None

class movieurl(object):
    Name =None
    UrlName=None
    playurl=None
    
    
class MovieThread(Thread):
    def __init__(self,url,movieName):
        Thread.__init__(self)
        
        self.log=mylog()
        self.url = url
        self.movieName = movieName
    
    def time_out(fn,*args,**kwargs):
        def wrapper(*args,**kwargs):
            try:
                result = fn(*args,**kwargs)
                return result
            except FunctionTimedOut:
                
                print("timeout")
                return None
        return wrapper
        
   #线程
    @time_out
    @func_set_timeout(100)
    def run(self):
        try:           
            urlList,moviedatas,urlnameList = self.GetMovieUrl(self.url,self.movieName)
            SavemovieData(moviedatas)            
            if urlList != None:                                       
                for i in range(len(urlList)):
                    try:                       
                        addres=movieurl()
                        a,b = self.GetVkeyParam(urlList[i])
                        type=re.findall("'(.*)'",a)
                        vkey=re.findall("'(.*)'",b)
                        if type != None and vkey !=None:
                            addurl=[]
                            addres.UrlName=urlnameList[i]
                            addres.Name=self.movieName
                            addres.playurl=vkey[0]
                            addurl.append(addres)                                                                       
                            Savemovieadd(addurl)
                    except Exception as e:
                        print(e)
                        self.log.info("%s数据有问题"+str(e)%(str(self.movieName)))
                        #payload,DownloadUrl = self.GetOtherParam(type[0],vkey[0])
                       
                            #print(videoUrl)
        except Exception as e:
            print(e)                      
        finally:
            connectlock.release()

                

    #获取电影的播放链接页面和
    @time_out
    @func_set_timeout(60)
    def GetMovieUrl(self,url,movieName):
            time.sleep(2)
            heads = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
                "Host":"www.dililitv.com",
                'Accept-Language':'zh-CN,zh;q=0.9',
                "Referer":"https://www.dililitv.com/film/"
                }
            moviedat=moviedataitem()
            moviedatas=[]
            html = requests.get(url,headers=heads).text
            #print(html)
            xmlContent = etree.HTML(html)
            #获取播放链接id
            urlidList = xmlContent.xpath("//div[@id='video_list_li']/div[@class='vlink']/a/@id")
            #链接对应的来源
            urlnameList = xmlContent.xpath("//div[@id='video_list_li']/div[@class='vlink']/a/text()")
            #获取视频信息
            #海报      
            #简介
            #dataurl=movieurl()
            #dataurls=[]
            #dataurl.Name=movieName
            
            Synopsisa = xmlContent.xpath("//p[@class='jianjie']//span/text()")
            moviedat.Synopsis=re.sub('\s',' ',Synopsisa[0])#1
            #数据
            moviedat.Poster= xmlContent.xpath("//div[@class='video_img']/img/@src")#(2)
          
            moviedata=xmlContent.xpath("//div[@class='video_info']")[0].xpath('string(.)').split("\n")
            #导演
            #print(movieda)
            
            moviedat.Name=movieName#(3)
            print(moviedat.Name)
            moviedat.Director = moviedata[0].strip().split(":")[1]#(4)
            #编剧
            moviedat.Screenwriter= moviedata[1].strip().split(": ")[1]#(5)
            #主演
            moviedat.Tostar = moviedata[2].strip().split(": ")[1]#(6)
            #类型
            #预防格式问题
            moviedat.Type = moviedata[3].strip().split(": ")[1]#(7)
            #国家
    
            if moviedata[4].strip().split(": ")[0]=="官方网站":
                moviedat.Country=moviedata[5].strip().split(": ")[1]#(8)
                moviedat.Language=moviedata[6].strip().split(": ")[1]#(9)
                Timea =moviedata[7].strip().split(": ")[1]
                moviedat.Time=re.sub('\(.*',"",Timea)#(10)
                Filmlengtha =moviedata[8].strip().split(": ")[1]
                moviedat.Filmlength =re.sub('\(.*',"",Filmlengtha)#(11)
                if moviedata[9].strip().split(": ")[0]=="IMDb编码":
                    moviedat.Score =moviedata[10].strip().split(": ")[1]#(12)
                elif moviedata[10].strip().split(": ")[0]=="IMDb编码":
                    moviedat.Score =moviedata[11].strip().split(": ")[1]
            else:
                moviedat.Country=moviedata[4].strip().split(": ")[1]
                moviedat.Language=moviedata[5].strip().split(": ")[1]
                Timea = moviedata[6].strip().split(": ")[1]
                moviedat.Time=re.sub('\(.*',"",Timea)
                Filmlengtha =moviedata[7].strip().split(": ")[1]
                moviedat.Filmlength =re.sub('\(.*',"",Filmlengtha)
                if moviedata[8].strip().split(": ")[0]=="IMDb编码":
                    moviedat.Score =moviedata[9].strip().split(": ")[1]
                elif moviedata[9].strip().split(": ")[0]=="IMDb编码":
                    moviedat.Score =moviedata[10].strip().split(": ")[1]
                
            moviedatas.append(moviedat)
            #print(moviedatas)
            self.log.info(movieName+"电影信息获取成功........")
            
            UrlList=[]
            for i in range(len(urlidList)):
                urle=urla+"/vplay/"+urlidList[i]+".html"
                UrlList.append(urle)
            if len(UrlList)>0:
                return UrlList,moviedatas,urlnameList
                self.log.info("电影播放链接获取成功........")
            else:
                return None,moviedatas,urlnameList
                self.log.info("电影播放链接获取失败........")
            
    def GetVkeyParam(self,secUrl):
        heads = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            "Host": "www.dililitv.com"
            }
        try :
            html = requests.get(secUrl,headers=heads).text
           
            bs = BeautifulSoup(html,"html.parser")
            
            content = bs.find("body").find("script")
            #reContent = re.findall('"(.*?)"',content.text)
            reContent = re.findall('=(.*)',content.text)
            urla=re.sub('%2F','/',reContent[0])
            urlc=re.sub('%3D','=',urla)
            urlb=re.sub('%3A',':',urlc)
            if reContent[0] == None:
                self.log.info("电影播放链接获取失败....")
            return  reContent[1],urlb    
        except:
            return None,None
            self.log.info("键值获取数据失败.....")
       
        '''    def GetOtherParam(self,type,vKey):
       
        url = "https://api.1suplayer.me/player/?userID=&type=%s&vkey=%s"%(type,vKey)
        self.log.info("链接播放url......"+url)
        #print(url)
        heads = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            "Host": "api.1suplayer.me",
            "Referer":"https://www.dililitv.com/film/"
            }
        try:
            html = requests.get(url,headers=heads).text
            bs = BeautifulSoup(html,"html.parser")
            content = bs.find("body").find("script").text
            recontent = re.findall(" = '(.+?)'",content)            
            payload = {
                    "type":recontent[3],
                    "vkey":recontent[4],
                    "ckey":recontent[2],
                    "userID":"",
                    "userIP":recontent[0],
                    "refres":1,
                    "my_url":recontent[1]
                    }
            return payload,url
            
        except:
            return None,None'''

        
    '''def GetDownloadUrl(self,payload,refereUrl):
        heads = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            "Host": "api.1suplayer.me",
            "Referer": refereUrl,
            "Origin": "https://api.1suplayer.me",
            "X-Requested-With": "XMLHttpRequest"
            }
        while True:
            retData = requests.post("https://api.1suplayer.me/player/api.php",data=payload,headers=heads).json()
            if  retData["code"] == 200:
                return retData["url"]
                print(retData["url"])
            elif retData["code"] == 404:
                payload["refres"] += 1;
                continue
            else:
                return None'''

#获取视频信息链接
def main(url):
    print("%s开始执行，进程号为%d"%(url,os.getpid()))
    html = requests.get(url,headers=gHeads,timeout=10).text
    xmlcontent = etree.HTML(html)
    UrlList = xmlcontent.xpath("//div[@class='m-movies clearfix']//article/a/@href")
    NameList = xmlcontent.xpath("//div[@class='m-movies clearfix']//article/a/h2/text()")
    for i in range(len(UrlList)):
        connectlock.acquire()
        #视频链接
        url = UrlList[i]
        #视频名字
        name = NameList[i]#.encode("utf-8")
        #print(name)
        #执行线程
        t = MovieThread(url,name)
        t.start()
    
if __name__ == '__main__':
    alist=[]
    for i in range(52,58):
        urlv=urla+"/page/"+str(i+1)
        alist.append(urlv)
    pool=Pool(2)
    for i in range(len(alist)):
        url=alist[i]
        print(url)
        pool.apply_async(main,(url,))
    pool.close()
    pool.join()
