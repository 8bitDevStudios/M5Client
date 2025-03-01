import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu, Toplevel
import requests
import serial
import serial.tools.list_ports
import os
import threading
import webbrowser

# Куда летят зависимости
data_directory = os.path.join(os.getenv('APPDATA'), 'M5Client_data')

# Создание папки, если она не существует
os.makedirs(data_directory, exist_ok=True)

# Зависимости
required_files = {
    "cathack.png": "https://github.com/Teapot321/M5Client/raw/main/Background/cathack.png",
    "bruce.png": "https://github.com/Teapot321/M5Client/raw/main/Background/bruce.png",
    "nemo.png": "https://github.com/Teapot321/M5Client/raw/main/Background/nemo.png",
    "m5launcher.png": "https://github.com/Teapot321/M5Client/raw/main/Background/m5launcher.png",
    "marauder.png": "https://github.com/Teapot321/M5Client/raw/main/Background/marauder.png",
    "factory.png": "https://github.com/Teapot321/M5Client/raw/main/Background/factory.png",
    "esptool.exe": "https://github.com/Teapot321/M5Client/raw/refs/heads/main/esptool.exe"
}

# Словарь с ссылками на бинарные файлы для каждого устройства
firmware_urls = {
    "Bruce": {
        "Card": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Bruce/Card.bin",
        "Plus1": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Bruce/Plus1.bin",
        "Plus2": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Bruce/Plus2.bin"
    },
    "CatHack": {
        "Plus2": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Cathack/Plus2.bin"
    },
    "Factory": {
        "Card": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Factory/Card.bin",
        "Plus1": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Factory/Plus1.bin",
        "Plus2": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Factory/Plus2.bin"
    },
    "M5Launcher": {
        "Card": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/M5Launcher/Card.bin",
        "Plus1": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/M5Launcher/Plus1.bin",
        "Plus2": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/M5Launcher/Plus2.bin"
    },
    "Marauder": {
        "Card": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Marauder/Card.bin",
        "Plus1": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Marauder/Plus1.bin",
        "Plus2": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Marauder/Plus2.bin"
    },
    "Nemo": {
        "Card": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Nemo/Card.bin",
        "Plus1": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Nemo/Plus1.bin",
        "Plus2": "https://github.com/Teapot174/M5Client/raw/refs/heads/main/FW/Nemo/Plus2.bin"
    }
}

# Проверка наличия зависимостей и их загрузка
def check_and_download_files():
    for filename, url in required_files.items():
        file_path = os.path.join(data_directory, filename)
        if not os.path.exists(file_path):
            download_file(url, file_path)

def download_file(url, file_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"File {file_path} downloaded.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to upload {file_path}: {e}")

# Установка библиотек
def install_requirements():
    required_packages = [
        "requests",
        "pyserial",
        "tkinterdnd2",
    ]

    for package in required_packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Установка esptool
def install_esptool():
    esptool_path = os.path.join(data_directory, 'esptool.exe')

    if not os.path.exists(esptool_path):
        download_file(required_files["esptool.exe"], esptool_path)

# Получение URL для прошивки
def get_latest_firmware_url():
    device = device_var.get()
    firmware_name = current_firmware.get()

    if firmware_name in firmware_urls and device in firmware_urls[firmware_name]:
        return firmware_urls[firmware_name][device]
    else:
        raise Exception(f"Firmware for {firmware_name} on device {device} not found.")

# Установка бина
def install_firmware():
    try:
        firmware_url = get_latest_firmware_url()
        firmware_path = os.path.join(data_directory, "Firmware.bin")  # Имя файла изменено на Firmware.bin

        response = requests.get(firmware_url)
        response.raise_for_status()  # Проверка на ошибки
        with open(firmware_path, 'wb') as f:
            f.write(response.content)
        flash_firmware(firmware_path)
    except Exception as e:
        messagebox.showerror("M5Client", f"Failed to download the firmware: {e}")

# Прошивка устройства
def flash_firmware(firmware_path):
    com_port = com_port_var.get()
    esptool_path = os.path.join(data_directory, 'esptool.exe')

    loading_window = Toplevel(root)
    loading_window.title("M5Client")
    loading_window.geometry("300x100")
    loading_window.configure(bg="#050403")

    loading_label = tk.Label(loading_window, text="Flashing...", bg="#050403", fg="#ffffff",
                             font=("Arial", 14))
    loading_label.pack(pady=20)

    root.update()

    def flash_device():
        try:
            command = [esptool_path, '--port', com_port, '--baud', '1500000', 'write_flash', '0x00000', firmware_path]
            subprocess.run(command, check=True)
            messagebox.showinfo("M5Client", "The firmware is installed")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to flash the device: {e}")
        finally:
            loading_window.destroy()
            unblock_buttons()

    threading.Thread(target=flash_device).start()

def start_installation():
    install_button.config(state=tk.DISABLED)
    install_firmware()

def block_buttons():
    install_button.config(state=tk.DISABLED, bg="gray", fg="white")
    com_port_menu.config(state=tk.DISABLED, bg="gray", fg="white")
    switch_firmware_button.config(state=tk.DISABLED, bg="gray", fg="white")
    device_menu.config(state=tk.DISABLED, bg="gray", fg="white")
    drivers_button.config(state=tk.DISABLED, bg="gray", fg="white")

def unblock_buttons():
    install_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    com_port_menu.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    switch_firmware_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    device_menu.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    drivers_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    update_button_colors()

def get_com_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

root = tk.Tk()
root.title("M5Client | v2.7")
root.configure(bg="#050403")
root.geometry("600x350")
root.resizable(False, False)

# Проверяем и загружаем необходимые зависимости
check_and_download_files()

