import psutil
import socket
import platform
import datetime
import subprocess
import os
import json
import locale
import re

IS_WINDOWS = platform.system() == 'Windows'


def _safe_run(cmd, shell=True, timeout=10):
    try:
        return subprocess.check_output(cmd, shell=shell, stderr=subprocess.DEVNULL, timeout=timeout).decode('utf-8', errors='ignore').strip()
    except Exception:
        return None


def _na(val, default='N/A'):
    if val is None or val == '' or val == 0 and default == 'N/A':
        return default
    return val


def _format_storage(bytes_val):
    try:
        bytes_val = float(bytes_val)
        gb = bytes_val / (1024 ** 3)
        if gb >= 1024:
            return f"{gb / 1024:.2f} TB"
        return f"{gb:.2f} GB"
    except Exception:
        return 'N/A'


def _parse_intel_gen(model):
    try:
        m = re.search(r'i[3579]-(\d{2,5})', model, re.I)
        if m:
            digits = m.group(1)
            if len(digits) >= 2:
                gen = int(digits[:2])
                if gen >= 10:
                    return f"{gen}th Gen"
                return f"{gen}th Gen"
        m = re.search(r'(\d{4,5})[A-Z]', model)
        if m:
            gen = int(str(m.group(1))[:2])
            return f"{gen}th Gen"
    except Exception:
        pass
    return 'N/A'


def _parse_amd_gen(model):
    try:
        m = re.search(r'Ryzen\s+\d+\s+(\d{4})', model, re.I)
        if m:
            num = int(m.group(1))
            if num >= 7000:
                return 'Zen 4'
            if num >= 5000:
                return 'Zen 3'
            if num >= 3000:
                return 'Zen 2'
            if num >= 2000:
                return 'Zen+'
            return 'Zen'
    except Exception:
        pass
    return 'N/A'


def _memory_type_name(code):
    mapping = {
        '20': 'DDR', '21': 'DDR2', '24': 'DDR3', '26': 'DDR4', '34': 'DDR5',
        '0': 'Unknown', '1': 'Other', '2': 'DRAM'
    }
    return mapping.get(str(code).strip(), 'N/A')


def get_security_score():
    score = 0
    details = []

    try:
        output = subprocess.check_output('netsh advfirewall show currentprofile', shell=True).decode()
        if 'State' in output and 'ON' in output:
            score += 20
            details.append({"name": "Firewall", "status": "ON", "points": "+20", "icon": "fa-shield-alt", "color": "text-success"})
        else:
            details.append({"name": "Firewall", "status": "OFF", "points": "+0", "icon": "fa-shield-alt", "color": "text-danger"})
    except Exception:
        details.append({"name": "Firewall", "status": "Unknown", "points": "+0", "icon": "fa-shield-alt", "color": "text-warning"})

    open_ports = 0
    for port in [21, 22, 23, 80, 443, 3389]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                if s.connect_ex(('127.0.0.1', port)) == 0:
                    open_ports += 1
        except Exception:
            pass
    if open_ports == 0:
        score += 20
        details.append({"name": "Open Ports", "status": "0 Open", "points": "+20", "icon": "fa-door-open", "color": "text-success"})
    elif open_ports <= 3:
        score += 10
        details.append({"name": "Open Ports", "status": f"{open_ports} Open", "points": "+10", "icon": "fa-door-open", "color": "text-warning"})
    else:
        details.append({"name": "Open Ports", "status": f"{open_ports} Open", "points": "+0", "icon": "fa-door-open", "color": "text-danger"})

    failed_logins = 0
    if failed_logins == 0:
        score += 20
        details.append({"name": "Failed Logins", "status": "0 Attempts", "points": "+20", "icon": "fa-user-lock", "color": "text-success"})
    elif failed_logins <= 3:
        score += 10
        details.append({"name": "Failed Logins", "status": f"{failed_logins} Attempts", "points": "+10", "icon": "fa-user-lock", "color": "text-warning"})
    else:
        details.append({"name": "Failed Logins", "status": f"{failed_logins} Attempts", "points": "+0", "icon": "fa-user-lock", "color": "text-danger"})

    av_found = False
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in ['msmpeng.exe', 'avgui.exe', 'avastui.exe', 'norton.exe']:
                av_found = True
                break
        except Exception:
            pass
    if av_found:
        score += 20
        details.append({"name": "Antivirus", "status": "Running", "points": "+20", "icon": "fa-virus-slash", "color": "text-success"})
    else:
        details.append({"name": "Antivirus", "status": "Not Found", "points": "+0", "icon": "fa-virus-slash", "color": "text-danger"})

    try:
        out = subprocess.check_output('sc query wuauserv', shell=True).decode()
        if 'RUNNING' in out:
            score += 20
            details.append({"name": "Auto Update", "status": "Enabled", "points": "+20", "icon": "fa-sync", "color": "text-success"})
        else:
            details.append({"name": "Auto Update", "status": "Disabled", "points": "+0", "icon": "fa-sync", "color": "text-danger"})
    except Exception:
        details.append({"name": "Auto Update", "status": "Unknown", "points": "+0", "icon": "fa-sync", "color": "text-warning"})

    return score, details


