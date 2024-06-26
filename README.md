# quick-ternaries

Quick Ternaries is a python application designed to make ternary plotting a breeze. 

# Setup

Below are installation instructions for macOS and Windows. Regardless of your operating system, we recommend following the Automatic setup instructions, and launching the tool with the provided launcher. This way, each time you boot up the tool, it will check for updates and offer to install them if any are found.

Note: This tool requires Python 3.11+.

For basic instructions on how to use the Terminal/Command Prompt, see the [New to the Terminal](#new-to-the-terminal) section.

## macOS

### Automatic

- Download the macOS launcher zipfile from the [macOS Launcher Release](https://github.com/ariessunfeld/quick-ternaries/releases/download/mac-launcher/quick-ternaries-mac-launcher.zip)
- Open the Finder and unzip the launcher by double-clicking the zipfile
- Right-click the file `quick-ternaries_mac.command`, click `Open`, and then click `Open Anyway`
  - (After doing this once, your computer will trust the file, and you can just double-click `quick-ternaries_mac.command` to launch the app.)
- Follow the prompts in the Terminal and agree to update if asked

### Manual

- Open the Terminal and navigate to the location where you want to install the tool
- Create a new virtual environment called `ternaries-env` (or whatever you like) by running the command `python3.11 -m venv ternaries-env`
- Activate the virtual environment by running `source ternaries-env/bin/activate`
- Update `pip` by running `pip install --upgrade pip`
- Build the `quick-ternaries` package from source by running `pip install git+https://github.com/ariessunfeld/quick-ternaries.git`
  - NOTE: If you do not have Git installed, download the latest `.whl` file from the [`dist`](https://github.com/ariessunfeld/quick-ternaries/tree/main/dist) folder in this repository and run `pip install path/to/that/file.whl`
- Launch the tool (and test installation) by running `quick-ternaries`

## Windows

### Automatic

- Download the Windows launcher zipfile from the [Windows Launcher Release](https://github.com/ariessunfeld/quick-ternaries/releases/download/windows-launcher/quick-ternaries-windows-launcher.zip)
- Open the File Browser, click the zipfile, and unzip it by clicking Extract All
- Right-click the `quick-ternaries_windows.bat` file, click `Run`, and then click `Run Anyway`
  - (After doing this once, your computer will trust the file, and you can just double-click `quick-ternaries_windows.bat` to launch the app.)
- Follow the prompts in the command prompt and agree to update if asked

### Manual

- Open the Command Prompt and navigate to the location where you want to install the tool
- Create a new virtual environment called `ternaries-env` (or whatever you like) by running the command `python3.11 -m venv ternaries-env`
- Activate the virtual environment by running `call ternaries-env\Scripts\activate.bat`
- Update `pip` by running `pip install --upgrade pip`
- Build the `quick-ternaries` package from source by running the command `pip install git+https://github.com/ariessunfeld/quick-ternaries.git`
  - NOTE: If you do not have Git installed, download the latest `.whl` file from the [`dist`](https://github.com/ariessunfeld/quick-ternaries/tree/main/dist) folder in this repository and run `pip install path\to\that\file.whl`
- Launch the tool (and test installation) by running the command `quick-ternaries`

## New to the Terminal

New to the Terminal / Command Prompt? No worries. 

### Opening the Terminal / Command Prompt

On macOS, to access the Terminal, the easiest way is to press Cmd+Space and type `Terminal`. A black rectangle icon should appear. Click on it, and you will launch the Terminal application (also known as `Terminal.app`).

On Windows, the terminal is called the Command Prompt. To access it, press the Windows key and type `Command Prompt`. A black rectangle icon should be among the options. Click on it, and you will launch the Command Prompt application (also known as `cmd.exe`.)

### Running Commands

When you read "Run the following command...", that means to type the command into the Terminal / Command Prompt and press the `Enter` or `Return` key. When you press `Enter` or `Return`, the Terminal / Command Prompt will execute the command.

### Navigating to a Directory

To move around different folders in the Terminal or Command Prompt, use the `cd` command. on macOS, the easiest way to get to a specific location is to open the Finder, locate the folder you want to be in, right-click the folder, then hold down the `option` key and choose `copy [foldername] as Pathname`. Then go back to the Terminal and type `cd`, then hit the `Space` bar, and then paste the pathname you copied by pressing `Cmd+V`. So, for example, if the path you copied was `/Users/yourname/Documents/someFolder/anotherFolder/`, the command would look like `cd /Users/yourname/Documents/someFolder/anotherFolder/`. 

In the Command Prompt, the process is similar. The easiest way to get to a specific folder in the Command Prompt is to open the File Browser, navigate to the desired folder, then click in the textbox at the top of the window and copy the path shown there, likely starting with `C:\...`. Then go into the Command Prompt and run the command `cd C:\...`, pasting the path you copied where the `C:\...` is.

# Usage

## Loading Data

The first step in using the Quick Ternaries tool is to load your dataset. This can be an `.xlsx` file or `.csv`, both are supported. The tool will try to identify the appropriate header row automatically, so don't worry if you have a few blank rows before the column names.

## Selecting a Ternary Type

After loading data, you need to select a ternary type. This is where you define the axes of your ternary diagram. By default, the tool will assume you want `Al2O3, CaO+Na2O+K2O, FeOT+MgO`. There a few other presets you can choose from, but if you need something not listed, you can choose to use a `Custom` type. This will display a selection interface showing the columns in your loaded data. You can select columns and then click the appropriate arrows to add columns to axes of your diagram. 

For example, if you have a column called `SiO2` in your data, it will appear on the left. If you want `SiO2` to be on the top apex of your ternary diagram, click `SiO2`, and then click the `>>` arrow for the `Top` box. If you make a mistake, you can click the item in any box and click the `<<` arrow to put it back.

## Filtering

TODO, multiple filters, etc

## Adding a Heatmap

TODO, setting range bounds, default values, etc

## TODO - more sections

TODO


# Copyright and License

O#: O4762  
see LICENSE for OSS and MIT license details
