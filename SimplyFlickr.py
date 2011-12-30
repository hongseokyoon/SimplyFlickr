import wx
import local
import remote
import flickr
import time
from wx.lib.pubsub import Publisher
import threadjob

class SplashDialog(wx.Dialog):
  def __init__(self, parent):
    wx.Dialog.__init__(self, parent, title = 'SimplyFlickr', size = (300, 200))

    sizer = wx.BoxSizer(wx.VERTICAL)
    
    gauge = wx.Gauge(self, size = (200, 50))
    gauge.SetRange(100)
    gauge.SetValue(50)
    
    sizer.Add(gauge, 1, wx.ALIGN_CENTER)
    sizer.Add(wx.Button(self))
    
    self.SetSizer(sizer)
    #self.SetAutoLayout(1)
    #sizer.Fit(self)
    
class AuthDialog(wx.Dialog):
  def __init__(self, parent, url):
    wx.Dialog.__init__(self, parent, title = 'Authentication')
    self.Center(wx.CENTER_ON_SCREEN)
    
    hyperlink_ctrl_authurl  = wx.HyperlinkCtrl(self, wx.ID_ANY, 'Go to authenticate this application', url)
    button_ok               = wx.Button(self, wx.ID_ANY, 'Click this button after authentication')
    
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(hyperlink_ctrl_authurl, flag = wx.ALL | wx.ALIGN_CENTER, border = 20)
    sizer.Add(button_ok, flag = wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_CENTER, border = 20)
    
    self.SetSizer(sizer)
    self.SetAutoLayout(1)
    sizer.Fit(self)
    
    self.Bind(wx.EVT_BUTTON, self.OnButtonOK, button_ok)
    self.Bind(wx.EVT_CLOSE, self.OnClose, self)
    
  def OnButtonOK(self, event):
    self.SetReturnCode(wx.ID_OK)
    self.Destroy()
    
  def OnClose(self, event):
    self.SetReturnCode(wx.ID_CANCEL)
    event.Skip()



