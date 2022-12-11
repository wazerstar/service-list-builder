# Service-List-Builder

Build scripts to toggle between minimal and default services in Windows based on user-defined lists

I am not responsible for damage caused to computer. This tool is powerful and for advanced users only. There is a risk of damaging your operating system if you disable core services that are required for Windows to function correctly. It is your responsibility to use suitable service configurations for your specific operating system. It is also recommended that you use this tool before installing any programs as any other services not defined in the lists will be disabled (e.g services installed by anticheats, or you could simply enable them after building the scripts but the first method is recommended).

## Usage and Program Logic

- Download the latest release from the [releases tab](https://github.com/amitxv/Service-List-Builder/releases)

- Open **lists.ini** in a text editor

    - Note: All entries are case sensitive

    - Every user mode service **NOT** specified in the **[Automatic_Services]** and **[Manual_Services]** sections will get disabled. These two sections act as whitelist of user mode services **NOT** to disable.

    - Kernel mode services to disable can be explicitly specified in the **[Drivers_To_Disable]** section. This section does not follow the "disable all except" logic. Only the kernel mode services specified in this section will get disabled

    - Paths to folders or binaries can be specified in the **[Toggle_Files_Folders]** section. The logic behind this is that when a binary gets renamed to anything other than its original file name, it will not run. Avoid folders and binaries with ``#`` in the name due to conflict with inline comments

- Pass **lists.ini** as an argument to the program through the command-line with the command below to build the scripts

  ```bat
  service-list-builder --config "lists.ini"
  ```

- The scripts will be built in the **build** folder. [NSudo](https://github.com/M2Team/NSudo) is required to run the scripts with with **Enable All Privileges** checkbox enabled to prevent errors when writing to registry and renaming files

## Example

<img src="./img/lists.png" width="1000">
