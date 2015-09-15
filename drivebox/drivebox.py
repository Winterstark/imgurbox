import os, sys, traceback, httplib2, ast
from datetime import datetime

from apiclient import discovery, http
from apiclient.http import MediaFileUpload
import oauth2client
from oauth2client import client, tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = "https://www.googleapis.com/auth/drive.file"
CLIENT_SECRET_FILE = "client_secret.json"
APPLICATION_NAME = "drivebox"


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser("~")
    credential_dir = os.path.join(home_dir, ".credentials")
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, "drive-quickstart.json")

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print("Storing credentials to " + credential_path)
    return credentials


def createFolder(service, title, parentID=None):
    body = {
      "title": title,
      "mimeType": "application/vnd.google-apps.folder"
    }

    if parentID:
        body["parents"] = [{"id": parentID}]

    root_folder = service.files().insert(body = body).execute()
    log_msg("Created new folder: " + title + " (ID: " + root_folder["id"] + ")")

    return root_folder["id"]


def getMimeType(path):
    MIME_TYPES = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
        ".potx": "application/vnd.openxmlformats-officedocument.presentationml.template",
        ".ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".sldx": "application/vnd.openxmlformats-officedocument.presentationml.slide",
        ".dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
        ".xlam": "application/vnd.ms-excel.addin.macroEnabled.12",
        ".xlsb": "application/vnd.ms-excel.sheet.binary.macroEnabled.12"
    }
    extension = os.path.splitext(path)[1].replace(".", "")

    if extension in MIME_TYPES:
        return MIME_TYPES[extension]
    else:
        return "file/" + extension


def uploadFile(service, parentID, path):
    log_msg("Uploading file: " + path + ". Progress: ", "")

    media_body = MediaFileUpload(path, resumable=True)
    if '"_mimetype": null' in media_body.to_json(): #unrecognized mimetype: set it manually
        media_body = MediaFileUpload(path, mimetype=getMimeType(path), resumable=True)

    body = {"title": os.path.basename(path)}
    if parentID: #set the parent folder
        body["parents"] = [{"id": parentID}]

    request = service.files().insert(media_body=media_body, body=body)

    while True:
        status, done = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            if progress < 100:
                log_msg("%d%%" % progress, " ... ")
        if done:
            id = request.execute()["id"]
            log_msg("100% Done! ID: " + id)
            return id


def updateFile(service, fileID, path, createRevision):
    log_msg("Updating file: " + path + ". Progress: ", "")

    file = service.files().get(fileId=fileID).execute()
    media_body = MediaFileUpload(path, resumable=True)
    if '"_mimetype": null' in media_body.to_json(): #unrecognized mimetype: set it manually
        media_body = MediaFileUpload(path, mimetype=getMimeType(path), resumable=True)

    request = service.files().update(fileId=fileID, body=file, newRevision=createRevision, media_body=media_body)

    while True:
        status, done = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            if progress < 100:
                log_msg("%d%%" % progress, " ... ")
        if done:
            log_msg("100% Done!")
            return


#also works for folders
def deleteFile(service, fileID, path):
    service.files().delete(fileId=fileID).execute()


def downloadFile(service, fileID, path):
    log_msg("Restoring file: " + path + " (ID: " + fileID + "). Progress: ", "")

    with open(path, "wb") as f:
        request = service.files().get_media(fileId=fileID)
        media_request = http.MediaIoBaseDownload(f, request)

        while True:
            status, done = media_request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                log_msg("%d%%" % progress, "")
                if progress < 100:
                    log_msg(" ... ", "")
            if done:
                log_msg("DONE!")
                return


def downloadFolder(service, folderID, path):
    os.makedirs(path)
    log_msg("Restored folder " + path + " (ID: " + folderID + ")")
    
    files = service.files().list(maxResults=1000, q="'" + folderID + "' in parents and mimeType!='application/vnd.google-apps.folder'").execute().get('items', [])
    for file in files:
        downloadFile(service, file["id"], path + os.sep + file["title"])

    folders = service.files().list(maxResults=1000, q="'" + folderID + "' in parents and mimeType='application/vnd.google-apps.folder'").execute().get('items', [])
    for folder in folders:
        downloadFolder(service, folder["id"], path + os.sep + folder["title"])


#also works for folders
def addFile(service, path, parentFolder, manageRevisions=False):
    manageRevisions = manageRevisions or parentFolder["revs"] #if it's not explicitly set to True, use the parent folder's value

    if os.path.isfile(path): #file
        parentFolder["contents"][path] = {"id": uploadFile(service, parentFolder["id"], path), "size": str(os.path.getsize(path)), "revs": manageRevisions}
    elif os.path.isdir(path): #folder
        path = os.path.normpath(path) #just in case the path has a redundant '\' at the end
        folderID = createFolder(service, os.path.basename(path), parentFolder["id"])

        parentFolder["contents"][path] = {"id": folderID, "contents": {}, "revs": manageRevisions}
        checkForChanges(service, path, parentFolder["contents"][path])