class BasicPanel(wx.Panel):
  def __init__(self, parent, rootTitle):
    wx.Panel.__init__(self, parent)
    
    self.threads    = []
    
    sizer           = wx.BoxSizer(wx.VERTICAL)
    
    self.viewSizer  = wx.BoxSizer(wx.HORIZONTAL)
    self.inputSizer = wx.BoxSizer(wx.HORIZONTAL)
    
    self.photosets  = []
    self.tree       = wx.TreeCtrl(self)
    
    self.tree.AddRoot(rootTitle)
    
    sizer.Add(self.viewSizer, 1, flag = wx.EXPAND)
    sizer.Add(self.inputSizer, 0)
    
    if rootTitle == 'Local':
      self.viewSizer.Add(self.tree, 1, flag = wx.EXPAND | wx.TOP | wx.LEFT, border = 5)
    else:
      self.viewSizer.Add(self.tree, 1, flag = wx.EXPAND | wx.TOP | wx.RIGHT, border = 5)
    
    self.SetSizer(sizer)
    self.SetAutoLayout(1)
    sizer.Fit(self)
    
    self.tree.Bind(wx.EVT_LEFT_DOWN, self.OnTreeLeftClick)
  
  def _FindThread(self, name):
    return len([thread for thread in self.threads if thread.__class__.__name__]) > 0
    
  def _AddThread(self, thread):
    self.threads.append(thread)
    
  def _DelThread(self, name):
    self.threads  = filter(lambda thread: thread.__class__.__name__ != name, self.threads)
  
  def _StopThread(self, name):
    print ">> _StopThread name: {0}".format(name)
    map(lambda thread: thread.stop(), [thread for thread in self.threads if thread.__class__.__name__ == name])
    
  def StopThreads(self):
    print ">> StopThreads"
    map(lambda thread: thread.stop(), self.threads)
    self.threads  = []
  
  def _AddPhotoset(self, photoset):
    self.photosets.append(photoset)    
    self._UpdateTree()
  
  def _DelPhotoset(self, photoset):
    self.photosets.remove(photoset)
    self._UpdateTree()
    
  def _ClearPhotosets(self):
    del self.photosets[:]
    self._UpdateTree()
  
  def _GetPhotosetTitle(self, photoset):
    return photoset.title
  
  def _GetPhotoTitle(self, photo):
    return photo.title
  
  def _AppendTreeItem(self, photoset):
    item  = self.tree.AppendItem(self.tree.GetRootItem(), '[ ] ' + self._GetPhotosetTitle(photoset), data = wx.TreeItemData(photoset))
    photoset.data = item
    
    # sub trees - photos
    for photo in photoset.photos:
      photo.data  = self.tree.AppendItem(item, '[ ] ' + self._GetPhotoTitle(photo), data = wx.TreeItemData(photo))
    
    # expand root
    if self.tree.GetChildrenCount(self.tree.GetRootItem(), False) == 1:
      self.tree.Expand(self.tree.GetRootItem())

  def _UpdateTree(self):
    """
    Update tree items as photosets list
    """
    
    # remove all children if no photoset exists
    if len(self.photosets) == 0:
      self.tree.DeleteChildren(self.tree.GetRootItem())
      return
      
    itemID, cookie  = self.tree.GetFirstChild(self.tree.GetRootItem())
    
    for photoset in self.photosets:
      if not itemID.IsOk():
        self._AppendTreeItem(photoset)  # add photoset
        continue    
      
      while itemID.IsOk():
        treePhotoset  = self.tree.GetItemData(itemID).GetData()
        itemIDCopy  = itemID
        itemID  = self.tree.GetNextSibling(itemID)
        if (photoset == treePhotoset):  break       
        self.tree.Delete(itemIDCopy)
    
    while itemID.IsOk():
      itemIDCopy  = itemID
      itemID  = self.tree.GetNextSibling(itemID)
      self.tree.Delete(itemIDCopy)
  
  def _TreeSubItemChecked(self, itemID):
    if self.tree.GetChildrenCount(itemID) > 0:
      itemID, cookie  = self.tree.GetFirstChild(itemID)
      
      while itemID.IsOk():
        if not self._TreeItemChecked(itemID):
          return False
          
        itemID  = self.tree.GetNextSibling(itemID)
          
    return True
    
  def _CheckTreeSubItem(self, itemID, check = True):
    if self.tree.GetRootItem() != itemID and \
    self.tree.GetChildrenCount(itemID) > 0:
      itemID, cookie  = self.tree.GetFirstChild(itemID)
      
      while itemID.IsOk():
        self._CheckTreeItem(itemID, check)
        itemID  = self.tree.GetNextSibling(itemID)
        
  def _CheckTreeParentItem(self, itemID):
    itemID  = self.tree.GetItemParent(itemID)
    if itemID == self.tree.GetRootItem(): return
    
    self._CheckTreeItem(itemID, self._TreeSubItemChecked(itemID))
  
  def _TreeItemChecked(self, itemID):
    text  = self.tree.GetItemText(itemID)
    return True if text[1] == 'v' else False    
  
  def _TreeItemCheckable(self, itemID):
    return self.tree.GetRootItem() != itemID
  
  def _CheckTreeItem(self, itemID, check = True):
    text  = self.tree.GetItemText(itemID)    
    text  = ('[v]' if check else '[ ]') + text[3:]
    self.tree.SetItemText(itemID, text)
    
  def _ToggleTreeItemCheck(self, itemID):
    if not self._TreeItemCheckable(itemID): return
    
    checked = not self._TreeItemChecked(itemID)
    
    self._CheckTreeItem(itemID, checked)
    self._CheckTreeSubItem(itemID, checked)
    self._CheckTreeParentItem(itemID)
    
  def OnTreeLeftClick(self, event):
    itemID, flags = self.tree.HitTest(event.GetPosition())
    if (flags & wx.TREE_HITTEST_ONITEM) != 0:
      #self.tree.SetItemBold(itemID, not self.tree.IsBold(itemID))
      self._ToggleTreeItemCheck(itemID)
      
    event.Skip()
      
