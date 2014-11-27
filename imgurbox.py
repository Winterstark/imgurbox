# imgurbox v1.0 (2014-10-13)
# https://github.com/Winterstark/imgurbox

import base64, webbrowser, sys
from os import path, listdir, makedirs, remove
from datetime import datetime
from urllib import request
from imgurpython import ImgurClient
from imgurpython.imgur.models.account import Account
from imgurpython.imgur.models.album import Album
from imgurpython.imgur.models.image import Image
from imgurpython.helpers.error import ImgurClientError


def get_authorization():
    #get authorization from user
    client = ImgurClient("a5d6a74712d69cc", "a7b83fe3bfdb6c21135c1f41f1d10de37638c5b3")

    webbrowser.open(client.get_auth_url("pin"))

    print("Before using imgurbox you need to authorize it to access you imgur account.")
    print("A page has been opened in your browser. Click \"Allow\" and then copy the PIN number.")
    pin = input("Enter authorization PIN here: ")

    credentials = client.authorize(pin, "pin")
    client.set_user_auth(credentials["access_token"], credentials["refresh_token"])

    #save credentials for next time
    log_msg("Received user authorization. Tokens: {0}:{1}".format(credentials["access_token"], credentials["refresh_token"]))

    with open("credentials.txt", "w") as f:
        f.write(credentials["access_token"] + "\n" + credentials["refresh_token"] + "\n")

    return client


def upload_from_path(self, path, config=None, anon=True):
    if not config: config = dict()

    fd = open(path, 'rb')
    contents = fd.read()
    b64 = base64.b64encode(contents)

    data = {
        'image': b64,
        'type': 'base64',
    }

    data.update({meta: config[meta] for meta in set(self.allowed_image_fields).intersection(config.keys())})
    return self.make_request('POST', 'upload', data, anon)


def create_album(self, fields):
    post_data = {field: fields[field] for field in set(self.allowed_album_fields).intersection(fields.keys())}

    if 'ids' in post_data:
        self.logged_in()

    return self.make_request('POST', 'album', data=post_data)


def get_account(self, username):
        self.validate_user_context(username)
        account_data = self.make_request('GET', 'account/%s' % username)

        return Account(
            account_data['id'],
            account_data['url'],
            account_data['bio'],
            account_data['reputation'],
            account_data['created'],
            account_data['pro_expiration'],
        )


def get_album(self, album_id):
    album = self.make_request('GET', 'album/%s' % album_id)
    return Album(album)


def get_album_images(self, album_id):
    images = self.make_request('GET', 'album/%s/images' % album_id)
    return [Image(image) for image in images]


def album_add_images(self, album_id, ids):
    if isinstance(ids, list):
        ids = ','.join(ids)

    return self.make_request('POST', 'album/%s/add' % album_id, {'ids': ids})


def album_remove_images(self, album_id, ids):
    if isinstance(ids, list):
        ids = ','.join(ids)

    return self.make_request('DELETE', 'album/%s/remove_images' % album_id, {'ids': ids})


def delete_image(self, image_id):
    return self.make_request('DELETE', 'image/%s' % image_id)


def get_image(self, image_id):
    image = self.make_request('GET', 'image/%s' % image_id)
    return Image(image)


def log_msg(msg):
    global log
    log += msg + "\n"

    print(msg)


#MAIN
log = "imgurbox started @ " + str(datetime.now()) + "\n"
allowedTypes = [".jpg", ".jpeg", ".gif", ".png", ".apng", ".tiff", ".bmp", ".pdf", ".xcf"]
index = {}

#init imgur client
if path.isfile("credentials.txt"):
    print("Initializing Imgur service...")
    with open("credentials.txt") as f:
        accessToken = f.readline().rstrip()
        refreshToken = f.readline().rstrip()
        client = ImgurClient("a5d6a74712d69cc", "a7b83fe3bfdb6c21135c1f41f1d10de37638c5b3", accessToken, refreshToken)

        #verify authorization
        try:
            get_account(client, "me")
        except ImgurClientError as err:
            log_msg("Error while initializing Imgur client:" + err.error_message)
            client = get_authorization()
