# encoding: utf-8

import gvsig
from gvsig import getResource
from gvsig.libs.formpanel import FormPanel, load_icon

from fnmatch import fnmatch

from org.gvsig.andami import PluginsLocator
from org.gvsig.tools.swing.api import ToolsSwingLocator
from org.gvsig.app import ApplicationLocator
from org.gvsig.tools.swing.api.windowmanager import WindowManager_v2
from org.gvsig.andami.preferences import AbstractPreferencePage
from org.gvsig.tools import ToolsLocator

from java.io import File
from java.io import FileOutputStream
from java.util import Properties
from javax.swing import JPanel
from javax.swing import ListCellRenderer
from javax.swing import DefaultListModel
from javax.swing import JCheckBox
from javax.swing import JLabel
from java.awt import GridBagLayout
from java.awt import GridBagConstraints
from javax.swing import UIManager
from java.awt import Dimension
from javax.swing import SwingUtilities
from java.awt.event import ActionListener
from java.awt import BorderLayout

class ActionListCellRenderer(FormPanel,ListCellRenderer):
  def __init__(self, theList):
    FormPanel.__init__(self,getResource(__file__,"ActionListRenderer.xml"))
    self.theList = theList
    self.actionsManager = PluginsLocator.getActionInfoManager()
    defaults = UIManager.getDefaults()
    self.selectionBackground = defaults.getColor("List.selectionBackground")
    self.selectionForeground = defaults.getColor("List.selectionForeground")
    self.background = defaults.getColor("List.background")
    self.foreground = defaults.getColor("List.foreground")
    self.asJComponent().setBackground(self.background)
    self.iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
    noicon = self.iconTheme.getNoIcon()
    self.lblIcon.setPreferredSize(Dimension(noicon.getIconWidth(), noicon.getIconHeight()))


  def getListCellRendererComponent(self,list, actionName, index, isSelected, cellHasFocus):
    action = self.actionsManager.getAction(actionName)
    if action == None:
      self.lblIcon.setIcon(None)
      self.lblName.setText("")
      self.lblName.setBackground(self.background)
      self.lblName.setForeground(self.foreground)
    else:
      if isSelected == 1:
        self.lblName.setBackground(self.selectionBackground)
        self.lblName.setForeground(self.selectionForeground)
      else:
        self.lblName.setBackground(self.background)
        self.lblName.setForeground(self.foreground)
      if self.iconTheme.exists(action.getIconName()) :
        self.lblIcon.setIcon(action.getIcon())
      else:
        self.lblIcon.setIcon(None)
      self.lblName.setText(action.getName())

    return self.asJComponent()


