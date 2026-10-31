# PDF para Markdown

Aplicativo de janela para Windows que converte PDFs em arquivos `.md` usando o [Microsoft MarkItDown](https://github.com/microsoft/markitdown). Inclui OCR local para páginas digitalizadas com [RapidOCR](https://github.com/RapidAI/RapidOCR) e [PyMuPDF](https://pymupdf.readthedocs.io/). Não precisa abrir o navegador.

## Iniciar

1. Instale Python 3.11 a 3.14.
2. Dê dois cliques em `run.bat`. Na primeira vez, o script cria um ambiente virtual e instala as dependências, incluindo os modelos de OCR.
3. Na janela, adicione um ou mais PDFs, escolha a pasta de destino e selecione o modo de OCR:
   - **Automático:** usa OCR em páginas com pouco ou nenhum texto selecionável; mantém o MarkItDown nas demais.
   - **Forçar OCR:** reconhece todas as páginas como imagem.
   - **Desativado:** usa somente a conversão padrão do MarkItDown.
4. Clique em **Converter PDFs**.
5. Selecione um arquivo convertido para visualizar o Markdown. Use **Abrir pasta** para acessar os `.md`.

Os PDFs e o OCR são processados localmente. O aplicativo não os envia a serviços externos e não guarda cópias deles. Um arquivo `.md` existente nunca é sobrescrito: o próximo ganha um sufixo numérico.

## Criar um executável

Dê dois cliques em `build_exe.bat`. Ele instala o PyInstaller no ambiente virtual e gera `dist\PDF-para-Markdown.exe`, incluindo os modelos de OCR. O `.exe` pode ser aberto sem Python instalado na máquina de destino. O arquivo será maior por conter os modelos e as bibliotecas de inferência.

O [workflow do GitHub Actions](.github/workflows/build-windows.yml) também testa a conversão real, gera o `.exe` no Windows e o disponibiliza como artefato da execução.

## Limitações

- O OCR de páginas digitalizadas gera texto simples; títulos e tabelas dessas páginas podem precisar de ajustes manuais no Markdown.
- PDFs protegidos por senha podem falhar.
- Documentos grandes podem consumir bastante memória durante a conversão.

## Testes

Após instalar as dependências:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
```

