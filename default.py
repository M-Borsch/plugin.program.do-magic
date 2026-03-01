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

# Custom Favourites window class for managing the favourites items.
class CustomFavouritesDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

        # Map control IDs to custom handler methods. You can find the control IDs inside
        # the custom skin XML bundled with this add-on (/resources/skins/Default/1080i/CustomFavouritesDialog[sm lg].XML).
        self.idHandlerDict = {
            101: self.doSelect,
            301: self.close,
            302: self.doReload,
            # 303: self.doConfigure,
            303: self.doSortItems,
            304: self.doPreSuffix,
        }

        # Map action IDs to custom handler methods. See more action IDs in
        # https://github.com/xbmc/xbmc/blob/master/xbmc/input/actions/ActionIDs.h
        self.actionHandlerDict = {
            # All click/select actions are already handled by 'idHandlerDict' above.
            #7: self.doSelect, # ACTION_SELECT_ITEM
            #100: self.doSelect, # ACTION_MOUSE_LEFT_CLICK
            #108: self.doSelect, # ACTION_MOUSE_LONG_CLICK
            9: self.doUnselectClose, # ACTION_PARENT_DIR
            92: self.doUnselectClose, # ACTION_NAV_BACK
            10: self.doUnselectClose, # ACTION_PREVIOUS_MENU
            101: self.doUnselectClose, # ACTION_MOUSE_RIGHT_CLICK
            110: self.doUnselectClose # ACTION_BACKSPACE
        }
        self.noop = lambda: None

    @staticmethod
    def _makeFavourites(favouritesGen):
        LISTITEM = xbmcgui.ListItem
        artDict = {'thumb': None}
        for index, data in enumerate(favouritesGen):
            # The path of each ListItem contains the original favourite entry XML text (with the label, thumb and URL)
            # and this is what's written to the favourites file upon saving -- what changes is the order of the items.
            # add action field to Label2
            li = LISTITEM(data[0], data[3], path=data[2])
            artDict['thumb'] = data[1] # Slightly faster than recreating a dict on every item.

            li.setArt(artDict)

            if DEBUG == '1': log_msg = "[COLOR red]Manage Kodi Favourites INFO:[/COLOR] New Label = %s" % data[2]
            if DEBUG == '1': xbmc.log(log_msg, level=xbmc.LOGINFO)

            li.setProperty('origThumb', data[4])
            li.setProperty('sortname', data[5])

            li.setProperty('index', str(index)) # To help with resetting, if necessary.
            yield li

    # Function used to start the dialog.
    def doCustomModal(self, favouritesGen):

        currentVer = '0' if not ADDON.getAddonInfo('version') else ADDON.getAddonInfo('version')
        self.setProperty(CURRENTVER, currentVer)
        reorderingMethod = '0' if not ADDON.getSetting('reorderingMethod') else ADDON.getSetting('reorderingMethod')
        self.setProperty(REORDER_METHOD, reorderingMethod)
        fontSize = '0' if not ADDON.getSetting('fontSize') else ADDON.getSetting('fontSize')
        self.setProperty(FONT_SIZE, fontSize)
                
        # Determine the Prefix Text from Configuration Settings
        if ADDON.getSetting('prefixTextCus'):
            cur_prefix_text = ADDON.getSetting('prefixTextCus')
        else:
            cur_prefix_text = ADDON.getSetting('prefixTextSel')
            
        # Determine the Prefix Color from Configuration Settings
        if ADDON.getSetting('prefixColorCus'):
            cur_prefix_color = ADDON.getSetting('prefixColorCus')
        else:
            cur_prefix_color = ADDON.getSetting('prefixColSel')

        # Determine the Suffix Text from Configuration Settings
        if ADDON.getSetting('suffixTextCus'):
            cur_suffix_text = ADDON.getSetting('suffixTextCus')
        else:
            cur_suffix_text = ADDON.getSetting('suffixTextSel')
            
        # Determine the Suffix Color from Configuration Settings
        if ADDON.getSetting('suffixColorCus'):
            cur_suffix_color = ADDON.getSetting('suffixColorCus')
        else:
            cur_suffix_color = ADDON.getSetting('suffixColSel')

        PrefixTextColor = '[COLOR yellow]' + cur_prefix_text + ' / ' + cur_prefix_color + '[/COLOR]'
        SuffixTextColor = '[COLOR yellow]' + cur_suffix_text + ' / ' + cur_suffix_color + '[/COLOR]'

        self.setProperty(PREFIX_TEXT_COLOR, PrefixTextColor)
        self.setProperty(SUFFIX_TEXT_COLOR, SuffixTextColor)
     
        if DEBUG == '1': xbmcgui.Dialog().ok('Manage Kodi Favourites', 'INFO: "%s"\n(Entry: Prefix Label)' %  str(cur_prefix_text))
        if DEBUG == '1': xbmcgui.Dialog().ok('Manage Kodi Favourites', 'INFO: "%s"\n(Entry: Prefix Color)' %  str(cur_prefix_color))
        
        self.allItems = list(self._makeFavourites(favouritesGen))
        self.indexFrom = None # Integer index of the source item (or None when nothing is selected).
        self.isDirty = False # Bool saying if there were any user-made changes at all.

        self.doModal()
        if self.isDirty:
            return self._makeNewResult()
        else:
            return ''

    # Automatically called before the dialog is shown. The UI controls exist now.
    def onInit(self):
        self.panel = self.getControl(101)
        self.panel.reset()
        self.panel.addItems(self.allItems)
        self.setFocusId(100) # Focus the group containing the panel, not the panel itself.
        reorderingMethod = '0' if not ADDON.getSetting('reorderingMethod') else ADDON.getSetting('reorderingMethod')
        setRawWindowProperty(REORDER_METHOD, reorderingMethod)
        thumbSize = '0' if not ADDON.getSetting('thumbSize') else ADDON.getSetting('thumbSize')
        setRawWindowProperty(THUMB_SIZE, thumbSize)

    def onClick(self, controlId):
        self.idHandlerDict.get(controlId, self.noop)()

    def onAction(self, action):
        self.actionHandlerDict.get(action.getId(), self.noop)()

    def doSelect(self):
        selectedPosition = self.panel.getSelectedPosition()
        if self.indexFrom == None:
            # Selecting a new item to reorder.
            self.indexFrom = selectedPosition
            self.panel.getSelectedItem().setProperty('selected', '1')
        else:
            # Something was already selected, so do the reodering.
            if self.indexFrom != selectedPosition:
                self.allItems[self.indexFrom].setProperty('selected', '')

                # Reorder the two distinct items in a specific way:
                reorderingMethod = getRawWindowProperty(REORDER_METHOD)

                # If using the swap mode, or if the items are direct neighbors, then
                # just swap them.
                if reorderingMethod == '0' \
                   or (self.indexFrom == (selectedPosition + 1)) \
                   or (self.indexFrom == (selectedPosition - 1)):
                    # Swap A and B.
                    self.allItems[self.indexFrom], self.allItems[selectedPosition] = (
                        self.allItems[selectedPosition], self.allItems[self.indexFrom]
                    )
                else:
                    itemFrom = self.allItems.pop(self.indexFrom)
                    if reorderingMethod == '1':
                        # Place A behind B.
                        # In case A is at some point BEHIND of B, reduce
                        # one index because popping A caused the list to shrink.
                        if self.indexFrom < selectedPosition:
                            selectedPosition = selectedPosition - 1
                    else:
                        # Place A ahead of B (the original ordering method).
                        # In case A is at some point AHEAD of B, move up
                        # one index because .insert() always puts it behind.
                        if self.indexFrom > selectedPosition:
                            selectedPosition = selectedPosition + 1
                    self.allItems.insert(selectedPosition, itemFrom)

                # Reset the selection state.
                self.isDirty = True
                self.indexFrom = None

                # Commit the changes to the UI, and highlight item A.
                self.panel.reset()
                self.panel.addItems(self.allItems)
                self.panel.selectItem(selectedPosition)
            else: # User reselected the item, so just unmark it.
                self.indexFrom = None
                self.panel.getSelectedItem().setProperty('selected', '')

    