class ActionConfiguratorPanel(FormPanel,ActionListener):
  """
  Este panel se encarga de la activacion y desactivacion de las
  acciones de gvSIG.
  """
  def __init__(self):
    FormPanel.__init__(self,getResource(__file__,"actionConfigurator.xml"))
    self.actionsManager = PluginsLocator.getActionInfoManager()
    self._hasChanges = False
    self.initLists()
    self.initComponents()

  def hasChanges(self):
    return self._hasChanges;

  def resetChangesFlags(self):
    self._hasChanges = False

  def initLists(self):
    self.activeActionNames = list()
    self.inactiveActionNames = list()
    for action in self.actionsManager.getActions():
      if action.isActive():
        self.activeActionNames.append(action.getName())
      else:
        self.inactiveActionNames.append(action.getName())
    self.activeActionNames.sort()
    self.inactiveActionNames.sort()

  def updateLists(self):
    self.updateActionsList(self.activeActionNames, self.lstActiveActions)
    self.updateActionsList(self.inactiveActionNames, self.lstInactiveActions)

  def updateActionsList(self, names,jlist, pattern=None):
    if pattern != None:
      if not ("*" in pattern or "?" in pattern) :
        pattern = "*" + pattern + "*"
    model = DefaultListModel()
    for actionName in names:
      if pattern == None or fnmatch(actionName,pattern):
        model.addElement(actionName)
    jlist.setModel(model)

  def initComponents(self):
    self.lstActiveActions.setCellRenderer(ActionListCellRenderer(self.lstActiveActions))
    self.lstInactiveActions.setCellRenderer(ActionListCellRenderer(self.lstInactiveActions))
    iconTheme = ToolsSwingLocator.getIconThemeManager().getCurrent()
    self.btnInactiveAction.setIcon(iconTheme.get("go-next"))
    self.btnActiveAction.setIcon(iconTheme.get("go-previous"))
    self.btnInactiveAction.setText("")
    self.btnActiveAction.setText("")
    self.setPreferredSize(600,350)
    self.updateLists()
    self.translateUI()

  def translateUI(self):
    i18nManager = ToolsLocator.getI18nManager()

    self.lblActiveActions.setText(i18nManager.getTranslation("_Active_actions"))
    self.lblInactiveActions.setText(i18nManager.getTranslation("_Inactive_actions"))
    self._title = i18nManager.getTranslation("_Action_configurator")
    self._header = i18nManager.getTranslation("_Select_active_actions")

  def applyChanges(self):
    for actionName in self.activeActionNames:
      action = self.actionsManager.getAction(actionName)
      if action != None:
        action.setActive(True)
    for actionName in self.inactiveActionNames:
      action = self.actionsManager.getAction(actionName)
      if action != None:
        action.setActive(False)
    application = ApplicationLocator.getManager()
    application.refreshMenusAndToolBars()
    self._hasChanges = False

  def saveState(self):
    home = PluginsLocator.getManager().getApplicationHomeFolder()
    props = Properties()
    for actionName in self.inactiveActionNames:
      props.setProperty(actionName,"false")
    fos = FileOutputStream(File(home,"actions-states.properties"))
    props.store(fos,"")
    fos.close()

  def btnInactiveAction_click(self,*args):
    actionName = self.lstActiveActions.getSelectedValue()
    if actionName in ("",None):
      return
    self.activeActionNames.remove(actionName)
    self.inactiveActionNames.append(actionName)
    self.inactiveActionNames.sort()
    self.updateLists()
    self._hasChanges = True

  def btnActiveAction_click(self,*args):
    actionName = self.lstInactiveActions.getSelectedValue()
    if actionName in ("",None):
      return
    self.inactiveActionNames.remove(actionName)
    self.activeActionNames.append(actionName)
    self.activeActionNames.sort()
    self.updateLists()
    self._hasChanges = True

  def txtFilterActiveActions_keyPressed(self,event):
    names = self.activeActionNames
    jlist = self.lstActiveActions
    jtext = self.txtFilterActiveActions
    if event.getKeyChar() == "\x1b" : # ESC
      self.updateActionsList(names, jlist)
      jtext.setText("")
      return
    if event.getKeyChar() == "\n" :
      if  jtext.getText()=="":
        self.updateActionsList(names, jlist)
      else:
        self.updateActionsList(names, jlist, jtext.getText())
      return

  def txtFilterInactiveActions_keyPressed(self,event):
    names = self.inactiveActionNames
    jlist = self.lstInactiveActions
    jtext = self.txtFilterInactiveActions
    if event.getKeyChar() == "\x1b" : # ESC
      self.updateActionsList(names, jlist)
      jtext.setText("")
      return
    if event.getKeyChar() == "\n" :
      if  jtext.getText()=="":
        self.updateActionsList(names, jlist)
      else:
        self.updateActionsList(names, jlist, jtext.getText())
      return

  def actionPerformed(self, event):
    if event.getID()==WindowManager_v2.BUTTON_OK:
      self.applyChanges()
      self.saveState()
      self.hide()

    elif event.getID()==WindowManager_v2.BUTTON_CANCEL:
      self.hide()

    elif event.getID()==WindowManager_v2.BUTTON_APPLY:
      self.applyChanges()

  def showDialog(self,title=None):
    if title == None:
      title = self._title
    self.showWindow(title, WindowManager_v2.MODE.DIALOG)

  def showWindow(self,title=None, mode=WindowManager_v2.MODE.WINDOW):
    if title == None:
      title = self._title
    dialog = ToolsSwingLocator.getWindowManager().createDialog(
        self.asJComponent(),
        title,
        self._header,
        WindowManager_v2.BUTTONS_APPLY_OK_CANCEL
    )
    dialog.addActionListener(self)
    dialog.show(mode)

class ActionConfiguratorPreferencePage(AbstractPreferencePage):
  """
  Esta clase se encarga de gestionar que el panel que maneja
  la activacion/desactivacion de acciones se pueda presentar
  como una pagina de preferencias de gvSIG
  """
  def __init__(self):
    AbstractPreferencePage.__init__(self)
    self.actionsPanel = ActionConfiguratorPanel()
    self.setLayout(BorderLayout())
    self.add(self.actionsPanel.asJComponent(), BorderLayout.CENTER)
    self._icon = load_icon((__file__,"images", "active-actions.png"))
    self.translateUI()

  def translateUI(self):
    i18nManager = ToolsLocator.getI18nManager()

    self._title = i18nManager.getTranslation("_Action_configurator")

  def getID(self):
    return "ActionConfiguratorPreferencePage"

  def getTitle(self):
    return self._title

  def getIcon(self):
    return self._icon

  def isResizeable(self):
    return True

  def isValueChanged(self):
    return self.actionsPanel.hasChanges()

  def setChangesApplied(self):
    self.actionsPanel.resetChangesFlags()

  def getPanel(self):
    return self

  def initializeDefaults(self):
    self.actionsPanel.initLists()
    self.actionsPanel.updateLists()

  def storeValues(self):
    self.actionsPanel.applyChanges()
    self.actionsPanel.saveState()

  def initializeValues(self):
    self.actionsPanel.initLists()
    self.actionsPanel.updateLists()

def selfRegister():
  #
  # Registramos los ficheros de traducciones
  i18nManager = ToolsLocator.getI18nManager()
  i18nManager.addResourceFamily("text",File(getResource(__file__,"i18n")))

  #
  # Registramos la pagina de propiedades en las preferencias de gvSIG.
  manager = PluginsLocator.getManager()
  preferencesExtension = manager.getExtension("org.gvsig.coreplugin.PreferencesExtension")
  preferencesExtension.addPreferencesPage(ActionConfiguratorPreferencePage())

def main(*args):
  #
  # Esta funcion main es solo para hacer pruebas
  #
  #selfRegister()
  #i18nManager = ToolsLocator.getI18nManager()
  #i18nManager.addResourceFamily("text",File(getResource(__file__,"i18n")))
  panel = ActionConfiguratorPanel()
  panel.showWindow()
