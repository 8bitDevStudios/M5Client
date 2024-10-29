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
    device = device_var.get()  # Получаем текущее устройство
    if current_firmware.get() == "Bruce":
        api_url = 'https://api.github.com/repos/pr3y/Bruce/releases/latest'
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()
        for asset in release_data['assets']:
            if device == 'Plus2' and 'plus2' in asset['name'].lower():
                return asset['browser_download_url']
            elif device == 'Plus1' and 'plus' in asset['name'].lower() and 'plus2' not in asset['name'].lower():
                return asset['browser_download_url']
            elif device == 'Cardputer' and 'cardputer' in asset['name'].lower():
                return asset['browser_download_url']  # Ссылка на прошивку для Cardputer
        raise Exception("Прошивка для устройства не найдена.")
    elif current_firmware.get() == "Nemo":
        if device == 'Plus2':
            return "https://github.com/n0xa/m5stick-nemo/releases/download/v2.7.0/M5Nemo-v2.7.0-M5StickCPlus2.bin"
        elif device == 'Plus1':
            return "https://github.com/n0xa/m5stick-nemo/releases/download/v2.7.0/M5Nemo-v2.7.0-M5StickCPlus.bin"
        elif device == 'Cardputer':
            return "https://github.com/n0xa/m5stick-nemo/releases/download/v2.7.0/M5Nemo-v2.7.0-M5Cardputer.bin"  # Ссылка на прошивку для Cardputer
    else:  # CatHack
        if device != 'Plus2':
            raise Exception("Прошивка CatHack доступна только на Plus2.")
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
            unblock_buttons()  # Разблокируем кнопки после завершения прошивки

    threading.Thread(target=flash_device).start()

def start_installation():
    install_button.config(state=tk.DISABLED)
    install_firmware()

def block_buttons():
    install_button.config(state=tk.DISABLED, bg="gray", fg="white")
    com_port_menu.config(state=tk.DISABLED, bg="gray", fg="white")
    driver_button.config(state=tk.DISABLED, bg="gray", fg="white")
    switch_firmware_button.config(state=tk.DISABLED, bg="gray", fg="white")
    device_menu.config(state=tk.DISABLED, bg="gray", fg="white")

def unblock_buttons():
    install_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    com_port_menu.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    driver_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    switch_firmware_button.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    device_menu.config(state=tk.NORMAL, bg="#050403", fg="#ff8e19")
    update_button_colors()  # Обновляем цвета кнопок после разблокировки

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
    elif current_firmware.get() == "Bruce":
        current_firmware.set("Nemo")
        switch_firmware_button.config(text="Nemo")
        img.config(image=nemo_image)
    else:
        current_firmware.set("CatHack")
        switch_firmware_button.config(text="CatHack")
        img.config(image=cat_hack_image)

    # Устанавливаем стандартное устройство Plus2
    device_var.set("Plus2")
    update_device_options()  # Обновляем выбор устройства
    update_button_colors()  # Обновляем цвета кнопок

def update_device_options():
    current_firmware_value = current_firmware.get()
    device_menu['menu'].delete(0, 'end')  # Удаляем все элементы
    if current_firmware_value == "CatHack":
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
    else:
        device_menu['menu'].add_command(label='Plus2', command=lambda: device_var.set('Plus2'))
        device_menu['menu'].add_command(label='Plus1', command=lambda: device_var.set('Plus1'))
        # Добавляем Cardputer
        device_menu['menu'].add_command(label='Cardputer', command=lambda: device_var.set('Cardputer'))

def update_button_colors():
    if current_firmware.get() == "Nemo":
        color = "#060606"
        text_color = "#7d9f71"
    elif current_firmware.get() == "Bruce":
        color = "#030407"
        text_color = "#a82da4"
    else:
        color = "#050403"
        text_color = "#ff8e19"

    install_button.config(bg=color, fg=text_color)
    com_port_menu.config(bg=color, fg=text_color)
    driver_button.config(bg=color, fg=text_color)
    switch_firmware_button.config(bg=color, fg=text_color)
    device_menu.config(bg=color, fg=text_color)

switch_firmware_button = tk.Button(root, text="CatHack", command=switch_firmware,
                                   bg="#050403", fg="#ff8e19", borderwidth=2, relief="solid",
                                   highlightbackground="#d9d9d9", highlightcolor="white", font=("Fixedsys", 11))

# Выбор устройства
device_var = StringVar(root)
device_var.set("Plus2")  # Установите значение по умолчанию

# Инициализация меню выбора устройства
device_menu = OptionMenu(root, device_var, "Plus2")
device_menu.config(bg="#050403", fg="#ff8e19", highlightbackground="#161615", borderwidth=2)

com_port_var = StringVar(root)
com_ports = get_com_ports()
com_port_var.set(com_ports[0] if com_ports else "Нет доступных портов")

com_port_menu = OptionMenu(root, com_port_var, *com_ports)
com_port_menu.config(bg="#050403", fg="#ff8e19", highlightbackground="#161615", borderwidth=2)

# Привязка событий для кнопок
def on_enter_install(event):
    install_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_install(event):
    update_button_colors()

def on_enter_driver(event):
    driver_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_driver(event):
    update_button_colors()

def on_enter_switch(event):
    switch_firmware_button.config(bg="white", fg="#050403", highlightbackground="#d9d9d9")

def on_leave_switch(event):
    update_button_colors()

install_button.bind("<Enter>", on_enter_install)
install_button.bind("<Leave>", on_leave_install)
driver_button.bind("<Enter>", on_enter_driver)
driver_button.bind("<Leave>", on_leave_driver)
switch_firmware_button.bind("<Enter>", on_enter_switch)
switch_firmware_button.bind("<Leave>", on_leave_switch)

# Обновленные координаты для размещения кнопок
install_button.place(relx=0.17, rely=0.11, anchor='center')
com_port_menu.place(relx=0.37, rely=0.11, anchor='center')
driver_button.place(relx=0.5, rely=0.93, anchor='center')
switch_firmware_button.place(relx=0.85, rely=0.05, anchor='n')  # Кнопка выбора прошивки передвинута вправо
device_menu.place(relx=0.525, rely=0.11, anchor='center')  # Меню выбора устройства передвинуто на 3.5% влево

install_button.config(bg="#050403", fg="#ff8e19", highlightbackground="#d9d9d9", borderwidth=2)

install_esptool()

root.mainloop()
