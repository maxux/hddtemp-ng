import subprocess
import sys
import json

class HDDTempNG:
    def __init__(self, disks=[]):
        self.drives = disks
        self.temperatures = {}

    def sata(self, drive):
        a = subprocess.run(['smartctl', '-j', '--attributes', drive], capture_output=True)
        data = json.loads(a.stdout.decode('utf-8'))

        for field in data['ata_smart_attributes']['table']:
            if field['id'] == 194:
                return {"now": field['value'], "worst": field['worst']}

        return {}

    def nvme(self, drive):
        a = subprocess.run(['nvme', 'smart-log', '--output-format=json', drive], capture_output=True)
        data = json.loads(a.stdout.decode('utf-8'))

        return {"now": data['temperature'] - 273, "worst": 0}

    def autodetect(self):
        with open("/proc/partitions", "r") as f:
            data = f.read()

        partitions = []
        lines = data.split("\n")

        for line in lines[2:-1]:
            data = line.split()

            if data[3].startswith("sd"):
                if data[3][-1].isdigit():
                    continue

                partitions.append("/dev/" + data[3])

            if data[3].startswith("nvme"):
                if "p" in data[3]:
                    continue

                partitions.append("/dev/" + data[3])

        self.drives = partitions

        return partitions


    def fetch(self):
        sys.stdout.write(f"[+] fetching ")
        sys.stdout.flush()

        for drive in self.drives:
            sys.stdout.write(".")
            sys.stdout.flush()

            if "/dev/sd" in drive:
                self.temperatures[drive] = self.sata(drive)

            if "nvme" in drive:
                self.temperatures[drive] = self.nvme(drive)

    def dump(self):
        print("")

        for disk in self.temperatures.keys():
            value = self.temperatures[disk]
            print(f"[+] {disk}: {value['now']}°C [{value['worst']}°C]")

    def hddserve(self):
        print("")

        for disk in self.temperatures.keys():
            value = self.temperatures[disk]
            sys.stdout.write(f"|{disk}|{disk}|{value['now']}|C|")

        print("")

hdd = HDDTempNG()
hdd.autodetect()
hdd.fetch()
hdd.dump()
hdd.hddserve()
