import flickr
import local
import wx
import time
#from threading import Thread, Event
import threading
from wx.lib.pubsub import Publisher

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
    wx.Dialog.__init__(self, parent, title = 'Authentication', size = (300, 300))
    
    hyperlink_ctrl_authurl  = wx.HyperlinkCtrl(self, wx.ID_ANY, 'here', url, pos = (10, 10), size = (200, 100))
    
    button_ok = wx.Button(self, wx.ID_ANY, 'Complete authentication', pos = (10, 110), size = (100, 50))
    
    self.Bind(wx.EVT_BUTTON, self.OnButtonOK, button_ok)
    self.Bind(wx.EVT_CLOSE, self.OnClose, self)
    
  def OnButtonOK(self, event):
    self.SetReturnCode(wx.ID_OK)
    self.Destroy()
    
  def OnClose(self, event):
    self.SetReturnCode(wx.ID_CANCEL)
    event.Skip()

class StoppableThread(threading.Thread):
  def __init__(self):
    super(StoppableThread, self).__init__()
    self._stop = threading.Event()

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()
    
class UploadPhotosetsThread(StoppableThread):
  def __init__(self, localPhotosets, callback = None):
    StoppableThread.__init__(self)
    self.localPhotosets = localPhotosets
    self.callback       = callback
    self.start()
    
  def run(self):
    for localPhotoset in self.localPhotosets:
      localPhotoset.upload(self.callback)
    
class LoadPhotosetsThread(StoppableThread):
  def __init__(self, flickr, callback = None):
    StoppableThread.__init__(self)
    self.flickr   = flickr
    self.callback = callback
    self.start()
    
  def run(self):
    try:
      self.flickr.load_photosets(self.callback)
      Publisher().sendMessage(('UpdateFlickrTree'), None)
    except wx.PyDeadObjectError:
      pass
      
class LocalPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent)
    
    sizer       = wx.BoxSizer(wx.VERTICAL)
    
    viewSizer   = wx.BoxSizer(wx.HORIZONTAL)
    inputSizer  = wx.BoxSizer(wx.HORIZONTAL)
    
    self.photosets  = []
    self.tree       = wx.TreeCtrl(self, style = wx.TR_HIDE_ROOT)
    self.addButton  = wx.Button(self, label = '+', size = (30, 30))
    self.delButton  = wx.Button(self, label = '-', size = (30, 30))
    self.upButton   = wx.Button(self, label = '^', size = (30, 30))
    
    self.tree.AddRoot('root')    
    
    sizer.Add(viewSizer, 1, flag = wx.EXPAND)
    sizer.Add(inputSizer, 0)
    
    viewSizer.Add(self.tree, 1, flag = wx.EXPAND | wx.TOP | wx.LEFT, border = 5)
    inputSizer.Add(self.addButton, flag = wx.ALL, border = 5)
    inputSizer.Add(self.delButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)
    inputSizer.Add(self.upButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)
    
    self.SetSizer(sizer)
    self.SetAutoLayout(1)
    sizer.Fit(self)
    
    self.Bind(wx.EVT_BUTTON, self.OnAddButton, self.addButton)
    self.Bind(wx.EVT_BUTTON, self.OnDelButton, self.delButton)
    self.Bind(wx.EVT_BUTTON, self.OnUpButton, self.upButton)    
    self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSelChanged, self.tree)
    
  def OnAddButton(self, event):
    dialog  = wx.DirDialog(self)
    if (dialog.ShowModal() == wx.ID_OK):
      dir = dialog.GetPath().replace('\\', '/')
      
      if self.__PhotosetExist(dir):
        wx.MessageDialog(self, 'Duplicated path: %s' % dir, 'Error', wx.OK).ShowModal()
      else:
        self.__AddPhotoset(local.Photoset(dir))
  
    dialog.Destroy()
    
  def OnDelButton(self, event):
    if not self.tree.GetSelection().IsOk(): return
    if self.tree.GetItemParent(self.tree.GetSelection()) != self.tree.GetRootItem(): return
    
    photoset  = self.tree.GetItemData(self.tree.GetSelection()).GetData()
    self.__DelPhotoset(photoset)
    
  def OnUpButton(self, event):
    #UploadPhotosetsThread(self.photosets, self.UploadPhotosetsThreadCallback)
    pass
      
  def OnTreeSelChanged(self, event):
    #photoset  = self.tree.GetItemData(event.GetItem()).GetData()
    #if localPhotoset:
    #  self.statusBar.SetStatusText(localPhotoset.dir) 
    pass
  
  def __PhotosetExist(self, dir):
    for photoset in self.photosets:
      if photoset.dir == dir:
        return True
        
    return False
  
  def __AddPhotoset(self, photoset):
    self.photosets.append(photoset)    
    self.__UpdateTree()
  
  def __DelPhotoset(self, photoset):
    self.photosets.remove(photoset)
    self.__UpdateTree()  
  
  def __GetPhotosetTitle(self, photoset):
    total_size  = 0
    for photo in photoset.photos:
      total_size  += photo.size
    
    return '%s: %d photo(s) %.1d MB' % (photoset.title, len(photoset.photos), total_size / 1024.0 / 1024.0)
  
  def __GetPhotoTitle(self, photo):
    return photo.title
  
  def __AppendTreeItem(self, photoset):
    item  = self.tree.AppendItem(self.tree.GetRootItem(), self.__GetPhotosetTitle(photoset), data = wx.TreeItemData(photoset))
    
    # sub trees - photos
    for photo in photoset.photos:
      self.tree.AppendItem(item, self.__GetPhotoTitle(photo), data = wx.TreeItemData(photo))

  def __UpdateTree(self):
    """Update tree items as photosets list"""    
    if len(self.photosets) == 0:
      self.tree.DeleteAllItems()
      return
    
    print 'list:', self.photosets
    itemID, cookie  = self.tree.GetFirstChild(self.tree.GetRootItem())
    
    for photoset in self.photosets:
      if not itemID.IsOk():
        self.__AppendTreeItem(photoset)
        continue
      
      #treePhotoset  = self.tree.GetItemData(itemID).GetData()      
      
      while itemID.IsOk():
        treePhotoset  = self.tree.GetItemData(itemID).GetData()
        itemIDCopy  = itemID
        itemID  = self.tree.GetNextSibling(itemID)
        if (photoset == treePhotoset):  break
        
        self.tree.Delete(itemIDCopy)
    
    while itemID.IsOk():
      itemIDCyop  = itemID
      itemID  = self.tree.GetNextSibling(itemID)
      self.tree.Delete(itemIDCopy)
    
class FlickrPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent)
    
    sizer       = wx.BoxSizer(wx.VERTICAL)
    
    viewSizer   = wx.BoxSizer(wx.HORIZONTAL)
    inputSizer  = wx.BoxSizer(wx.HORIZONTAL)
    
    self.tree       = wx.TreeCtrl(self, style = wx.TR_HIDE_ROOT)
    self.loadButton = wx.Button(self, label = 'L', size = (30, 30))
    self.downButton = wx.Button(self, label = 'v', size = (30, 30))
    
    self.tree.AddRoot('root')
    
    sizer.Add(viewSizer, 1, flag = wx.EXPAND)
    sizer.Add(inputSizer, 0)
    
    viewSizer.Add(self.tree, 1, flag = wx.EXPAND | wx.TOP | wx.RIGHT, border = 5)
    inputSizer.Add(self.loadButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)
    inputSizer.Add(self.downButton, flag = wx.TOP | wx.RIGHT | wx.BOTTOM, border = 5)
    
    self.SetSizer(sizer)
    self.SetAutoLayout(1)
    sizer.Fit(self)
    
class MainFrame(wx.Frame):
  def __init__(self, parent):
    wx.Frame.__init__(self, parent, title = 'SimplyFlickr', size = (600, 400))
    
    self.localPhotosets   = []
    self.flickrPhotosets  = []
    
    splitter  = wx.SplitterWindow(self, style = wx.SP_BORDER)
    
    localPanel  = LocalPanel(splitter)
    flickrPanel = FlickrPanel(splitter)
    splitter.SplitVertically(localPanel, flickrPanel)
    
    #self.__ComposeLeftPanel(leftPanel)
    #self.__ComposeRightPanel(rightPanel)
    
    #SplashDialog(self).ShowModal()
    
    if not flickr.login():
      if AuthDialog(self, flickr.auth()).ShowModal() == wx.ID_OK:
        flickr.login()
      else:
        wx.MessageDialog(self, 'Failed to login', 'Error', wx.OK)
        self.Destroy()
     
    Publisher().subscribe(self.AfterLoadPhotosets, ('UpdateFlickrTree'))
    #self.thread = LoadPhotosetsThread(flickr, self.LoadPhotosetsThreadCallback)
    #flickr.load_photosets()
    #self.__UpdateFlickrTree()
    
    splitter.SetSashPosition(self.GetClientSize()[0] / 2)
    splitter.SetMinimumPaneSize(100)
    #splitter.SetSashSize(5)
    
    self.SetSizeHints(300, 200)
    '''
    self.statusBar  = self.CreateStatusBar()
    self.statusBar.StatusText = 'SimplyFlickr'
    
    statusBarClientWidth, statusBarClientHeight = self.statusBar.GetClientSize()
    statusBarGauge = wx.Gauge(self.statusBar, size = (statusBarClientWidth / 2 - 20, statusBarClientHeight - 6), pos = (statusBarClientWidth / 2 + 10, 3))
    '''
    
    self.__ComposeStatusBar()
    
    self.Bind(wx.EVT_SIZE, self.OnSize, self)
    self.Bind(wx.EVT_CLOSE, self.OnClose, self)
    '''
    self.Bind(wx.EVT_BUTTON, self.OnAddButton, localPanel.addButton)
    self.Bind(wx.EVT_BUTTON, self.OnDelButton, localPanel.delButton)
    self.Bind(wx.EVT_BUTTON, self.OnUpButton, localPanel.upButton)    
    self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnLocalTreeSelChanged, localPanel.tree)
    '''
    self.Bind(wx.EVT_BUTTON, self.OnDownButton, flickrPanel.downButton)
    
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
    
  def OnSize(self, event):
    
    event.Skip()
    
  def OnClose(self, event):
    if self.thread: self.thread.stop()
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
    
    self.statusBarGauge = wx.Gauge(self.statusBar, pos = (2, 2), size = (200, statusBarClientHeight - 4))
    self.statusBarText  = wx.StaticText(self.statusBar, pos = (210, 2), size = (statusBarClientWidth - 210, statusBarClientHeight - 4))

  def OnAddButton(self, event):
    dialog  = wx.DirDialog(self)
    if (dialog.ShowModal() == wx.ID_OK):
      dir = dialog.GetPath().replace('\\', '/')
      self.__AddLocalPhotoset(dir)
    dialog.Destroy()
    
  def OnDelButton(self, event):    
    self.__DelLocalPhotoset(self.localTree.GetSelection())
    
  def OnUpButton(self, event):
    UploadPhotosetsThread(self.localPhotosets, self.UploadPhotosetsThreadCallback)
    
  def OnDownButton(self, event):
    pass
  
  def OnLocalTreeSelChanged(self, event):
    localPhotoset = self.localTree.GetItemData(event.GetItem()).GetData()
    if localPhotoset:
      self.statusBar.SetStatusText(localPhotoset.dir)
  
  def AfterLoadPhotosets(self, msg):
    self.__UpdateFlickrTree()
    
  def __AddLocalPhotoset(self, dir):
    if len([photoset for photoset in self.localPhotosets if photoset.dir == dir]) > 0:
      wx.MessageDialog(self, 'Duplicated path: %s' % dir, 'Error', wx.OK)
      return
    
    # manipulate localPhotoset array
    new_photoset  = local.Photoset(dir)
    self.localPhotosets.append(new_photoset)
    
    # manipulate tree ctrl
    item  = self.localTree.AppendItem(self.localTreeRoot, self.__GetLocalPhotosetTitle(new_photoset), data = wx.TreeItemData(new_photoset))
    
    for photo in new_photoset.photos:
      self.localTree.AppendItem(item, photo.title)
    
  def __DelLocalPhotoset(self, itemID):
    localPhotoset = self.localTree.GetItemData(itemID).GetData()
    if localPhotoset:
      self.localPhotosets.remove(localPhotoset)
      self.localTree.Delete(itemID)
        
  
  def __GetLocalPhotosetTitle(self, photoset):
    total_size  = 0
    for photo in photoset.photos:
      total_size  += photo.size
    
    return '%s: %d photo(s) %.1d MB' % (photoset.title, len(photoset.photos), total_size / 1024.0 / 1024.0)
  
  def __GetFlickrPhotosetTitle(self, photoset):
    return '%s: %d photo(s)' % (photoset.title, len(photoset.photos))
  # __UpdatLlocalTree(self):
  #  pass
    
  def __UpdateFlickrTree(self):
    self.flickrTree.DeleteAllItems()
    
    for photoset in flickr.Photosets:
      item  = self.flickrTree.AppendItem(self.flickrTreeRoot, self.__GetFlickrPhotosetTitle(photoset), data = wx.TreeItemData(photoset))
      for photo in photoset.photos:
        self.flickrTree.AppendItem(item, photo.title, data = wx.TreeItemData(photo))
    
app   = wx.App(False)
frame = MainFrame(None)
app.MainLoop()