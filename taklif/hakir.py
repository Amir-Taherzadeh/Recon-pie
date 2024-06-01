import requests
from bs4 import BeautifulSoup
import dns.resolver
import socket
import whois
import re
import openpyxl

class SubdomainEnumerator:
    def __init__(self, target_domain, wordlist_file, common_ports):
        self.target_domain = target_domain
        self.wordlist_file = wordlist_file
        self.common_ports = common_ports
        self.emails = []
        self.excel_data = []

    def enumerate_subdomains(self):
        with open(self.wordlist_file, 'r') as f:
            #halghe bar roy hameheh khat hay word list
            for line in f:
                subdomain = line.strip()
                domain = subdomain + '.' + self.target_domain
                try:
                    #dnse ip ra minevisad
                    answers = dns.resolver.resolve(domain, 'A')
                    #port baz (22,32)
                    for answer in answers:
                        ipaddress = str(answer)
                        open_ports = []
                        #sooket minveseh (301,404,200)
                        for port in self.common_ports:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1)
                            result = sock.connect_ex((ipaddress, port))
                            if result == 0:
                                open_ports.append(port)
                            sock.close()

                        if open_ports:
                            print("------------------------------------------------------------")
                            print(f"Subdomain: {subdomain}")
                            print(f"IP Address: {ipaddress}")
                            print(f"Open Ports: {', '.join(map(str, open_ports))}")
                            print(f"URL: http://{subdomain}.{self.target_domain}")
                            print("------------------------------------------------------------")
                            self.excel_data.append(['Subdomain', subdomain])
                            self.excel_data.append(['IP Address', ipaddress])
                            self.excel_data.append(['Open Ports', ', '.join(map(str, open_ports))])
                            self.excel_data.append(['URL', f"http://{subdomain}.{self.target_domain}"])
                            self.scrape_links(subdomain)
                #chek mikoneh ke oon wordlist agar true boodan va vojood dastan etlatetsham dar bira
                except dns.resolver.NXDOMAIN:
                    pass
                except dns.resolver.NoAnswer:
                    pass
                except dns.resolver.Timeout:
                    pass
                except Exception as e:
                    print(f"Error occurred: {e}")

        self.finalize_operations()

    def scrape_links(self, subdomain):
        url = f'http://{subdomain}.{self.target_domain}'
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            print(f"Title: {title}")
            self.excel_data.append(['Title', title])
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                title = link.get_text().strip()
                if href and href.startswith('http'):
                    status = requests.head(href).status_code
                    print(f"Link: {href}")
                    print(f"Title: {title}")
                    print(f"Status Code: {status}")
                    self.excel_data.append(['Link', href])
                    self.excel_data.append(['Title', title])
                    self.excel_data.append(['Status Code', status])
                #email hay dakhl saite ra chap mikonad
                elif href and href.startswith('mailto:'):
                    email = href.replace('mailto:', '')
                    print(f"Extracted Email: {email}")
                    self.emails.append(email)
        else:
            print(f"Failed to retrieve the page for {subdomain}.{self.target_domain}")

    def get_whois_info(self, domain):
        try:
            #who is yaro ra minevisad
            w = whois.whois(domain)
            print(f"WHOIS Info: {w}")
            self.excel_data.append(['WHOIS Info', str(w)])
        except Exception as e:
            print(f"Error getting WHOIS info: {e}")

    def finalize_operations(self):
        #jolo giri az bi tartib neveshteh shodan etlaatat dar exel (anjam alamiat dar enthay kar)
        self.extract_emails()
        self.get_whois_info(self.target_domain)
        self.extract_contacts_from_website()
        self.write_to_excel()

    def extract_emails(self):
        if not self.emails:
            print("No emails were extracted.")
        else:
            for email in self.emails:
                print(f"Extracted Email: {email}")
                self.excel_data.append(['Extracted Email', email])

    def write_to_excel(self):
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = "Subdomain Info"

        for row in self.excel_data:
            sheet.append(row)

        excel_file = f"{self.target_domain}_info.xlsx"
        wb.save(excel_file)
        print(f"Excel file saved: {excel_file}")

    def extract_contacts_from_website(self):
        emails, phone_numbers, phone_numbers1 = self._extract_contacts_from_website(self.target_domain)
        for email in emails:
            print(f"Extracted Email: {email}")
            self.excel_data.append(['Extracted Email', email])
        for number in phone_numbers:
            print(f"Phone Number: {number}")
            self.excel_data.append(['Phone Number', number])
        for number in phone_numbers1:
            print(f"Phone Number: {number}")
            self.excel_data.append(['Phone Number', number])

    @staticmethod
    def _extract_contacts_from_website(target_domain):
        url = f"https://{target_domain}"
        response = requests.get(url)
        if response.status_code == 200:
            emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', response.text)
            phone_numbers = re.findall(r"021-\d{8}", response.text)
            phone_numbers1 = re.findall(r"021\d{8}", response.text)
            return emails, phone_numbers, phone_numbers1
        else:
            print("Failed to retrieve the website content.")
            return [], [], []

# Usage example:
# enumerator = SubdomainEnumerator('example.com', 'wordlist.txt', [80, 443])
# enumerator.enumerate_subdomains()
