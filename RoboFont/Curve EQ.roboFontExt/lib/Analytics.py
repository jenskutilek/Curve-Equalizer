# -*- coding: utf-8 -*-

from AppKit import NSMutableDictionary
from mojo.extensions import getExtensionDefault
from os.path import exists, expanduser, join
from time import time

from EQExtensionID import extensionID


DEBUG = getExtensionDefault("%s.%s" %(extensionID, "debug"), False)


class Analytics(object):
    
    def __init__(self):
        self.persistent_storage_dir = join(
            expanduser("~"),
            "Library",
            "Application Support",
            "CurveEQ",
        )
        self.persistent_storage_file = "%s.plist" % extensionID
        self.persistent_storage_path = join(self.persistent_storage_dir, self.persistent_storage_file)
        self.time = str(int(time()))
        self.session = {}
        self.events = {}
        self.session_active = False
        self.load()
    
    def load(self):
        if not exists(self.persistent_storage_dir):
            from os import mkdir
            mkdir(self.persistent_storage_dir)
        self.data = NSMutableDictionary.dictionaryWithContentsOfFile_(self.persistent_storage_path)
        if self.data is None:
            self.data = NSMutableDictionary()
            self.data["uuid"] = self.get_uuid()
            self.data["path"] = __file__
            self.data["exid"] = extensionID
            self.data["sessions"] = {}
    
    def save(self):
        if self.session_active:
            self.end_session()
        result = self.data.writeToFile_atomically_(self.persistent_storage_path, True)
        if DEBUG:
            if not result:
                print "ERROR writing stats to file."
    
    def start_session(self):
        self.time = str(int(time()))
        self.session = {}
        self.events = {}
        self.session_active = True
    
    def end_session(self):
        if self.events:
            self.session["events"] = self.events
        self.session["end"] = int(time())
        self.data["sessions"][self.time] = self.session
        if DEBUG:
            print self.data
        self.session_active = False
    
    def clear(self):
        self.data["sessions"] = {}
    
    def send(self):
        pass
    
    def get_uuid(self):
        import uuid
        return str(uuid.uuid4())
    
    def log(self, event):
        if event in self.events:
            self.events[event].append(int(time()))
        else:
            self.events[event] = [int(time())]


if __name__ == "__main__":
    a = Analytics()
    a.start_session()
    a.log("quad")
    a.log("free")
    a.log("quad")
    a.save()