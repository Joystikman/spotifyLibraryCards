import requests, csv, json, os, pathlib, base64
import os.path
from imagedominantcolor import DominantColor

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

def getLibraryCovers(debug, access_token):
    #get folder path
    data_folder = pathlib.Path("pochettes")

    #request url
    next_url = "https://api.spotify.com/v1/me/albums?limit=10&offset=0"

    #auth
    bearer = 'Bearer {}'
    headers = {
        'Authorization': bearer.format(access_token)
    }

    #request to get user saved albums
    payload={}
    spotify_request = json.loads(requests.request("GET", next_url, headers=headers, data=payload).text)

    if not debug:
        next_url = spotify_request['next']
    else :
        print("debug :\n")
        print("url next : "+spotify_request['next'])

    for album in spotify_request['items'] :
        album_id = album['album']['id']
        album_uri = album['album']['uri']
        album_artist = album['album']['artists'][0]['name']
        album_name = album['album']['name']
        album_cover_url = album['album']['images'][0]['url']
        album_release_date = album['album']['release_date']
        print(album_artist+' '+album_name+' '+album_release_date+"\n")
        cover = requests.get(album_cover_url, allow_redirects=True)
        open(data_folder / f'{album_id}.png', 'wb').write(cover.content)
        dominantcolor = DominantColor(data_folder / f'{album_id}.png')
        background_color = '{:02x}{:02x}{:02x}'.format(dominantcolor.r, dominantcolor.g, dominantcolor.b)
        spotify_code_url = f'https://scannables.scdn.co/uri/plain/png/{background_color}/white/640/{album_uri}'
        print('\n'+spotify_code_url)
        spotify_code = requests.get(spotify_code_url)
        open(data_folder / f'{album_id}-code.png', 'wb').write(spotify_code.content)


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
debug = True

getLibraryCovers(debug,access_token)