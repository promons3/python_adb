import sys # Need to have acces to sys.stdout
import string
import os
import subprocess
import pickle
import tempfile
import datetime
import multiprocessing
import time
import shutil
import codecs
import glob
import re

from subprocess import STDOUT, check_output
#from multiprocessing.dummy import Pool as ThreadPool
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
    
class FindDeviceError(RuntimeError):
    pass


class DeviceNotFoundError(FindDeviceError):
    def __init__(self, serial):
        self.serial = serial
        super(DeviceNotFoundError, self).__init__(
            'No device with serial {}'.format(serial))


class NoUniqueDeviceError(FindDeviceError):
    def __init__(self):
        super(NoUniqueDeviceError, self).__init__('No unique device')    

class Multi(): 
     
    def folder_creation(filepath):
        #global folderpath
        apklist = []
        folderpath = input('Please provide the path of APKs folder:-')
        
        if os.path.exists(folderpath):
            directory = os.path.normpath(folderpath)
            apklist = glob.glob(os.path.join(folderpath, '*.apk'))
            if not apklist:
                print('')
                print('******* in the given path, .apk files are not found. Please check once again. ********')
                time.sleep(1)
                exit()
            else:    
                return apklist
                        
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
            if 'unknwon' in line: 
                continue    

            serial, _ = re.split(r'\s+', line, maxsplit=1)
            line2.append(serial)     
        return line2
    
    def app_installation(self, apk2, packagename, activityname, line1):
        
        self.apk2 = apk2
        self.line1 = line1     
        line2 = ''.join([str(x) for x in line1]) 
        apk3 = ''.join([str(x1) for x1 in apk2])
        dir_path = os.path.dirname(os.path.realpath(apk2))
        os.chdir(dir_path)
        file_name = os.path.basename(apk2).rsplit('.', 1)[0]
        #print('directory path with file name', dir_path) juzt to check directory path
        today = datetime.date.today()
        subdir = "AppTesting_On_"
        
        final_directory = os.path.join(dir_path, subdir+str(today)+'/'+file_name)
        #print(os.getpid())
        try:
            if not os.path.exists(final_directory):
                os.makedirs(final_directory)
                #return 
            else:
                pass              
        except(FileExistsError)as e:
            pass
                
        os.chdir(final_directory)
        DEVNULL = open(os.devnull, 'wb')
        
        try:
            device_name = subprocess.check_output(['adb', '-s', line2, 'shell', 'getprop', 'ro.product.model']).decode('ascii').strip()
        except subprocess.CalledProcessError as e:
            print(e)   
        
        pit = subprocess.Popen(['adb', '-s', line2, 'install', '-t', apk3], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        pipe, err = pit.communicate()
        file = open('%s_hi.txt' %line2, 'wb')
        pickle.dump((pipe, err), file) # to add pipe and err objects in a one text file, so used pickle
        file.close()
        with open('%s_hi.txt' %line2, 'rb') as f2:
            l1 = f2.readlines()
            for l2 in l1:
                if b"Failure" in l2:
                    l2 = l2.rstrip()
                    l2 = l2.decode('utf8', 'ignore')
                    print('your application is NOT INSTALLED on', device_name, 'as an error message appears', l2)
                    print('')
                    break       
            else:
                process2 = subprocess.Popen(['adb', '-s', line2, 'logcat', '-c'], stdout=DEVNULL, shell=True)
                launch = subprocess.Popen(['adb', '-s', line2, 'shell', 'am', 'start', '-n', packagename +'/' + activityname], stdout=DEVNULL, shell=True)
                print("App has launched on device", device_name, "Please check out on the respective device.")
                print('')
                time.sleep(30)
                with open('%s.txt' %line2, 'w+') as f1:
                    subprocess.Popen(['adb', '-s', line2, 'logcat', '-v', 'threadtime', '-d'], stdout=f1)
                    f1.flush()
                    time.sleep(1)
                f1.close()
                
                try:    
                    process2 = subprocess.Popen(['adb', '-s', line2, 'shell', 'am', 'force-stop', activityname], stdout=DEVNULL, shell=True)
                except(OSError)as e:
                    if e.errno != os.errno.EXIST:
                        print(e.errno)
                        raise
                try:   
                    process3 = subprocess.Popen(['adb', '-s', line2, 'shell', 'pm', 'clear', packagename], stdout=DEVNULL, stderr=subprocess.PIPE, shell=True)
                    
                except(OSError, IOError) as e:
                    print(e)
                try: 
                    print('')                
                    process4 = subprocess.Popen(['adb', '-s', line2, 'shell', 'pm', 'uninstall', packagename], stdout=DEVNULL, shell=True)
                    print("Your app has uninstalled from the device", device_name)
                    print('')  
                except(OSError, IOError) as e:
                    print(e)                        
                    print('')
                                                                 
        f2.close()
        os.remove('%s_hi.txt' %line2)
        


if __name__ == "__main__":
    c = Multi()
    line1 = c.collect_deviceid()
    if not line1:
        print('')
        print('*******Devices are not found in \'device\' mode, or devices are not connected. please check the connection(s).*******')
        time.sleep(1)
        exit()
    apk4 = c.folder_creation()
    print('')
    print("***********Build installation is going on...**************...Please be patient & keep smiling :)")
    print('')
    p = Pool()
    for apk2 in apk4:
        print('Build Name is:-', apk2)
        pipe = subprocess.Popen(['aapt', 'dump', 'badging', apk2], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding = "utf-8", errors='ignore')
        result = pipe.communicate()[0] #byte to string coversion used decode method.
        result =result.strip()
        
        file = codecs.open('newdump.txt', 'wb', encoding='utf-8', errors='replace')
        file.writelines(str(result))
        file.close()
        
        with codecs.open('newdump.txt', 'rb', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                if "package: name=" in line: 
                    line = line.strip('package: name=')
                    head, sep, tail = line.partition(' ')
                    head = line.partition(' ')
                    #head = head.replace("'", "")
                    packagename = head[0]
                    print('Package name of the application is:-', packagename)
                elif "launchable-activity: name=" in line:
                    line = line.strip('launchable-activity: name=')
                    activityname, sep, tail = line.partition(' ')
                    #head = head.replace("'", "")
                    print('Activity name of application is:-', activityname)
                    print('')                    
                else:
                    pass                
        f.close()
        os.remove('newdump.txt')
            
        #l = multiprocessing.Lock()
        try:
            func = partial(c.app_installation, apk2, packagename, activityname)
            p.map(func, line1)
        except KeyboardInterrupt:
            p.close()
            p.join()
            p.terminate()    
    #p.close()
    p.terminate()
    p.join()
    print('*******done with testing of all availble apps in the given path with all connected devices.*******')
    #os.remove('devicename.txt')
    exit()
   