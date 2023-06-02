#!/usr/bin/env python3

import os
import urllib.request
import threading

COUNTER__TXT = "domain_filters/{counter}.txt"

# These files are taken from https://firebog.net/

domain_filter_list = [  # Malicious links
                      'https://raw.githubusercontent.com/DandelionSprout/adfilt/master/Alternate%20versions%20Anti-Malware%20List/AntiMalwareHosts.txt',
                      'https://osint.digitalside.it/Threat-Intel/lists/latestdomains.txt',
                      'https://s3.amazonaws.com/lists.disconnect.me/simple_malvertising.txt',
                      'https://v.firebog.net/hosts/Prigent-Crypto.txt',
                      'https://raw.githubusercontent.com/FadeMind/hosts.extras/master/add.Risk/hosts',
                      'https://bitbucket.org/ethanr/dns-blacklists/raw/8575c9f96e5b4a1308f2f12394abd86d0927a4a0/bad_lists/Mandiant_APT1_Report_Appendix_D.txt',
                      'https://phishing.army/download/phishing_army_blocklist_extended.txt',
                      'https://gitlab.com/quidsup/notrack-blocklists/raw/master/notrack-malware.txt',
                      'https://v.firebog.net/hosts/RPiList-Malware.txt',
                      'https://v.firebog.net/hosts/RPiList-Phishing.txt',
                      'https://raw.githubusercontent.com/Spam404/lists/master/main-blacklist.txt',
                      'https://raw.githubusercontent.com/AssoEchap/stalkerware-indicators/master/generated/hosts',
                      'https://urlhaus.abuse.ch/downloads/hostfile/',
                      # Suspicious links
                      'https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/KADhosts.txt',
                      'https://raw.githubusercontent.com/FadeMind/hosts.extras/master/add.Spam/hosts',
                      'https://v.firebog.net/hosts/static/w3kbl.txt']

shortener_domains = ['t.ly', 'bit.ly', 'ow.ly', 'tinyurl.com']


def download_files():
    """This method will make sure the directory for the bot is present and then download all the files"""
    if not os.path.exists('domain_filters'):
        os.mkdir('domain_filters')

    counter = 1
    for url in domain_filter_list:
        urllib.request.urlretrieve(url, COUNTER__TXT.format(counter=counter))
        counter += 1


def load_bad_domains():
    """This method will go through all files that has been downloaded and load them into a list which will be returned"""
    # At least one file needs to be present
    if not os.path.exists('domain_filters') or not os.path.exists('domain_filters/1.txt'):
        print("No files downloaded. Improper usage of the script.")
        exit(1)

    maindict = {}
    threads = []
    files_to_process = os.listdir('domain_filters')
    counter = 0
    # Start threads
    for index in range(len(files_to_process)):
        counter += 1
        if not os.path.exists(COUNTER__TXT.format(counter=counter)):
            break
        x = threading.Thread(target=load_file, args=(COUNTER__TXT.format(counter=counter), maindict, index),)
        threads.append(x)
        x.start()

    # Wait for threads to finish
    for thread in threads:
        thread.join()

    return_list = []
    for x in maindict:
        return_list.extend(maindict[x])

    return_list.extend(shortener_domains)
    return return_list


def load_file(filename, maindict, index):
    """Helper method to add threading to loading files. This is to speed it up"""
    return_list = []
    f = open(filename, 'r')
    content = f.readlines()
    f.close()
    for line in content:
        if line.startswith('#') or len(line) < 2 or "/" in line:
            continue
        # If it is a hostlist we need to remove the leading ip redirect which is always quad zero
        elif line.startswith('0.0.0.0'):
            # Some files have a bad syntax in where there is no space between IP and host, so we have to take
            # that into account
            line_split = line.replace('0.0.0.0', '').strip()
            return_list.append(line_split)
        elif " " not in line.strip():
            return_list.append(line.strip())
    if len(return_list) > 0:
        maindict[index] = return_list

