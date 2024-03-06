function main() {
    # pack executable
    pyinstaller ".\service_list_builder\main.py" --onefile --name service-list-builder

    if (Test-Path ".\build\") {
        Remove-Item -Path ".\build\" -Recurse
    }

    # create folder structure
    New-Item -ItemType Directory -Path ".\build\service-list-builder\"

    # create final package
    Move-Item ".\dist\service-list-builder.exe" ".\build\service-list-builder\"
    Move-Item ".\service_list_builder\build\" ".\build\service-list-builder\"
    Move-Item ".\service_list_builder\lists.ini" ".\build\service-list-builder\"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
