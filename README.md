imgurbox
========

imgurbox is a python script that syncs pictures to your Imgur account. It is designed to be used with multiple folders, each one representing an Imgur album. Any change you make will be updated as soon as the script runs, creating a system similar to Dropbox, which is useful for backup, sharing, etc.

The script detects the following changes:
* New file in directory -> upload it to the associated album
* Deleted file -> delete it from Imgur
* File moved from one directory to another -> move the uploaded image accordingly

However, the script is not a complete replacement for Dropbox:
* Because the script uses filenames to identify images, having multiple files with the same name (in different directories) could lead to confusion in certain scenarios. For example, if you delete the picture "pic1.jpg" from one folder, and add a different picture with the same name "pic1.jpg" to another folder, imgurbox will think you only moved "pic1.jpg" from one folder to another.
* This also means the script doesn't detect changes made to the images themselves (any edits made to their content).
* Also note that imgurbox tracks only changes made locally — if you delete an image in Imgur the script will not delete the corresponding file (but will, in fact, reupload the image again).
* Finally, you should be aware that Imgur [deletes images](http://imgur.com/faq#long) if they haven't been viewed for 6 months. If that happens imgurbox will reupload them, but this can be worked around by sharing your images with others or downloading a complete copy of your albums every 6 months.


Installation and usage
-----------------------
1. (You need to have [Python](https://www.python.org/download) installed on your computer)
2. Download [imgurbox.py](https://github.com/Winterstark/imgurbox/blob/master/imgurbox.py)
3. Create a new text file "albums.txt" in imgurbox.py's directory and enter a list of directories that you want to sync (one directory path per line). You can also add existing Imgur albums that you want to download to your computer (one album ID per line).
4. Run imgurbox.py
5. The first time you run the script you will be prompted to give it authorization to access your Imgur account. A page will be opened in your browser; click "Allow" and use the given PIN in imgurbox.

You could set imgurbox.py to run regularly (when your OS starts, for example), or just run it whenever you want to sync your images.

Remember that you can edit "albums.txt" at any time:
* Adding a directory path will upload its contents to a new Imgur album
* Adding an existing Imgur album ID will download it to your computer

In case of any problems check the file "log.txt" to see what operations the script has done.


APIs used
----------

* [imgurpython](https://github.com/Imgur/imgurpython)