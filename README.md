# Okulo

A small eye-shaped desktop buddy that just... Hangs around! And stares! Menacingly... And, well, doesn't have to be an eye.


## Building from Source

### 0. Dependencies

Make sure you've installed:
* Python
* [git](https://git-scm.com/) (optional)
* [inno setup](https://jrsoftware.org/isinfo.php) (optional)


### 1. Clone the repository

Make sure you have Git installed, then clone the repository:

```powershell
git clone https://github.com/CnosuSystem/Okulo.git
cd Okulo
```

If you don't have Git, simply download the raw source .zip file from GitHub and put it in your preffered directory. Then open it in the terminal.

### 2. Set up the virtual enviroment

Create a virtual environment to keep Okulo's dependencies separate from other Python projects:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

You don't need to activate the virtual environment; the commands above use its Python interpreter directly.

### 3. Build the project

Run the following command from the repository root:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --onedir --windowed --icon "source\assets\icons\okulo.ico" --name "Okulo" --add-data "source\assets;assets/"  "source\main.py"
```

PyInstaller packages Okulo into a distributable application. The executable will be located at dist/Okulo/Okulo.exe.

You can delete the build/ directory after building, as it contains temporary build files. Keep dist/ if you want to retain the packaged application.

### 4. Build installer (optional)

If you have Inno Setup installed, open inno_installer_script.iss in Inno Setup and compile it to create the installer.

The installer will be located at Output/Okulo-Setup.exe. It lets users install Okulo into their chosen directory.

**Note:** Okulo may require administrator privileges to save configuration files, depending on the installation directory and your Windows permissions. The installer also associates .oemf files with Okulo.


## Usage

Reffer to [USAGE.md](https://github.com/CnosuSystem/Okulo/blob/main/USAGE.md) in order to learn about how to use this software.


## Changelog

For the changelog, please reffer to the [CHANGELOG.md](https://github.com/CnosuSystem/Okulo/blob/main/CHANGELOG.md) file in the root of this project's GitHub repository.


## Authors

* [@Cnosu](https://spacehey.com/cnosu) - The guy that did all the coding and the drawing


## License

This project is licensed under the [GNU GPLv3 License](https://www.gnu.org/licenses/gpl-3.0.en.html#license-text) - see the [LICENSE.md](https://github.com/CnosuSystem/Okulo?tab=GPL-3.0-1-ov-file) file for details.