#===================================================================================

def execFunction():

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
    # Clear the results property and go back one screen (to wherever the user came from).
    clearWindowProperty(PROPERTY_FAVOURITES_RESULT)
    clearWindowProperty(REORDER_METHOD)
    clearWindowProperty(THUMB_SIZE)
    clearWindowProperty(FONT_SIZE)
    clearWindowProperty(PREFIX_TEXT_COLOR)
    clearWindowProperty(SUFFIX_TEXT_COLOR)
    clearWindowProperty(CURRENTVER)

    xbmc.executebuiltin('Action(Back)')
    # Alternative action, going to the Home screen.
    #xbmc.executebuiltin('ActivateWindow(home)') # ID taken from https://kodi.wiki/view/Window_IDs

elif '/configure' in PLUGIN_URL:
    # Call up the configuration panel.
    # Activate the Settings window
    xbmc.executebuiltin('Addon.OpenSettings(do-magic)')

elif '/function' in PLUGIN_URL:

    password = '' if not ADDON.getSetting('do-magicPWD') else ADDON.getSetting('do-magicPWD')
    function = '' if not ADDON.getSetting('do-magicFunction') else ADDON.getSetting('do-magicFunction')

    if DEBUG2 == '1': xbmcgui.Dialog().ok('do-magic', 'INFO: "%s"\n\n(PWD)' % password)
    if DEBUG2 == '1': xbmcgui.Dialog().ok('do-magic', 'INFO: "%s"\n\n(Function)' % function)

    if  password == ADDON.getLocalizedString(30005) and function == ADDON.getLocalizedString(30006):
        execFunction()
    else:
        # Display an error dialog if the operation fails
        dialog = xbmcgui.Dialog()
        dialog.ok("File Operation Error", f"[COLOR red]do-magic: [/COLOR]Operation Denied.\n\nInvalid PWD or Function")

else:
    # Create the menu items.
    xbmcplugin.setContent(PLUGIN_ID, 'files')
    configureItem = xbmcgui.ListItem('[B]Configure... (Enter PWD/Function in Settings)[/B]')
    configureItem.setArt({'thumb': 'DefaultFolderBack.png'})
    configureItem.setInfo('video', {'plot': 'Configure the default actions in Settings panel for Prefix, Suffix, Colors and Insert/Swap modes.'})
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

