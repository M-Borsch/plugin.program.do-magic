# -*- coding: utf-8 -*-
# Manage Kodi Favourites program add-on for Kodi 17.6+.
# Lets you see and manage your Kodi favourites, to organize them.
# In other words, this is an add-on to edit your
# favourites.xml file.
#
# --------------------------------------------------------------------
# M-Borsch 2026-06-21: Version 1.2
# - Add DailyUpload download function
# - Add download of Kodi Log function
# M-Borsch 2026-05-28: Version 1.1
# - Add Streamtape download function
# --------------------------------------------------------------------
#
# ====================================================================
import re
import sys
import json
import traceback
import xbmc
import xbmcgui
import os
import requests as reqs
import shutil
import xbmcvfs
import urllib.request

try:
    # Python 2.x
    from HTMLParser import HTMLParser
    PARSER = HTMLParser()
    DECODE_STRING = lambda val: val.decode('utf-8')
except ImportError as e:
    # Python 3.4+ (see https://stackoverflow.com/a/2360639)
    import html
    PARSER = html
    DECODE_STRING = lambda val: val # Pass-through.

import xbmc, xbmcgui, xbmcplugin, xbmcvfs
from xbmcaddon import Addon

# BeautifulSoup4 (installed from Kodi repo: script.module.beautifulsoup4)
from bs4 import BeautifulSoup
import urllib.request

DEBUG = '0'
DEBUG2 = '1'
# Flag to put up the Under Construction Popup
DEBUG3 = '0'
SETTINGS_PATH = 'special://addons/pvr.stalker/resources/settings.xml'
LOG_PATH = 'special://logpath/'


ADDON = Addon()
PLUGIN_ID = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]

#===================================================================================

def execFunction():

    dialog = xbmcgui.Dialog()
    # Parameters: yesno(heading, message, yeslabel='Yes', nolabel='No')
    # labels to "OK" and "Cancel"
    choice = dialog.yesno("Run " + magicFunction, "Do you want to proceed?\n\n[I]Use the [B]Configure...[/B] option to select a different Function[/I]", yeslabel="Proceed...", nolabel="Cancel")

    if choice:
        # User clicked OK (Yes)
        if magicFunction == ADDON.getLocalizedString(30007):
            execDownloadFunction()
        elif magicFunction == ADDON.getLocalizedString(30012):
            execHashFunction() 
        elif magicFunction == ADDON.getLocalizedString(30017):
            execBackgroudFunction()
        elif magicFunction == ADDON.getLocalizedString(30026):
            addMBKodiFileSources()
        elif magicFunction == ADDON.getLocalizedString(30029):
            execConfBackgroudFunction() 
        elif magicFunction == ADDON.getLocalizedString(30046):
            execStalkerDownloadFunction()
        elif magicFunction == ADDON.getLocalizedString(30048):
            execDailyDownloadFunction() 
        #elif magicFunction == ADDON.getLocalizedString(30008):
            #execStalkerTweakFunction() 
        else:
            # Display an error dialog if the operation fails
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Operation Denied.\n\nNot Authorized to Run Function")

def isValidFile(filename):
    # List of allowed image extensions
    allowed = ['.jpg', '.jpeg', '.png']
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed

def execStalkerDownloadFunction():
    url = magicStalkerUrl
    name = url.split('/')
    if name[-1] == '':
        name.pop(-1)
    name = name[-1]

    r = reqs.get(url)
    rstr = str(r.content)

#    rstr = rstr[rstr.find('/streamta.pe/'):]
    rstr = rstr[rstr.find('/streamtape.com/'):]
    link = rstr[:rstr.find('<')]
    rstr = rstr[rstr.find("xcdd"):]
    rstr = rstr[:rstr.find("\\")]
    rstr = rstr[-2:]
    link = 'https:/' + link[:-2] + rstr + '&stream=1'

    # Display a notification dialog (requires xbmcgui)
    dialog = xbmcgui.Dialog()
    line2 = "[COLOR blue]Copy:[/COLOR] " + link + " [COLOR blue]\nTo:[/COLOR] [COLOR green]" + magicStalkerDir + magicStalkerName + "[/COLOR]"

    dialog.ok("[COLOR red]do-magic: [/COLOR]Streamtape Function", line2)
    
    checkFile(f"{magicStalkerDir}{magicStalkerName}")
    # stalkerdownload(link, f"{magicStalkerDir}{magicStalkerName}")
    stalkerdownload(magicStalkerUrl, f"{magicStalkerDir}{magicStalkerName}")

