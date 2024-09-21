import requests, csv, json, os, pathlib, base64, time
import os.path
from imagedominantcolor import DominantColor
from PIL import Image, ImageDraw, ImageFont

# Spotify Library Cards

#auth
# return : access_token
def auth():
    logins = []
    with open('login.csv', newline='') as login_list :
        print(login_list)
        login_reader = csv.reader(login_list, delimiter='\n')
    for login in login_reader :
        logins.append(login[0])

    client_id = logins[0]
    client_secret = logins[1]
    basicAuth = base64.standard_b64encode((client_id+':'+client_secret).encode('ascii')).decode('ascii')
    #get access token
    url = "https://accounts.spotify.com/api/token"

    with open('token.csv', newline='') as tokens_list :
        token_reader = csv.reader(tokens_list, delimiter='\n')
    for token in token_reader :
        refresh_token = token[0]

    #print(refresh_token)

    refresh_payload=f'grant_type=refresh_token&refresh_token={refresh_token}'
    refresh_headers = {
    'Authorization': f'Basic {basicAuth}',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': '__Host-device_id=AQCh8qnCYhmcJnOLb6x0aprMHa9W0lOcemXzMgKYeyxrV7oN6Fg-6dUpYdId7Do9QM1xrmvZNmf14KeOXH_84ONt4xiQTmKku3A'
    }
    auth_response = requests.request("POST", url, headers=refresh_headers, data=refresh_payload)

    #print(auth_response.text)
    if auth_response.status_code == 200 :
        access_token = json.loads(auth_response.text)["access_token"]
    #print(access_token)
    else :
        print('--------------ERROR----------------')
        print(auth_response.content)

    return access_token

####Toolbox######
def getXAlignement(length):
    return int(((354/2)-(length/2)))

def getMaxLenght(txt,fontname,fontsize,image):
    #print("\n### longueur du texte : ")
    #print(int(image.textlength(txt, ImageFont.truetype(fontname, fontsize))))
    if image.textlength(txt, ImageFont.truetype(fontname, fontsize)) > 314 :
        return getMaxLenght(txt,fontname,fontsize-1,image)
    else :
        return fontsize
   

### Spotify Library Cards ###

def generateCardsFromLibrary(debug, access_token,url):
    #get folder path
    data_folder = pathlib.Path("pochettes")
    cartes_folder = pathlib.Path("cartes")
    #auth
    bearer = 'Bearer {}'
    headers = {
        'Authorization': bearer.format(access_token)
    }
    #request to get user saved albums
    payload={}
    spotify_request = json.loads(requests.request("GET", url, headers=headers, data=payload).text)
    next_url = None
    if not debug:
        next_url = spotify_request['next']
    else :
        print("debug :\n")
        print("url next : "+spotify_request['next'])
    #Cards creation
    for album in spotify_request['items'] :
        #var
        title_fontsize = 28
        title_font_name = "fonts/NotoSansJP-SemiBold.ttf"
        artist_fontsize = 22
        artist_font_name = "fonts/NotoSansJP-Light.ttf"
        #album data
        album_id = album['album']['id']
        album_uri = album['album']['uri']
        album_artist = album['album']['artists'][0]['name']
        album_name = album['album']['name']
        album_cover_url = album['album']['images'][0]['url']
        album_release_date = album['album']['release_date']
        album_genre = album['album']['genres']
        if len(album_genre) > 0 : album_genre = album_genre[0]
        else : album_genre = None
        print(album_genre)
        if album_genre : print(album_artist+' '+album_name+' '+album_release_date+' '+album_genre+"\n")
        else : print(album_artist+' '+album_name+' '+album_release_date+' '+"None\n")
        cover = requests.get(album_cover_url, allow_redirects=True)
        open(data_folder / f'{album_id}.png', 'wb').write(cover.content)
        dominantcolor = DominantColor(data_folder / f'{album_id}.png')
        background_color = '{:02x}{:02x}{:02x}'.format(dominantcolor.r, dominantcolor.g, dominantcolor.b)
        spotify_code_url = f'https://scannables.scdn.co/uri/plain/png/{background_color}/white/640/{album_uri}'
        spotify_code = requests.get(spotify_code_url)
        open(data_folder / f'{album_id}-code.png', 'wb').write(spotify_code.content)
        #create card
        spotify_card = Image.new('RGB',(354,531),(dominantcolor.r, dominantcolor.g, dominantcolor.b))
        #add cover + code
        savedCover = Image.open(data_folder / f'{album_id}.png').resize((314,314))
        savedCode = Image.open(data_folder / f'{album_id}-code.png').resize((314,74))
        spotify_card.paste(savedCover,(getXAlignement(314),20))
        spotify_card.paste(savedCode,(getXAlignement(314),338))
        #convert image to draw
        spotify_card_draw = ImageDraw.Draw(spotify_card)
        #add description zone
        spotify_card_draw.rectangle([(0, 416), (354, 531)],fill='white')
        #get font size
        title_fontsize = getMaxLenght(album_name,title_font_name,title_fontsize,spotify_card_draw)
        artist_fontsize = getMaxLenght(album_name,artist_font_name,artist_fontsize,spotify_card_draw)
        # create font
        title_font = ImageFont.truetype(title_font_name, title_fontsize)
        artist_font = ImageFont.truetype(artist_font_name, artist_fontsize)
        # draw text
        spotify_card_draw.text((177,470),album_name,font=title_font,fill="black",anchor="mb",align="center")
        spotify_card_draw.text((177,502),album_artist+' - '+album_release_date[:4],font=artist_font,fill="black",anchor="mb",align="center")
        #save card
        if album['album']['album_type'] == 'album' :
            spotify_card.save(cartes_folder / f'albums/{album_id}-card.png')
        else :
            spotify_card.save(cartes_folder / f'singles/{album_id}-card.png')
        time.sleep(1)
    if next_url is not None :
        print('############ -> page suitante : '+next_url)
        time.sleep(10)
        getLibraryCovers(debug,access_token,next_url)

