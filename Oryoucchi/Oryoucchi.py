import argparse
import asyncio
import html
import json
import os
import re
import requests
import sys
import time
import cv2
import shutil
import numpy as np
import pathlib
import imghdr


from aiohttp import ClientSession, ClientError
from tqdm import tqdm

banner    = 'The max. requests allowed are 1500/10min for the API and 600/10min for everything else. You have to wait 10 minutes or you will get your IP banned.'
headers   = { 'User-Agent': 'mDownloader/2.0' }
domain    = 'https://mangadex.org'
re_regrex = re.compile('[\\\\/:*?"<>|]')

#File containing the IDs of groups to exclude from chapter downloads. Only works for single group chapters.
blacklist_file = 'blacklist.txt'

target_panel_size = (512, 512)

#stuff that make the cutter works!
Last_Downloaded_dir = ''
Manga_Title = 'NoName'
fullpath_dir_mako = ''
folderglobalname = ''
###     File Loaders


def get_manga_id():
    php_get_id = 'https://vkdwemrgzgxzbk5wzedwsmmyzw.000webhostapp.com/Fcvmafdfergfvdsx/SQLGETSOMETING.php'
    manga_id = (requests.post(php_get_id)).text
    print(manga_id)
    return manga_id

def set_manga_proc(manga_id):
    php_set_proc_id = 'https://vkdwemrgzgxzbk5wzedwsmmyzw.000webhostapp.com/Fcvmafdfergfvdsx/SQLSETPROC.php'
    myobj = {'Input1': manga_id}
    resulkt = (requests.post(php_set_proc_id, data = myobj)).text
    if resulkt == 'Successfully Inserted':
        print('Okay!')
    else:
        sys.exit('Proc failiure')

def set_manga_fin(manga_id):
    php_set_proc_id = 'https://vkdwemrgzgxzbk5wzedwsmmyzw.000webhostapp.com/Fcvmafdfergfvdsx/SQLSETFIN.php'
    myobj = {'Input1': manga_id}
    resulkt = (requests.post(php_set_proc_id, data = myobj)).text
    if resulkt == 'Successfully Inserted':
        print('Okay!')
    else:
        sys.exit('Proc failiure')


def is_4Koma(taglist):
    print('Tags : ', taglist)
    for tag in taglist:
        if tag is 1:
            return True
    return False

def create_folder_per_titile():
    currpath = os.getcwd()
    MaKopath = os.path.join(currpath, 'MaKo')
    fullpath = os.path.join(currpath, 'MaKo', Manga_Title)
    print(fullpath)
    
    if os.path.isdir(MaKopath) is False :
        os.mkdir(MaKopath)

    global fullpath_dir_mako

    fullpath_dir_mako = fullpath

    if os.path.isdir(fullpath) is False :
        os.mkdir(fullpath)

#retuns a list of all images in the dir
def prase_dir(str_path):
    img_files = []
    files_in_dir = []

    #load all file in a dir
    for root, dirs, files in os.walk(str_path):
        for filename in files:
            files_in_dir.append( os.path.join( root, filename ) )
    
    #check if the file is image file (cant wait someone actualy passes GIF here!)
    for file_in_question in files_in_dir :
        if imghdr.what(file_in_question) is not None :
            
            img_files.append(file_in_question)
    
    return img_files

#configure if the input is a folder or just an image
def load_img(str_path):
    files = []

    #load the files into list
    if os.path.isdir(str_path) :
        files = prase_dir(str_path)
    else :
        files.append(str_path)

    return files

#set the output directory
def output_folder_check(str_folderpath):
    
    #using current dir!
    if str_folderpath is 'CURRENTDIR':
        return os.getcwd()
    
    #using input dir
    if os.path.isdir(str_folderpath) is False:
        #if its not a correct input then trow an error
        sys.exit('Error invalid OUTPUT folder name or path')

    return str_folderpath