def stalkerdownload(url, filename):
    
    # stream=True allows downloading the file in parts
    with reqs.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

def oldstalkerdownload(url, fileName):
    with open(fileName, "wb") as w:
        # print('File opened')
        r = reqs.get(url, stream=True)
        total = int(r.headers.get("content-length"))
        downloaded = 0
        for data in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)):    
            downloaded += len(data)
            percentage = int((downloaded/total)/0.02)
            # sys.stdout.write(f'\r[{"*"*percentage}{"."*(50-percentage)}]')
            xbmc.executebuiltin('Notification(Streamtape, Downloading..., 2000)')   

            w.write(data)

def checkFile(name :str):
    if not(os.path.isfile(name)):
        with open(name, "x"):
            pass

def execConfBackgroudFunction():

    if magicConfBackgroundFlag:

        # Get the base add-on path (encoded)
        addon_path = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))

        # Define path to a resource file
        resource_file = os.path.join(addon_path, 'resources', magicConfBackground)

        # Check if file exists
        if isValidFile(resource_file) and xbmcvfs.exists(resource_file):
            # Process the file
            updateConfluenceBackground(resource_file)
        else:
            # Display an error dialog if the operation fails
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Error: Invalid Filename \n\n" +  resource_file)

    else:
         # Check if file exists
        if isValidFile(magicConfCusBackground) and xbmcvfs.exists(magicConfCusBackground):
            # Process the file
            updateConfluenceBackground(magicConfCusBackground)
        else:
            # Display an error dialog if the operation fails
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Error: Invalid Filename \n\n" +  magicConfCusBackground)


def addMBKodiFileSources():

        userdata_pathDIR = xbmcvfs.translatePath('special://userdata/')
        filename = 'sources.xml'
        # debugfilename = 'debug.xml'

         # Get the base add-on path (encoded)
        addon_path = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))

        # Define path to a resource file
        replacement_file_path = os.path.join(addon_path, 'resources', 'MB-KODI-sources.xml')

         # Check if file exists
        if xbmcvfs.exists(replacement_file_path):
            
            # Process the file
            # File paths (ensure these paths are correct for your Kodi setup)
            target_file_path = os.path.join(userdata_pathDIR, filename)
            #debug_file_path  = os.path.join(userdata_pathDIR, debugfilename)
            string_to_replace = '</files>'
            
            # Read the content that will be used for replacement
            with open(replacement_file_path, 'r') as f:
                new_content = f.read()
            
            # Read the target file
            with open(target_file_path, 'r') as f:
                target_data = f.read()
            
            # Replace the specific string with the new content
            updated_data = target_data.replace(string_to_replace, new_content)
            
            # Save the changes back to the target file
            with open(target_file_path, 'w') as f:
               f.write(updated_data)

            # Save the changes back to the debug target file
            #with open(debug_file_path, 'w') as f:
            #    f.write(updated_data)
                
            # Display a confirmation dialog (requires xbmcgui)
            dialog = xbmcgui.Dialog()
            line2 = "[COLOR blue]MB-KODI-ADDONS: [/COLOR][COLOR green]MB-KODI-ADDONS File Source Successfully Added[/COLOR]\n\n[COLOR red]IMPORTANT: These File Sources will show up next time you restart KODI...[/COLOR]"
        
            dialog.ok("[COLOR red]do-magic: [/COLOR]File Sources Function", line2)
            #xbmc.executebuiltin('LoadProfile(%s)' % xbmc.getInfoLabel('System.ProfileName'))

        else:
            # Display an error dialog if the operation fails
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Error: Invalid Filename \n\n" +  replacement_file_path)

def updateConfluenceBackground(targetfilename):

        # Define the absolute path to your new background image
        new_background_path = targetfilename
        
        # Enable the custom background setting in Confluence
        # In Confluence, the toggle is typically controlled by 'Skin.HasSetting(CustomBackground)'
        xbmc.executebuiltin('Skin.SetBool(CustomBackground, true)')
        
        # Set the background image path
        # Confluence uses the setting 'CustomBackgroundPath' to store the image location
        xbmc.executebuiltin(f'Skin.SetString(CustomBackgroundPath, "{new_background_path}")')