def _get_drive_type(mountpoint):
    if IS_WINDOWS:
        try:
            letter = mountpoint.rstrip('\\').rstrip(':')
            out = _safe_run(f'powershell -Command "(Get-PhysicalDisk | Get-Disk | Get-Partition | Where-Object {{ $_.DriveLetter -eq \'{letter}\' }} | Get-Volume).FileSystemLabel; (Get-PhysicalDisk | Where-Object {{ (Get-Partition -DiskNumber $_.DeviceId -ErrorAction SilentlyContinue | Where-Object DriveLetter -eq \'{letter}\') }}).MediaType"')
            if out:
                if 'SSD' in out.upper() or 'SOLID' in out.upper():
                    return 'SSD'
                if 'HDD' in out.upper() or 'HARD' in out.upper():
                    return 'HDD'
        except Exception:
            pass
        out = _safe_run(f'wmic diskdrive get MediaType /format:list')
        if out and 'SSD' in out.upper():
            return 'SSD'
        if out and 'Fixed' in out:
            return 'HDD'
    else:
        try:
            dev = mountpoint.replace('/mnt/', '').replace('/', '')
            out = _safe_run(f'cat /sys/block/{dev}/queue/rotational 2>/dev/null', shell=True)
            if out == '0':
                return 'SSD'
            if out == '1':
                return 'HDD'
        except Exception:
            pass
    return 'N/A'


def _get_volume_label(mountpoint):
    if IS_WINDOWS:
        letter = mountpoint.rstrip('\\')
        out = _safe_run(f'wmic logicaldisk where "DeviceID=\'{letter}\'" get VolumeName /value')
        if out:
            for line in out.splitlines():
                if 'VolumeName=' in line:
                    name = line.split('=', 1)[1].strip()
                    return name if name else 'Local Disk'
    return mountpoint


def get_storage_details():
    drives = []
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                usage = psutil.disk_usage(part.mountpoint)
                letter = part.mountpoint
                if IS_WINDOWS:
                    letter = part.device.replace('\\', '')
                name = _get_volume_label(part.mountpoint)
                drives.append({
                    'letter': letter,
                    'name': name,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'total_fmt': _format_storage(usage.total),
                    'used_fmt': _format_storage(usage.used),
                    'free_fmt': _format_storage(usage.free),
                    'usage_percent': round(usage.percent, 1),
                    'type': _get_drive_type(part.mountpoint)
                })
            except Exception:
                continue
    except Exception:
        pass
    return drives


