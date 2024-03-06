function main() {
    if (Test-Path ".\build\") {
        Remove-Item -Path ".\build\" -Recurse
    }

    # create folder structure
    New-Item -ItemType Directory -Path ".\build\service-list-builder\"

    # pack executable
    New-Item -ItemType Directory -Path ".\build\pyinstaller\"
    Push-Location ".\build\pyinstaller\"
    pyinstaller "..\..\service_list_builder\main.py" --onefile --name service-list-builder
    Pop-Location


    # create final package
    Copy-Item ".\build\pyinstaller\dist\service-list-builder.exe" ".\build\service-list-builder\"
    Copy-Item ".\service_list_builder\build\" ".\build\service-list-builder\" -Recurse
    Copy-Item ".\service_list_builder\lists.ini" ".\build\service-list-builder\"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