def updateKodiBackground(targetfilename):
    
        userdata_pathDIR = xbmcvfs.translatePath('special://userdata/')
    
        ADDONS_PATH = xbmcvfs.translatePath('special://home/')
        BACKGROUND_PATH = os.path.join(ADDONS_PATH, "addons/skin.confluence/backgrounds/")
    
        filename = 'SKINDEFAULT.jpg'
    
        # setup target location
        save_path = BACKGROUND_PATH + filename
    
        # Copy the background file to target location using Kodi's built-in SMB handling
        if xbmcvfs.copy(targetfilename, save_path):
            xbmc.log("Background: File downloaded successfully", xbmc.LOGINFO)
        else:
            xbmc.log("Background: Failed to download file", xbmc.LOGERROR)
    
        # Optional: Inform the user
        xbmc.executebuiltin('Notification(Background, Updated, 2000)')
            
        # Display a confirmation dialog (requires xbmcgui)
        dialog = xbmcgui.Dialog()
        line2 = "[COLOR blue]Set Background To: [/COLOR][COLOR green]" + targetfilename + "[/COLOR]\n\n" + "Reloading Kodi profile. This may take several seconds..."
    
        dialog.ok("[COLOR red]do-magic: [/COLOR]Background Function", line2)
        xbmc.executebuiltin('LoadProfile(%s)' % xbmc.getInfoLabel('System.ProfileName'))

def execBackgroudFunction():

    if magicBackgroundFlag:

        # Get the base add-on path (encoded)
        addon_path = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))

        # Define path to a resource file
        resource_file = os.path.join(addon_path, 'resources', magicBackground)

        # Check if file exists
        if isValidFile(resource_file) and xbmcvfs.exists(resource_file):
            # Process the file
            updateCofluenceBackground(resource_file)
        else:
            # Display an error dialog if the operation fails
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Error: Invalid Filename \n\n" +  resource_file)

    else:
         # Check if file exists
        if isValidFile(magicCusBackground) and xbmcvfs.exists(magicCusBackground):
            # Process the file
            updateKiodiBackground(magicCusBackground)
        else:
            # Display an error dialog if the operation fails
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Error: Invalid Filename \n\n" +  magicCusBackground)

def execHashFunction():

    # Generate a salt and hash password
    hashed = xbmc.getCacheThumbName( magicHash ).split('.', 1)[0]
    
    # Display a confirmation dialog (requires xbmcgui)
    dialog = xbmcgui.Dialog()
    line2 = "[COLOR blue]Hashing:[/COLOR] " + magicHash + " [COLOR blue]\nTo:[/COLOR] [COLOR green]" + hashed + "[/COLOR]"

    dialog.ok("[COLOR red]do-magic: [/COLOR]HASH Function", line2)


def execDownloadFunction():

    if magicDownloadFlag:
        srcFile = ADDON.getLocalizedString(30035) + 'd/' + magicUrl
    else:
        srcFile = magicUrl
    
    # Display a confirmation dialog (requires xbmcgui)
    dialog = xbmcgui.Dialog()
    line2 = "[COLOR blue]From:[/COLOR] " + srcFile + "\n[COLOR green]To:[/COLOR] " + magicDir + magicName

    dialog.ok("[COLOR red]do-magic: [/COLOR]Downloading file", line2)

    # Check if file exists
    if xbmcvfs.exists(srcFile):
        # Process the file
        # Start the download
        download_with_progress(srcFile, magicName)
    else:
        # Display an error dialog if the operation fails
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Error: Invalid Source Filename \n\n" +  srcFile)