def _get_ram_chip_info():
    ram_type = 'N/A'
    ram_speed = 'N/A'
    if IS_WINDOWS:
        out = _safe_run('wmic memorychip get speed,memorytype /format:list')
        if out:
            speeds = []
            types = []
            current_type = None
            current_speed = None
            for line in out.splitlines():
                line = line.strip()
                if line.startswith('MemoryType='):
                    current_type = line.split('=', 1)[1].strip()
                    if current_type:
                        types.append(_memory_type_name(current_type))
                elif line.startswith('Speed='):
                    current_speed = line.split('=', 1)[1].strip()
                    if current_speed and current_speed.isdigit() and int(current_speed) > 0:
                        speeds.append(current_speed)
            if types:
                ram_type = types[0]
            if speeds:
                ram_speed = f"{speeds[0]} MHz"
    else:
        out = _safe_run('dmidecode --type memory 2>/dev/null')
        if out:
            m = re.search(r'Type:\s*(DDR\d+)', out)
            if m:
                ram_type = m.group(1)
            m = re.search(r'Speed:\s*(\d+)\s*MT/s', out)
            if m:
                ram_speed = f"{m.group(1)} MHz"
    return ram_type, ram_speed


def get_ram_details():
    try:
        svmem = psutil.virtual_memory()
        ram_type, ram_speed = _get_ram_chip_info()
        return {
            'total': svmem.total,
            'used': svmem.used,
            'free': svmem.available,
            'total_fmt': _format_storage(svmem.total),
            'used_fmt': _format_storage(svmem.used),
            'free_fmt': _format_storage(svmem.available),
            'usage_percent': round(svmem.percent, 1),
            'type': ram_type,
            'speed': ram_speed
        }
    except Exception:
        return {
            'total': 0, 'used': 0, 'free': 0,
            'total_fmt': 'N/A', 'used_fmt': 'N/A', 'free_fmt': 'N/A',
            'usage_percent': 0, 'type': 'N/A', 'speed': 'N/A'
        }


def get_processor_details():
    name = platform.processor() or 'N/A'
    brand = 'N/A'
    generation = 'N/A'
    arch = platform.machine() or 'N/A'

    if IS_WINDOWS:
        out = _safe_run('wmic cpu get name /format:list')
        if out:
            for line in out.splitlines():
                if line.startswith('Name='):
                    name = line.split('=', 1)[1].strip()
                    break

    if not name or name == 'N/A' or 'Intel' not in name and 'AMD' not in name:
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('model name'):
                        name = line.split(':', 1)[1].strip()
                        break
        except Exception:
            pass

    name_upper = name.upper()
    if 'INTEL' in name_upper:
        brand = 'Intel'
        generation = _parse_intel_gen(name)
    elif 'AMD' in name_upper:
        brand = 'AMD'
        generation = _parse_amd_gen(name)

    if arch in ('AMD64', 'x86_64'):
        arch = 'x64'
    elif arch in ('i386', 'i686'):
        arch = 'x86'
    elif 'arm' in arch.lower() or 'aarch' in arch.lower():
        arch = 'ARM'

    physical_cores = psutil.cpu_count(logical=False) or 'N/A'
    logical_cores = psutil.cpu_count(logical=True) or 'N/A'

    current_speed = 'N/A'
    max_speed = 'N/A'
    try:
        freq = psutil.cpu_freq()
        if freq:
            if freq.current:
                current_speed = f"{freq.current / 1000:.2f} GHz"
            if freq.max:
                max_speed = f"{freq.max / 1000:.2f} GHz"
    except Exception:
        pass

    return {
        'name': name,
        'generation': generation,
        'brand': brand,
        'physical_cores': physical_cores,
        'logical_cores': logical_cores,
        'current_speed': current_speed,
        'max_speed': max_speed,
        'architecture': arch
    }


