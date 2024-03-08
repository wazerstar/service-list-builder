function Is-Admin() {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function main() {
    if (-not (Is-Admin)) {
        Write-Host "error: administrator privileges required"
        return 1
    }

    if (Test-Path ".\tmp\") {
        Remove-Item -Path ".\tmp\" -Recurse -Force
    }

    mkdir ".\tmp\"

    $urls = @{
        "NSudo" = "https://github.com/M2TeamArchived/NSudo.git"
    }

    # ===========
    # Setup NSudo
    # ===========

    # clone NSudo repo
    git clone $urls["NSudo"] ".\tmp\NSudo\"

    # build binaries
    MSBuild.exe ".\tmp\NSudo\Source\Native\NSudo.sln" -p:Configuration=Release -p:Platform=x64

    # copy binary to service_list_builder project directory
    Copy-Item ".\tmp\NSudo\Source\Native\Output\Binaries\Release\x64\NSudoLG.exe" ".\service_list_builder\"

    return 0
}

$_exitCode = main
Write-Host # new line
exit $_exitCode
