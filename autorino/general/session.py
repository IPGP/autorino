#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 15:37:46 2024

@author: psakicki
"""

class SessionGnss:
    def __init__(self,name,protocol,hostname,remote_dir,tmp_dir,
                 remote_fname, sta_user,sta_pass,site,session_period):
        self.name = name
        self.protocol = protocol
        self.hostname = hostname
        self.remote_dir = remote_dir ## setter bellow
        self.tmp_dir = tmp_dir
        self.remote_fname = remote_fname
        self.sta_user = sta_user
        self.sta_pass = sta_pass  
        self.site = site ## setter bellow
        self.site4 = site  ## setter bellow       
        self.site9 = site   ## setter bellow         
        self.session_period = session_period
        self.translate_dict = self._translate_dict_init()
        
    def __repr__(self):
        return "session {} on {}".format(self.session_period,self.site4)
        
    #test sur session period !!!!!! sur protocol !!!

    ############ getters and setters 
    @property
    def remote_dir(self):
        return self._remote_dir
    
    @remote_dir.setter
    def remote_dir(self,value):
        if value[0] == "/":
            self._remote_dir = "".join(list(value)[1:])
        else:
            self._remote_dir = value

    @property
    def site4(self):
        return self._site4
    @site4.setter
    def site4(self,value):
        self._site4 = value[:4]

    @property
    def site9(self):
        return self._site9
    @site9.setter
    def site9(self,value):
        if len(value) == 9:
            self._site9 = value
        elif len(value) == 4:
            self._site9 = value + "00XXX"
        else:
            raise Exception("given site code != 9 or 4 chars.: " + value)
            
    ############ methods
    def _translate_dict_init(self):
        """
        generate the translation dict based on all the SessionGnss 
        object attributes
        
        site code have 2 declinations: 
        <site> (lowercase) and <SITE> (uppercase)
        """
        trsltdict = dict()
        attributes = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        for a in attributes:
            trsltdict[a] = str(getattr(self, a)).upper()
            if a.lower() in ('site','site4','site9'):
                trsltdict[a.upper()] = str(getattr(self, a)).upper()
                trsltdict[a.lower()] = str(getattr(self, a)).lower()
        return trsltdict