def get_gpu_details():
    gpu_name = 'N/A'
    gpu_brand = 'N/A'
    gpu_vram = 'N/A'
    gpu_usage = 'N/A'
    resolution = 'N/A'
    display_count = 'N/A'

    if IS_WINDOWS:
        out = _safe_run('wmic path win32_VideoController get name,AdapterRAM /format:list')
        if out:
            current_name = None
            current_vram = None
            for line in out.splitlines():
                line = line.strip()
                if line.startswith('Name='):
                    current_name = line.split('=', 1)[1].strip()
                elif line.startswith('AdapterRAM='):
                    current_vram = line.split('=', 1)[1].strip()
                    if current_name and current_name.lower() not in ('', 'microsoft basic display driver'):
                        gpu_name = current_name
                        if current_vram and current_vram.isdigit():
                            vram_gb = int(current_vram) / (1024 ** 3)
                            if vram_gb > 0.1:
                                gpu_vram = f"{vram_gb:.1f} GB"
                        break
    else:
        out = _safe_run('lspci 2>/dev/null | grep -i vga')
        if out:
            gpu_name = out.split(':', 2)[-1].strip() if ':' in out else out

    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            g = gpus[0]
            gpu_name = g.name or gpu_name
            gpu_usage = f"{g.load * 100:.1f}%"
            if g.memoryTotal:
                gpu_vram = f"{g.memoryTotal:.0f} MB"
    except Exception:
        pass

    name_upper = (gpu_name or '').upper()
    if 'NVIDIA' in name_upper or 'GEFORCE' in name_upper or 'RTX' in name_upper or 'GTX' in name_upper:
        gpu_brand = 'NVIDIA'
    elif 'AMD' in name_upper or 'RADEON' in name_upper:
        gpu_brand = 'AMD'
    elif 'INTEL' in name_upper:
        gpu_brand = 'Intel'

    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
        if monitors:
            display_count = len(monitors)
            primary = monitors[0]
            resolution = f"{primary.width}x{primary.height}"
            if len(monitors) > 1:
                resolutions = [f"{m.width}x{m.height}" for m in monitors]
                resolution = ', '.join(resolutions)
    except Exception:
        pass

    return {
        'name': gpu_name,
        'brand': gpu_brand,
        'vram': gpu_vram,
        'usage': gpu_usage,
        'resolution': resolution,
        'display_count': display_count
    }


def get_os_details():
    uname = platform.uname()
    os_full = 'N/A'
    os_version = 'N/A'
    os_build = 'N/A'
    os_arch = 'N/A'
    activation = 'N/A'
    last_update = 'N/A'
    system_language = 'N/A'

    try:
        system_language = locale.getdefaultlocale()[0] or 'N/A'
        if system_language and system_language != 'N/A':
            system_language = system_language.replace('_', '-')
    except Exception:
        pass

    if IS_WINDOWS:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion')
            product_name = winreg.QueryValueEx(key, 'ProductName')[0]
            build = winreg.QueryValueEx(key, 'CurrentBuildNumber')[0]
            display_version = ''
            try:
                display_version = winreg.QueryValueEx(key, 'DisplayVersion')[0]
            except Exception:
                pass
            os_full = product_name
            os_version = display_version or uname.release
            os_build = build
            winreg.CloseKey(key)
        except Exception:
            os_full = f"{uname.system} {uname.release}"
            os_version = uname.release
            os_build = uname.version

        out = _safe_run('cscript //nologo %windir%\\system32\\slmgr.vbs /xpr')
        if out:
            if 'permanently activated' in out.lower() or 'license is valid' in out.lower():
                activation = 'Activated'
            elif 'grace period' in out.lower():
                activation = 'Grace Period'
            else:
                activation = 'Not Activated'

        out = _safe_run('powershell -Command "(Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn"')
        if out and out.strip():
            last_update = out.strip()
    else:
        os_full = f"{uname.system} {uname.release}"
        os_version = uname.release
        os_build = uname.version
        out = _safe_run('lsb_release -ds 2>/dev/null')
        if out:
            os_full = out.strip('"')

    bits = platform.architecture()[0]
    os_arch = bits if bits else 'N/A'

    return {
        'full_name': os_full,
        'version': os_version,
        'build': os_build,
        'architecture': os_arch,
        'activation': activation,
        'last_update': last_update,
        'language': system_language
    }


