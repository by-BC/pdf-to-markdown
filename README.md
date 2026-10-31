# PDF para Markdown

Aplicativo de janela para Windows que converte PDFs em arquivos `.md` usando o [Microsoft MarkItDown](https://github.com/microsoft/markitdown). Não precisa abrir o navegador.

## Iniciar

1. Instale Python 3.10 a 3.14.
2. Dê dois cliques em `run.bat`. Na primeira vez, o script cria um ambiente virtual e instala o MarkItDown.
3. Na janela, adicione um ou mais PDFs, escolha a pasta de destino e clique em **Converter PDFs**.
4. Selecione um arquivo convertido para visualizar o Markdown. Use **Abrir pasta** para acessar os `.md`.

Os PDFs são lidos localmente. O aplicativo não os envia a serviços externos e não guarda cópias deles. Um arquivo `.md` existente nunca é sobrescrito: o próximo ganha um sufixo numérico.

## Criar um executável

Dê dois cliques em `build_exe.bat`. Ele instala o PyInstaller no ambiente virtual e gera `dist\PDF-para-Markdown.exe`. O `.exe` pode ser aberto sem Python instalado na máquina de destino.

## Limitações

- A conversão padrão extrai texto. PDFs digitalizados só com imagens podem precisar de OCR.
- PDFs protegidos por senha podem falhar.
- Documentos grandes podem consumir bastante memória durante a conversão.

## Testes

Após instalar as dependências:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```