class LocalPanel(BasicPanel):
  def __init__(self, parent, uploadCallback = None):
    BasicPanel.__init__(self, parent, 'Local')
    
    self.uploadCallback = uploadCallback
    
    self.addButton    = wx.Button(self, label = '+', size = (30, 30))
    self.delButton    = wx.Button(self, label = '-', size = (30, 30))
    self.uploadButton = wx.Button(self, label = '^', size = (30, 30))
 
    self.inputSizer.Add(self.addButton, flag = wx.ALL, border = 5)
    self.inputSizer.Add(self.delButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)
    self.inputSizer.Add(self.uploadButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)

    self.Bind(wx.EVT_BUTTON, self.OnAddButton, self.addButton)
    self.Bind(wx.EVT_BUTTON, self.OnDelButton, self.delButton)
    self.Bind(wx.EVT_BUTTON, self.OnUploadButton, self.uploadButton)
    
    Publisher().subscribe(self.LoadLocalPhotoset, ('LoadLocalPhotoset'))
    Publisher().subscribe(self.UploadLocalPhotosets, ('UploadLocalPhotosets'))
    
  def OnAddButton(self, event):
    if self._FindThread('LoadLocalPHotoset'):
      wx.MessageDialog(self, u'Already adding folder...', 'Error', wx.OK).ShowModal()
      return
      
    dialog  = wx.DirDialog(self)
    if (dialog.ShowModal() == wx.ID_OK):
      dir = dialog.GetPath().replace('\\', '/')
      
      if len([photoset for photoset in self.photosets if photoset.dir == dir]) > 0: # dir already exists
        wx.MessageDialog(self, u'Duplicated path: {0}'.format(dir), 'Error', wx.OK).ShowModal()
      else:
        self._AddThread(threadjob.LoadLocalPhotoset(dir))
  
    dialog.Destroy()
    
  def OnDelButton(self, event):
    if not self.tree.GetSelection().IsOk(): return
    if self.tree.GetItemParent(self.tree.GetSelection()) != self.tree.GetRootItem(): return
    
    photoset  = self.tree.GetItemData(self.tree.GetSelection()).GetData()
    self._DelPhotoset(photoset)
    
  def OnUploadButton(self, event):
    if self._FindThread('UploadLocalPhotosets'):
      wx.MessageDialog(self, u'Already uploading...', 'Error', wx.OK).ShowModal()
      return
      
    self._AddThread(threadjob.UploadLocalPhotosets(self._GetCheckedPhotosets(), self.uploadCallback))
  
  def _GetCheckedPhotosets(self):
    # filter checked photos only
    checked_photosets = []

    for photoset in self.photosets:
      checked_photoset  = local.Photoset(dir = photoset.dir, data = photoset.data)
      checked_photoset.photos = [photo for photo in photoset.photos if self._TreeItemChecked(photo.data)]
      if len(checked_photoset.photos) > 0:
        checked_photosets.append(checked_photoset)
    
    return checked_photosets
  
  def _GetPhotosetTitle(self, photoset):  # override
    return u'{0}: {1} photo(s) {2:.2f} MB'.format(photoset.title, len(photoset.photos), photoset.size() / 1024.0 / 1024.0)

  # pubsub message callback ===================================================
  def LoadLocalPhotoset(self, msg):
    self._AddPhotoset(msg.data)
    self._DelThread('LoadLocalPhotoset')
    
  def UploadLocalPhotosets(self, msg):
    print 'Done uploading'
    print self.threads
    self._DelThread('UploadLocalPhotosets')
    print self.threads
    
class FlickrPanel(BasicPanel):
  def __init__(self, parent, downloadCallback = None):
    BasicPanel.__init__(self, parent, 'Flickr')
     
    self.downloadCallback = downloadCallback
    
    self.loadButton = wx.Button(self, label = 'L', size = (30, 30))
    self.downloadButton = wx.Button(self, label = 'v', size = (30, 30))
    
    self.inputSizer.Add(self.loadButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)
    self.inputSizer.Add(self.downloadButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)
  
    self.Bind(wx.EVT_BUTTON, self.OnLoadButton, self.loadButton)
    self.Bind(wx.EVT_BUTTON, self.OnDownloadButton, self.downloadButton)
    
    Publisher().subscribe(self.LoadRemotePhotoset, ('LoadRemotePhotoset'))
    Publisher().subscribe(self.LoadRemotePhotosets, ('LoadRemotePhotosets'))
    
  def OnLoadButton(self, event):
    self._ClearPhotosets()
    threadjob.LoadRemotePhotosets()
    
  def OnDownloadButton(self, event):
    threadjob.DownloadPhotosetsThread(self._GetCheckedPhotosets, self.downloadCallback)
    
  def _GetPhotosetTitle(self, photoset):
    return '%s: %d photo(s)' % (photoset.title, len(photoset.photos))

  # pubsub message callback ===================================================
  def LoadRemotePhotoset(self, msg):
    self._AddPhotoset(msg.data)
    
  def LoadRemotePhotosets(self, msg):
    pass
  
