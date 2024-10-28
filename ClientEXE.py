import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu, Toplevel
import requests
import serial
import time
import serial.tools.list_ports
import os
import zipfile
import threading

# Папка для загрузки файлов
data_directory = os.path.join(os.getenv('APPDATA'), 'm5client_data')

# Создание папки, если она не существует
os.makedirs(data_directory, exist_ok=True)

# Список необходимых файлов
required_files = {
    "cathack.png": "https://github.com/Teapot321/M5Client/raw/main/cathack.png",
    "bruce.png": "https://github.com/Teapot321/M5Client/raw/main/bruce.png",
    "nemo.png": "https://github.com/Teapot321/M5Client/raw/main/nemo.png",
    "esptool.zip": "https://github.com/espressif/esptool/releases/download/v4.8.0/esptool-v4.8.0-win64.zip"
}

# Проверка наличия файлов и их загрузка
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
        print(f"Файл {file_path} загружен.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить {file_path}: {e}")

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
    esptool_zip_path = os.path.join(data_directory, 'esptool.zip')
    esptool_dir = os.path.join(data_directory, 'esptool480')

    if not os.path.exists(os.path.join(esptool_dir, 'esptool-win64', 'esptool.exe')):
        def download_and_extract():
            try:
                with zipfile.ZipFile(esptool_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(esptool_dir)
                os.remove(esptool_zip_path)
                messagebox.showinfo("M5Client", "Все зависимости успешно установлены!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось установить esptool: {e}")

        threading.Thread(target=download_and_extract).start()

# Драйвер
def download_and_install_driver():
    driver_url = "https://github.com/Teapot321/M5Client/raw/refs/heads/main/CH341SER.EXE"
    driver_path = os.path.join(data_directory, "CH341SER.EXE")

    block_buttons()
    loading_window = Toplevel(root)
    loading_window.title("Загрузка драйвера")
    loading_window.geometry("300x100")
    loading_window.configure(bg="#050403")

    loading_label = tk.Label(loading_window, text="Скачивание драйвера...", bg="#050403", fg="#ffffff",
                             font=("Arial", 14))
    loading_label.pack(pady=20)

    root.update()

    def download_driver():
        try:
            response = requests.get(driver_url)
            with open(driver_path, 'wb') as f:
                f.write(response.content)

            subprocess.run(driver_path, check=True)
            messagebox.showinfo("Успех", "Драйвер установлен успешно!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось установить драйвер: {e}")
        finally:
            loading_window.destroy()
            unblock_buttons()

    threading.Thread(target=download_driver).start()

# URL
def get_latest_firmware_url():
    if current_firmware.get() == "Bruce":
        api_url = 'https://api.github.com/repos/pr3y/Bruce/releases/latest'
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()
        for asset in release_data['assets']:
            if 'plus2' in asset['name'].lower():
                return asset['browser_download_url']
        raise Exception("Прошивка для Plus2 не найдена.")
    elif current_firmware.get() == "Nemo":
        return "https://github.com/n0xa/m5stick-nemo/releases/download/v2.7.0/M5Nemo-v2.7.0-M5StickCPlus2.bin"
    else:
        api_url = "https://api.github.com/repos/Stachugit/CatHack/releases/latest"
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()
        asset = release_data['assets'][0]
        return asset['browser_download_url']

# Установка бина
def install_firmware():
    try:
        firmware_url = get_latest_firmware_url()
        firmware_path = os.path.join(data_directory, "latest_firmware.bin")

        response = requests.get(firmware_url)
        with open(firmware_path, 'wb') as f:
            f.write(response.content)
        flash_firmware(firmware_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить прошивку: {e}")

# Прошивка стика
def flash_firmware(firmware_path):
    com_port = com_port_var.get()
    esptool_path = os.path.join(data_directory, 'esptool480', 'esptool-win64', 'esptool.exe')

    loading_window = Toplevel(root)
    loading_window.title("Прошивка устройства")
    loading_window.geometry("300x100")
    loading_window.configure(bg="#050403")

    loading_label = tk.Label(loading_window, text="Прошивка устройства...", bg="#050403", fg="#ffffff",
                             font=("Arial", 14))
    loading_label.pack(pady=20)

    root.update()

    def flash_device():
        try:
            command = [esptool_path, '--port', com_port, '--baud', '1500000', 'write_flash', '0x00000', firmware_path]
            subprocess.run(command, check=True)
            messagebox.showinfo("Успех", "Прошивка установлена успешно!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Ошибка", f"Не удалось прошить устройство: {e}")
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
    driver_button.config(state=tk.DISABLED, bg="gray", fg="white")
    switch_firmware_button.config(state=tk.DISABLED, bg="gray", fg="white")

def unblock_buttons():
    if current_firmware.get() == "Nemo":
        install_button.config(state=tk.NORMAL, bg="#060606", fg="#7d9f71")
        com_port_menu.config(state=tk.NORMAL, bg="#060606", fg="#7d9f71")
        driver_button.config(state=tk.NORMAL, bg="#060606", fg="#7d9f71")
        switch_firmware_button.config(state=tk.NORMAL, bg="#060606", fg="#7d9f71")
    elif current_firmware.get() == "Bruce":
        install_button.config(state=tk.NORMAL, bg="#030407", fg="#a82da4")
        com_port_menu.config(state=tk.NORMAL, bg="#030407", fg="#a82da4")
        driver_button.config(state=tk.NORMAL, bg="#030407", fg="#a82da4")
        switch_firmware_button.config(state=tk.NORMAL, bg="#030407", fg="#a82da4")
    else:
        install_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
        com_port_menu.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
        driver_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
        switch_firmware_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")

def get_com_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

root = tk.Tk()
root.title("M5Client")
root.configure(bg="#050403")
root.geometry("600x350")
root.resizable(False, False)

# Проверяем и загружаем необходимые файлы
check_and_download_files()

# Загружаем изображения
cat_hack_image = tk.PhotoImage(file=os.path.join(data_directory, "cathack.png"))
bruce_image = tk.PhotoImage(file=os.path.join(data_directory, "bruce.png"))
nemo_image = tk.PhotoImage(file=os.path.join(data_directory, "nemo.png"))

img = tk.Label(root, image=cat_hack_image, bg="#050403")
img.place(relx=0.5, rely=0.0, anchor='n')

install_button = tk.Button(root, text="Install", command=lambda: threading.Thread(target=start_installation).start(),
                           bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid", highlightbackground="#d9d9d9",
                           highlightcolor="white", font=("Fixedsys", 20))

driver_button = tk.Button(root, text="Driver", command=download_and_install_driver,
                          bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid", highlightbackground="#d9d9d9",
                          highlightcolor="white", font=("Fixedsys", 11))

current_firmware = StringVar(value="CatHack")

def switch_firmware():
    global current_firmware
    if current_firmware.get() == "CatHack":
        current_firmware.set("Bruce")
        switch_firmware_button.config(text="Bruce")
        img.config(image=bruce_image)
        install_button.config(bg="#030407", fg="#a82da4")
        com_port_menu.config(bg="#030407", fg="#a82da4")
        driver_button.config(bg="#030407", fg="#a82da4")
        switch_firmware_button.config(bg="#030407", fg="#a82da4")
    elif current_firmware.get() == "Bruce":
        current_firmware.set("Nemo")
        switch_firmware_button.config(text="Nemo")
        img.config(image=nemo_image)
        install_button.config(bg="#060606", fg="#7d9f71")
        com_port_menu.config(bg="#060606", fg="#7d9f71")
        driver_button.config(bg="#060606", fg="#7d9f71")
        switch_firmware_button.config(bg="#060606", fg="#7d9f71")
    else:
        current_firmware.set("CatHack")
        switch_firmware_button.config(text="CatHack")
        img.config(image=cat_hack_image)
        install_button.config(bg="#050403", fg="#ff8e19")
        com_port_menu.config(bg="#050403", fg="#ff8e19")
        driver_button.config(bg="#050403", fg="#ff8e19")
        switch_firmware_button.config(bg="#050403", fg="#ff8e19")

switch_firmware_button = tk.Button(root, text="CatHack", command=switch_firmware,
                                   bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid",
                                   highlightbackground="#d9d9d9", highlightcolor="white", font=("Fixedsys", 11))

com_port_var = StringVar(root)
com_ports = get_com_ports()
com_port_var.set(com_ports[0] if com_ports else "Нет доступных портов")

com_port_menu = OptionMenu(root, com_port_var, *com_ports)
com_port_menu.config(bg="#050403", fg="#ff8e19", highlightbackground="#161615", borderwidth=2)

# Привязка событий для кнопок
def on_enter_install(event):
    install_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_install(event):
    if current_firmware.get() == "Nemo":
        install_button.config(bg="#060606", fg="#7d9f71")
    elif current_firmware.get() == "Bruce":
        install_button.config(bg="#030407", fg="#a82da4")
    else:
        install_button.config(bg="#050403", fg="#ff8e19")

def on_enter_driver(event):
    driver_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_driver(event):
    if current_firmware.get() == "Nemo":
        driver_button.config(bg="#060606", fg="#7d9f71")
    elif current_firmware.get() == "Bruce":
        driver_button.config(bg="#030407", fg="#a82da4")
    else:
        driver_button.config(bg="#050403", fg="#ff8e19")

def on_enter_switch(event):
    switch_firmware_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_switch(event):
    if current_firmware.get() == "Nemo":
        switch_firmware_button.config(bg="#060606", fg="#7d9f71")
    elif current_firmware.get() == "Bruce":
        switch_firmware_button.config(bg="#030407", fg="#a82da4")
    else:
        switch_firmware_button.config(bg="#050403", fg="#ff8e19")

install_button.bind("<Enter>", on_enter_install)
install_button.bind("<Leave>", on_leave_install)
driver_button.bind("<Enter>", on_enter_driver)
driver_button.bind("<Leave>", on_leave_driver)
switch_firmware_button.bind("<Enter>", on_enter_switch)
switch_firmware_button.bind("<Leave>", on_leave_switch)

install_button.place(relx=0.17, rely=0.11, anchor='center')
com_port_menu.place(relx=0.37, rely=0.11, anchor='center')
driver_button.place(relx=0.5, rely=0.93, anchor='center')
switch_firmware_button.place(relx=0.93, rely=0.05, anchor='ne')

install_button.config(bg="#050403", fg="#ff8e19", highlightbackground="#d9d9d9", borderwidth=2)

install_esptool()

root.mainloop()