def generateCardsFromSogList(debug, access_token):
    songsList = []

    #repo folders
    data_folder = pathlib.Path("pochettes")
    cartes_folder = pathlib.Path("cartes")

    #api attributs
    search_url = "https://api.spotify.com/v1/search?q={}&type=album&include_external=audio"
    album_url = "https://api.spotify.com/v1/albums/{}"
    payload={}

    with open('songsList.csv', newline='') as songs_csv :
        song_to_get = csv.reader(songs_csv, delimiter=',')
        for song in song_to_get :
            bearer = 'Bearer {}'
            headers = {
                'Authorization': bearer.format(access_token)
            }
            nom_song = song[0]
            print("Recherche : "+nom_song)
            try :
                trackId = int(song[1])-1
            except IndexError as error :
                trackId = 0
            #Request Spotify API
            search_data = requests.request("GET", search_url.format(nom_song), headers=headers, data=payload)
            songsList.append(json.loads(search_data.text)['albums']['items'][0])

    if debug :
        print(songsList)
    
    #Cards creation
    for album in songsList :
        #var
        title_fontsize = 28
        title_font_name = "fonts/NotoSansJP-SemiBold.ttf"
        artist_fontsize = 22
        artist_font_name = "fonts/NotoSansJP-Light.ttf"
        #album data
        album_id = album['id']
        album_uri = album['uri']
        album_artist = album['artists'][0]['name']
        album_name = album['name']
        album_cover_url = album['images'][0]['url']
        album_release_date = album['release_date']
        #album cover
        cover = requests.get(album_cover_url, allow_redirects=True)
        open(data_folder / f'{album_id}.png', 'wb').write(cover.content)
        dominantcolor = DominantColor(data_folder / f'{album_id}.png')
        background_color = '{:02x}{:02x}{:02x}'.format(dominantcolor.r, dominantcolor.g, dominantcolor.b)
        spotify_code_url = f'https://scannables.scdn.co/uri/plain/png/{background_color}/white/640/{album_uri}'
        spotify_code = requests.get(spotify_code_url)
        open(data_folder / f'{album_id}-code.png', 'wb').write(spotify_code.content)
        #create card
        spotify_card = Image.new('RGB',(354,531),(dominantcolor.r, dominantcolor.g, dominantcolor.b))
        #add cover + code
        savedCover = Image.open(data_folder / f'{album_id}.png').resize((314,314))
        savedCode = Image.open(data_folder / f'{album_id}-code.png').resize((314,74))
        spotify_card.paste(savedCover,(getXAlignement(314),20))
        spotify_card.paste(savedCode,(getXAlignement(314),338))
        #convert image to draw
        spotify_card_draw = ImageDraw.Draw(spotify_card)
        #add description zone
        spotify_card_draw.rectangle([(0, 416), (354, 531)],fill='white')
        #get font size
        title_fontsize = getMaxLenght(album_name,title_font_name,title_fontsize,spotify_card_draw)
        artist_fontsize = getMaxLenght(album_name,artist_font_name,artist_fontsize,spotify_card_draw)
        # create font
        title_font = ImageFont.truetype(title_font_name, title_fontsize)
        artist_font = ImageFont.truetype(artist_font_name, artist_fontsize)
        # draw text
        spotify_card_draw.text((177,470),album_name,font=title_font,fill="black",anchor="mb",align="center")
        spotify_card_draw.text((177,502),album_artist+' - '+album_release_date[:4],font=artist_font,fill="black",anchor="mb",align="center")
        #save card
        spotify_card.save(cartes_folder / f'songs listed/{album_id}-card.png')
        time.sleep(1)


################################################################################

#authentification#####
logins = []

with open('login.csv', newline='') as login_list :
  login_reader = csv.reader(login_list, delimiter='\n')
  for login in login_reader :
    logins.append(login[0])

client_id = logins[0]
client_secret = logins[1]
basicAuth = base64.standard_b64encode((client_id+':'+client_secret).encode('ascii')).decode('ascii')

#get access token
url = "https://accounts.spotify.com/api/token"


with open('token.csv', newline='') as tokens_list :
  token_reader = csv.reader(tokens_list, delimiter='\n')
  for token in token_reader :
    refresh_token = token[0]

#print(refresh_token)

refresh_payload=f'grant_type=refresh_token&refresh_token={refresh_token}'
refresh_headers = {
  'Authorization': f'Basic {basicAuth}',
  'Content-Type': 'application/x-www-form-urlencoded',
  'Cookie': '__Host-device_id=AQCh8qnCYhmcJnOLb6x0aprMHa9W0lOcemXzMgKYeyxrV7oN6Fg-6dUpYdId7Do9QM1xrmvZNmf14KeOXH_84ONt4xiQTmKku3A'
}
auth_response = requests.request("POST", url, headers=refresh_headers, data=refresh_payload)

#print(auth_response.text)
if auth_response.status_code == 200 :
  access_token = json.loads(auth_response.text)["access_token"]
  #print(access_token)
else :
  print('--------------ERROR----------------')
  print(auth_response.content)


##########################################################################
###########    EXECUTION    #################
debug = False
generateCardsFromSogList(debug, access_token)