else:
    client = get_authorization()

#load albums
newDirs = []

if path.isfile("albums.txt"):
    print("Loading albums list...")
    albums = {}

    with open("albums.txt") as f:
        for line in f:
            line = line.strip()
            if line != "" and (len(line) < 2 or line[:2] != "//"):
                if "->" in line:
                    delimit = line.index("->")
                    
                    albumDir = line[:delimit].strip()
                    albumId = line[delimit+2:].strip()

                    if "imgur.com/a/" in albumId:
                        lb = albumId.index("imgur.com/a/") + 12
                        albumId = albumId[lb:]

                    albums[albumDir] = albumId
                else:
                    #new album
                    if "imgur.com/a/" in line:
                        lb = line.index("imgur.com/a/") + 12
                        line = line[lb:]

                    if path.isdir(line):
                        log_msg("New directory: " + line)

                        #upload dir
                        name = path.basename(line)
                        album = create_album(client, {"title": name, "layout": "grid"})
                        files = listdir(line)
                        n = len(files)
                        index[line] = {}

                        for i in range(n):
                            filename = line + "\\" + path.basename(files[i])

                            if path.splitext(filename)[1] in allowedTypes:
                                log_msg("Uploading file {0}/{1}: {2}...".format(i+1, n, filename))
                                index[line][path.basename(filename)] = upload_from_path(client, filename, {"album": album["id"]}, False)["id"]
                            else:
                                log_msg("Can't upload {0} because Imgur doesn't support its file type.".format(filename))

                        albums[line] = album["id"]
                        newDirs.append(line)
                    else:
                        album = get_album(client, line)
                        log_msg("New album: " + album.title)

                        if not path.isdir(album.title):
                            makedirs(album.title)
                            index[album.title] = {}

                            #download album    
                            imgs = get_album_images(client, album.id)
                            n = len(imgs)

                            for i in range(n):
                                try:
                                    filename = imgs[i].name + imgs[i].link[imgs[i].link.rfind('.'):] #original filename + extension
                                except:
                                    filename = imgs[i].link[imgs[i].link.rfind('/')+1:] #imgur link

                                log_msg("Downloading image {0}/{1}: {2}...".format(i+1, n, filename))

                                with open(album.title + "\\" + filename, "b+w") as f:
                                    f.write(request.urlopen(imgs[i].link).read())

                                index[album.title][filename] = imgs[i].id

                        albums[album.title] = album.id
                        newDirs.append(album.title)
else:
    #first time running with no albums: sync imgur albums to disk
    log_msg("albums.txt not found!")
    print("Create a file \"albums.txt\" with a list of directory paths that you want to sync to Imgur (or Imgur album IDs that you want to sync to this computer).")
    print("Check the readme for more information.")
    input("Press Enter to exit...")
    sys.exit(0)

#modifiedDirs indicates which directory's index has changed and needs to be saved
modifiedDirs = {albumDir: False for albumDir, albumId in albums.items()}

for newDir in newDirs:
    modifiedDirs[newDir] = True

#load previous index (containing both filenames and imgur IDs)
if path.isdir("index"):
    print("Loading previous file index...")
    for file in listdir("index"):
        found = False

        with open("index\\" + file) as f:
            #find full directory path
            dirName = path.splitext(file)[0]

            for albumDir, albumId in albums.items():
                if path.basename(albumDir) == dirName:
                    dirPath = albumDir
                    found = True
                    break

            if found:
                index[dirPath] = {}
                for line in f.read().splitlines():
                    fields = line.replace("http://imgur.com/", "").split(" -> ")

                    if len(fields) == 3:
                        index[dirPath][fields[0]] = [fields[1], fields[2]]
                    else:
                        #index from previous version, is missing filesizes
                        filePath = dirPath + "\\" + fields[0]
                        modifiedDirs[dirPath] = True

                        if path.isfile(filePath):
                            index[dirPath][fields[0]] = [fields[1], str(path.getsize(filePath))]
                        else:
                            index[dirPath][fields[0]] = [fields[1], "-1"]

        if not found:
            if input(file + " is present in the old file index, but not the albums list. Enter 'y' to delete it from the file index: ").lower() == "y":
                remove("index\\" + file)