def get_device_details():
    hostname = socket.gethostname()
    device_type = 'Desktop 🖥️'
    battery_pct = 'N/A'
    battery_status = 'N/A'
    battery_health = 'N/A'
    bios_version = 'N/A'

    battery = psutil.sensors_battery()
    if battery is not None:
        device_type = 'Laptop 💻'
        battery_pct = f"{round(battery.percent, 1)}%"
        if battery.power_plugged:
            battery_status = 'Charging'
        else:
            battery_status = 'Discharging'
    else:
        device_type = 'Desktop 🖥️'

    os_info = get_os_details()
    os_name_lower = (os_info.get('full_name') or '').lower()
    if 'server' in os_name_lower:
        device_type = 'Server 🗄️'

    boot_time_timestamp = psutil.boot_time()
    bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
    now = datetime.datetime.now()
    uptime_delta = now - bt
    uptime = f"{uptime_delta.days} days, {uptime_delta.seconds // 3600} hours, {(uptime_delta.seconds // 60) % 60} minutes"
    last_boot = bt.strftime("%Y-%m-%d %H:%M:%S")

    if IS_WINDOWS:
        out = _safe_run('wmic bios get version /format:list')
        if out:
            for line in out.splitlines():
                if line.startswith('Version='):
                    bios_version = line.split('=', 1)[1].strip()
                    break
    else:
        out = _safe_run('dmidecode --type bios 2>/dev/null')
        if out:
            m = re.search(r'Version:\s*(.+)', out)
            if m:
                bios_version = m.group(1).strip()

    return {
        'hostname': hostname,
        'device_type': device_type,
        'battery_percent': battery_pct,
        'battery_status': battery_status,
        'battery_health': battery_health,
        'uptime': uptime,
        'last_boot_time': last_boot,
        'bios_version': bios_version
    }


def get_network_adapters():
    adapters = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for iface, addr_list in addrs.items():
            if iface.lower().startswith('lo') or 'loopback' in iface.lower():
                continue
            ip = 'N/A'
            mac = 'N/A'
            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                elif hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK:
                    mac = addr.address
                elif addr.family == 17 or (hasattr(addr, 'family') and str(addr.family) == 'AddressFamily.AF_LINK'):
                    mac = addr.address

            conn_type = 'Ethernet'
            iface_lower = iface.lower()
            if 'wi' in iface_lower or 'wlan' in iface_lower or 'wireless' in iface_lower:
                conn_type = 'WiFi'

            speed = 'N/A'
            if iface in stats:
                s = stats[iface].speed
                if s and s > 0:
                    speed = f"{s} Mbps"

            if ip != 'N/A' or mac != 'N/A':
                adapters.append({
                    'name': iface,
                    'ip': ip,
                    'mac': mac,
                    'connection_type': conn_type,
                    'speed': speed
                })
    except Exception:
        pass

    if not adapters:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            adapters.append({
                'name': 'Primary',
                'ip': ip,
                'mac': 'N/A',
                'connection_type': 'N/A',
                'speed': 'N/A'
            })
        except Exception:
            pass

    return adapters


def get_device_info():
    return {
        'storage': get_storage_details(),
        'ram': get_ram_details(),
        'processor': get_processor_details(),
        'gpu': get_gpu_details(),
        'os': get_os_details(),
        'device': get_device_details(),
        'network': get_network_adapters()
    }


