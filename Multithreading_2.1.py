#!/usr/bin/python
import sys # Need to have acces to sys.stdout
import string
import os
import subprocess, shlex
import pickle
import tempfile
import datetime
import multiprocessing
import time
import shutil
import codecs
import glob
import re
import signal


from subprocess import STDOUT, check_output
from multiprocessing import Pool
from functools import partial
from subprocess import DEVNULL
from subprocess import Popen
from deviceslogfile import devicename


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
        apkfiles_list = []
        folderpath1 = input('Please provide the path of APKs folder:-')
        folderpath = folderpath1.replace("\\", "\\\\")
        print('you can see me:', folderpath)
        print(re.escape(folderpath))
        
        if os.path.exists(folderpath):
            directory = os.path.normpath(folderpath)
            apkfiles_list = glob.glob(os.path.join(folderpath, '*.apk')) or glob.glob(os.path.join(folderpath))
            if not apkfiles_list:
                print('')
                print('******* in the given path, .apk files are not found. Please check once again. ********')
                time.sleep(1)
                exit()
            else:         
                return apkfiles_list
                        
        else:
            print('')
            print('*****Given path is not a valid, so please check out for correct one*****')
            time.sleep(1)
            exit()
            
    
    def collect_deviceid(self):
        
        device_id = []
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
            device_id.append(serial)     
        return device_id
    
    def app_installation(self, apkfile_path, packagename, activityname, line1):
        
        self.apkfile_path = apkfile_path
        self.line1 = line1     
        device_id = ''.join([str(x) for x in line1]) 
        actual_filepath = ''.join([str(x1) for x1 in apkfile_path])
        dir_path = os.path.dirname(os.path.realpath(apkfile_path))
        os.chdir(dir_path)
        file_name = os.path.basename(apkfile_path).rsplit('.', 1)[0]
        today = time.strftime("%d-%b-%Y")
        subdir = "ADB_Logs_"
        
        final_directory = os.path.join(dir_path, subdir+str(today)+'/'+file_name)
        
        try:
            if not os.path.exists(final_directory):
                os.makedirs(final_directory)
            else:
                pass              
        except(FileExistsError)as e:
            pass
                
        os.chdir(final_directory)
        DEVNULL = open(os.devnull, 'w')
        
        try:
            device_name = subprocess.check_output(['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model']).decode('ascii').strip()
        except subprocess.CalledProcessError as e:
            print(e)   
        
        pit = subprocess.Popen(['adb', '-s', device_id, 'install', '-r', actual_filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        pipe, err = pit.communicate()
        file = open('%s_hi.txt' %device_id, 'wb')
        pickle.dump((pipe, err), file) # to add pipe and err objects in a one text file, so used pickle
        file.close()
        with open('%s_hi.txt' %device_id, 'rb') as f2:
            l1 = f2.readlines()
            for l2 in l1:
                if b"Failure [INSTALL_FAILED_TEST_ONLY" in l2:
                    pit = subprocess.Popen(['adb', '-s', device_id, 'install', '-t', actual_filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
                    time.sleep(1)
                    
                elif b"Failure" in l2:
                        l2 = l2.rstrip()   
                        l2 = l2.decode('utf8', 'ignore')
                        print('Your application is NOT INSTALLED on', device_name, 'as an error message appears', l2)
                        print('')
                        break
                
            else:
                process2 = subprocess.Popen(['adb', '-s', device_id, 'logcat', '-c'], stdout=DEVNULL)
                device_id1 = devicename(device_id)
                
                with open('%s.txt' %device_id1, 'w') as f1:
                                       
                    process5 = subprocess.Popen(['adb', '-s', device_id, 'logcat', '-v', 'threadtime'], stdout=f1, shell=True)
                    f1.flush()
					
                    launch = subprocess.Popen(['adb', '-s', device_id, 'shell', 'monkey', '-p', packagename, '-c', 'android.intent.category.LAUNCHER', '1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                    print('App has launched on device', device_name, 'Please check out on the respective device')
                    print('')
                    time.sleep(20)
                
                    try:  
                        time.sleep(1)
                        process2 = subprocess.Popen(['adb', '-s', device_id, 'shell', 'am', 'kill', packagename], stdout=DEVNULL, shell=True)						
                    except(OSError)as e:
                        if e.errno != os.errno.EXIST:
                            print(e.errno)
                            raise
                    try:   
                        process3 = subprocess.Popen(['adb', '-s', device_id, 'shell', 'pm', 'clear', packagename], stdout=DEVNULL, stderr=subprocess.PIPE, shell=True)
                    except(OSError, IOError) as e:
                        print(e)
                    try: 
                        print('')                
                        process4 = subprocess.Popen(['adb', '-s', device_id, 'shell', 'pm', 'uninstall', packagename], stdout=DEVNULL)
                        print("Your app has uninstalled from the device", device_name)
                        print('')  
                    except(OSError, IOError) as e:
                        print(e)                        
                        print('')
                     
                    Popen("TASKKILL /F /PID {pid} /T".format(pid=process5.pid), stdout=DEVNULL)                    
                    f1.flush()    
                                       
                f1.close() 
                process6 = subprocess.Popen(['adb', '-s', device_id, 'logcat', '-c'], stdout=DEVNULL)
                
        f2.close()
        os.remove('%s_hi.txt' %device_id)
        
        
        


if __name__ == "__main__":
    c = Multi()
    line1 = c.collect_deviceid()
    if not line1:
        print('')
        print('*******Devices are not found in \'device\' mode, or devices are not connected. please check the connection(s).*******')
        time.sleep(1)
        exit()
    allapk_files = c.folder_creation()
    print('')
    print("***********Build installation is going on...**************...Please be patient & keep smiling :)")
    print('')
    p = Pool()
    for apkfile_path in allapk_files:
        line1 = c.collect_deviceid()
        print("Build's full path is:-", apkfile_path)
        pipe = subprocess.Popen(['aapt', 'dump', 'badging', apkfile_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding = "utf-8", errors='ignore')
        result = pipe.communicate()[0] #byte to string coversion used decode method.
        result =result.strip()
        
        file = codecs.open('newdump.txt', 'wb', encoding='utf-8', errors='replace')
        file.writelines(str(result))
        file.close()
		
        activityname = ""
        with codecs.open('newdump.txt', 'rb', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("package: name="):
                    line = line.strip('package: name=')
                    head, sep, tail = line.partition(' ')
                    head = line.partition(' ')
                    packagename = head[0]
                    print('Package name of the application is:-', packagename)
                elif line.startswith("launchable-activity: name="):    
                    line = line.strip('launchable-activity: name=')
                    activityname, sep, tail = line.partition(' ')
                    print('Activity name of application is:-', activityname)
                    print('')                  
                else:
                    pass              
        f.close()
        os.remove('newdump.txt')

        try: 
            func = partial(c.app_installation, apkfile_path, packagename, activityname)
            p.map(func, line1)
        except KeyboardInterrupt:
            os.kill(p.pid, signal.CTRL_C_EVENT)
            p.close()
            p.join()
            p.terminate(SIGTERM)    
    p.terminate()
    p.join()
    print('*******Done with testing of all availble apps in the given path with all connected devices.*******')
    exit()
   