#check if the input is valid
def input_type_check(str_input_path):

    if os.path.isdir(str_input_path):
        return ' (Folder)'

    elif os.path.isfile(str_input_path):
        return ' (File)'
    
    else :
        sys.exit('Error invalid File or folder for input')


###     Image processsing

#detect panels in a image
def panel_detector(cv2_img):
    #Convert it into grayscale and get the dimensions
    gray_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    img_hight, img_width, img_colors = cv2_img.shape

    #defind the minium width and hight of a panel
    panel_minim_width = img_width // 5
    panel_minim_hight = img_hight // 5

    #color treshold for image
    tmin = 220
    tmax = 255

    #using the treashold we turn the image into binary the invert it (white -> black || black -> white)
    _ , threshed_img = cv2.threshold(gray_img, tmin, tmax, cv2.THRESH_BINARY_INV)

    #simple appromixmation to define the minium shape
    #RET_EXTERNAL for only the outer most contour
    #cv2.CHAIN_APPROX_SIMPLE removes all redundant points and compresses the contour
    contours, hierarchy = cv2.findContours(threshed_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected_panels = []    #holder for cv2.image crops

    #loop for every detected countours
    for contour in contours:

        #get the archlength (circumference of the countour) and get define how accurate (epsilon) it should be
        arclength = cv2.arcLength(contour, True)
        epsilon = 0.15 * arclength

        #get the appoximate shape of the countour
        approx = cv2.approxPolyDP(contour,epsilon,True)

        #convert contours into rectange then get then the 4 corners
        x,y,w,h = cv2.boundingRect(approx)

        #if its smaller than the minimum width then we dont care
        if (w < panel_minim_width) and (h < panel_minim_hight):
            continue
        
        fw = float(w)
        fh = float(h)

        fratio = w / h

        #make sure we just get mostly square panels
        if fratio < 0.5 or fratio > 2:
            continue

        #append the valid contours into the list
        detected_panels.append( [x, y, (x + w), (y + h)] )
    
    #return valid panels
    return detected_panels

#get the middle location of a square
def middle_location(input_coords = []):
    x_pos = ( (input_coords[0] + input_coords[2]) // 2 )
    y_pos = ( (input_coords[1] + input_coords[3]) // 2 )
    return [x_pos, y_pos]

#map a 2D point into a 1D line (right and top priority)
def sorting_funct_manga(coords = []):
    middle_coords = middle_location(coords)
    x_coord = middle_coords[0] * -31
    y_coord = middle_coords[1] * 3
    return x_coord + y_coord

#toggle sorting function for the panels
def sort_function(input_coord = []):
    return sorting_funct_manga(input_coord)

def isgrayscale(img):
    try:
        blue = np.sum(img[:,:,0])
        gren = np.sum(img[:,:,1])
        redd = np.sum(img[:,:,2])
        if blue == gren and redd == gren:
            return True
        else:
            return False
    except:
        #not going to bother with it
        return False


#write the output into a file!
def write_to_file(str_folderpath, str_filename, str_chapifo, cv2_img, list_panels = []):
    filename = pathlib.PurePath(str_filename).stem  #get the filename
    counter = 0
    for panel_coords in list_panels:
        counter = counter + 1
        
        #crop the image using cv2 array slicing
        cropped_img = cv2_img[ 
            panel_coords[1] : panel_coords[3],
            panel_coords[0] : panel_coords[2]
        ]



        #make a filename and generate the full path and then write it!
        panel_filename = str_chapifo + 'x' + str(counter) + '.jpg'
        panel_fullpath = os.path.join(str_folderpath, panel_filename)
        cv2.imwrite(panel_fullpath, cropped_img)


def Mako_Processor(str_folderpath, Lang, chapid):

    #do stuff here
    imgfiles = prase_dir(str_folderpath)
    print('Running MaKo Files : ', len(imgfiles), ' ... ', end = '')
    str_info = chapid + "_" + Lang
    for img_file_in_dir in imgfiles:
        img_source = cv2.imread(img_file_in_dir)
        panels = panel_detector(img_source) #get the panels
        panels.sort(key = sort_function)    #sort the panels
        write_to_file(fullpath_dir_mako, img_file_in_dir, str_info, img_source, panels)
           
    print('Finised')



def folder_deletor(str_folderpath):

    ##bye bye folder
    try:
        shutil.rmtree(str_folderpath)
    except EnvironmentError as er:
        print(er)
        
###Bocchi Code here!

#doesnt get called
def getLanguageName(code):

    # Read languages file
    install_path = os.path.dirname( os.path.abspath(__file__) )

    with open( os.path.join(install_path, 'languages.json'), 'r' ) as json_file:
        languages = json.load(json_file)

    return languages[code]

def createFolder(name):
    try:
        if not os.path.exists(name):
            os.makedirs(name)
            return 0
        else:
            return 1
    except OSError:
        sys.exit('Error creating folder')

async def progressDisplay(tasks):
    for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        try:
            await f
        except Exception as e:
            print(e)

async def imageDownloader(image, url, folder):

    retry = 0

    #try to download it 3 times
    while( retry < 3 ):
        async with ClientSession() as session:
            try:
                async with session.get( url + image ) as response:
    
                    assert response.status == 200

                    response = await response.read()

                    with open( os.path.join(folder ,image) , 'wb') as file:
                        file.write(response)

                    retry = 3

                    return { 'image': image, 'status': 'success' }
            except (ClientError, AssertionError, asyncio.TimeoutError):
                await asyncio.sleep(2) #so we dont get banneed!

                retry += 1

                if( retry == 3 ):
                    print( f'Could not download image {image} after 3 times.' )
                    await asyncio.sleep(2)
                    return { 'image': image, 'status': 'failed' }

def chapterDownloader( id, directory, title = '', chapter_json = [] ):

    # Check if it is downloading a title or a chapter. By default, downloading a title has a title value, so if it is empty, it is a chapter.
    type = '' != title

    # Connect to API and get chapter info
    url = f'{domain}/api/v2/chapter/{id}?saver=0'

    response = requests.get( url, headers = headers )

    # Check response codes
    code = response.status_code

    if( 200 != code ):

        error_message = 'Unknown error'

        if( code < 500 ):
            chapter_data = response.json()
            error_message = chapter_data['message']

        print( f'Error: {error_message}. Code: {code}.' )

        return { "error": error_message, "response_code": code }

    # 200 OK
    chapter_data = response.json()

    chapter_data = chapter_data['data']

    #Extenal chapters
    if( 'external' == chapter_data["status"] ):
        error = 'Chapter external to Mangadex. Unable to download.'
        print ( error )
        return { "error": error, "response_code": code }

    elif( 'delayed' == chapter_data["status"] ):
        error = 'Delayed chapter. Unable to download.'
        print ( error )
        return { "error": error, "response_code": code }

    else:
        url = f'{chapter_data["server"]}{chapter_data["hash"]}/'

        metadata = { 
            'url': url, 
            'hash': chapter_data['hash'],
            'server': chapter_data['server'],
            'volume': chapter_data['volume'],
            'chapter': chapter_data['chapter'],
            'title': chapter_data['title']
        }

        if 'serverFallback' in chapter_data:
            metadata['serverFallback'] = chapter_data['serverFallback']

        metadata['images'] = { 'success': [], 'failed': [] }

        # Get the groups
        groups = ', '.join( group['name'] for group in chapter_data['groups'] )
        groups = re_regrex.sub( '_', html.unescape( groups ) )

        # Volume naming
        volume = ''

        if ( '' != chapter_data['volume'] ):
            v = int( chapter_data['volume'] )
            volume = f'(v0{v}) ' if ( v < 10 ) else f'(v{v}) '

        # Chapter naming
        chapter = '000'

        if ( '' != chapter_data['chapter'] ):

            chapter_values = chapter_data['chapter'].split('.')

            c = int(chapter_values[0])

            if ( c < 10 ):
                chapter = f'c00{c}'
            elif ( c >= 10 and c < 100 ):
                chapter = f'c0{c}'
            elif ( c >= 100 and c < 999 ):
                chapter = f'c{c}'
            else:
                chapter = f'd{c}'

            if ( len( chapter_values ) > 1):
                for part in chapter_values[1:]:
                    chapter += '.' + part

        # Chapter name
        chapter_name = '[Oneshot]' if ( '' == chapter_data['volume'] and '' == chapter_data['chapter'] and '' == chapter_data['title'] ) else ( f'[{chapter_data["title"]}] ' if '' != chapter_data['title'] else '' )

        # Manga Title
        title = title if ( '' != title ) else re_regrex.sub( '_', html.unescape( chapter_data['mangaTitle'] ) )

        # Language
        language = chapter_data['language']

        #Follows Daiz's naming scheme. (Or at least tries to)
        folder = f'{directory}/{title}/{title} [{language}] - {chapter} {volume}{chapter_name}[{groups}]'
        
        global Last_Downloaded_dir
        global folderglobalname
        Last_Downloaded_dir = folder
        folderglobalname = os.path.join(directory, title)
        images = chapter_data['pages']
        resume = 0

        # Check if folder exists. If it does, check if the json for the chapter exists and download failed images. If no failed images, skip it.
        if ( createFolder(folder) ):

            # If title, check the chapter_json sent to function
            if ( type ):

                # Duplicated chapter
                if not chapter_json:
                    folder = f'{folder}[DUPLICATE]'
                    createFolder(folder)
                else:
                    images = chapter_json['images']['failed'] if ( len( chapter_json['images']['failed'] ) > 0 ) else []
                    resume = 1
            else:
                #If chapter, search for the chapter json file
                chapter_json = f'{folder}/{id}.json'

                if( os.path.exists( chapter_json ) ):
                    with open(chapter_json, 'r') as json_file:
                        chapter_json = json.load(json_file)

                    images = chapter_json['images']['failed'] if ( len( chapter_json['images']['failed'] ) > 0 ) else []
                    resume = 1

        if ( len( images ) > 0 ):

            print ( f'Downloading Volume {volume}Chapter {chapter} - Title: {chapter_name}' )

            # Images Download Tasks
            loop  = asyncio.get_event_loop()
            tasks = []

            for image in images:
                task = asyncio.ensure_future( imageDownloader( image, url, folder ) )
                tasks.append(task)

            runner = progressDisplay(tasks)
            loop.run_until_complete(runner)

            # Get the responses back
            for t in tasks:
                result = t.result()
                metadata['images'][ result['status'] ].append( result['image'] )

            if ( type ):
                return metadata
            else:
                #Update chapter metadata
                if ( resume ):
                    chapter_json['images']['success'].extend( metadata['images']['success'] )
                    chapter_json['images']['failed'] = metadata['images']['failed']

                    metadata = chapter_json

                with open( os.path.join( folder, f'{id}.json' ), 'w') as file:
                    json.dump( metadata, file, indent=4, ensure_ascii=False )

def titleDownloader(id, directory, language, data = []):

    if not data:
        # Connect to API and get manga info
        url = f'{domain}/api/v2/manga/{id}?include=chapters'

        response = requests.get( url, headers = headers)

        if ( response.status_code != 200 ):
            print( f'Title {id}. Request status error: {response.status_code}. Skipping...' )
            return;

        data = response.json()

    data = data['data']

    if is_4Koma(data['manga']["tags"]) :
        print('Okay!')
    else :
        print('Not 4 Koma!')
        sys.exit('Please load 4 Koma Only!')

    title = re_regrex.sub( '_', html.unescape( data['manga']['title'] ) )

    print(title)

    if 'chapters' not in data:
        print( f'Title {id} - {title} has no chapters. Skipping...' )
        return

    print( f'{"-"*69}\nDownloading Title: {title}\n{"-"*69}' )
    
    global Manga_Title
    Manga_Title = title
    
    #make folder to outptu MaKo Crops
    create_folder_per_titile()

    json_data = { 'id': id, 'title': title }
    json_data['chapters'] = {}

    # Check if the title json file exists
    title_json = os.path.join( directory, title, f'{id}.json' )

    if( os.path.exists( title_json ) ):
        with open(title_json, 'r') as json_file:
            json_data = json.load(json_file)

    # Flag for checking if at least one chapter was downloaded
    downloaded = False

    print(len(data['chapters']))

    # Loop chapters
    for chapter in data['chapters']:
        # Only chapters of language selected. Default language: English.
        #naah download every fucking thing we can get
        if ( True ):

            downloaded = True

            #List will not accept an int as index
            chapter_id = str( chapter['id'] )

            # Check if chapter id exists
            if ( chapter_id in json_data['chapters'] ):

                #Check if it has no error logged. If error, download the whole chapter
                if ( 'error' in json_data['chapters'][ chapter_id ] ):
                    json_data['chapters'][ chapter_id ] = chapterDownloader( chapter['id'], directory, title )
                else:
                    # Check if it has failed images
                    if ( len( json_data['chapters'][ chapter_id ]['images']['failed'] ) > 0 ):

                        chapter_response = chapterDownloader( chapter['id'], directory, title, json_data['chapters'][ chapter_id ] )

                        #Update success and failed images
                        json_data['chapters'][ chapter_id ]['images']['success'].extend( chapter_response['images']['success'] )
                        json_data['chapters'][ chapter_id ]['images']['failed'] = chapter_response['images']['failed']
            else:
                json_data['chapters'][ chapter_id ] = chapterDownloader( chapter['id'], directory, title )
            
            #here for removing all of its hard work uwu

            ##load the dir
            #print(Last_Downloaded_dir)
            if os.path.isdir(Last_Downloaded_dir) : 
                #there should be no possiblity that it the folder does not exist now right ?

                New_path_root_list = os.path.split(Last_Downloaded_dir)
                NewPath_root = New_path_root_list[0]
                NewPath = os.path.join(NewPath_root, 'Processed')
                
                os.rename(Last_Downloaded_dir, NewPath)

                #MaKo
                Mako_Processor(NewPath, chapter['language'], chapter_id)

                #delete folder
                folder_deletor(NewPath)

    if ( downloaded ):
        # Create or Update json
        with open( os.path.join( directory, title, f'{id}.json' ) , 'w') as file:
            json.dump( json_data, file, indent=4, ensure_ascii=False )
    else:
        print( 'No chapters found in the selected language.' )

def fileDownloader(filename, directory, language):

    titles = []

    if( os.path.exists(filename) ):

        # Open file and read lines
        with open(filename, 'r') as item:
            titles = [ line.rstrip('\n') for line in item ]

        if( len(titles) == 0 ):
            sys.exit('Empty file!')
        else:
            print ( banner )

            for id in titles:
                titleDownloader( id, directory, language )
                print( 'Download Complete. Waiting 15 seconds...' )
                time.sleep(15)
    else:
        sys.exit('File not found!')


if __name__ == "__main__":
    print('THIS IS not quite BOCCHI MD DOWLOADER !!!')
    print('NO ARGS NEEDED !!!!!')
    parser = argparse.ArgumentParser()



    parser.add_argument('--language',  '-l', default='gb')         # Chapters language to download
    parser.add_argument('--directory', '-d', default='downloads/') # Directory to download the files
    parser.add_argument('--type',      '-t', default='title')      # Type of download. Can be title or chapter. This is used when not downloading from list. Planned downloading from Groups and Users.
    #parser.add_argument('id')                                      # Title or Chapter ID

    args = parser.parse_args()

    if ( True ):
        print ( banner )
        
        manga_id_plz = get_manga_id()
        #do stuff with getting newest ID
        
        set_manga_proc(manga_id_plz)

        titleDownloader( manga_id_plz, args.directory, args.language )
        #delte the title folder
        folder_deletor(folderglobalname)

        set_manga_fin(manga_id_plz)

        print('Done.....')

        #set the ID

    else:
        sys.exit('Invalid options.')
