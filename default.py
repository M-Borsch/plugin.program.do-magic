# -*- coding: utf-8 -*-
# Manage Kodi Favourites program add-on for Kodi 17.6+.
# Lets you see and manage your Kodi favourites, to organize them.
# In other words, this is an add-on to edit your
# favourites.xml file.
#
# --------------------------------------------------------------------
# M-Borsch 2026-02-28: Version 1.0.0
# - Initial Release
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

DEBUG = '0'
DEBUG2 = '1'
# Flag to put up the Under Construction Popup
DEBUG3 = '0'
SETTINGS_PATH = 'special://addons/pvr.stalker/resources/settings.xml'

ADDON = Addon()
PLUGIN_ID = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]

#===================================================================================

def execFunction():
    # Display a confirmation dialog (requires xbmcgui)
    dialog = xbmcgui.Dialog()
    dialog.ok("File Operation", "[COLOR red]do-magic: [/COLOR]Call to function Stub!\n\nContinue...")

    if  magicFunction == ADDON.getLocalizedString(30007):
        execDownloadFunction()
    else:
        # Display an error dialog if the operation fails
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Operation Denied.\n\nNot Authorized to Run Function")


def execDownloadFunction():
    # Display a confirmation dialog (requires xbmcgui)
    dialog = xbmcgui.Dialog()
    dialog.ok("File Operation", "[COLOR red]do-magic: [/COLOR]Call to Download Stub!\n\nContinue...")
    
    # Define the download parameters
    # Read from settings.....
    
    # Start the download
    download_with_progress(magicUrl, magicName)

def download_with_progress(url, dest_name):
    dp = xbmcgui.DialogProgress()
    dp.create('Downloading', 'Starting download...')
    
    # Use xbmcvfs to handle paths across different OSs
    save_path = xbmcvfs.translatePath(os.path.join(magicDir, dest_name))

    def reporthook(count, block_size, total_size):
        if total_size > 0:
            percent = int(count * block_size * 100 / total_size)
            dp.update(percent, f"Downloaded {percent}% of file")
        
        if dp.iscanceled():
            urllib.request.urlcleanup()
            raise Exception("Download Canceled")

    try:
        urllib.request.urlretrieve(url, save_path, reporthook)
        dp.close()
    except Exception as e:
        dp.close()
        print(f"Error: {e}")
        
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

elif '/function' in PLUGIN_URL:   
    magicPassword = '' if not ADDON.getSetting('magicPWD') else ADDON.getSetting('magicPWD')
    magicFunction = '' if not ADDON.getSetting('magicFUNCTION') else ADDON.getSetting('magicFUNCTION')
    magicName = '' if not ADDON.getSetting('magicNAME') else ADDON.getSetting('magicNAME')
    magicUrl = '' if not ADDON.getSetting('magicURL') else ADDON.getSetting('magicURL')
    magicDir = '' if not ADDON.getSett0ing('magicDIR') else ADDON.getSetting('magicDIR')

    if DEBUG == '1': xbmcgui.Dialog().ok('do-magic', 'INFO: "%s"\n\n(PWD)' % magicPassword)
    if DEBUG == '1': xbmcgui.Dialog().ok('do-magic', 'INFO: "%s"\n\n(Function)' % magicFunction)

    if  do-magicPassword == ADDON.getLocalizedString(30005):
        execFunction()
    else:
        # Display an error dialog if the operation fails
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Operation Denied.\n\nInvalid PWD")

else:
    # Create the menu items.
    xbmcplugin.setContent(PLUGIN_ID, 'files')
    configureItem = xbmcgui.ListItem('[B]Configure... (Enter PWD/Function in Settings)[/B]')
    configureItem.setArt({'thumb': 'DefaultFolderBack.png'})
    configureItem.setInfo('video', {'plot': 'Configure the default actions in Settings panel.'})
    execute_function = xbmcgui.ListItem('[COLOR red][B]Execute Function [/COLOR](Advanced! - This will modify your Kodi install[/B]')
    execute_function.setArt({'thumb': 'DefaultAddonsUpdates.png'})
    execute_function.setInfo('video', {'plot': 'Advanced - Modify certain Kodi Functionality'})
    exitItem = xbmcgui.ListItem('[B]Exit[/B]')
    exitItem.setArt({'thumb': 'DefaultFolderBack.png'})
    exitItem.setInfo('video', {'plot': 'Exit the add-on (same as pressing Back), without saving your changes.'})

    xbmcplugin.addDirectoryItems(
        PLUGIN_ID,
        (
            # PLUGIN_URL already ends with a slash, so just append the route to it.
            (PLUGIN_URL + 'configure', configureItem, False),
            (PLUGIN_URL + 'function', execute_function, False),
            (PLUGIN_URL + 'exit_only', exitItem, False)
        )
    )
    xbmcplugin.endOfDirectory(PLUGIN_ID)