#works for files and folders
def checkForChanges(service, path, file):
    if os.path.exists(path):
        if "size" in file: #file
            currentFilesize = str(os.path.getsize(path))

            if currentFilesize == file["size"]:
                pass #file is already synced
            else:
                #file has changed: upload new version
                updateFile(service, file["id"], path, file["revs"])
                file["size"] = currentFilesize
        else: #folder
            #check if previously-indexed files have been changed or deleted
            for subFile in file["contents"]:
                checkForChanges(service, subFile, file["contents"][subFile])

            #check for new files
            currentFiles = [path + os.sep + filename for filename in os.listdir(path)]

            for subFilePath in currentFiles:
                if subFilePath not in file["contents"]:
                    addFile(service, subFilePath, file)
    else:
        print(path + " has been deleted.\n1. Restore it using the synced version on Google Drive\n2. Delete the synced version on Google Drive as well (PERMANENT)\n3. Do nothing")
        choice = input("What would you like to do? (1/2/3) ")

        if len(choice) > 0:
            if choice[0] == "1":
                if "size" in file: #file
                    downloadFile(service, file["id"], path)
                    file["size"] = str(os.path.getsize(path))
                else: #folder
                    downloadFolder(service, file["id"], path)
            elif choice[0] == "2":
                log_msg("Deleting synced version of " + path + " (ID: " + file["id"] + ")... ", "")
                deleteFile(service, file["id"], path)
                log_msg("DONE!")

                file["id"] = "DEL ME PLS"
            else:
                pass #do nothing


def removeDeletedFiles(folder):
    toDel = []

    for path, file in folder["contents"].items():
        if file["id"] == "DEL ME PLS":
            toDel.append(path)
        elif "contents" in file: #subfolder
            removeDeletedFiles(file)

    for path in toDel:
        del folder["contents"][path]

    return toDel


def log_msg(msg, newline="\n"):
    global log
    log += msg + newline

    print(msg, end=newline)
    sys.stdout.flush()


def main():
    global index #index is global because in the event of a crash, save_data() will still be able to access it and save any successfully-executed changes

    #init service
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("drive", "v2", http=http)

    #load previous file index
    if os.path.isfile("index.txt"):
        print("Loading previous file index")
        with open("index.txt") as f:
            fileContents = f.read()
            if fileContents != "":
                index = ast.literal_eval(fileContents)
            else:
                index = {"id": "", "contents": {}, "revs": False}
    else: #init file index
        index = {"id": "", "contents": {}, "revs": False}

    if index["id"] == "":
        #check if drivebox folder exists
        results = service.files().list(maxResults=10, q="mimeType = 'application/vnd.google-apps.folder'").execute()
        items = results.get("items", [])

        for item in items:
            if item["title"] == "drivebox":
                index["id"] = item["id"]
                break

        if index["id"] == "": #create new drivebox folder
            index["id"] = createFolder(service, "drivebox")

    if index["id"] == "":
        log_msg("Unable to find or create drivebox folder on Google Drive.")
    else:
        for path, file in index["contents"].items():
            checkForChanges(service, path, file)

        removedPaths = removeDeletedFiles(index) #cleanup any deleted files from the index
        
        #check for new files/folders
        currentPaths = []
        revs = [] #list of paths that use manageRevisions
        updatePaths = False

        if os.path.isfile("paths.txt"):
            lines = [line.rstrip("\n") for line in open("paths.txt")]

            for line in lines:
                line = line.strip().replace('"', '')
                if "*" in line:
                    line = line.replace("*", "")
                    revs.append(line)
                    manageRevisions = True
                else:
                    manageRevisions = False

                currentPaths.append(line)

                if line not in index["contents"]:
                    if os.path.exists(line):
                        addFile(service, line, index, manageRevisions)
                    elif line in removedPaths:
                        currentPaths.remove(line)
                        updatePaths = True
                    else:
                        log_msg("path.txt contains a non-existent path: " + line)

            if updatePaths:
                with open("paths.txt", "w") as f:
                    for path in currentPaths:
                        if path in revs:
                            f.write("*" + path + "\n")
                        else:
                            f.write(path + "\n")
        elif index["contents"] == {}:
            #first time running with no paths: sync imgur albums to disk
            log_msg("paths.txt not found or empty!")
            print("Create a file \"paths.txt\" with a list of file and folder paths that you want to sync to Google Drive.")
            input("Press Enter to exit...")

        #check for removed paths
        toDel = []

        for path, file in index["contents"].items():
            if path not in currentPaths:
                log_msg(path + " has been removed from paths.txt. Deleting synced version (ID: " + file["id"] + ")... ", "")
                deleteFile(service, file["id"], path)
                log_msg("DONE!")
                toDel.append(path)
        
        for path in toDel:
            del index["contents"][path]


def save_data():
    print("Saving changes")
    with open("index.txt", "w") as f:
        f.write(str(index))

    #update log
    with open("log.txt", "a") as f:
        f.write(log + "\n")


#START POINT (and Exception handling)
if __name__ != "__main__": #if this file was called from another python script set the current working directory to this one
    os.chdir(os.path.dirname(__file__))

try:
    log = "drivebox started @ " + str(datetime.now()) + "\n"
    main()
except:
    log_msg("Uh-oh: " + str(traceback.format_exception(*sys.exc_info())))
    print("Press Enter to exit...")
    input()
finally:
    save_data()