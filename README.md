## Service-List-Builder

Build scripts to toggle between minimal & default services in Windows based on user defined lists

Contact: https://twitter.com/amitxv

I am not responsible for damage caused to computer. This tool is powerful & for advanced users only. There is a risk of damaging your operating system if you disable core services that are required for Windows to function correctly. It is your responsibility to use suitable service configurations for your specific operating system. It is also recommended that you use this tool before installing any programs as any other services not defined in the lists will be disabled (e.g services installed by anticheats, or you could simply enable them after building the scripts but the first method is recommended)

## Usage
- Download the latest release from the [releases tab](https://github.com/amitxv/Service-List-Builder/releases)

- Open lists.ini in a text editor

- You can import your service list seperated by new lines under the **[Automatic_Services]** and **[Manual_Services]** sections. Whatever services you do not specify under these fields will get disabled

- Additionally you can also import a list of drivers to be disabled seperated by new lines under the **[Drivers_To_Disable]** section. The "disable all except" logic does not apply here in contrast to the previous two sections

- Additionally you can include full folder paths or binaries (without quotes) to get renamed, so that they do not run, under the **[Toggle_Files_Folders]** section

- Additional notes:

  - All entries are case sensitive

  - This tool automatically handles driver filters for the following
  
    - EhStorClass
    - fvevol
    - iorate
    - rdyboost
    - ksthunk
    - volsnap

- Pass lists.ini as an argument to the program through the command-line with the command below to build the scripts

  ```bat
  service-list-builder --config "lists.ini"
  ```

- The scripts will be built in the **build** folder. [NSudo](https://github.com/M2Team/NSudo) is required to run the scripts with with **Enable All Privileges** checkbox enabled to prevent errors when writing to registry & renaming files

## Example

<img src="./img/lists.png" width="1000"> 