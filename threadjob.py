import threading
import local
import wx
import flickr
from wx.lib.pubsub import Publisher

class StoppableThread(threading.Thread):
  def __init__(self):
    super(StoppableThread, self).__init__()
    self._stop = threading.Event()

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()
    
class AddPhotosetThread(StoppableThread):
  def __init__(self, dir, callback = None):
    '''
    callback(local.Photoset)
    '''
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
    '''
    callback(local.Photoset, local.Photo, progress, done)
    '''
    StoppableThread.__init__(self)
    self.localPhotosets = localPhotosets
    self.callback       = callback
    self.start()
    
  def run(self):
    try:
      photoset_count  = 0
      for localPhotoset in self.localPhotosets:
        photoset_count  += 1
        print u"starting uploading...({0}/{1}) {2}".format(photoset_count, len(self.localPhotosets), localPhotoset.title)
        localPhotoset.upload(self.callback)
      
      print "DONE"
    except wx.PyDeadObjectError:
      pass
    
class LoadPhotosetsThread(StoppableThread):
  def __init__(self, flickr, callback = None):
    '''
    callback(photoset_num, total_photoset, flickr.Photoset, done)
    '''
    StoppableThread.__init__(self)
    self.flickr   = flickr
    self.callback = callback
    self.start()
    
  def run(self):
    try:
      photosets = flickr.load_photosets(self.callback)
    except wx.PyDeadObjectError:
      # thread is stopped
      pass
      
class DownloadPhotosetsThread(StoppableThread):
  def __init__(self, flickrPhotosets, callback = None):
    '''
    callback(flickr.Photoset, flickr.Photo, progress, done)
    '''
    StoppableThread.__init__(self)
    
    self.flickrPhotosets  = flickrPhotosets
    self.callback         = callback
    self.start()
    
  def run(self):
    try:
      for flickrPhotoset in self.flickrPhotosets:
        flickrPhotoset.download(self.callback)
    except wx.PyDeadObjectError:
      pass