def get_system_metrics():
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count(logical=True)

    svmem = psutil.virtual_memory()
    ram_total = svmem.total
    ram_free = svmem.available
    ram_used = svmem.used
    ram_usage_percent = svmem.percent

    try:
        partitions = psutil.disk_partitions()
        primary_mount = partitions[0].mountpoint
        disk_usage = psutil.disk_usage(primary_mount)
        disk_total = disk_usage.total
        disk_free = disk_usage.free
        disk_used = disk_usage.used
        disk_usage_percent = disk_usage.percent
    except Exception:
        disk_total = 0
        disk_free = 0
        disk_used = 0
        disk_usage_percent = 0

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        network_status = "Connected"
    except Exception:
        ip_address = "N/A"
        network_status = "Disconnected"

    net_io = psutil.net_io_counters()
    bytes_sent = net_io.bytes_sent
    bytes_recv = net_io.bytes_recv

    device_info = get_device_info()
    uname = platform.uname()
    os_name_version = device_info['os'].get('full_name') or f"{uname.system} {uname.release}"
    uptime = device_info['device'].get('uptime', 'N/A')

    processes = []
    for proc in psutil.process_iter(['name', 'memory_percent']):
        try:
            processes.append(proc.info)
        except Exception:
            pass
    processes = sorted([p for p in processes if p['memory_percent'] is not None], key=lambda p: p['memory_percent'], reverse=True)[:5]
    for p in processes:
        p['memory_percent'] = round(p['memory_percent'], 2)

    battery = psutil.sensors_battery()
    battery_info = {}
    if battery:
        battery_info = {
            "percent": round(battery.percent, 2),
            "plugged_in": battery.power_plugged
        }
    else:
        battery_info = {"percent": None, "plugged_in": None}

    sec_score, sec_details = get_security_score()

    current_time = datetime.datetime.now()
    date_str = current_time.strftime("%Y-%m-%d")
    time_str = current_time.strftime("%H:%M:%S")

    issues = []
    fixes = []

    if cpu_usage > 80:
        issues.append("High CPU Warning")
        fixes.append("Close background applications consuming CPU cycles.")
    if ram_usage_percent > 80:
        issues.append("High RAM Warning")
        fixes.append("Close tabs or applications; consider upgrading RAM.")
    if disk_usage_percent > 85:
        issues.append("Critical Disk Space Warning")
        fixes.append("Delete temporary files or uninstall unused programs.")
    if network_status == "Disconnected":
        issues.append("Network Issue")
        fixes.append("Check your internet connection or router.")

    proc = device_info['processor']
    gpu = device_info['gpu']
    ram = device_info['ram']
    dev = device_info['device']
    os_det = device_info['os']

    return {
        "cpu": {"usage": cpu_usage, "cores": cpu_cores},
        "ram": {"total": ram_total, "free": ram_free, "used": ram_used, "usage_percent": ram_usage_percent},
        "disk": {"total": disk_total, "free": disk_free, "used": disk_used, "usage_percent": disk_usage_percent},
        "network": {"status": network_status, "ip": ip_address, "bytes_sent": bytes_sent, "bytes_recv": bytes_recv},
        "os": {"name_version": os_name_version, "uptime": uptime},
        "processes": processes,
        "battery": battery_info,
        "security": {"score": sec_score, "details": sec_details},
        "time": {"date": date_str, "time": time_str},
        "issues": issues,
        "fixes": fixes,
        "device_info": device_info,
        "processor_name": proc.get('name', 'N/A'),
        "processor_gen": proc.get('generation', 'N/A'),
        "cpu_cores": proc.get('physical_cores', 'N/A'),
        "cpu_threads": proc.get('logical_cores', 'N/A'),
        "cpu_speed": proc.get('current_speed', 'N/A'),
        "gpu_name": gpu.get('name', 'N/A'),
        "gpu_vram": gpu.get('vram', 'N/A'),
        "gpu_usage": gpu.get('usage', 'N/A'),
        "ram_type": ram.get('type', 'N/A'),
        "ram_speed": ram.get('speed', 'N/A'),
        "drives": device_info['storage'],
        "os_version": os_det.get('version', 'N/A'),
        "os_build": os_det.get('build', 'N/A'),
        "device_name": dev.get('hostname', 'N/A'),
        "device_type": dev.get('device_type', 'N/A'),
        "screen_resolution": gpu.get('resolution', 'N/A'),
        "display_count": gpu.get('display_count', 'N/A'),
        "network_adapters": device_info['network'],
        "bios_version": dev.get('bios_version', 'N/A'),
        "last_boot_time": dev.get('last_boot_time', 'N/A'),
    }
