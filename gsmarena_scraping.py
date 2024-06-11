import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import subprocess

VULTR_API_KEY = 'ASDSADASDASDASDASDASDASDSA'
SNAPSHOT_ID = 'ac5e4520-3e21-4703-91e4-9cerwrew'
REGION = 'ewr'
PLAN = 'vc2-1c-0.5gb'
class Gsmarena:
    def __init__(self):
        self.url = 'https://www.gsmarena.com/'
        self.new_folder_name = 'GSMArenaDataset'
        self.absolute_path = os.path.join(os.getcwd(), self.new_folder_name)
        self.max_retries = 5
        self.current_instance_id = None

    def create_vm(self):
        print("Creating VM...")
        url = 'https://api.vultr.com/v2/instances'
        headers = {
            'Authorization': f'Bearer {VULTR_API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {
            'region': REGION,
            'plan': PLAN,
            'snapshot_id': SNAPSHOT_ID,
            'enable_ipv6': False
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 202:
            print("VM creation initiated successfully.")
            instance_id = response.json()['instance']['id']
            print("Waiting for VM to become operational...")
            time.sleep(180)  # Adding delay for VM to become operational
            return instance_id
        else:
            print(f"Failed to create VM: {response.status_code} {response.text}")
            return None

    def get_vm_ip(self, instance_id):
        print(f"Retrieving IP for VM {instance_id}...")
        url = f'https://api.vultr.com/v2/instances/{instance_id}'
        headers = {
            'Authorization': f'Bearer {VULTR_API_KEY}'
        }
        for _ in range(30):  # Retry for up to 5 minutes
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                instance_info = response.json()
                ip_address = instance_info['instance']['main_ip']
                if ip_address and ip_address != '0.0.0.0':
                    return ip_address
            time.sleep(10)
        print(f"Failed to retrieve VM IP for instance {instance_id}.")
        return None

    def dispose_vm(self, instance_id):
        print(f"Disposing VM {instance_id}...")
        url = f'https://api.vultr.com/v2/instances/{instance_id}'
        headers = {
            'Authorization': f'Bearer {VULTR_API_KEY}'
        }
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            print(f"VM {instance_id} disposed successfully.")
        else:
            print(f"Failed to dispose VM: {response.status_code} {response.text}")

    def update_openvpn_config(self, new_ip):
        print(f"Updating OpenVPN config with new IP {new_ip}...")
        config_file_path = '/etc/openvpn/client.conf'
        with open(config_file_path, 'r') as file:
            config_data = file.readlines()
        
        with open(config_file_path, 'w') as file:
            for line in config_data:
                if line.startswith('remote'):
                    file.write(f'remote {new_ip} 1194\n')
                else:
                    file.write(line)

    def restart_openvpn(self):
        print("Restarting OpenVPN client...")
        try:
            result = subprocess.run(['systemctl', 'restart', 'openvpn@client'], check=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
            print("OpenVPN client restarted successfully.")
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"Failed to restart OpenVPN client: {e.stderr}")
            raise

    def stop_openvpn(self):
        print("Stopping OpenVPN client...")
        try:
            result = subprocess.run(['systemctl', 'stop', 'openvpn@client'], check=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args, output=result.stdout, stderr=result.stderr)
            print("OpenVPN client stopped successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to stop OpenVPN client: {e.stderr}")
            raise

    def switch_ip(self):
        print("Switching IP...")
        # Stop OpenVPN client
        try:
            self.stop_openvpn()
        except Exception as e:
            print(f"An error occurred while stopping OpenVPN: {e}")

        # Dispose of the old VM if it exists
        if self.current_instance_id:
            self.dispose_vm(self.current_instance_id)
            self.current_instance_id = None

        # Create a new VM and switch to its IP
        instance_id = self.create_vm()
        if instance_id:
            new_ip = self.get_vm_ip(instance_id)
            if new_ip:
                self.update_openvpn_config(new_ip)
                try:
                    self.restart_openvpn()
                    self.current_instance_id = instance_id
                    print(f"Switched to new IP: {new_ip}")
                except Exception as e:
                    print(f"An error occurred: {e}")
                    self.dispose_vm(instance_id)
            else:
                print(f"Failed to get a valid IP for instance {instance_id}")

    def crawl_html_page(self, sub_url):
        print(f"Crawling HTML page: {sub_url}")
        url = self.url + sub_url
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                response = requests.get(url, timeout=10, headers=headers)
                if response.status_code == 429:
                    print(f"429 Too Many Requests: Switching IP...")
                    self.switch_ip()
                    continue
                response.raise_for_status()
                return BeautifulSoup(response.text, 'html.parser')
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}. Retrying...")
                retry_count += 1
                time.sleep(5)  # Adding delay to prevent rapid retries
        print(f"Failed to fetch page after {self.max_retries} retries.")
        return None

    def crawl_phone_brands(self):
        print("Crawling phone brands...")
        phones_brands = []
        soup = self.crawl_html_page('makers.php3')
        if soup:
            table = soup.find_all('table')[0]
            table_a = table.find_all('a')
            for a in table_a:
                temp = [a['href'], a.find('span').text.split(' ')[0], a['href']]
                phones_brands.append(temp)
        return phones_brands

    def crawl_phones_models(self, phone_brand_link):
        print(f"Crawling phone models for brand link: {phone_brand_link}")
        models = []
        soup = self.crawl_html_page(phone_brand_link)
        if soup:
            data = soup.find(class_='section-body')
            if data:
                for line in data.findAll('a'):
                    model_name = line.find('strong').text
                    model_link = line['href']
                    models.append((model_name, model_link))
        return models

    def create_folder(self):
        if not os.path.exists(self.new_folder_name):
            os.makedirs(self.new_folder_name)
            print(f"Creating {self.new_folder_name} Folder....")
        else:
            print(f"{self.new_folder_name} directory already exists")

    def save_specification_to_file(self):
        print("Starting to save specifications to file...")
        phone_brands = self.crawl_phone_brands()
        self.create_folder()
        for brand in phone_brands:
            print(f"Processing brand: {brand[1]}")
            csv_file = f"{brand[1]}.csv"
            csv_file_path = os.path.join(self.absolute_path, csv_file)
            retry_count = 0
            while retry_count < self.max_retries:
                try:
                    models = self.crawl_phones_models(brand[0])
                    if models:
                        with open(csv_file_path, "w", newline='', encoding='utf-8') as file:
                            writer = csv.writer(file)
                            writer.writerow(["Model Name", "Model Link"])
                            for model_name, model_link in models:
                                writer.writerow([model_name, self.url + model_link])
                    break  # Break the retry loop if successful
                except Exception as e:
                    print(f"Error processing {brand[1]}: {e}. Retrying...")
                    retry_count += 1
        print("Completed saving specifications to file.")

if __name__ == "__main__":
    gsmarena = Gsmarena()
    gsmarena.save_specification_to_file()
