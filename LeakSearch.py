#!/usr/bin/python3
#============================#
#  LeakSearch by @JoelGMSec  #
#    https://darkbyte.net    #
#============================#

import os
import json
import urllib3
import requests
import argparse
from tabulate import tabulate
from neotermcolor import colored
from requests import ConnectionError
urllib3.disable_warnings()

banner = """
  _               _     ____                      _     
 | |    ___  __ _| | __/ ___|  ___  __ _ _ __ ___| |__  
 | |   / _ \/ _` | |/ /\___ \ / _ \/ _` | '__/ __| '_ \ 
 | |__|  __/ (_| |   <  ___) |  __/ (_| | | | (__| | | |
 |_____\___|\__,_|_|\_\|____/ \___|\__,_|_|  \___|_| |_|"""

banner2 = """                                               
  ------------------- by @JoelGMSec -------------------
  """

def find_leaks_proxynova(email, proxy, number):
    url = f"https://api.proxynova.com/comb?query={email}"
    headers = {'User-Agent': 'curl'}
    session = requests.session()

    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}

    response = session.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        data = json.loads(response.text)
        total_results = data.get("count", 0)
        print(colored(f"[*] Found {total_results} different records in database", "magenta"), end='')

        lines = data.get("lines", [])[:number]
        return lines
    else:
        print(colored(f"[!] Failed to fetch results from ProxyNova. Status code: {response.status_code}\n", "red"))
        return []

def find_leaks_local_db(database, keyword, number):
    if not os.path.exists(database):
        print(colored(f"[!] Local database file not found: {database}\n", "red"))
        exit(-1)

    if database.endswith('.json'):
        with open(database, 'r') as json_file:
            try:
                data = json.load(json_file)
                lines = data.get("lines", [])
            except json.JSONDecodeError:
                print(colored("[!] Error: Failed to parse local database as JSON\n", "red"))
                exit(-1)
    else:
        file_length = os.path.getsize(database)
        block_size = 1
        line_count = 0
        results = []

        try:
            with open(database, 'r') as file:
                while True:
                    block = [next(file).strip() for _ in range(block_size)]
                    line_count += len(block)

                    if not block or line_count > file_length:
                        break

                    filtered_block = [line for line in block if keyword.lower() in line.lower()]
                    results.extend(filtered_block)

                    print(colored(f"\r[*] Reading {line_count} lines in database..", "magenta"), end='', flush=True)

                    if number is not None and len(results) >= number:
                        break

        except KeyboardInterrupt:
            print (colored("\n[!] Exiting..\n", "red"))
            exit(-1)

        except:
            pass
        
        return results[:number] if number is not None else results

def main(database, keyword, output=None, proxy=None, number=20):
    print(colored(f"[>] Searching for {keyword} leaks in {database}..", "yellow"))

    if database.lower() == "proxynova":
        results = find_leaks_proxynova(keyword.strip(), proxy, number)
    else:
        results = find_leaks_local_db(database.strip(), keyword.strip(), number)

    if not results:
        print(colored(f"\n[!] No leaks found in {database}!\n", "red"))
    else:
        print_results(results, output, number)

def print_results(results, output, number):
    print(colored(f"\n[-] Selecting the first {len(results)} results..", "blue"))
    headers = ["Username@Domain", "Password"]
    table_data = []

    for line in results:
        parts = line.split(":")
        if len(parts) == 2:
            username_domain, password = parts
            table_data.append([username_domain, password])

    if output is not None:
        if output.endswith('.json'):
            with open(output, 'w') as json_file:
                json.dump({"lines": results}, json_file, indent=2)
                print(colored(f"[+] Data saved successfully in {output}!\n", "green"))
        else:
            with open(output, 'w') as txt_file:
                txt_file.write(tabulate(table_data, headers, showindex="never"))
                print(colored(f"[+] Data saved successfully in {output}!\n", "green"))
    else:
        print(colored("[+] Done!\n", "green"))
        print(tabulate(table_data, headers, showindex="never"))
        print()

if __name__ == '__main__':
    print(colored(banner, "blue"))
    print(colored(banner2, "green"))
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--database", default="ProxyNova", help="Database used for the search (ProxyNova or LocalFile)")
    parser.add_argument("-k", "--keyword", help="Keyword (user/domain/pass) to search for leaks in the DB")
    parser.add_argument("-n", "--number", type=int, default=20, help="Number of results to show (default is 20)")
    parser.add_argument("-o", "--output", help="Save the results as json or txt into a file")
    parser.add_argument("-p", "--proxy", help="Set HTTP/S proxy (like http://localhost:8080)")
    args = parser.parse_args()

    if not args.keyword:
        parser.print_help()
        exit(-1)

    try:
        main(args.database, args.keyword, args.output, args.proxy, args.number)

    except ConnectionError:
        print(colored("[!] Can't connect to service! Check your internet connection!\n", "red"))
    
    except KeyboardInterrupt:
        print (colored("\n[!] Exiting..\n", "red"))
        exit(-1)

    except Exception as e:
        print(colored(f"\n[!] Error: {e}\n", "red"))
      
