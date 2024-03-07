function main() {
    if (Test-Path ".\tmp\") {
        Remove-Item -Path ".\tmp\" -Recurse -Force
    }

    $urls = @{
        "NSudo" = "https://github.com/M2TeamArchived/NSudo.git"
    }

    # =============
    # Setup NSudo
    # =============
    git clone $urls["NSudo"] ".\tmp\NSudo\"
    Push-Location ".\tmp\NSudo\"

    # build NSudo
    MSBuild.exe ".\Source\Native\NSudo.sln" -p:Configuration=Release -p:Platform=x64

    Pop-Location

    Copy-Item ".\tmp\NSudo\Source\Native\Output\Binaries\Release\x64\NSudoLG.exe" ".\service_list_builder\"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
