###### BASED on GeodeZYX log

###### USEFUL TUTOS
## https://coderzcolumn.com/tutorials/python/logging-simple-guide-to-log-events-in-python
## https://coderzcolumn.com/tutorials/python/logging-config-simple-guide-to-configure-loggers-from-dictionary-and-config-files-in-python#2

log_config_dict = {
    "version":1,
    'disable_existing_loggers': False,

    
    "root":{
        "handlers" : ["console_root"],
        "level": "WARN",
        "propagate": False
    },
    
    
    'loggers': {
        "autorino" : {
            "handlers" : ["console_gyxz"],
            "level": "DEBUG",
            "propagate": False

        }
    },
    
    "handlers":{        
        "console_root":{
#            "formatter":"fmtgzyx1",
            "class":"logging.StreamHandler",
            "level":"DEBUG",
        },
        "console_gyxz":{
            "formatter":"fmtgzyx1",
            "class":"logging.StreamHandler",
            "level":"DEBUG",
        }
    },
    "formatters":{
        "fmtgzyx1": {
            "format": "%(asctime)s.%(msecs)03d|%(levelname).1s|%(funcName)-15s|%(message)s",
            "datefmt":"%y%m%dT%H:%M:%S"
        }
    },
}

