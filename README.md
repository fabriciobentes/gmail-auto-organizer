# Gmail Auto Organizer

Automação pessoal para manter a Caixa de entrada limpa sem apagar mensagens importantes.

## O que ela faz

A cada 5 minutos, o GitHub Actions consulta o Gmail e procura mensagens que estejam:

- na Caixa de entrada;
- já lidas;
- com um dos marcadores configurados.

Quando encontra uma mensagem nessas condições, remove apenas o rótulo `INBOX`. Na prática, a mensagem é arquivada e continua disponível normalmente no respectivo marcador.

A automação **não exclui mensagens**, **não envia mensagens para a Lixeira** e **não remove os marcadores existentes**.

## Marcadores monitorados

- 99
- Âmbar
- Anhanguera
- Banco PAN
- ChatGPT
- Claro
- GitHub
- Google
- Gov
- IFAM
- Linkedin
- Mercado Livre
- Mercado Pago
- Motorola
- Netflix
- Nubank
- Shopee
- Uber

A lista pode ser alterada em `gmail_cleanup.py`.

## Arquivos

- `gmail_cleanup.py`: lógica principal da automação.
- `oauth_setup.py`: assistente local para gerar a autorização OAuth do Gmail.
- `requirements.txt`: dependências Python.
- `.github/workflows/gmail-cleanup.yml`: execução automática a cada 5 minutos.

## Configuração do Gmail

A automação usa a Gmail API com o escopo `gmail.modify`.

Você precisará criar um aplicativo OAuth no Google Cloud, baixar o arquivo `credentials.json` e executar uma única vez:

```bash
python oauth_setup.py
```

O script abrirá o navegador para você autorizar a conta Google e criará `token.json`.

Depois, copie todo o conteúdo de `token.json` para um secret do GitHub chamado:

```text
GMAIL_TOKEN_JSON
```

Caminho no GitHub:

`Settings > Secrets and variables > Actions > New repository secret`

O arquivo `token.json` e o `credentials.json` estão protegidos pelo `.gitignore` e nunca devem ser enviados ao repositório.

## Teste manual

Na aba **Actions**, abra o workflow **Gmail - Arquivar mensagens lidas** e use **Run workflow**.

Você pode executar com `dry_run=true` para apenas listar quantas mensagens seriam arquivadas sem modificar o Gmail.

## Execução automática

O workflow está configurado para:

```cron
*/5 * * * *
```

Isso significa aproximadamente uma execução a cada 5 minutos. O GitHub pode atrasar alguns minutos uma execução agendada em períodos de alta carga.

## Segurança

- O token OAuth fica somente em GitHub Actions Secrets.
- O script não contém senha do Gmail.
- O código não chama operações de exclusão ou Lixeira.
- A única alteração feita é remover o rótulo `INBOX` de mensagens já lidas e já classificadas.
