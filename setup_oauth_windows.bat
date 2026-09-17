@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo Gmail Auto Organizer - Configuracao OAuth
 echo ==============================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao foi encontrado.
    echo Instale o Python 3.10 ou superior e marque a opcao para adicionar ao PATH.
    echo Depois execute este arquivo novamente.
    pause
    exit /b 1
)

if not exist "credentials.json" (
    echo ERRO: O arquivo credentials.json nao esta nesta pasta.
    echo Baixe a credencial OAuth do Google Cloud e salve-a aqui com o nome credentials.json.
    pause
    exit /b 1
)

echo Instalando dependencias necessarias...
py -m pip install --upgrade pip
if errorlevel 1 goto :erro

py -m pip install -r requirements.txt
if errorlevel 1 goto :erro

echo.
echo Abrindo autorizacao do Google no navegador...
py oauth_setup.py
if errorlevel 1 goto :erro

if exist "token.json" (
    echo.
    echo ==============================================
    echo SUCESSO: token.json foi criado.
    echo Nao envie esse arquivo para o repositorio.
    echo O proximo passo sera copia-lo para o secret
    echo GMAIL_TOKEN_JSON no GitHub Actions.
    echo ==============================================
) else (
    echo ERRO: token.json nao foi criado.
)

pause
exit /b 0

:erro
echo.
echo Ocorreu um erro durante a configuracao.
pause
exit /b 1
