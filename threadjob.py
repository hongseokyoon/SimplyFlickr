import threading
import local
import wx
#from wx.lib.pubsub import Publisher

class StoppableThread(threading.Thread):
  def __init__(self):
    super(StoppableThread, self).__init__()
    self._stop = threading.Event()

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()
    
class AddPhotosetThread(StoppableThread):
  def __init__(self, dir, callback):
    StoppableThread.__init__(self)
    self.dir      = dir
    self.callback = callback
    self.start()
    
  def run(self):
    try:    
      print 'run AddPhotosetThread'
      localPhotoset = local.Photoset(self.dir)
      print self.dir
      print localPhotoset
      if self.callback: self.callback(localPhotoset)
    except wx.PyDeadObjectError:
      pass
    
class UploadPhotosetsThread(StoppableThread):
  def __init__(self, localPhotosets, callback = None):
    StoppableThread.__init__(self)
    self.localPhotosets = localPhotosets
    self.callback       = callback
    self.start()
    
  def run(self):
    try:
      for localPhotoset in self.localPhotosets:
        localPhotoset.upload(self.callback)
    except wx.PyDeadObjectError:
      pass
    
class LoadPhotosetsThread(StoppableThread):
  def __init__(self, flickr, callback = None):
    StoppableThread.__init__(self)
    self.flickr   = flickr
    self.callback = callback
    self.start()
    
  def run(self):
    try:
      self.flickr.load_photosets(self.callback)
      #Publisher().sendMessage(('UpdateFlickrTree'), None)
    except wx.PyDeadObjectError:
      # thread is stopped
      pass
      
class DownloadPhotosetsThread(StoppableThread):
  def __init__(self, flickrPhotosets, callback = None):
    StoppableThread.__init__(self)
    
    self.flickrPhotosets  = flickrPhotosets
    self.callback         = callback
    self.start()
    
  def run(self):
    try:
      for flickrPhotoset in self.flickrPhotosets:
        flickrPhotoset.download(callback)
    except wx.PyDeadObjectError:
      pass