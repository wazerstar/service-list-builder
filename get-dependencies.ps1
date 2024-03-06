function main() {
    if (Test-Path ".\tmp\") {
        Remove-Item -Path ".\tmp\" -Recurse
    }

    $urls = @{
        "NSudo" = "https://github.com/M2TeamArchived/NSudo.git"
    }

    # =============
    # Setup MinSudo
    # =============
    git clone $urls["NSudo"] ".\tmp\NSudo\"
    Push-Location ".\tmp\NSudo\"

    # build MinSudo
    MSBuild.exe ".\Source\Native\NSudo.sln" -p:Configuration=Release -p:Platform=x64

    Pop-Location

    Copy-Item ".\tmp\NSudo\Source\Native\Output\Binaries\Release\x64\NSudoLG.exe" ".\service_list_builder\build"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