def download_with_progress(url, dest_name):
    
    dp = xbmcgui.DialogProgress()
    dp.create('Downloading', 'Starting download...\n\nPlease Wait...may take time depending on file size')
    
    # Use xbmcvfs to handle paths across different OSs
    save_path = xbmcvfs.translatePath(os.path.join(magicDir, dest_name))

    def reporthook(count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            dp.update(percent, f"Downloaded {percent}% of file")
        
        if dp.iscanceled():
            urllib.request.urlcleanup()
            raise Exception("Download Cancelled")

    # Copy file using Kodi's built-in SMB handling
    if xbmcvfs.copy(url, save_path):
        xbmc.log("File downloaded successfully", xbmc.LOGINFO)
         # Optional: Inform the user
        xbmc.executebuiltin('Notification(Downloader, ' + dest_name + ' dowloaded, 2000)')
    else:
        xbmc.log("Failed to download file", xbmc.LOGERROR)
    #try:
    #    urllib.request.urlretrieve(url, save_path, reporthook)
    #    dp.close()
    #except Exception as e:
    #    dp.close()
    #    print(f"Error: {e}")
        
def execStalkerTweekFunction():
    xbmc.executebuiltin('Notification(Stalker, Tweeked, 2000)')

def writeoutLog():

    # --- Configuration Variables ---
    # Type of browse dialog: 1 = ShowAndGetDir
    browse_type = 0
    
    # Dialog heading
    heading = 'Select the directory to save kodi.log file'
    
    # The starting path. Use "" to list local drives and network shares
    # or specify a default path like 'special://home/addons/'
    default_path = '' 
    
    # File mask for directories.
    file_mask = '/' 
    
    # Enable multiple file selection (optional)
    enable_multiple = False
    
    # --- Show the browse dialog ---
    dialog = xbmcgui.Dialog()
    selected_file_path = dialog.browse(
        browse_type,
        heading,
        '',  # shares parameter: "" for local/network sources, "files" for file sources
        file_mask,
        enableMultiple=enable_multiple,
        defaultt=default_path # default path to start browsing from
    )
    # --- Process the result ---
    if selected_file_path:
        
        # xbmc.log(f"[COLOR red]Manage Kodi Favourites: [/COLOR]Selected file path: {selected_file_path}", xbmc.LOGINFO)
        
        # You can now use xbmcvfs to read the file content
        # Example (requires importing xbmcvfs):
        # import xbmcvfs
        # with xbmcvfs.File(selected_file_path, 'r') as f:
        #     content = f.read()
        #     xbmc.log(f"File content snippet: {content[:100]}", xbmc.LOGINFO)

        # Define source and destination paths using xbmc.translatePath()
        # 'special://home/' is a common built-in path in Kodi that points to the userdata folder
        src = xbmcvfs.translatePath(LOG_PATH) + "kodi.log"
        dst = xbmcvfs.translatePath(selected_file_path) + "kodi.log"
    
        # Add error handling using a try-except block
        try:
            # shutil.copyfile(src, dst)
            xbmcvfs.copy(src, dst)
            # Display a confirmation dialog (requires xbmcgui)
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation", "[COLOR green]Manage Kodi Favourites: [/COLOR]kodi.log successfully copied!\n")
        except IOError as e:
            # Display an error dialog if the operation fails
            dialog = xbmcgui.Dialog()
            dialog.ok("File Operation Error", f"[COLOR red]Manage Kodi Favourites: [/COLOR]Error copying kodi.log file: {e}")
    
    else:
        xbmc.log("[COLOR red]Manage Kodi Favourites: [/COLOR]File selection cancelled by user.", xbmc.LOGINFO)

def fetch_html(url):
    """Fetch HTML safely with error handling."""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read()
    except Exception as e:
        xbmc.log(f"Error fetching URL: {e}", xbmc.LOGERROR)
        return None

def parse_titles(html):
    """Parse HTML and extract <title> or <h1> text using BeautifulSoup."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        titles = []

        # Example extraction: page title
        if soup.title and soup.title.string:
            titles.append(soup.title.string.strip())

        # Example: all H1 tags
        for h1 in soup.find_all("h1"):
            if h1.text:
                titles.append(h1.text.strip())

        return titles

    except Exception as e:
        xbmc.log(f"BeautifulSoup parsing error: {e}", xbmc.LOGERROR)
        return []

def list_items(handle, items):
    """Display list items in Kodi UI."""
    for text in items:
        li = xbmcgui.ListItem(label=text)
        xbmcplugin.addDirectoryItem(handle=handle, url="", listitem=li, isFolder=False)
    xbmcplugin.endOfDirectory(handle)

def router():
    handle = int(sys.argv[1])
    test_url = "https://dailyuploads.net/ck1d7zjasu8u"

    html = fetch_html(test_url)
    if html is None:
        xbmcgui.Dialog().notification("Error", "Failed to fetch page.", xbmcgui.NOTIFICATION_ERROR)
        return

    titles = parse_titles(html)
    if not titles:
        xbmcgui.Dialog().notification("No Data", "No titles found.", xbmcgui.NOTIFICATION_INFO)
        return

    list_items(handle, titles)

def download_from_dailyuploads(url, output_path):
    """
    Safely attempts to download the publicly accessible file linked on DailyUploads.
    Does not bypass CAPTCHA or restricted/protected downloads.
    """

    # Basic input validation
    if not isinstance(url, str) or not url.startswith("http"):
        xbmcgui.Dialog().notification("No Data", "Invalid URL provided..", xbmcgui.NOTIFICATION_INFO)


    try:
        session = reqs.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

        # Step 1: Fetch landing page
        resp = session.get(url, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Step 2: Look for the main download button or link
        # DailyUploads often uses <a id="downloadbtn"> or similar
        download_link = None

        # Common patterns
        possible_ids = ["downloadbtn", "download", "dlbutton", "ck1d7zjasu8u"]
        for pid in possible_ids:
            tag = soup.find("a", id=pid)
            if tag and tag.get("href"):
                download_link = urljoin(url, tag["href"])
                break

        # Fallback: try class name
        if not download_link:
            tag = soup.find("a", class_="btn")
            if tag and tag.get("href"):
                download_link = urljoin(url, tag["href"])

        if not download_link:
            xbmcgui.Dialog().notification("No Data", "Could not find a direct download link on the page !!", xbmcgui.NOTIFICATION_INFO)
            xbmc.log(f"[COLOR red]do-magic: [/COLOR]Error: Could not find a direct download link on the page !!", xbmc.LOGERROR)

        # Step 3: Fetch the actual file
        # Hard Code download link
        # REMOVE THIS CODE
        download_link = "https://dailyuploads.net/ck1d7zjasu8u/Voicemails.for.Isabelle.2026.1080p.NF.WEB-DL.10bit.DDP5.1.x265-FaS.mkv"
        
        # Display the download link
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation", f"[COLOR green]do-magic: [/COLOR]Downloading from: {download_link}")
        file_resp = session.get(download_link, timeout=20, stream=True)
        file_resp.raise_for_status()

        # Infer a filename if not given
        filename = output_path
        if output_path.endswith("/"):
            parsed = urlparse(download_link)
            name = parsed.path.split("/")[-1] or "downloaded_file"
            filename = output_path + name

        # Step 4: Save the file
        with open(filename, "wb") as f:
            for chunk in file_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print("File saved to:", filename)
        return filename

    except reqs.RequestException as e:
        xbmc.log(f"[COLOR red]do-magic: [/COLOR]Network Error: {e}", xbmc.LOGERROR)
    except Exception as e:
        xbmc.log(f"[COLOR red]do-magic: [/COLOR]Unexpected Error: {e}", xbmc.LOGERROR)


def execDailyDownloadFunction():

    # router()

    try:
        # url = "https://dailyuploads.net/ck1d7zjasu8u"
        url = "https://dailyuploads.net/ck1d7zjasu8u/Voicemails.for.Isabelle.2026.1080p.NF.WEB-DL.10bit.DDP5.1.x265-FaS.mkv"
        output = magicDailyDir + magicDailyName  # Change as needed
        download_from_dailyuploads(url, output)
    except Exception as e:
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation", f"[COLOR red]do-magic: [/COLOR]Error Downloading: {e}")
        xbmc.log(f"[COLOR red]do-magic: [/COLOR]Unexpected Error: {e}", xbmc.LOGERROR)

    # xbmc.executebuiltin('Notification(DailyUpload, File Dwnloaded, 2000)')  

def execStalkerFunction():

    # --- Configuration Variables ---
    # Type of browse dialog: 1 = ShowAndGetFile
    browse_type = 1
    # Dialog heading
    heading = 'Select the settings.xml file'
    # The starting path. Use "" to list local drives and network shares
    # or specify a default path like 'special://home/addons/'
    default_path = 'special://home' 
    # File mask for readable files (e.g., text, xml, log files). Use '|' to separate extensions.
    file_mask = 'settings.xml' 
    # Enable multiple file selection (optional)
    enable_multiple = False
    
    # --- Show the browse dialog ---
    dialog = xbmcgui.Dialog()
    selected_file_path = dialog.browse(
        browse_type,
        heading,
        '',  # shares parameter: "" for local/network sources, "files" for file sources
        file_mask,
        enableMultiple=enable_multiple,
        defaultt=default_path # default path to start browsing from
    )

    # Does the selected file include "settings.xml"
    if "settings.xml" in selected_file_path:
    
        # --- Process the result ---
        if selected_file_path:
            xbmc.log(f"[COLOR red]do-magic: [/COLOR]Selected file path: {selected_file_path}", xbmc.LOGINFO)
            # You can now use xbmcvfs to read the file content
            # Example (requires importing xbmcvfs):
            # import xbmcvfs
            # with xbmcvfs.File(selected_file_path, 'r') as f:
            #     content = f.read()
            #     xbmc.log(f"File content snippet: {content[:100]}", xbmc.LOGINFO)
    
            # Define source and destination paths using xbmc.translatePath()
            # 'special://home/' is a common built-in path in Kodi that points to the userdata folder
            src = xbmcvfs.translatePath(selected_file_path)
            dst = xbmcvfs.translatePath(SETTINGS_PATH)
            
            # Add error handling using a try-except block
            try:
                # shutil.copyfile(src, dst)
                xbmcvfs.copy(src, dst)
                # Display a confirmation dialog (requires xbmcgui)
                dialog = xbmcgui.Dialog()
                dialog.ok("File Operation", "[COLOR red]do-magic: [/COLOR]settings.xml successfully copied!\n\nYou must relaunch the impacted Addon to view the change")
            except IOError as e:
                # Display an error dialog if the operation fails
                dialog = xbmcgui.Dialog()
                dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Error copying settings.xml file: {e}")
        
        else:
            xbmc.log("[COLOR red]do-magic: [/COLOR]File selection cancelled by user.", xbmc.LOGINFO)
    else:
        # Display an error dialog if the operation fails
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Invalid Filename: Please select 'settings.xml'")

def getRawWindowProperty(prop):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    return window.getProperty(prop)

def setRawWindowProperty(prop, data):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    window.setProperty(prop, data)

def clearWindowProperty(prop):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    window.clearProperty(prop)

# Debugging helper. Logs a LOGNERROR-level message.
def xbmcLog(*args):
    xbmc.log('[COLOR yellow]Manage Kodi Favourites > [/COLOR]' + ' '.join((var if isinstance(var, str) else repr(var)) for var in args), level=xbmc.LOGERROR)
#===================================================================================

### Entry point ###

if '/exit_only' in PLUGIN_URL:
    xbmc.executebuiltin('Action(Back)')
    # Alternative action, going to the Home screen.
    #xbmc.executebuiltin('ActivateWindow(home)') # ID taken from https://kodi.wiki/view/Window_IDs

elif '/configure' in PLUGIN_URL:
    # Call up the configuration panel.
    # Activate the Settings window
    xbmc.executebuiltin('Addon.OpenSettings(do-magic)')

elif '/writeout_log' in PLUGIN_URL:
    
    # Let the user know that there are about to write out their kodi log file
    verbose = 'false' if not ADDON.getSetting('presuffixBool') else ADDON.getSetting('presuffixBool')
    msg_text = f"[COLOR red]DANGER! [/COLOR]This will save a copy of your Kodi Log file - overwriting any local version of kodi.log in the selected directory\n Proceed?"
    if verbose == 'true':
        if xbmcgui.Dialog().yesno('Manage Kodi Favourites', msg_text):
            # Activate the filemaanager
            writeoutLog()
    else:
        writeoutLog()

elif '/fmanager' in PLUGIN_URL:
    # Call up the File Manager.
    xbmc.executebuiltin("ActivateWindow(FileManager)")

elif '/function' in PLUGIN_URL:   
    magicPassword = '' if not ADDON.getSetting('magicPWD') else ADDON.getSetting('magicPWD')
    magicFunction = '' if not ADDON.getSetting('magicFUNCTION') else ADDON.getSetting('magicFUNCTION')

    magicDownloadFlag = '' if not ADDON.getSettingBool('magicDNLDFLG') else ADDON.getSettingBool('magicDNLDFLG')    
    magicName = '' if not ADDON.getSetting('magicNAME') else ADDON.getSetting('magicNAME')
    magicUrl = '' if not ADDON.getSetting('magicURL') else ADDON.getSetting('magicURL')
    magicDir = '' if not ADDON.getSetting('magicDIR') else ADDON.getSetting('magicDIR')

    magicStalkerName = '' if not ADDON.getSetting('magicSTALKNAME') else ADDON.getSetting('magicSTALKNAME')
    magicStalkerUrl = '' if not ADDON.getSetting('magicSTALKURL') else ADDON.getSetting('magicSTALKURL')
    magicStalkerDir = '' if not ADDON.getSetting('magicSTALKDIR') else ADDON.getSetting('magicSTALKDIR')

    magicDailyName = '' if not ADDON.getSetting('magicDAILYNAME') else ADDON.getSetting('magicDAILYNAME')
    magicDailyUrl = '' if not ADDON.getSetting('magicDAILYURL') else ADDON.getSetting('magicDAILYURL')
    magicDailyDir = '' if not ADDON.getSetting('magicDAILYDIR') else ADDON.getSetting('magicDAILYDIR')
    
    magicHash = '' if not ADDON.getSetting('magicHASH') else ADDON.getSetting('magicHASH')
    
    magicBackgroundFlag = '' if not ADDON.getSettingBool('magicBKGNDFLG') else ADDON.getSettingBool('magicBKGNDFLG')
    magicConfBackgroundFlag = '' if not ADDON.getSettingBool('magicCONFBKGNDFLG') else ADDON.getSettingBool('magicCONFBKGNDFLG')
    
    magicCusBackground = '' if not ADDON.getSetting('magicCUSBKGNDFILE') else ADDON.getSetting('magicCUSBKGNDFILE')
    magicConfCusBackground = '' if not ADDON.getSetting('magicCONFCUSBKGNDFILE') else ADDON.getSetting('magicCONFCUSBKGNDFILE')

    magicBackground = '' if not ADDON.getSetting('magicBKGNDFILE') else ADDON.getSetting('magicBKGNDFILE')
    magicConfBackground = '' if not ADDON.getSetting('magicCONFBKGNDFILE') else ADDON.getSetting('magicCONFBKGNDFILE')
    
    if  xbmc.getCacheThumbName( magicPassword ).split('.', 1)[0] == ADDON.getLocalizedString(30005):
        execFunction()   
    else:
        # Display an error dialog if the operation fails
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation Error", f"[COLOR blue]do-magic: [/COLOR][COLOR blue]Operation Denied.\n\nInvalid PWD[/COLOR]")

else:
    # Create the menu items.
    xbmcplugin.setContent(PLUGIN_ID, 'files')
    configureItem = xbmcgui.ListItem('[B]Configure... (Enter PWD/Function in Settings)[/B]')
    configureItem.setArt({'thumb': 'DefaultFolderBack.png'})
    configureItem.setInfo('video', {'plot': 'Configure the default actions in Settings panel.'})
    execute_function = xbmcgui.ListItem('[COLOR lightgreen][B]   Execute Function [/COLOR](Advanced! - This may modify your Kodi install)[/B]')
    execute_function.setArt({'thumb': 'DefaultAddonsUpdates.png'})
    execute_function.setInfo('video', {'plot': 'Advanced - Modify certain Kodi Functionality'})
    writeoutLog = xbmcgui.ListItem('[COLOR red][B]-> Download Current Kodi Log file [/COLOR](Advanced! - Save a Copy of kodi.log file[/B]')
    writeoutLog.setArt({'thumb': 'DefaultFolderBack.png'})
    writeoutLog.setInfo('video', {'plot': 'Advanced - Download a copy of your Kodi Favourites file.[/COLOR]'})    
    file_manager = xbmcgui.ListItem('[COLOR red][B]   Launch File Manager...[/B][/COLOR]')
    file_manager.setArt({'thumb': 'DefaultAddonsUpdates.png'})
    file_manager.setInfo('video', {'plot': 'Launch File Manager...'})
    exitItem = xbmcgui.ListItem('[B]Exit[/B]')
    exitItem.setArt({'thumb': 'DefaultFolderBack.png'})
    exitItem.setInfo('video', {'plot': 'Exit the add-on (same as pressing Back), without saving your changes.'})

    xbmcplugin.addDirectoryItems(
        PLUGIN_ID,
        (
            # PLUGIN_URL already ends with a slash, so just append the route to it.
            (PLUGIN_URL + 'configure', configureItem, False),
            (PLUGIN_URL + 'function', execute_function, False),
            (PLUGIN_URL + 'writeout_log', writeoutLog, False),
            (PLUGIN_URL + 'fmanager', file_manager, False),
            (PLUGIN_URL + 'exit_only', exitItem, False)
        )
    )
    xbmcplugin.endOfDirectory(PLUGIN_ID)
