function main() {
    # pack executable
    pyinstaller service_list_builder\main.py --onefile --name service-list-builder

    # create folder structure
    mkdir building\service-list-builder
    Move-Item dist\service-list-builder.exe building\service-list-builder
    Move-Item service_list_builder\build building\service-list-builder
    Move-Item service_list_builder\lists.ini building\service-list-builder

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