else:
    makedirs("index")

#build current file index
fileIndex = {}
print("Building current file index...")

for albumDir, albumId in albums.items():
    fileIndex[albumDir] = []

    for file in listdir(albumDir):
        if path.splitext(file)[1].lower() in allowedTypes:
            fileIndex[albumDir].append(file)

#get a list of removed files
removedFiles = []

for dir in index:
    for filename, imgData in index[dir].items():
        if filename not in fileIndex[dir]:
            removedFiles.append(dir + "\\" + filename)
            modifiedDirs[dir] = True

#get a list of new and modified files
newFiles = []
modifiedFiles = []

for dir in fileIndex:
    for file in fileIndex[dir]:
        filePath = dir + "\\" + file

        if file not in index[dir]:
            newFiles.append(filePath)
            modifiedDirs[dir] = True
        else:
            fileSize = str(path.getsize(filePath))

            if index[dir][file][1] != fileSize:
                modifiedFiles.append([filePath, fileSize])

#apply local changes to Imgur albums
if len(newFiles) + len(removedFiles) + len(modifiedFiles) == 0:
    if len(newDirs) == 0:
        print("No change.")
else:
    #check if files have been moved
    for removedFile in removedFiles[:]:
        movedTo = ""
        for newFile in newFiles:
            if path.basename(newFile) == path.basename(removedFile):
                movedTo = newFile
                break

        if movedTo != "":
            log_msg("File {0} moved to {1}. Updating image...".format(removedFile, movedTo))

            destDir = path.dirname(movedTo)
            srcDir = path.dirname(removedFile)
            filename = path.basename(removedFile)

            srcAlbumId = albums[srcDir]
            destAlbumId = albums[destDir]
            imgId = index[srcDir][filename][0]
            fileSize = index[srcDir][filename][1]
            
            #update Imgur
            album_remove_images(client, srcAlbumId, imgId)
            album_add_images(client, destAlbumId, imgId)

            #update index
            del index[srcDir][filename]
            index[destDir][filename] = [imgId, fileSize]

            removedFiles.remove(removedFile)
            newFiles.remove(movedTo)

    #upload new files
    for newFile in newFiles:
        log_msg("Uploading new file: {0}...".format(newFile))
        
        albumDir = path.dirname(newFile)
        filename = path.basename(newFile)

        imgId = upload_from_path(client, newFile, {"album": albums[albumDir]}, False)["id"]
        index[albumDir][filename] = [imgId, str(path.getsize(newFile))]

    #delete removed files
    for removedFile in removedFiles:
        log_msg("Deleting old file: {0}...".format(removedFile))
        
        albumDir = path.dirname(removedFile)
        filename = path.basename(removedFile)

        delete_image(client, index[albumDir][filename][0])
        del index[albumDir][filename]

    #replace modified files
    for modifiedFile, fileSize in modifiedFiles:
        log_msg("File {0} has changed. Uploading new version...".format(modifiedFile))

        albumDir = path.dirname(modifiedFile)
        filename = path.basename(modifiedFile)

        delete_image(client, index[albumDir][filename][0])

        newImgId = upload_from_path(client, modifiedFile, {"album": albums[albumDir]}, False)["id"]
        index[albumDir][filename] = [newImgId, fileSize]
        modifiedDirs[albumDir] = True

#save data
print("Saving albums and file index...")

with open("albums.txt", "w") as f:
    for albumDir, albumId in albums.items():
        f.write("{0} -> http://imgur.com/a/{1}\n".format(albumDir, albumId))

#save index
for dir, modified in modifiedDirs.items():
    if modified:
        with open("index\\" + path.basename(dir) + ".txt", "w") as f:
            for filename, imgData in index[dir].items():
                f.write("{0} -> http://imgur.com/{1} -> {2}\n".format(filename, imgData[0], imgData[1]))

#update log
with open("log.txt", "a") as f:
    f.write(log + "\n")