# Загружаем изображения
cat_hack_image = tk.PhotoImage(file=os.path.join(data_directory, "cathack.png"))
bruce_image = tk.PhotoImage(file=os.path.join(data_directory, "bruce.png"))
nemo_image = tk.PhotoImage(file=os.path.join(data_directory, "nemo.png"))
m5launcher_image = tk.PhotoImage(file=os.path.join(data_directory, "m5launcher.png"))
marauder_image = tk.PhotoImage(file=os.path.join(data_directory, "marauder.png"))
factory_image = tk.PhotoImage(file=os.path.join(data_directory, "factory.png"))

img = tk.Label(root, image=cat_hack_image, bg="#050403")
img.place(relx=0.5, rely=0.0, anchor='n')

install_button = tk.Button(root, text="Install", command=lambda: threading.Thread(target=start_installation).start(),
                           bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid", highlightbackground="#d9d9d9",
                           highlightcolor="white", font=("Fixedsys", 20))

current_firmware = StringVar(value="CatHack")

def switch_firmware():
    global current_firmware
    if current_firmware.get() == "CatHack":
        current_firmware.set("Bruce")
        switch_firmware_button.config(text="Bruce")
        img.config(image=bruce_image)
    elif current_firmware.get() == "Bruce":
        current_firmware.set("Nemo")
        switch_firmware_button.config(text="Nemo")
        img.config(image=nemo_image)
    elif current_firmware.get() == "Nemo":
        current_firmware.set("Marauder")
        switch_firmware_button.config(text="Marauder")
        img.config(image=marauder_image)
    elif current_firmware.get() == "Marauder":
        current_firmware.set("M5Launcher")
        switch_firmware_button.config(text="M5Launcher")
        img.config(image=m5launcher_image)
    elif current_firmware.get() == "M5Launcher":
        current_firmware.set("Factory")
        switch_firmware_button.config(text="Factory")
        img.config(image=factory_image)
    else:
        current_firmware.set("CatHack")
        switch_firmware_button.config(text="CatHack")
        img.config(image=cat_hack_image)

    device_var.set("Plus2")
    update_device_options()
    update_button_colors()

def update_device_options():
    current_firmware_value = current_firmware.get()
    device_menu['menu'].delete(0, 'end')
    if current_firmware_value == "Factory":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Card', command=lambda: device_var.set('Card'))
    elif current_firmware_value == "CatHack":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
    elif current_firmware_value == "M5Launcher":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Card', command=lambda: device_var.set('Card'))
    elif current_firmware_value == "Marauder":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Card', command=lambda: device_var.set('Card'))
    elif current_firmware_value == "Factory":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Card', command=lambda: device_var.set('Card'))
    else:
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        device_menu['menu'].add_command(label='Card', command=lambda: device_var.set('Card'))

# Цвета кнопок
def update_button_colors():
    if current_firmware.get() == "Factory":
        color = "#000000"
        text_color = "#fab320"
    elif current_firmware.get() == "Nemo":
        color = "#060606"
        text_color = "#7d9f71"
    elif current_firmware.get() == "Bruce":
        color = "#030407"
        text_color = "#a82da4"
    elif current_firmware.get() == "M5Launcher":
        color = "#030703"
        text_color = "#9cb597"
    elif current_firmware.get() == "Marauder":
        color = "#000000"
        text_color = "#c3c3c3"
    else:
        color = "#050403"
        text_color = "#ff8e19"

    install_button.config(bg=color, fg=text_color)
    com_port_menu.config(bg=color, fg=text_color)
    switch_firmware_button.config(bg=color, fg=text_color)
    device_menu.config(bg=color, fg=text_color)
    drivers_button.config(bg=color, fg=text_color)

switch_firmware_button = tk.Button(root, text="CatHack", command=switch_firmware,
                                   bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid",
                                   highlightbackground="#d9d9d9", highlightcolor="white", font=("Fixedsys", 11))

device_var = StringVar(root)
device_var.set("Plus2")

device_menu = OptionMenu(root, device_var, "Plus2")
device_menu.config(bg="#050403", fg="#ff8e19", highlightbackground="#161615", borderwidth=2)

com_port_var = StringVar(root)
com_ports = get_com_ports()
com_port_var.set(com_ports[0] if com_ports else "No ports available")

com_port_menu = OptionMenu(root, com_port_var, *com_ports)
com_port_menu.config(bg="#050403", fg="#ff8e19", highlightbackground="#161615", borderwidth=2)

# Гит(Типотика) с драйверами
def open_drivers_page():
    webbrowser.open("https://github.com/Teapot321/M5Client/tree/main/Drivers")

drivers_button = tk.Button(root, text="?", command=open_drivers_page,
                           bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid",
                           highlightbackground="#d9d9d9", highlightcolor="white", font=("Fixedsys", 1))

install_button.bind("<Enter>", lambda e: install_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9"))
install_button.bind("<Leave>", lambda e: update_button_colors())
switch_firmware_button.bind("<Enter>", lambda e: switch_firmware_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9"))
switch_firmware_button.bind("<Leave>", lambda e: update_button_colors())
drivers_button.bind("<Enter>", lambda e: drivers_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9"))
drivers_button.bind("<Leave>", lambda e: update_button_colors())

install_button.place(relx=0.17, rely=0.11, anchor='center')
com_port_menu.place(relx=0.40, rely=0.11, anchor='center')
switch_firmware_button.place(relx=0.5, rely=0.90, anchor='n')
device_menu.place(relx=0.54, rely=0.11, anchor='center')
drivers_button.place(relx=0.31, rely=0.07, anchor='n')

install_button.config(bg="#050403", fg="#ff8e19", highlightbackground="#d9d9d9", borderwidth=2)

install_esptool()

root.mainloop()