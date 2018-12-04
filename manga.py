import requests

from os import mkdir, getcwd, path, access, W_OK, listdir
from PIL import Image
from io import BytesIO
import argparse
from shutil import rmtree, which
from sys import stdout
import validators

from kindlecomicconverter import comic2ebook

parser = argparse.ArgumentParser()
parser.add_argument("url", help='''
    url of manga series.
    Currently supports - 
        Helvetica Scans
        Hot Chocolate Scans
        Jaimini’s Box
        Kirei Cake
        MangaHere
        Mangadex
        MangaFox
        Mangakakalot
        Manganelo
        MangaRock
        MangaStream
        Meraki Scans
        Phoenix Serenade
        Sense Scans
        Sen Manga
        Silent Sky Scans
        Tuki Scans
''')
parser.add_argument("--start",help="Downloads from the specified chapter number",default=1,type=int)
parser.add_argument("--end",help="Downloads till the specified chapter number", default = 0,type=int)
parser.add_argument("--ki",help="keep manga files after creating kindle files",action="store_true")
parser.add_argument("--dest",help="downloads and saves manga/mobi files in the specified directory. Default - This script folder",default=getcwd())

args = parser.parse_args()

def validateArgs():
    valids = []
    if which('kindlegen') is None :
        valids.append('kindle gen is missing. download kindlegen from https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211 and place the exe in your env scripts folder')
    if not validators.url(args.url) :
        valids.append('url error')
    if args.start >=1:
        if args.end != 0 and args.start > args.end :
            valids.append('error. --start should less than --end')
    else :
        valids.append('error. --start >=1')  
    if(args.dest != getcwd()):
        if not path.exists(args.dest) and access(args.dest, W_OK): valids.append('Please check if the directory exists and you have required permission to write to the directory')
    
    if len(valids) > 0 :
        print('errors in input arguments')
        print('\n')
        print(valids)
        quit()

    main(args.url,args.start,args.end,args.ki,args.dest)

def main(url,start,end,ki,dest):
    content = getSeries(url)
    download(content,start,end,ki,dest)
    

def getSeries(src):
    series = requests.get("https://api.poketo.app/series?url=" + src)

    if(series.status_code == requests.codes.ok):
        return series.json()
    
    series.raise_for_status()

def download(content,start,end,ki,dest):
    if not path.exists(dest + '\\downloads'): mkdir(dest + '\\downloads')
    
    if end == 0 : end = len(content['chapters'])
    
    requested_chapters = [x for x in content['chapters'] if start <= int(float(x['chapterNumber'])) <= end ]

    series_dir = dest + '\\downloads\\' + content['title']
    
    if not path.exists(series_dir): mkdir(series_dir) 
    
    for chapter in requested_chapters:
        c = requests.get('https://api.poketo.app/chapter?url=' + chapter['url'])

        if(c.status_code != requests.codes.ok): 
            print('ignored chapter '+ chapter['chapterNumber'] + '. server returned '+ str(c.status_code) + 'error')

        print('downloading chapter ' + chapter['chapterNumber'])

        if not path.exists(series_dir+ '\\' + content['title'] + ' ' + chapter['chapterNumber']): mkdir(series_dir+ '\\' + content['title'] + ' ' + chapter['chapterNumber'])
        
        pages_url = [ x['url'] for x in c.json()['pages'] ]
        
        page_count = 1

        for page in pages_url:
            
            stdout.write('\rDownloaded : [' + str(page_count) + '/' + str(len(pages_url)) + '] pages' )
            p = requests.get(page,stream=True)
            
            if p.status_code != 200 : 
                print('\n' + str(p.status_code) + ' error for page' + str(page_count))
                continue
            
            im = Image.open(BytesIO(p.content))
            im.save(series_dir+ '\\' + content['title'] + ' ' + chapter['chapterNumber'] + '\\' + str(page_count) + '.jpg', 'JPEG')
            
            page_count +=1
            stdout.flush()
        
        files_list_in_dir = [f for f in listdir(series_dir+ '\\' + content['title'] + ' ' + chapter['chapterNumber']) if path.isfile(path.join(series_dir+ '\\' + content['title'] + ' ' + chapter['chapterNumber'], f))]
        
        if(len(files_list_in_dir) > 0) : 
            createBook(series_dir+ '\\' + content['title'] + ' ' + chapter['chapterNumber'],content['title'] + ' ' + str(chapter['chapterNumber']))
        else : 
            print('no images in ' + content['title'] + ' ' + chapter['chapterNumber'])
        
        if(not ki):
            rmtree(series_dir+ '\\' + content['title'] + ' ' + chapter['chapterNumber'])

def createBook(folder,title):
    comic2ebook.main([folder, '-p','KV','-m','True','-f','MOBI','-u','True','--title',title])


if __name__ == '__main__':
    validateArgs()
    