class MainFrame(wx.Frame):
  def __init__(self, parent):
    wx.Frame.__init__(self, parent, title = 'SimplyFlickr', size = (600, 400))
        
    splitter    = wx.SplitterWindow(self, style = wx.SP_BORDER)    
    self.localPanel  = LocalPanel(splitter)
    self.flickrPanel = FlickrPanel(splitter, self.Callback_LoadFlickrPhotosets)
    splitter.SplitVertically(self.localPanel, self.flickrPanel)
    
    # authentication
    (succ, auth_url)  = flickr.login()
    print (succ, auth_url)
    if not succ:
      if AuthDialog(self, auth_url).ShowModal() == wx.ID_OK:
        print flickr.auth()
      else:
        wx.MessageDialog(self, 'Failed to login', 'Error', wx.OK)
        self.Destroy()
        
    Publisher().subscribe(self.AddFlickrPhotoset, ('AddFlickrPhotoset'))
    
    splitter.SetSashPosition(self.GetClientSize()[0] / 2)
    splitter.SetMinimumPaneSize(100)
    #splitter.SetSashSize(5)
    
    self.SetSizeHints(300, 200)
    
    self.__ComposeStatusBar()
    
    self.Bind(wx.EVT_CLOSE, self.OnClose, self)
    
    self.Show()
  
  def LoadPhotosetsThreadCallback(self, photoset_num, total_photoset, photoset, done):    
    if photoset_num == total_photoset and done:
      self.UpdateStatusBar(100, 'Done')
    else:    
      if done:
        self.UpdateStatusBar(photoset_num / float(total_photoset) * 100, 'Loading %s... Done' % (photoset.title))
        time.sleep(0.2)
      else:
        self.UpdateStatusBar(photoset_num / float(total_photoset) * 100, 'Loading %s...' % (photoset.title))
      
  def UploadPhotosetsThreadCallback(self, photoset, photo, progress, done):
    print 'UploadPhotosetsThreadCallback:', photoset.title, photo.title, progress, done
    
  def OnClose(self, event):
    #if self.thread: self.thread.stop()
    self.localPanel.StopThreads()
    self.flickrPanel.StopThreads()
    event.Skip()
  '''  
  def __UpdateStatusBarText(self):
    width, height = self.statusBar.GetClientSize()
    width - 210
  '''
  def UpdateStatusBar(self, progress = None, text = None):
    if progress != None: self.statusBarGauge.SetValue(progress)
    if text != None: 
      self.statusBarString  = text
      
      self.statusBarText.SetLabel(text)
      #self.__UpdateStatusBarText()
    
  def __ComposeStatusBar(self):
    self.statusBar  = self.CreateStatusBar()
    
    statusBarClientWidth, statusBarClientHeight = self.statusBar.GetClientSize()
    
    #self.statusBarGauge = wx.Gauge(self.statusBar, pos = (2, 2), size = (200, statusBarClientHeight - 4))
    self.statusBarText  = wx.StaticText(self.statusBar, pos = (210, 2), size = (statusBarClientWidth - 210, statusBarClientHeight - 4))

  def AddFlickrPhotoset(self, msg):
    self.flickrPanel._AddPhotoset(msg.data)
    self.flickrPanel._UpdateTree()

  def Callback_LoadFlickrPhotosets(self, len, total, photoset, done):
    if done:
      Publisher().sendMessage(('AddFlickrPhotoset'), photoset)
      
app   = wx.App(False)
frame = MainFrame(None)
app.MainLoop()