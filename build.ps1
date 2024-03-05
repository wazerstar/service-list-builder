function main() {
    # pack executable
    pyinstaller service_list_builder\main.py --onefile --name service-list-builder

    if (Test-Path "building") {
        Remove-Item -Path "building" -Recurse
    }

    # create folder structure
    New-Item -ItemType Directory -Path building\service-list-builder
    Move-Item dist\service-list-builder.exe building\service-list-builder
    Move-Item service_list_builder\build building\service-list-builder
    Move-Item service_list_builder\lists.ini building\service-list-builder

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
