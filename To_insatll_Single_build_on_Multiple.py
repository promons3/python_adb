import sys # Need to have acces to sys.stdout
import string
import os
import subprocess
import pickle
import tempfile
import datetime
import multiprocessing
import time
import codecs
import pickle

from subprocess import STDOUT, check_output
from multiprocessing import Pool
from functools import partial
from subprocess import DEVNULL


def split_lines(s):
   
    """Splits lines in a way that works even on Windows and old devices.
    Windows will see \r\n instead of \n, old devices do the same, old devices on Windows will see \r\r\n.
    """
    # rstrip is used here to workaround a difference between splineslines and
    # re.split:
    # >>> 'foo\n'.splitlines()
    # ['foo']
    # >>> re.split(r'\n', 'foo\n')
    # ['foo', '']
    return re.split(r'[\r\n]+', s.rstrip())

class Multi(): 
     
    def folder_creation(filepath):
        print()
        folderpath = input('Please provide the path of your .apk file:-')
        
        if os.path.isfile(folderpath):
            try:
                apklist = folderpath
                print('')
                return apklist
            except:
                raise       
        else:
            print('')
            print('*****Given path is not a valid, so please check out for correct one*****')
            time.sleep(1)
            exit()
    
    
    def collect_deviceid(self):
        line2 = []
        out = split_lines(subprocess.check_output(['adb', 'devices']).decode('utf-8'))
        for line in out[1:]:
            
            if not line.strip():
                continue
            if 'offline' in line:
                continue
            if 'unauthorized' in line: 
                continue
            if 'unknown' in line: 
                continue
 
            serial, _ = re.split(r'\s+', line, maxsplit=1)
            line2.append(serial)     
        return line2
        
    def menifest(self):
       
        pipe = subprocess.Popen(['aapt', 'dump', 'badging', apk2], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding = "utf-8", error="ignore")
        result = pipe.communicate()[0] #byte to string coversion used decode method.
        result =result.strip()
        file = codecs.open('newdump.txt', 'w', encoding='ascii', errors='ignore')
        file.writelines(str(result))
        file.close()
        with codecs.open('newdump.txt', 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                if "package: name=" in line:
                    line = line.strip('package: name=')
                    head, sep, tail = line.partition(' ')
                    head = line.partition(' ')
                    pack = head[0]
                    print('Package name of the application is:-', pack)
                elif "launchable-activity: name=" in line:
                    line = line.strip('launchable-activity: name=')
                    activity, sep, tail = line.partition(' ')
                    print('Activity name of application is:-', activity)  
                    print('')                    
                else:
                    pass                
        f.close()
        os.remove('newdump.txt')
        return (pack, activity)
        
    def app_installation(self, apk2, packagename, activityname, line1):
        
        self.apk2 = apk2
        self.line1 = line1     
        line2 = ''.join([str(x) for x in line1]) 
        
        dir_path = os.path.dirname(os.path.realpath(apk2))
        
        os.chdir(dir_path)
        DEVNULL = open(os.devnull, 'wb')
        device_name = subprocess.check_output(['adb', '-s', line2, 'shell', 'getprop', 'ro.product.model'], shell=True).decode('ascii').strip()
        
        pit = subprocess.Popen(['adb', '-s', line2, 'install', '-r', apk2], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        pipe, err = pit.communicate()
        file = open('%s_hi.txt' %line2, 'wb')
        pickle.dump((str(pipe), str(err)), file) # to add pipe and err objects in a one text file, so used pickle
        file.close()
        with open('%s_hi.txt' %line2, 'rb') as f2:
            f3 = f2.readlines()
            for f4 in f3:
                if b"Failure" in f4:
                    f4 = f4.rstrip()
                    f4 = f4.decode('utf8', 'ignore')
                    print('your application is NOT INTSALLED on', device_name, 'as error message appears', str(f4))
                    print('')
                    break
                              
            else:
                try:
                    launch = subprocess.Popen(['adb', '-s', line2, 'shell', 'am', 'start', '-n', packagename +'/' + activityname], stdout=DEVNULL, shell=True)
                    print('your application has launched on device', device_name, 'keep testing On and Enjoy too!!!.')
                    print('')
                except(OSError, IOError) as e:
                    print(e)                    
        f2.close()
        os.remove('%s_hi.txt' %line2)
                
 
if __name__ == "__main__":
    
    while True:
        c = Multi()
        line1 = c.collect_deviceid()
    
        if not line1:
            print('')
            print('*******Devices are not found in  \'device\' mode, or devices are not connected. please check the connection(s).*******')
            time.sleep(3)
            exit()
        apk2 = c.folder_creation()
        print('')
        print("***********Build installation is going on...**************...Please be patient & keep smiling :)")
        print('')
        
        packagename, activityname = c.menifest()
        p = Pool()
        
        try:
            func = partial(c.app_installation, apk2, packagename, activityname)
            p.map(func, line1)
        except KeyboardInterrupt:
            p.close()
            p.join()
   
