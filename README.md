imgurbox
========

imgurbox is a python script that syncs pictures to your Imgur account. It is designed to be used with multiple folders, each one representing an Imgur album. Any change you make will be updated as soon as the script runs, creating a system similar to Dropbox, which is useful for backup, sharing, etc.

![imgurbox screenshot](http://i.imgur.com/adjvGAX.png)

The script detects the following changes:
* New file in directory -> upload it to the associated album
* Deleted file -> delete it from Imgur
* File moved from one directory to another -> move the uploaded image accordingly
* Changed the contents of a file -> delete the old version from Imgur and upload the new one

However, the script is not a complete replacement for Dropbox:
* Because the script uses filenames to identify images, having multiple files with the same name (in different directories) could lead to confusion in certain scenarios. For example, if you delete the picture "pic1.jpg" from one folder, and add a different picture with the same name "pic1.jpg" to another folder, imgurbox will think you only moved "pic1.jpg" from one folder to another.
* Also note that imgurbox tracks only changes made locally — if you delete an image in Imgur the script will not delete the corresponding file (but will, in fact, reupload the image again).
* Finally, you should be aware that Imgur [deletes images](http://imgur.com/faq#long) if they haven't been viewed for 6 months. If that happens imgurbox will reupload them, but this can be worked around by sharing your images with others (so they contribute views) or downloading a complete copy of your albums every 6 months.


Installation and usage
-----------------------
1. (You need to have [Python](https://www.python.org/download), [imgurpython](https://github.com/Imgur/imgurpython) installed on your computer), and [colorama](https://pypi.python.org/pypi/colorama)
2. Download [imgurbox.py](https://github.com/Winterstark/imgurbox/blob/master/imgurbox.py)
3. Create a new text file "albums.txt" in imgurbox.py's directory and enter a list of directories that you want to sync (one directory path per line). You can also add existing Imgur albums that you want to download to your computer (one album ID per line).
4. Run imgurbox.py
5. The first time you run the script you will be prompted to give it authorization to access your Imgur account. A page will be opened in your browser; click "Allow" and use the given PIN in imgurbox.

You could set imgurbox.py to run regularly (when your OS starts, for example), or just run it whenever you want to sync your images.

Remember that you can edit "albums.txt" at any time:
* Adding a directory path will upload its contents to a new Imgur album
* Adding an existing Imgur album ID will download it to your computer

In case of any problems check the file "log.txt" to see what operations the script has done.


drivebox
----------

![drivebox screenshot](http://i.imgur.com/DJOwWDj.png)

drivebox.py is basically imgurbox.py using Google Drive instead of Imgur. The advantages of this are:
* Images will not be downgraded in quality if they are too large
* You can backup any type of file, not just images
* Folder hierarchy is preserved
* The files won't be automatically deleted after 6 months
* Google Drive can keep track of older versions of files (but not files older than 30 days)

The script is used in the same way as imgurbox.py, except that you need to install [Google Drive API Client Library for Python](https://developers.google.com/api-client-library/python/start/installation) first, and then add your files and folder paths to "paths.txt" (NOT "albums.txt"). If you want a file or folder to keep track of different file versions, add an asterisk '*' at the beginning of the path.

drivebox has two alternate modes of running which are selected with command line arguments:
* /r repairs index.txt (rebuilds it by listing all of the files uploaded to Google Drive; useful if index.txt got deleted or damaged)
* /u removes unused files on Google Drive (these files can be left behind if the script crashes after it deletes files from the index but before it updates Google Drive; these files don't have to be deleted, but they do take up space)


APIs used
----------

* [imgurpython](https://github.com/Imgur/imgurpython)
* [Google Drive API Client Library for Python](https://developers.google.com/api-client-library/python/start/installation)
* [colorama](https://pypi.python.org/pypi/colorama)