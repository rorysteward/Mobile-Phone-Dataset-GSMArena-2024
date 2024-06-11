# Mobile-Phone-Dataset-GSMArena
This is Python script which scrape the GSMArena website mobile phones and save in the csv format files.

Difference - 
Vultr automatic VM provisioning, changing the IP addresses and in event of 429 error, dispose the VM and spawn new one
It does not enter the links - it grabs only the model name and links to it.
Don't forget to destroy the last VM.


### Prerequisites

* Python3.x
* Pip
* Snapshot with OpenVPN server and enabled on boot created (tested under Debian 12)
* Client config file in /etc/openvpn/client.conf (systemctl)
* 
### Installing

* Install reqiurement text file using pip3
  
  ```
  pip3 install -r requirements.txt
  ```

### Running

  Run this command on your terminal
  ```
  python3 gsmarena_scraping.py
  ```

## Built With

* [Beautifulsoup4](https://pypi.org/project/beautifulsoup4/) - Beautifulsoup4 python librabry for website scraping.

## Authors

* **Deepak Chawla** - [Github](https://github.com/Deepakchawla), [Linkedin](https://www.linkedin.com/in/deepakchawla1307/) and [Website](http://deepakchawla.me/).
* Enhanced by https://github.com/rorysteward

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
